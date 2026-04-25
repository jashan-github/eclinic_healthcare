"""
Payment Service
Handles Sentoo payment creation and webhook processing

PAYMENT FLOW:
1. Patient initializes payment -> Creates payment record with 15 min expiry
2. Patient completes payment on Sentoo
3. Either:
   a) Success redirect -> Verify status from API -> Create appointment if paid
   b) Webhook received -> Verify status from API -> Create appointment if paid
4. Both paths check for existing appointment to prevent duplicates
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from loguru import logger
from datetime import datetime, timezone, timedelta, date as date_type

from app.models.appointment_request import AppointmentRequest
from app.models.appointment_payment import AppointmentPayment
from app.models.appointment import Appointment
from app.models.user import User
from app.models.service import Service
from app.services.audit_service import AuditService
from app.core.security import CurrentUser, UserRole
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException
)
from app.utils.notification_helper import send_payment_success_notification
from app.utils.sentoo_client import SentooClient
from app.utils.waiver_helper import apply_waiver_for_request
from app.services.service_commission_service import set_payment_commission
from app.core.config import settings
from app.core.security import ConsultationMode, create_access_token, UserRole
import httpx
import asyncio
import threading


# Payment expiry time in minutes
PAYMENT_EXPIRY_MINUTES = 15


class PaymentService:
    """Service for payment operations using Sentoo"""
    
    def __init__(self, db: Session, sentoo_merchant_id: Optional[str] = None, sentoo_merchant_secret: Optional[str] = None):
        """Initialize payment service"""
        self.db = db
        self.audit_service = AuditService(db)
        
        # Initialize Sentoo client
        if sentoo_merchant_id and sentoo_merchant_secret:
            from app.core.config import settings
            self.sentoo_client = SentooClient(
                merchant_id=sentoo_merchant_id,
                merchant_secret=sentoo_merchant_secret,
                api_url=settings.SENTOO_API_URL
            )
        else:
            from app.core.config import settings
            if settings.SENTOO_MERCHANT_ID and settings.SENTOO_MERCHANT_SECRET:
                self.sentoo_client = SentooClient(
                    merchant_id=settings.SENTOO_MERCHANT_ID,
                    merchant_secret=settings.SENTOO_MERCHANT_SECRET,
                    api_url=settings.SENTOO_API_URL
                )
            else:
                logger.warning("Sentoo credentials not configured")
                self.sentoo_client = None
    
    def _create_appointment_from_request(self, request: AppointmentRequest, payment: AppointmentPayment) -> Appointment:
        """
        Create appointment from appointment request
        
        This is the SINGLE place where appointments are created from payments.
        Both webhook and success redirect call this method.
        
        Returns:
            Created appointment or existing appointment if already exists
        """
        # Check if appointment already exists (idempotency)
        existing_appointment = self.db.query(Appointment).filter(
            Appointment.doctor_id == request.doctor_id,
            Appointment.patient_id == request.patient_id,
            Appointment.appointment_date == request.preferred_date,
            Appointment.start_time == request.preferred_time,
            Appointment.deleted_at.is_(None)
        ).first()
        
        if existing_appointment:
            logger.info(f"Appointment already exists: {existing_appointment.id}")
            return existing_appointment
        
        # Calculate end_time
        start_datetime = datetime.combine(request.preferred_date, request.preferred_time)
        end_datetime = start_datetime + timedelta(minutes=request.duration_minutes)
        end_time = end_datetime.time()
        
        # Create appointment
        appointment = Appointment(
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            service_id=request.service_id,
            clinic_id=request.clinic_id,
            doctor_service_availability_id=request.doctor_service_availability_id,
            appointment_date=request.preferred_date,
            start_time=request.preferred_time,
            end_time=end_time,
            status='CONFIRMED',
            consultation_mode=request.consultation_mode,
            duration_minutes=request.duration_minutes,
            price_amount=payment.amount,
            currency=request.currency,
            pricing_source=request.pricing_source
        )
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        logger.info(f"Created appointment {appointment.id} for payment {payment.id}")
        
        # Create video session automatically for teleconsultation appointments
        logger.info(
            f"Checking consultation_mode for appointment {appointment.id}: "
            f"request.consultation_mode='{request.consultation_mode}', "
            f"TELECONSULTATION.value='{ConsultationMode.TELECONSULTATION.value}'"
        )
        
        if request.consultation_mode == ConsultationMode.TELECONSULTATION.value:
            logger.info(f"Consultation mode is TELECONSULTATION, creating video session for appointment {appointment.id}")
            try:
                self._create_video_session_for_appointment(appointment, request)
            except Exception as e:
                # Log error but don't fail appointment creation
                logger.error(
                    f"Failed to create video session for appointment {appointment.id}: {str(e)}",
                    exc_info=True
                )
        else:
            logger.info(
                f"Skipping video session creation for appointment {appointment.id}: "
                f"consultation_mode='{request.consultation_mode}' is not TELECONSULTATION"
            )
        
        return appointment
    
    def _create_video_session_for_appointment(
        self,
        appointment: Appointment,
        request: AppointmentRequest
    ) -> None:
        """
        Create video session for teleconsultation appointment
        
        Makes HTTP request to webinar-service to create video session.
        Errors are logged but don't fail appointment creation.
        """
        from datetime import datetime, timezone as tz
        
        # Calculate scheduled times
        # Combine appointment date and start time
        scheduled_start_time = datetime.combine(
            appointment.appointment_date,
            appointment.start_time
        )
        
        # Add duration to get end time
        scheduled_end_time = scheduled_start_time + timedelta(minutes=appointment.duration_minutes)
        
        # Make timezone-aware (use UTC for consistency)
        scheduled_start_time = scheduled_start_time.replace(tzinfo=tz.utc)
        scheduled_end_time = scheduled_end_time.replace(tzinfo=tz.utc)
        
        # Get webinar service URL from config or use default
        webinar_service_url = getattr(settings, 'WEBINAR_SERVICE_URL', 'http://webinar-service:8002')
        if not webinar_service_url.startswith('http'):
            webinar_service_url = f"http://{webinar_service_url}"
        
        # Remove trailing slash
        webinar_service_url = webinar_service_url.rstrip('/')
        
        # Create video session via HTTP request
        # Note: ROOT_PATH is only for reverse proxy routing. When calling directly between services,
        # we should NOT include ROOT_PATH in the URL
        create_session_url = f"{webinar_service_url}/api/v1/video-sessions"
        
        # Fetch doctor and patient names for channel label (DoctorName_PatientName_YYYYMMDD_HHmm)
        doctor = self.db.query(User).filter(User.id == appointment.doctor_id).first()
        patient = self.db.query(User).filter(User.id == appointment.patient_id).first()
        doctor_display_name = (doctor.name if doctor else "Doctor").strip() or "Doctor"
        patient_display_name = (patient.name if patient else "Patient").strip() or "Patient"

        # Prepare request payload
        # Note: doctor_id is extracted from JWT token (current_user["id"])
        payload = {
            "patient_id": str(appointment.patient_id),
            "appointment_id": str(appointment.id),
            "session_type": "appointment",  # lowercase as per schema
            "scheduled_start_time": scheduled_start_time.isoformat(),
            "scheduled_end_time": scheduled_end_time.isoformat(),
            "recording_enabled": False,
            "doctor_display_name": doctor_display_name,
            "patient_display_name": patient_display_name,
        }
        
        logger.info(
            f"Creating video session for appointment {appointment.id} "
            f"via {create_session_url}"
        )
        
        try:
            # Generate JWT token for doctor to authenticate the request
            # The webinar service will validate this token
            token_data = {
                "sub": str(appointment.doctor_id),
                "user_id": str(appointment.doctor_id),
                "role": UserRole.DOCTOR.value,
                "clinic_id": str(appointment.clinic_id) if appointment.clinic_id else None
            }
            access_token = create_access_token(data=token_data)
            
            # Make HTTP request to webinar-service
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    create_session_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}"
                    }
                )
                
                if response.status_code == 201:
                    result = response.json()
                    if result.get("success"):
                        session_id = result.get("data", {}).get("session_id")
                        logger.info(
                            f"✓ Video session created successfully for appointment {appointment.id}: "
                            f"session_id={session_id}"
                        )
                    else:
                        logger.warning(
                            f"Video session creation returned success=False for appointment {appointment.id}: "
                            f"{result.get('message', 'Unknown error')}"
                        )
                else:
                    logger.error(
                        f"Failed to create video session for appointment {appointment.id}: "
                        f"HTTP {response.status_code} - {response.text}"
                    )
        except httpx.TimeoutException:
            logger.error(
                f"Timeout creating video session for appointment {appointment.id}: "
                f"webinar-service did not respond within 10 seconds"
            )
        except httpx.RequestError as e:
            logger.error(
                f"Request error creating video session for appointment {appointment.id}: {str(e)}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error creating video session for appointment {appointment.id}: {str(e)}",
                exc_info=True
            )
        
        # Send notification (email + WhatsApp) in a thread with its own DB session (session not thread-safe)
        from app.core.database import SessionLocal
        patient_id = str(appointment.patient_id)
        doctor_id = str(appointment.doctor_id)
        appointment_id_str = str(appointment.id)
        appointment_date_str = str(appointment.appointment_date)
        appointment_time_str = str(appointment.start_time)
        amount = float(payment.amount)
        curr = payment.currency

        def _run_notification():
            db = SessionLocal()
            try:
                asyncio.run(send_payment_success_notification(
                    db=db,
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    appointment_id=appointment_id_str,
                    appointment_date=appointment_date_str,
                    appointment_time=appointment_time_str,
                    payment_amount=amount,
                    currency=curr,
                ))
            except Exception as e:
                logger.error(f"Failed to send payment success notification: {str(e)}")
            finally:
                db.close()
        try:
            threading.Thread(target=_run_notification, daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to start payment success notification thread: {str(e)}")
        
        return appointment
    
    def _complete_payment_and_create_appointment(
        self,
        payment: AppointmentPayment,
        transaction_id: str,
        source: str = "api"
    ) -> Dict[str, Any]:
        """
        Complete payment and create appointment
        
        This is called when payment is confirmed as successful.
        Handles idempotency - safe to call multiple times.
        
        Args:
            payment: Payment record
            transaction_id: Sentoo transaction ID
            source: Source of completion (api, webhook, redirect)
            
        Returns:
            Result dict with appointment_id
        """
        # Get appointment request
        request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.id == payment.appointment_request_id
        ).first()
        
        if not request:
            logger.error(f"Appointment request not found: {payment.appointment_request_id}")
            return {"status": "error", "message": "Appointment request not found"}
        
        # Update payment status if not already completed
        old_status = payment.status
        if payment.status != 'COMPLETED':
            payment.status = 'COMPLETED'
            payment.sentoo_webhook_id = transaction_id
            payment.webhook_received_at = datetime.now(timezone.utc)
            set_payment_commission(self.db, payment)  # only upcoming: lock commission at completion
            self.db.commit()
            logger.info(f"Payment {payment.id} status updated from {old_status} to COMPLETED")
        
        # Create appointment (handles idempotency internally)
        appointment = self._create_appointment_from_request(request, payment)
        
        # Audit log
        self.audit_service.create_audit_log(
            actor_user_id=None,
            action="PAYMENT_COMPLETED",
            entity_type="appointment_payment",
            entity_id=payment.id,
            audit_metadata={
                "appointment_request_id": str(request.id),
                "appointment_id": str(appointment.id),
                "old_status": old_status,
                "new_status": "COMPLETED",
                "transaction_id": transaction_id,
                "source": source
            }
        )
        
        return {
            "status": "success",
            "appointment_id": str(appointment.id),
            "payment_status": "COMPLETED"
        }
    
    def initialize_payment(
        self,
        current_user: CurrentUser,
        request_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize Sentoo payment for an accepted appointment request
        
        Payment expires after 15 minutes.
        """
        # Get appointment request
        request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.id == request_id
        ).first()
        
        if not request:
            raise NotFoundException(
                message="Appointment request not found",
                errors={"request_id": ["Appointment request with this ID does not exist"]}
            )
        
        # Check user has access (must be the patient)
        if not current_user.has_role(UserRole.PATIENT):
            raise ForbiddenException(
                message="Access denied",
                errors={"access": [f"Only patients can initialize payment. Your role: {current_user.role}"]}
            )
        
        if str(current_user.id) != str(request.patient_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"access": ["You can only initialize payment for your own appointments"]}
            )
        
        # Check request status is ACCEPTED
        if request.status != 'ACCEPTED':
            raise BadRequestException(
                message="Cannot initialize payment",
                errors={"status": ["Appointment request must be ACCEPTED before payment"]}
            )
        
        # Original amount and waiver (compute once so we can reuse for existing-payment check)
        if request.price_amount is None or request.price_amount < 0:
            raise BadRequestException(
                message="Invalid payment amount",
                errors={"amount": ["Payment amount must be set and non-negative"]}
            )
        original_amount = request.price_amount if isinstance(request.price_amount, Decimal) else Decimal(str(request.price_amount))
        amount_after_waiver, waiver_percent, skip_payment_gateway = apply_waiver_for_request(
            self.db, original_amount, getattr(request, "waiver_percent", None)
        )
        
        # Check if payment already exists
        existing_payment = self.db.query(AppointmentPayment).filter(
            AppointmentPayment.appointment_request_id == request_id
        ).first()
        
        if existing_payment:
            # If payment is COMPLETED, ensure appointment exists
            if existing_payment.status == 'COMPLETED':
                logger.info(f"Payment {existing_payment.id} is already COMPLETED")
                
                # Ensure appointment exists
                appointment = self._create_appointment_from_request(request, existing_payment)
                
                return {
                    "payment_id": str(existing_payment.id),
                    "sentoo_payment_id": existing_payment.sentoo_payment_id,
                    "payment_url": existing_payment.payment_url,
                    "amount": float(existing_payment.amount),
                    "currency": existing_payment.currency,
                    "status": existing_payment.status,
                    "appointment_id": str(appointment.id),
                    "appointment_created": True
                }
            
            # Re-use existing PENDING only if amount matches current waiver (avoid returning old full-amount payment)
            existing_amount = existing_payment.amount if existing_payment.amount is not None else Decimal("-1")
            amount_matches = (existing_amount == amount_after_waiver)
            is_expired = False
            if existing_payment.created_at:
                expiry_time = existing_payment.created_at + timedelta(minutes=PAYMENT_EXPIRY_MINUTES)
                is_expired = datetime.now(timezone.utc) > expiry_time.replace(tzinfo=timezone.utc)
                if is_expired:
                    existing_payment.status = 'EXPIRED'
                    self.db.commit()
            
            # Return existing only if amount matches waiver, has URL, and not expired
            if amount_matches and existing_payment.payment_url and not is_expired and existing_payment.created_at:
                expiry_time = existing_payment.created_at + timedelta(minutes=PAYMENT_EXPIRY_MINUTES)
                return {
                    "payment_id": str(existing_payment.id),
                    "sentoo_payment_id": existing_payment.sentoo_payment_id,
                    "payment_url": existing_payment.payment_url,
                    "amount": float(existing_payment.amount),
                    "currency": existing_payment.currency,
                    "status": existing_payment.status,
                    "expires_at": expiry_time.isoformat()
                }
            
            # Amount mismatch (e.g. waiver changed), expired, or no URL: delete and create new with current waiver
            if not amount_matches:
                logger.info(f"Existing payment amount {existing_amount} != waived amount {amount_after_waiver}, recreating payment")
            else:
                logger.info(f"Deleting incomplete/expired payment {existing_payment.id}")
            self.db.delete(existing_payment)
            self.db.commit()

        # 100% waiver: create COMPLETED payment with amount=0, create appointment, no gateway redirect
        if skip_payment_gateway:
            request.waiver_percent = waiver_percent
            self.db.commit()
            payment = AppointmentPayment(
                appointment_request_id=request_id,
                sentoo_payment_id=None,
                payment_url=None,
                amount=Decimal("0"),
                currency=request.currency or "XCD",
                status="COMPLETED",
                waiver_percent=waiver_percent,
                amount_before_waiver=original_amount,
                idempotency_key=f"{request_id}_waiver_100",
            )
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            set_payment_commission(self.db, payment)
            appointment = self._create_appointment_from_request(request, payment)
            self.audit_service.create_audit_log(
                actor_user_id=current_user.id,
                action="PAYMENT_WAIVER_100",
                entity_type="appointment_payment",
                entity_id=payment.id,
                audit_metadata={
                    "appointment_request_id": str(request_id),
                    "waiver_percent": waiver_percent,
                    "amount_before_waiver": float(original_amount),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return {
                "payment_id": str(payment.id),
                "sentoo_payment_id": None,
                "payment_url": None,
                "amount": 0.0,
                "currency": payment.currency,
                "status": "COMPLETED",
                "waiver_applied": True,
                "waiver_percent": waiver_percent,
                "amount_before_waiver": float(original_amount),
                "appointment_id": str(appointment.id),
                "appointment_created": True,
            }

        # Check Sentoo client is configured
        if not self.sentoo_client:
            raise BadRequestException(
                message="Payment service not configured",
                errors={"payment": ["Sentoo payment gateway is not configured"]}
            )
        
        # Create Sentoo payment
        try:
            from app.core.config import settings
            
            base_url = settings.BASE_URL.rstrip('/')
            return_url = f"{base_url}/api/v1/patient/appointments/payment-success?payment_id={str(request_id)}"
            cancel_url = f"{base_url}/api/v1/patient/appointments/payment-cancelled?payment_id={str(request_id)}"
            description = f"Appointment payment - Request {str(request_id)[:8]}"
            
            sentoo_response = self.sentoo_client.create_payment(
                amount=amount_after_waiver,
                currency="XCG",
                reference_id=str(request_id),
                return_url=return_url,
                cancel_url=cancel_url,
                description=description,
                metadata={
                    "appointment_request_id": str(request_id),
                    "doctor_id": str(request.doctor_id),
                    "patient_id": str(request.patient_id)
                }
            )
            
            logger.info(f"Sentoo response: {sentoo_response}")
            
        except Exception as e:
            logger.error(f"Sentoo payment creation failed: {str(e)}", exc_info=True)
            raise BadRequestException(
                message="Payment initialization failed",
                errors={"payment": [f"Unable to initialize payment: {str(e)}"]}
            )
        
        # Parse Sentoo response
        sentoo_payment_id = None
        payment_url = None
        qr_code = None
        
        try:
            if isinstance(sentoo_response, dict) and 'success' in sentoo_response:
                success_obj = sentoo_response['success']
                if isinstance(success_obj, dict):
                    sentoo_payment_id = success_obj.get('message')
                    data_obj = success_obj.get('data', {})
                    if isinstance(data_obj, dict):
                        payment_url = data_obj.get('url')
                        qr_code = data_obj.get('qr_code')
        except Exception as e:
            logger.error(f"Error parsing Sentoo response: {str(e)}")
        
        # Create payment record with expiry
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=PAYMENT_EXPIRY_MINUTES)
        
        request.waiver_percent = waiver_percent
        payment = AppointmentPayment(
            appointment_request_id=request_id,
            sentoo_payment_id=sentoo_payment_id,
            payment_url=payment_url,
            amount=amount_after_waiver,
            currency="XCG",
            status='PENDING',
            waiver_percent=waiver_percent,
            amount_before_waiver=original_amount,
            idempotency_key=f"{request_id}_{sentoo_payment_id}" if sentoo_payment_id else f"{request_id}_pending"
        )
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        # Audit log
        self.audit_service.create_audit_log(
            actor_user_id=current_user.id,
            action="PAYMENT_INITIALIZED",
            entity_type="appointment_payment",
            entity_id=payment.id,
            audit_metadata={
                "appointment_request_id": str(request_id),
                "amount": float(amount_after_waiver),
                "amount_before_waiver": float(original_amount),
                "waiver_percent": waiver_percent,
                "currency": "XCG",
                "expires_at": expiry_time.isoformat()
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Payment initialized: {payment.id}, expires at {expiry_time}")
        
        return {
            "payment_id": str(payment.id),
            "sentoo_payment_id": payment.sentoo_payment_id,
            "payment_url": payment.payment_url,
            "qr_code": qr_code,
            "amount": float(payment.amount),
            "currency": payment.currency,
            "status": payment.status,
            "waiver_percent": payment.waiver_percent,
            "amount_before_waiver": float(payment.amount_before_waiver) if payment.amount_before_waiver is not None else None,
            "expires_at": expiry_time.isoformat()
        }
    
    def verify_and_complete_payment(
        self,
        current_user: CurrentUser,
        payment_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify payment status from Sentoo API and complete if paid
        
        Called after patient returns from Sentoo payment page.
        """
        # Get payment record
        payment = self.db.query(AppointmentPayment).filter(
            AppointmentPayment.id == payment_id
        ).first()
        
        if not payment:
            raise NotFoundException(
                message="Payment not found",
                errors={"payment_id": ["Payment with this ID does not exist"]}
            )
        
        # Get appointment request
        request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.id == payment.appointment_request_id
        ).first()
        
        if not request:
            raise NotFoundException(
                message="Appointment request not found",
                errors={"request_id": ["Associated appointment request not found"]}
            )
        
        # Check user has access
        if str(current_user.id) != str(request.patient_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"access": ["You can only verify payment for your own appointments"]}
            )
        
        # If payment is already completed, ensure appointment exists
        if payment.status == 'COMPLETED':
            appointment = self._create_appointment_from_request(request, payment)
            return {
                "status": "success",
                "payment_status": "COMPLETED",
                "is_paid": True,
                "appointment_id": str(appointment.id),
                "message": "Payment completed. Appointment confirmed."
            }
        
        # Check Sentoo client
        if not self.sentoo_client:
            raise BadRequestException(
                message="Payment service not configured",
                errors={"payment": ["Sentoo payment gateway is not configured"]}
            )
        
        # Check sentoo_payment_id exists
        if not payment.sentoo_payment_id:
            raise BadRequestException(
                message="Payment not initialized",
                errors={"payment": ["This payment was not properly initialized"]}
            )
        
        # Verify status from Sentoo API
        logger.info(f"Verifying payment {payment.id} with Sentoo (transaction: {payment.sentoo_payment_id})")
        
        try:
            sentoo_status = self.sentoo_client.verify_transaction_status(payment.sentoo_payment_id)
            logger.info(f"Sentoo status response: {sentoo_status}")
        except Exception as e:
            logger.error(f"Failed to verify Sentoo payment: {str(e)}", exc_info=True)
            raise BadRequestException(
                message="Unable to verify payment status",
                errors={"payment": [f"Could not verify payment: {str(e)}"]}
            )
        
        # Extract status
        api_status = sentoo_status.get('status', 'UNKNOWN')
        is_paid = sentoo_status.get('is_paid', False)
        
        # Map status
        status_mapping = {
            'COMPLETED': 'COMPLETED',
            'SUCCEEDED': 'COMPLETED',
            'PAID': 'COMPLETED',
            'PENDING': 'PENDING',
            'PROCESSING': 'PENDING',
            'FAILED': 'FAILED',
            'CANCELLED': 'CANCELLED',
            'EXPIRED': 'EXPIRED'
        }
        
        new_status = status_mapping.get(api_status.upper(), 'PENDING')
        
        # If paid, complete payment and create appointment
        if is_paid or new_status == 'COMPLETED':
            result = self._complete_payment_and_create_appointment(
                payment=payment,
                transaction_id=payment.sentoo_payment_id,
                source="verify"
            )
            return {
                "status": "success",
                "payment_status": "COMPLETED",
                "is_paid": True,
                "appointment_id": result.get("appointment_id"),
                "message": "Payment verified. Appointment confirmed."
            }
        
        # Update status if changed
        if payment.status != new_status:
            old_status = payment.status
            payment.status = new_status
            self.db.commit()
            logger.info(f"Payment {payment.id} status updated: {old_status} -> {new_status}")
        
        return {
            "status": "pending",
            "payment_status": new_status,
            "is_paid": False,
            "message": f"Payment status: {new_status}"
        }
    
    def process_webhook_by_transaction_id(
        self,
        transaction_id: str,
        webhook_id: str
    ) -> Dict[str, Any]:
        """
        Process Sentoo webhook by transaction_id
        
        IMPORTANT: Always fetch status from Sentoo API, not from webhook payload.
        Creates appointment if payment is successful.
        
        Returns:
            Processing result with appointment_id if created
        """
        logger.info(f"Processing webhook for transaction: {transaction_id}")
        
        # Find payment
        payment = self.db.query(AppointmentPayment).filter(
            AppointmentPayment.sentoo_payment_id == transaction_id
        ).first()
        
        if not payment:
            logger.warning(f"Payment not found for transaction: {transaction_id}")
            return {"status": "payment_not_found"}
        
        # Check if already processed (idempotency)
        if payment.status == 'COMPLETED' and payment.sentoo_webhook_id == transaction_id:
            logger.info(f"Webhook already processed for transaction: {transaction_id}")
            
            # Ensure appointment exists
            request = self.db.query(AppointmentRequest).filter(
                AppointmentRequest.id == payment.appointment_request_id
            ).first()
            
            if request:
                appointment = self._create_appointment_from_request(request, payment)
                return {
                    "status": "already_processed",
                    "appointment_id": str(appointment.id)
                }
            
            return {"status": "already_processed"}
        
        # Fetch status from Sentoo API
        try:
            sentoo_status = self.sentoo_client.verify_transaction_status(transaction_id)
            logger.info(f"Sentoo API status: {sentoo_status}")
        except Exception as e:
            logger.error(f"Failed to fetch status from Sentoo: {str(e)}", exc_info=True)
            return {"status": "api_error", "message": str(e)}
        
        # Extract status
        api_status = sentoo_status.get('status', 'UNKNOWN')
        is_paid = sentoo_status.get('is_paid', False)
        
        logger.info(f"Transaction {transaction_id}: status={api_status}, is_paid={is_paid}")
        
        # If paid, complete payment and create appointment
        if is_paid or api_status.upper() in ['COMPLETED', 'SUCCEEDED', 'PAID']:
            result = self._complete_payment_and_create_appointment(
                payment=payment,
                transaction_id=transaction_id,
                source="webhook"
            )
            logger.info(f"Webhook processed successfully: appointment={result.get('appointment_id')}")
            return result
        
        # Handle failed/cancelled
        if api_status.upper() in ['FAILED']:
            payment.status = 'FAILED'
            payment.sentoo_webhook_id = transaction_id
            payment.webhook_received_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.info(f"Payment {payment.id} marked as FAILED")
            return {"status": "payment_failed"}
        
        if api_status.upper() in ['CANCELLED', 'CANCELED']:
            payment.status = 'CANCELLED'
            payment.sentoo_webhook_id = transaction_id
            payment.webhook_received_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.info(f"Payment {payment.id} marked as CANCELLED")
            return {"status": "payment_cancelled"}
        
        # Update status for pending/processing
        old_status = payment.status
        payment.status = api_status.upper()
        payment.sentoo_webhook_id = transaction_id
        self.db.commit()
        logger.info(f"Payment {payment.id} status updated: {old_status} -> {api_status}")
        
        return {"status": "updated", "payment_status": api_status}
    
    def process_payment_success_redirect(
        self,
        payment: AppointmentPayment,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process payment success redirect
        
        Called when user is redirected back from Sentoo.
        Verifies status from API and creates appointment if paid.
        
        Returns:
            Result with is_paid flag and appointment_id if created
        """
        if not payment.sentoo_payment_id:
            logger.warning(f"Payment {payment.id} has no sentoo_payment_id")
            return {"is_paid": False, "status": payment.status}
        
        # If already completed, ensure appointment exists
        if payment.status == 'COMPLETED':
            request = db.query(AppointmentRequest).filter(
                AppointmentRequest.id == payment.appointment_request_id
            ).first()
            
            if request:
                appointment = self._create_appointment_from_request(request, payment)
                return {
                    "is_paid": True,
                    "status": "COMPLETED",
                    "appointment_id": str(appointment.id)
                }
            
            return {"is_paid": True, "status": "COMPLETED"}
        
        # Verify status from Sentoo API
        try:
            sentoo_status = self.sentoo_client.verify_transaction_status(payment.sentoo_payment_id)
            logger.info(f"Redirect verification - Sentoo status: {sentoo_status}")
        except Exception as e:
            logger.error(f"Failed to verify payment on redirect: {str(e)}", exc_info=True)
            return {"is_paid": False, "status": payment.status, "error": str(e)}
        
        api_status = sentoo_status.get('status', 'UNKNOWN')
        is_paid = sentoo_status.get('is_paid', False)
        
        # If paid, complete and create appointment
        if is_paid or api_status.upper() in ['COMPLETED', 'SUCCEEDED', 'PAID']:
            result = self._complete_payment_and_create_appointment(
                payment=payment,
                transaction_id=payment.sentoo_payment_id,
                source="redirect"
            )
            return {
                "is_paid": True,
                "status": "COMPLETED",
                "appointment_id": result.get("appointment_id")
            }
        
        # Update status
        status_mapping = {
            'PENDING': 'PENDING',
            'PROCESSING': 'PENDING',
            'FAILED': 'FAILED',
            'CANCELLED': 'CANCELLED',
            'CANCELED': 'CANCELLED'
        }
        
        new_status = status_mapping.get(api_status.upper(), 'PENDING')
        if payment.status != new_status:
            payment.status = new_status
            self.db.commit()
        
        return {"is_paid": False, "status": new_status}
    
    def _doctor_payments_date_range(
        self,
        period: Optional[str],
        date_from: Optional[date_type],
        date_to: Optional[date_type]
    ) -> Optional[tuple]:
        """Return (start_dt, end_dt, prev_start_dt, prev_end_dt) in UTC for period; None when period is None."""
        if not period:
            return None
        now = datetime.now(timezone.utc)
        if period == "week":
            days_since_monday = now.weekday()
            start_this_week = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_this_week = start_this_week + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
            prev_start = start_this_week - timedelta(days=7)
            prev_end = start_this_week - timedelta(microseconds=1)
            return (start_this_week, end_this_week, prev_start, prev_end)
        if period == "month":
            start_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                next_first = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                next_first = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_this_month = next_first - timedelta(microseconds=1)
            if now.month == 1:
                prev_first = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                prev_first = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            prev_end = start_this_month - timedelta(microseconds=1)
            return (start_this_month, end_this_month, prev_first, prev_end)
        if period == "custom" and date_from is not None and date_to is not None:
            start_dt = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_dt = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
            delta = (date_to - date_from).days + 1
            prev_end_dt = start_dt - timedelta(microseconds=1)
            prev_start_dt = prev_end_dt - timedelta(days=delta) + timedelta(microseconds=1)
            return (start_dt, end_dt, prev_start_dt, prev_end_dt)
        return None

    def get_doctor_payments(
        self,
        doctor_id: UUID,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        paymode: Optional[str] = None,
        service_id: Optional[UUID] = None,
        period: Optional[str] = None,
        date_from: Optional[date_type] = None,
        date_to: Optional[date_type] = None
    ) -> Dict[str, Any]:
        """
        Get doctor's payment transactions with stats.
        When period is set (week/month/custom), transactions and stats are filtered by that date range.
        """
        date_range = self._doctor_payments_date_range(period, date_from, date_to)
        start_dt, end_dt, prev_start_dt, prev_end_dt = (None, None, None, None)
        if date_range:
            start_dt, end_dt, prev_start_dt, prev_end_dt = date_range

        query = self.db.query(AppointmentPayment).join(
            AppointmentRequest,
            AppointmentPayment.appointment_request_id == AppointmentRequest.id
        ).filter(
            AppointmentRequest.doctor_id == doctor_id,
            AppointmentPayment.status == 'COMPLETED'
        )
        if start_dt is not None and end_dt is not None:
            query = query.filter(
                AppointmentPayment.created_at >= start_dt,
                AppointmentPayment.created_at <= end_dt
            )

        if paymode:
            # Map common paymode values to status
            paymode_upper = paymode.upper()
            if paymode_upper in ['COMPLETED', 'SUCCESS', 'PAID']:
                query = query.filter(AppointmentPayment.status == 'COMPLETED')
            elif paymode_upper in ['PENDING', 'PROCESSING']:
                query = query.filter(AppointmentPayment.status.in_(['PENDING', 'PROCESSING']))
            elif paymode_upper in ['FAILED', 'CANCELLED']:
                query = query.filter(AppointmentPayment.status.in_(['FAILED', 'CANCELLED']))
        
        if service_id:
            query = query.filter(AppointmentRequest.service_id == service_id)
        
        # Search by patient name or phone
        if search:
            search_term = f"%{search.lower()}%"
            # Join with User (patient) for search
            query = query.join(
                User,
                AppointmentRequest.patient_id == User.id
            ).filter(
                or_(
                    func.lower(User.name).like(search_term),
                    User.phone.like(search_term)
                )
            )
        
        total = query.count()

        offset = (page - 1) * per_page
        payments = query.options(
            joinedload(AppointmentPayment.appointment_request).joinedload(AppointmentRequest.patient),
            joinedload(AppointmentPayment.appointment_request).joinedload(AppointmentRequest.service)
        ).order_by(
            AppointmentPayment.created_at.desc()
        ).offset(offset).limit(per_page).all()

        # Stats: total = sum of amounts for the same filtered set (date + paymode + service_id + search)
        stats_query = self.db.query(
            func.sum(AppointmentPayment.amount)
        ).join(
            AppointmentRequest,
            AppointmentPayment.appointment_request_id == AppointmentRequest.id
        ).filter(AppointmentRequest.doctor_id == doctor_id)
        # Apply same status filter as main query
        if paymode:
            paymode_upper = paymode.upper()
            if paymode_upper in ['COMPLETED', 'SUCCESS', 'PAID']:
                stats_query = stats_query.filter(AppointmentPayment.status == 'COMPLETED')
            elif paymode_upper in ['PENDING', 'PROCESSING']:
                stats_query = stats_query.filter(AppointmentPayment.status.in_(['PENDING', 'PROCESSING']))
            elif paymode_upper in ['FAILED', 'CANCELLED']:
                stats_query = stats_query.filter(AppointmentPayment.status.in_(['FAILED', 'CANCELLED']))
        else:
            stats_query = stats_query.filter(AppointmentPayment.status == 'COMPLETED')
        if start_dt is not None and end_dt is not None:
            stats_query = stats_query.filter(
                AppointmentPayment.created_at >= start_dt,
                AppointmentPayment.created_at <= end_dt
            )
        if service_id:
            stats_query = stats_query.filter(AppointmentRequest.service_id == service_id)
        if search:
            search_term = f"%{search.lower()}%"
            stats_query = stats_query.join(
                User,
                AppointmentRequest.patient_id == User.id
            ).filter(
                or_(
                    func.lower(User.name).like(search_term),
                    User.phone.like(search_term)
                )
            )
        total_earned_result = stats_query.scalar()
        total_earned = float(total_earned_result) if total_earned_result else 0.0

        # Growth: compare to previous period (same filters applied)
        growth = 0.0
        if prev_start_dt is not None and prev_end_dt is not None:
            prev_query = self.db.query(
                func.sum(AppointmentPayment.amount)
            ).join(
                AppointmentRequest,
                AppointmentPayment.appointment_request_id == AppointmentRequest.id
            ).filter(
                AppointmentRequest.doctor_id == doctor_id,
                AppointmentPayment.created_at >= prev_start_dt,
                AppointmentPayment.created_at <= prev_end_dt
            )
            if paymode:
                paymode_upper = paymode.upper()
                if paymode_upper in ['COMPLETED', 'SUCCESS', 'PAID']:
                    prev_query = prev_query.filter(AppointmentPayment.status == 'COMPLETED')
                elif paymode_upper in ['PENDING', 'PROCESSING']:
                    prev_query = prev_query.filter(AppointmentPayment.status.in_(['PENDING', 'PROCESSING']))
                elif paymode_upper in ['FAILED', 'CANCELLED']:
                    prev_query = prev_query.filter(AppointmentPayment.status.in_(['FAILED', 'CANCELLED']))
            else:
                prev_query = prev_query.filter(AppointmentPayment.status == 'COMPLETED')
            if service_id:
                prev_query = prev_query.filter(AppointmentRequest.service_id == service_id)
            if search:
                search_term = f"%{search.lower()}%"
                prev_query = prev_query.join(
                    User,
                    AppointmentRequest.patient_id == User.id
                ).filter(
                    or_(
                        func.lower(User.name).like(search_term),
                        User.phone.like(search_term)
                    )
                )
            prev_total = prev_query.scalar()
            previous_period = float(prev_total) if prev_total else 0.0
            if previous_period > 0:
                growth = ((total_earned - previous_period) / previous_period) * 100
            elif total_earned > 0:
                growth = 100.0
        else:
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)
            sixty_days_ago = now - timedelta(days=60)
            current_30 = self.db.query(
                func.sum(AppointmentPayment.amount)
            ).join(
                AppointmentRequest,
                AppointmentPayment.appointment_request_id == AppointmentRequest.id
            ).filter(
                AppointmentRequest.doctor_id == doctor_id,
                AppointmentPayment.status == 'COMPLETED',
                AppointmentPayment.created_at >= thirty_days_ago,
                AppointmentPayment.created_at < now
            ).scalar()
            previous_30 = self.db.query(
                func.sum(AppointmentPayment.amount)
            ).join(
                AppointmentRequest,
                AppointmentPayment.appointment_request_id == AppointmentRequest.id
            ).filter(
                AppointmentRequest.doctor_id == doctor_id,
                AppointmentPayment.status == 'COMPLETED',
                AppointmentPayment.created_at >= sixty_days_ago,
                AppointmentPayment.created_at < thirty_days_ago
            ).scalar()
            current_period = float(current_30) if current_30 else 0.0
            previous_period = float(previous_30) if previous_30 else 0.0
            if previous_period > 0:
                growth = ((current_period - previous_period) / previous_period) * 100
            elif current_period > 0:
                growth = 100.0
        
        # Get currency (use first payment's currency, or default to USD)
        currency = "USD"
        if payments:
            currency = payments[0].currency
        
        # Build transactions list
        transactions = []
        serial_number = offset + 1
        for payment in payments:
            request = payment.appointment_request
            patient = request.patient if request else None
            service = request.service if request else None
            
            # Get patient name
            patient_name = patient.name if patient else "Unknown"
            patient_phone = patient.phone if patient else None
            
            # Get service name
            service_name = service.name if service else "Unknown"
            
            # Receipt number: Use sentoo_payment_id if available, otherwise payment id
            receipt_number = payment.sentoo_payment_id if payment.sentoo_payment_id else str(payment.id)
            
            transactions.append({
                "id": str(payment.id),
                "serial_number": serial_number,
                "patient_details": {
                    "id": str(request.patient_id) if request else None,
                    "name": patient_name,
                    "phone": patient_phone
                },
                "contact_number": patient_phone,
                "service": {
                    "id": str(request.service_id) if request else None,
                    "name": service_name
                },
                "amount": float(payment.amount),
                "amount_before_waiver": float(payment.amount_before_waiver) if payment.amount_before_waiver is not None else None,
                "waiver_percent": payment.waiver_percent,
                "currency": payment.currency,
                "paymode": payment.status,
                "receipt_number": receipt_number,
                "created_at": payment.created_at.isoformat() if payment.created_at else None
            })
            serial_number += 1
        
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        filter_info = {
            "period": period or "all",
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None
        }
        return {
            "stats": {
                "total_earned": total_earned,
                "growth": round(growth, 2),
                "currency": currency
            },
            "transactions": transactions,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            },
            "filter": filter_info
        }