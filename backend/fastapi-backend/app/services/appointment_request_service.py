"""
Appointment Request Service
Business logic for appointment request → approval → payment flow
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
# Import UUID type for type conversion
from uuid import UUID as UUIDType
from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from loguru import logger
import pytz
from app.core.config import settings

# Get timezone from settings
_app_timezone = None

def get_app_timezone():
    """Get application timezone from settings"""
    global _app_timezone
    if _app_timezone is None:
        _app_timezone = settings.get_timezone()
    return _app_timezone

def get_est_date() -> date:
    """Get current date in application timezone"""
    return datetime.now(get_app_timezone()).date()

def get_est_datetime() -> datetime:
    """Get current datetime in application timezone"""
    return datetime.now(get_app_timezone())

def get_est_time() -> time:
    """Get current time in application timezone"""
    return datetime.now(get_app_timezone()).time()

from app.utils.waiver_helper import get_request_price_display, get_waiver_settings_full
from app.models.appointment_request import AppointmentRequest
from app.models.appointment import Appointment
from app.models.user import User
from app.models.profile import UserProfile
from app.models.service import Service
from app.models.availability import DoctorAvailability
from app.models.doctor_service_availability import DoctorServiceAvailability
from app.models.doctor_service import DoctorService
from app.models.notification_read import NotificationRead
from app.utils.pricing_resolver import PricingResolver
from app.utils.slot_generator import SlotGenerator
from app.services.audit_service import AuditService
from app.core.security import CurrentUser, UserRole, ConsultationMode
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException
)
from app.utils.notification_helper import (
    send_appointment_request_notification,
    send_appointment_acceptance_notification,
    send_appointment_rejection_notification
)
from app.services.admin_settings_service import AdminSettingsService


class AppointmentRequestService:
    """Service for appointment request operations"""
    
    def __init__(self, db: Session):
        """
        Initialize appointment request service
        
        Args:
            db: Database session
        """
        self.db = db
        self.audit_service = AuditService(db)
        self.pricing_resolver = PricingResolver(db)
        self.slot_generator = SlotGenerator(db)
        self.admin_settings_service = AdminSettingsService(db)
    
    def create_request(
        self,
        current_user: CurrentUser,
        doctor_id: UUID,
        service_id: UUID,
        consultation_mode: str,
        preferred_date: date,
        preferred_time: time,
        reason: Optional[str] = None,
        doctor_service_availability_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AppointmentRequest:
        """
        Create an appointment request (status: PENDING)
        
        Rules:
        - Validates availability
        - Prevents overlapping requests
        - Calculates pricing
        - Does NOT create confirmed appointment
        - Does NOT create payment intent
        
        Args:
            current_user: Current patient user
            doctor_id: Doctor user ID
            service_id: Service ID
            consultation_mode: Consultation mode
            preferred_date: Preferred appointment date
            preferred_time: Preferred appointment time
            reason: Optional reason/symptoms (HIPAA-protected)
            doctor_service_availability_id: Optional availability assignment ID
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created AppointmentRequest object
        """
        # Validate consultation mode
        try:
            mode = ConsultationMode(consultation_mode)
            consultation_mode = mode.value
        except ValueError:
            raise BadRequestException(
                message="Invalid consultation mode",
                errors={"consultation_mode": [f"Must be one of: {[m.value for m in ConsultationMode]}"]}
            )
        
        # Get patient
        patient = self.db.query(User).filter(
            User.id == current_user.id,
            User.role == UserRole.PATIENT.value,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient does not exist"]}
            )
        
        # Check if HIPAA release form has been filled (required before first appointment)
        patient_profile = (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )
        if not patient_profile or not patient_profile.hipaa_form_filled:
            raise BadRequestException(
                message="HIPAA release form required",
                errors={
                    "hipaa_form": [
                        "You must complete the HIPAA release form before booking your first appointment. "
                        "Please fill out the form and try again."
                    ],
                    "action": ["Please complete the HIPAA release form first"]
                }
            )
        
        # Get doctor
        doctor = self.db.query(User).filter(
            User.id == doctor_id,
            User.role == UserRole.DOCTOR.value,
            User.is_active == True,
            User.deleted_at.is_(None)
        ).first()
        
        if not doctor:
            raise NotFoundException(
                message="Doctor not found",
                errors={"doctor_id": ["Doctor does not exist or is not active"]}
            )
        
        # Get service
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.is_bookable == True,
            Service.deleted_at.is_(None)
        ).first()
        
        if not service:
            raise NotFoundException(
                message="Service not found or not bookable",
                errors={"service_id": ["Service does not exist or is not available for booking"]}
            )
        
        # Validate booking date against admin settings
        is_valid_date, date_error = self.admin_settings_service.validate_booking_date(preferred_date)
        if not is_valid_date:
            raise BadRequestException(
                message="Invalid booking date",
                errors={"preferred_date": [date_error]}
            )
        
        # Reject past time: requested slot start must be after current time (app timezone)
        now_app = get_est_datetime()
        requested_start_naive = datetime.combine(preferred_date, preferred_time)
        tz = get_app_timezone()
        requested_start = requested_start_naive if requested_start_naive.tzinfo else tz.localize(requested_start_naive)
        if requested_start <= now_app:
            raise BadRequestException(
                message="Cannot book a slot in the past",
                errors={
                    "preferred_date": ["The selected date and time must be in the future."],
                    "preferred_time": ["Please select a time that is after the current time."]
                }
            )
        
        # Calculate duration with priority:
        # 1. doctor_service_availability_id (if provided)
        # 2. doctor_service_availability for the specific day and mode (if available)
        # 3. doctor_services (day-specific or default)
        duration_minutes = None
        
        if doctor_service_availability_id:
            availability_assignment = self.db.query(DoctorServiceAvailability).join(
                DoctorAvailability,
                DoctorServiceAvailability.availability_id == DoctorAvailability.id
            ).filter(
                DoctorServiceAvailability.id == doctor_service_availability_id,
                DoctorServiceAvailability.service_id == service_id,
                DoctorAvailability.doctor_id == doctor_id,
                DoctorServiceAvailability.consultation_mode == consultation_mode
            ).first()
            
            if availability_assignment:
                duration_minutes = availability_assignment.slot_duration_minutes
        
        if not duration_minutes:
            # Try to find doctor_service_availability for this specific day and mode
            python_weekday = preferred_date.weekday()  # 0=Monday, 6=Sunday
            
            availability_assignment = self.db.query(DoctorServiceAvailability).join(
                DoctorAvailability,
                DoctorServiceAvailability.availability_id == DoctorAvailability.id
            ).filter(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.day_of_week == python_weekday,
                DoctorAvailability.is_active == True,
                DoctorAvailability.deleted_at.is_(None),
                DoctorServiceAvailability.service_id == service_id,
                DoctorServiceAvailability.consultation_mode == consultation_mode
            ).first()
            
            if availability_assignment:
                duration_minutes = availability_assignment.slot_duration_minutes
        
        if not duration_minutes:
            # Fallback to doctor service default
            python_weekday = preferred_date.weekday()
            day_of_week = (python_weekday + 1) % 7  # Convert to 0=Sunday format
            
            doctor_service = self.db.query(DoctorService).filter(
                DoctorService.doctor_id == doctor_id,
                DoctorService.service_id == service_id,
                DoctorService.is_active == True,
                DoctorService.day_of_week == day_of_week
            ).first()
            
            if not doctor_service:
                doctor_service = self.db.query(DoctorService).filter(
                    DoctorService.doctor_id == doctor_id,
                    DoctorService.service_id == service_id,
                    DoctorService.is_active == True,
                    DoctorService.day_of_week.is_(None)
                ).first()
            
            if not doctor_service:
                raise BadRequestException(
                    message="Service not assigned to doctor",
                    errors={"service_id": ["This service is not assigned to the doctor for this day"]}
                )
            
            duration_minutes = doctor_service.slot_duration_minutes
        
        # Calculate end time
        start_datetime = datetime.combine(preferred_date, preferred_time)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        end_time = end_datetime.time()
        
        # Validate slot availability
        if not self.slot_generator.is_slot_available(
            doctor_id=doctor_id,
            service_id=service_id,
            slot_start=start_datetime,
            slot_end=end_datetime,
            consultation_mode=consultation_mode
        ):
            raise BadRequestException(
                message="Time slot not available",
                errors={
                    "preferred_time": ["The selected time slot is not available. Please select another time."]
                }
            )
        
        # Check for existing appointments at the same time
        existing_appointment = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == preferred_date,
            Appointment.start_time == preferred_time,
            Appointment.status.in_(['SCHEDULED', 'CONFIRMED']),
            Appointment.deleted_at.is_(None)
        ).first()
        
        if existing_appointment:
            raise BadRequestException(
                message="Time slot already booked",
                errors={
                    "preferred_time": ["This time slot has already been booked. Please select another time."]
                }
            )
        
        # Check for existing pending/accepted requests at the same time
        existing_request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.doctor_id == doctor_id,
            AppointmentRequest.preferred_date == preferred_date,
            AppointmentRequest.preferred_time == preferred_time,
            AppointmentRequest.status.in_(['PENDING', 'ACCEPTED']),
            AppointmentRequest.deleted_at.is_(None)
        ).first()
        
        if existing_request:
            raise BadRequestException(
                message="Time slot has pending request",
                errors={
                    "preferred_time": ["This time slot has a pending or accepted request. Please select another time."]
                }
            )
        
        # Resolve pricing (calculate but don't lock yet)
        try:
            price_amount, currency, pricing_source = self.pricing_resolver.resolve_price(
                doctor_id=doctor_id,
                service_id=service_id,
                doctor_service_availability_id=doctor_service_availability_id,
                consultation_mode=consultation_mode,
                currency=None  # No currency validation - get from pricing source
            )
        except BadRequestException as e:
            raise BadRequestException(
                message="Pricing unavailable",
                errors=e.errors or {"price": ["Unable to determine price for this appointment"]}
            )
        
        # Check if auto-approval is enabled BEFORE creating the request
        settings = self.admin_settings_service.get_settings()
        logger.info(f"Checking auto-approve setting: auto_approve_appointments={settings.auto_approve_appointments}")
        
        # Determine initial status based on auto-approve setting
        initial_status = 'ACCEPTED' if settings.auto_approve_appointments else 'PENDING'
        
        # Create appointment request with appropriate initial status
        appointment_request = AppointmentRequest(
            doctor_id=doctor_id,
            patient_id=patient.id,
            service_id=service_id,
            clinic_id=doctor.clinic_id,
            doctor_service_availability_id=doctor_service_availability_id,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            consultation_mode=consultation_mode,
            duration_minutes=duration_minutes,
            status=initial_status,  # Set status based on auto-approve setting
            reason=reason,  # HIPAA: stored but never logged
            price_amount=price_amount,
            currency=currency,
            pricing_source=pricing_source
        )
        
        self.db.add(appointment_request)
        self.db.commit()
        self.db.refresh(appointment_request)
        
        # Audit log: Request created (NO PHI, no symptoms content)
        self.audit_service.create_audit_log(
            actor_user_id=patient.id,
            action="APPOINTMENT_REQUEST_CREATED",
            entity_type="appointment_request",
            entity_id=appointment_request.id,
            audit_metadata={
                "appointment_request_id": str(appointment_request.id),
                "doctor_id": str(doctor_id),
                "service_id": str(service_id),
                "consultation_mode": consultation_mode,
                "preferred_date": preferred_date.isoformat(),
                "preferred_time": preferred_time.isoformat(),
                "price_amount": float(price_amount),
                "currency": currency,
                "has_reason": reason is not None,  # Only log if reason exists, not content
                "auto_approved": settings.auto_approve_appointments
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(
            f"Appointment request created: {appointment_request.id} by patient {patient.id} "
            f"for doctor {doctor_id} on {preferred_date} at {preferred_time} "
            f"(mode: {consultation_mode}, price: {price_amount} {currency}, status: {appointment_request.status})"
        )
        
        if settings.auto_approve_appointments:
            # Auto-approve the request
            logger.info(f"Auto-approving appointment request {appointment_request.id} (auto_approve_appointments is enabled)")
            
            # Re-validate availability (race condition check)
            start_datetime = datetime.combine(appointment_request.preferred_date, appointment_request.preferred_time)
            end_datetime = start_datetime + timedelta(minutes=appointment_request.duration_minutes)
            
            can_auto_approve = True
            skip_reason = None
            
            # Check slot availability
            try:
                if not self.slot_generator.is_slot_available(
                    doctor_id=appointment_request.doctor_id,
                    service_id=appointment_request.service_id,
                    slot_start=start_datetime,
                    slot_end=end_datetime,
                    consultation_mode=appointment_request.consultation_mode
                ):
                    can_auto_approve = False
                    skip_reason = "Slot no longer available"
                    logger.warning(f"Slot no longer available for auto-approval of request {appointment_request.id}")
            except Exception as e:
                logger.error(f"Error checking slot availability for auto-approval: {str(e)}")
                can_auto_approve = False
                skip_reason = f"Slot availability check failed: {str(e)}"
            
            # Check for conflicting appointments/requests
            if can_auto_approve:
                try:
                    existing_appointment = self.db.query(Appointment).filter(
                        Appointment.doctor_id == appointment_request.doctor_id,
                        Appointment.appointment_date == appointment_request.preferred_date,
                        Appointment.start_time == appointment_request.preferred_time,
                        Appointment.status.in_(['SCHEDULED', 'CONFIRMED']),
                        Appointment.deleted_at.is_(None)
                    ).first()
                    
                    existing_request = self.db.query(AppointmentRequest).filter(
                        AppointmentRequest.id != appointment_request.id,
                        AppointmentRequest.doctor_id == appointment_request.doctor_id,
                        AppointmentRequest.preferred_date == appointment_request.preferred_date,
                        AppointmentRequest.preferred_time == appointment_request.preferred_time,
                        AppointmentRequest.status.in_(['PENDING', 'ACCEPTED']),
                        AppointmentRequest.deleted_at.is_(None)
                    ).first()
                    
                    if existing_appointment or existing_request:
                        can_auto_approve = False
                        skip_reason = "Conflicting appointment/request found"
                        logger.warning(f"Conflicting appointment/request found for auto-approval of request {appointment_request.id}")
                except Exception as e:
                    logger.error(f"Error checking conflicts for auto-approval: {str(e)}")
                    can_auto_approve = False
                    skip_reason = f"Conflict check failed: {str(e)}"
            
            # Auto-approve if all checks passed
            if can_auto_approve:
                try:
                    # Update status to ACCEPTED FIRST (before any other operations)
                    appointment_request.status = 'ACCEPTED'
                    
                    # Ensure pricing is locked
                    if appointment_request.price_amount is None:
                        try:
                            price_amount, currency, pricing_source = self.pricing_resolver.resolve_price(
                                doctor_id=appointment_request.doctor_id,
                                service_id=appointment_request.service_id,
                                doctor_service_availability_id=appointment_request.doctor_service_availability_id,
                                consultation_mode=appointment_request.consultation_mode,
                                currency=appointment_request.currency
                            )
                            appointment_request.price_amount = price_amount
                            appointment_request.currency = currency
                            appointment_request.pricing_source = pricing_source
                        except BadRequestException as e:
                            logger.error(f"Failed to resolve price for auto-approval: {str(e)}")
                    
                    # Commit the status change immediately
                    self.db.commit()
                    self.db.refresh(appointment_request)
                    
                    logger.info(f"Appointment request {appointment_request.id} status updated to ACCEPTED (auto-approved)")
                    
                    # Audit log: Request auto-accepted (NO PHI) - wrap in try/except so it doesn't fail the approval
                    try:
                        self.audit_service.create_audit_log(
                            actor_user_id=str(doctor_id),  # Use doctor's ID for audit
                            action="APPOINTMENT_REQUEST_AUTO_ACCEPTED",
                            entity_type="appointment_request",
                            entity_id=appointment_request.id,
                            audit_metadata={
                                "appointment_request_id": str(appointment_request.id),
                                "patient_id": str(appointment_request.patient_id),
                                "service_id": str(appointment_request.service_id),
                                "consultation_mode": appointment_request.consultation_mode,
                                "price_amount": float(appointment_request.price_amount) if appointment_request.price_amount else None,
                                "currency": appointment_request.currency,
                                "auto_approved": True
                            },
                            ip_address=ip_address,
                            user_agent=user_agent
                        )
                    except Exception as e:
                        logger.warning(f"Failed to create audit log for auto-approved request: {str(e)}")
                    
                    # Trigger notification to patient (async, don't wait) - wrap in try/except
                    try:
                        import asyncio
                        import concurrent.futures
                        
                        # Get service name for email
                        service_name = service.name if service else "Appointment"
                        
                        # Store values needed for notification (don't pass db session to thread)
                        patient_id_str = str(appointment_request.patient_id)
                        request_id_str = str(appointment_request.id)
                        doctor_name_str = doctor.name
                        appointment_date_str = appointment_request.preferred_date.isoformat()
                        appointment_time_str = appointment_request.preferred_time.isoformat()
                        price_amount_float = float(appointment_request.price_amount) if appointment_request.price_amount else 0.0
                        currency_str = appointment_request.currency
                        consultation_mode_str = appointment_request.consultation_mode
                        
                        # Run async notification in thread pool to avoid event loop conflicts
                        def run_patient_notification():
                            try:
                                # Create new database session for this thread
                                from app.core.database import SessionLocal
                                db = SessionLocal()
                                try:
                                    # Create new event loop for this thread
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    try:
                                        loop.run_until_complete(
                                            send_appointment_acceptance_notification(
                                                db=db,
                                                patient_id=patient_id_str,
                                                request_id=request_id_str,
                                                doctor_name=doctor_name_str,
                                                appointment_date=appointment_date_str,
                                                appointment_time=appointment_time_str,
                                                price_amount=price_amount_float,
                                                currency=currency_str,
                                                service_name=service_name,
                                                consultation_mode=consultation_mode_str
                                            )
                                        )
                                    finally:
                                        loop.close()
                                finally:
                                    db.close()
                            except Exception as e:
                                logger.error(f"Error in patient notification thread: {str(e)}", exc_info=True)
                        
                        # Run in background thread (don't wait for completion)
                        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                        executor.submit(run_patient_notification)
                        executor.shutdown(wait=False)  # Don't wait for completion
                    except Exception as e:
                        logger.warning(f"Failed to trigger patient notification for auto-approved request: {str(e)}", exc_info=True)
                    
                    logger.info(f"Appointment request {appointment_request.id} auto-approved successfully (final status: {appointment_request.status})")
                except Exception as e:
                    logger.error(f"Failed to auto-approve appointment request {appointment_request.id}: {str(e)}", exc_info=True)
                    # Rollback if status update failed
                    self.db.rollback()
                    # Refresh to get original status
                    self.db.refresh(appointment_request)
            else:
                logger.info(f"Skipping auto-approval for request {appointment_request.id}: {skip_reason}")
        # Send email notification to doctor (always send, regardless of auto-approve status)
        # Use thread pool to run async function in sync context
        import asyncio
        import concurrent.futures
        try:
            # Get service name for email
            service_name = service.name if service else "Appointment"
            
            # Store values needed for notification (don't pass db session to thread)
            doctor_id_str = str(doctor_id)
            request_id_str = str(appointment_request.id)
            patient_name_str = patient.name
            appointment_date_str = preferred_date.isoformat()
            appointment_time_str = preferred_time.isoformat()
            
            # Run async notification in thread pool to avoid event loop conflicts
            def run_notification():
                try:
                    # Create new database session for this thread
                    from app.core.database import SessionLocal
                    db = SessionLocal()
                    try:
                        # Create new event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(
                                send_appointment_request_notification(
                                    db=db,
                                    doctor_id=doctor_id_str,
                                    request_id=request_id_str,
                                    patient_name=patient_name_str,
                                    appointment_date=appointment_date_str,
                                    appointment_time=appointment_time_str,
                                    service_name=service_name,
                                    consultation_mode=consultation_mode
                                )
                            )
                        finally:
                            loop.close()
                    finally:
                        db.close()
                except Exception as e:
                    logger.error(f"Error in notification thread: {str(e)}", exc_info=True)
            
            # Run in background thread (don't wait for completion)
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            executor.submit(run_notification)
            executor.shutdown(wait=False)  # Don't wait for completion
            
        except Exception as e:
            logger.warning(f"Failed to send doctor notification email: {str(e)}", exc_info=True)
        
        return appointment_request
    
    def list_doctor_requests(
        self,
        current_user: CurrentUser,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List appointment requests for a doctor
        
        Args:
            current_user: Current doctor user
            status: Optional status filter (PENDING, ACCEPTED, REJECTED)
            page: Page number
            limit: Items per page
            
        Returns:
            Dictionary with requests list and pagination
        """
        # Validate doctor role
        if current_user.role != UserRole.DOCTOR.value:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors can view appointment requests"]}
            )
        
        # Base query
        query = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.doctor_id == current_user.id,
            AppointmentRequest.deleted_at.is_(None)
        )
        
        # Filter by status
        if status:
            if status not in ['PENDING', 'ACCEPTED', 'REJECTED']:
                raise BadRequestException(
                    message="Invalid status",
                    errors={"status": ["Must be one of: PENDING, ACCEPTED, REJECTED"]}
                )
            query = query.filter(AppointmentRequest.status == status)
        else:
            # Default: only pending requests
            query = query.filter(AppointmentRequest.status == 'PENDING')
        
        # Get total count
        total = query.count()
        
        # Apply pagination with eager loading of patient, patient profile, and service relationships
        offset = (page - 1) * limit
        requests = query.options(
            joinedload(AppointmentRequest.patient).joinedload(User.profile),
            joinedload(AppointmentRequest.service)
        ).order_by(AppointmentRequest.created_at.desc()).offset(offset).limit(limit).all()
        
        # Helper function to calculate age from date_of_birth
        def calculate_age(date_of_birth):
            """Calculate age from date of birth"""
            if not date_of_birth:
                return None
            today = get_est_date()
            age = today.year - date_of_birth.year
            # Adjust if birthday hasn't occurred this year
            if today.month < date_of_birth.month or (today.month == date_of_birth.month and today.day < date_of_birth.day):
                age -= 1
            return age
        
        # Build response (NO PHI, no reason/symptoms)
        # Include patient and service information so doctor can see who created the request
        requests_data = []
        for req in requests:
            # Patient and service are eagerly loaded via joinedload
            patient = getattr(req, 'patient', None)
            service = getattr(req, 'service', None)
            patient_profile = getattr(patient, 'profile', None) if patient else None
            
            price_after, amount_before, waiver_pct = get_request_price_display(
                self.db, float(req.price_amount) if req.price_amount else None, doctor_waiver_percent=req.waiver_percent
            )
            request_data = {
                "id": str(req.id),
                "patient_id": str(req.patient_id),
                "patient": {
                    "id": str(req.patient_id),
                    "name": patient.name if patient else None,
                    "email": patient.email if patient else None,
                    "phone": patient.phone if patient else None,
                    "gender": patient_profile.gender if patient_profile else None,
                    "age": calculate_age(patient_profile.date_of_birth) if patient_profile and patient_profile.date_of_birth else None,
                    "description": patient_profile.bio if patient_profile else None,
                } if patient else None,
                "service_id": str(req.service_id),
                "service": {
                    "id": str(req.service_id),
                    "name": service.name if service else None,
                } if service else None,
                "doctor_id": str(req.doctor_id),
                "clinic_id": str(req.clinic_id),
                "preferred_date": req.preferred_date.isoformat(),
                "preferred_time": str(req.preferred_time),
                "consultation_mode": req.consultation_mode,
                "duration_minutes": req.duration_minutes,
                "status": req.status,
                "price_amount": price_after,
                "amount_before_waiver": amount_before,
                "waiver_percent": waiver_pct,
                "currency": req.currency,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "updated_at": req.updated_at.isoformat() if req.updated_at else None,
                # NOTE: reason/symptoms NOT included (HIPAA)
            }
            requests_data.append(request_data)
        
        # Calculate pagination
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        return {
            "requests": requests_data,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total": total,
                "total_pages": total_pages
            }
        }
    
    def list_doctor_appointment_notifications(
        self,
        current_user: CurrentUser,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List appointment notifications for a doctor
        
        Returns appointment requests formatted as notifications with:
        - Notification type (NEW_REQUEST, REQUEST_ACCEPTED, REQUEST_REJECTED)
        - Patient information
        - Appointment details
        - Status
        
        Args:
            current_user: Current doctor user
            status: Optional status filter (PENDING, ACCEPTED, REJECTED)
            page: Page number
            limit: Items per page
            
        Returns:
            Dictionary with notifications list and pagination
        """
        # Validate doctor role
        if current_user.role != UserRole.DOCTOR.value:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors can view appointment notifications"]}
            )
        
        # Base query
        query = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.doctor_id == current_user.id,
            AppointmentRequest.deleted_at.is_(None)
        )
        
        # Filter by status
        if status:
            if status not in ['PENDING', 'ACCEPTED', 'REJECTED']:
                raise BadRequestException(
                    message="Invalid status",
                    errors={"status": ["Must be one of: PENDING, ACCEPTED, REJECTED"]}
                )
            query = query.filter(AppointmentRequest.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination with eager loading of patient, patient profile, and service relationships
        offset = (page - 1) * limit
        requests = query.options(
            joinedload(AppointmentRequest.patient).joinedload(User.profile),
            joinedload(AppointmentRequest.service)
        ).order_by(AppointmentRequest.created_at.desc()).offset(offset).limit(limit).all()
        
        # Get read status for all notifications
        request_ids = [req.id for req in requests]
        read_statuses = {}
        if request_ids:
            read_records = self.db.query(NotificationRead).filter(
                NotificationRead.user_id == current_user.id,
                NotificationRead.appointment_request_id.in_(request_ids)
            ).all()
            read_statuses = {record.appointment_request_id: record.read_at for record in read_records}
        
        # Helper function to calculate age from date_of_birth
        def calculate_age(date_of_birth):
            """Calculate age from date of birth"""
            if not date_of_birth:
                return None
            today = get_est_date()
            age = today.year - date_of_birth.year
            # Adjust if birthday hasn't occurred this year
            if today.month < date_of_birth.month or (today.month == date_of_birth.month and today.day < date_of_birth.day):
                age -= 1
            return age
        
        # Build notifications response (NO PHI, no reason/symptoms)
        notifications_data = []
        for req in requests:
            # Patient and service are eagerly loaded via joinedload
            patient = getattr(req, 'patient', None)
            service = getattr(req, 'service', None)
            patient_profile = getattr(patient, 'profile', None) if patient else None
            
            # Determine notification type based on status
            notification_type = "NEW_REQUEST"
            if req.status == "ACCEPTED":
                notification_type = "REQUEST_ACCEPTED"
            elif req.status == "REJECTED":
                notification_type = "REQUEST_REJECTED"
            
            # Build notification message
            patient_name = patient.name if patient else "Unknown Patient"
            service_name = service.name if service else "Unknown Service"
            notification_message = f"New appointment request from {patient_name} for {service_name}"
            if req.status == "ACCEPTED":
                notification_message = f"Appointment request accepted: {patient_name} - {service_name}"
            elif req.status == "REJECTED":
                notification_message = f"Appointment request rejected: {patient_name} - {service_name}"
            
            # Check if notification is read
            is_read = req.id in read_statuses
            read_at = read_statuses.get(req.id)
            
            notification_data = {
                "id": str(req.id),
                "type": notification_type,
                "title": f"Appointment Request - {service_name}",
                "message": notification_message,
                "status": req.status,
                "is_read": is_read,
                "read_at": read_at.isoformat() if read_at else None,
                "appointment_request": {
                    "id": str(req.id),
                    "patient_id": str(req.patient_id),
                    "patient": {
                        "id": str(req.patient_id),
                        "name": patient.name if patient else None,
                        "email": patient.email if patient else None,
                        "phone": patient.phone if patient else None,
                        "gender": patient_profile.gender if patient_profile else None,
                        "age": calculate_age(patient_profile.date_of_birth) if patient_profile and patient_profile.date_of_birth else None,
                    } if patient else None,
                    "service_id": str(req.service_id),
                    "service": {
                        "id": str(req.service_id),
                        "name": service.name if service else None,
                    } if service else None,
                    "preferred_date": req.preferred_date.isoformat(),
                    "preferred_time": str(req.preferred_time),
                    "consultation_mode": req.consultation_mode,
                    "duration_minutes": req.duration_minutes,
                    "price_amount": float(req.price_amount) if req.price_amount else None,
                    "currency": req.currency,
                    "rejection_reason": req.rejection_reason,
                },
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "updated_at": req.updated_at.isoformat() if req.updated_at else None,
            }
            notifications_data.append(notification_data)
        
        # Calculate pagination
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        return {
            "notifications": notifications_data,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total": total,
                "total_pages": total_pages
            }
        }
    
    def list_patient_appointment_notifications(
        self,
        current_user: CurrentUser,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List appointment notifications for a patient
        
        Returns appointment requests formatted as notifications with:
        - Notification type (REQUEST_ACCEPTED, REQUEST_REJECTED)
        - Doctor information
        - Appointment details
        - Status
        
        Args:
            current_user: Current patient user
            status: Optional status filter (PENDING, ACCEPTED, REJECTED)
            page: Page number
            limit: Items per page
            
        Returns:
            Dictionary with notifications list and pagination
        """
        # Validate patient role
        if current_user.role != UserRole.PATIENT.value:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only patients can view appointment notifications"]}
            )
        
        # Base query
        query = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.patient_id == current_user.id,
            AppointmentRequest.deleted_at.is_(None)
        )
        
        # Filter by status
        if status:
            if status not in ['PENDING', 'ACCEPTED', 'REJECTED']:
                raise BadRequestException(
                    message="Invalid status",
                    errors={"status": ["Must be one of: PENDING, ACCEPTED, REJECTED"]}
                )
            query = query.filter(AppointmentRequest.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination with eager loading of doctor, doctor profile, medical_services, and service relationships
        offset = (page - 1) * limit
        requests = query.options(
            joinedload(AppointmentRequest.doctor).joinedload(User.profile),
            joinedload(AppointmentRequest.doctor).joinedload(User.medical_services),
            joinedload(AppointmentRequest.service)
        ).order_by(AppointmentRequest.created_at.desc()).offset(offset).limit(limit).all()
        
        # Get read status for all notifications
        request_ids = [req.id for req in requests]
        read_statuses = {}
        if request_ids:
            read_records = self.db.query(NotificationRead).filter(
                NotificationRead.user_id == current_user.id,
                NotificationRead.appointment_request_id.in_(request_ids)
            ).all()
            read_statuses = {record.appointment_request_id: record.read_at for record in read_records}
        
        # Build notifications response (NO PHI, no reason/symptoms)
        notifications_data = []
        for req in requests:
            # Doctor and service are eagerly loaded via joinedload
            doctor = getattr(req, 'doctor', None)
            service = getattr(req, 'service', None)
            doctor_profile = getattr(doctor, 'profile', None) if doctor else None
            
            # Get specializations from doctor's medical_services relationship
            specializations = None
            if doctor and hasattr(doctor, 'medical_services') and doctor.medical_services:
                specializations = [
                    {
                        "id": str(svc.id),
                        "name": svc.name if hasattr(svc, 'name') else None,
                        "image": svc.image if hasattr(svc, 'image') else None
                    }
                    for svc in doctor.medical_services
                ]
            
            # Determine notification type based on status
            notification_type = "NEW_REQUEST"
            if req.status == "ACCEPTED":
                notification_type = "REQUEST_ACCEPTED"
            elif req.status == "REJECTED":
                notification_type = "REQUEST_REJECTED"
            
            # Build notification message
            doctor_name = doctor.name if doctor else "Unknown Doctor"
            service_name = service.name if service else "Unknown Service"
            notification_message = f"Your appointment request for {service_name} is pending review by Dr. {doctor_name}"
            if req.status == "ACCEPTED":
                notification_message = f"Your appointment request has been accepted by Dr. {doctor_name} for {service_name}. Please proceed with payment to confirm your appointment."
            elif req.status == "REJECTED":
                reason_text = f" Reason: {req.rejection_reason}" if req.rejection_reason else ""
                notification_message = f"Your appointment request has been rejected by Dr. {doctor_name} for {service_name}.{reason_text} Please select another time slot."
            
            # Check if notification is read
            is_read = req.id in read_statuses
            read_at = read_statuses.get(req.id)
            
            notification_data = {
                "id": str(req.id),
                "type": notification_type,
                "title": f"Appointment Request - {service_name}",
                "message": notification_message,
                "status": req.status,
                "is_read": is_read,
                "read_at": read_at.isoformat() if read_at else None,
                "appointment_request": {
                    "id": str(req.id),
                    "doctor_id": str(req.doctor_id),
                    "doctor": {
                        "id": str(req.doctor_id),
                        "name": doctor.name if doctor else None,
                        "email": doctor.email if doctor else None,
                        "phone": doctor.phone if doctor else None,
                        "specializations": specializations,
                        "bio": doctor_profile.bio if doctor_profile else None,
                    } if doctor else None,
                    "service_id": str(req.service_id),
                    "service": {
                        "id": str(req.service_id),
                        "name": service.name if service else None,
                    } if service else None,
                    "preferred_date": req.preferred_date.isoformat(),
                    "preferred_time": str(req.preferred_time),
                    "consultation_mode": req.consultation_mode,
                    "duration_minutes": req.duration_minutes,
                    "price_amount": float(req.price_amount) if req.price_amount else None,
                    "currency": req.currency,
                    "rejection_reason": req.rejection_reason,
                },
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "updated_at": req.updated_at.isoformat() if req.updated_at else None,
            }
            notifications_data.append(notification_data)
        
        # Calculate pagination
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        return {
            "notifications": notifications_data,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total": total,
                "total_pages": total_pages
            }
        }
    
    def get_patient_request_statistics(
        self,
        current_user: CurrentUser
    ) -> Dict[str, Any]:
        """
        Get appointment request statistics for a patient
        
        Returns counts of:
        - Accepted requests
        - Rejected requests
        - Pending requests
        - Past requests (where preferred_date + preferred_time is in the past)
        
        Args:
            current_user: Current patient user
            
        Returns:
            Dictionary with statistics counts
        """
        # Validate patient role
        if current_user.role != UserRole.PATIENT.value:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only patients can view appointment request statistics"]}
            )
        
        # Base query for patient's requests
        base_query = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.patient_id == current_user.id,
            AppointmentRequest.deleted_at.is_(None)
        )
        
        # Get counts by status
        accepted_count = base_query.filter(AppointmentRequest.status == 'ACCEPTED').count()
        rejected_count = base_query.filter(AppointmentRequest.status == 'REJECTED').count()
        pending_count = base_query.filter(AppointmentRequest.status == 'PENDING').count()
        
        # Calculate past requests (where preferred_date + preferred_time is in the past)
        today = get_est_date()
        now = get_est_time()
        
        # Past requests: date is before today, or date is today but time has passed
        past_query = base_query.filter(
            or_(
                AppointmentRequest.preferred_date < today,
                and_(
                    AppointmentRequest.preferred_date == today,
                    AppointmentRequest.preferred_time < now
                )
            )
        )
        past_count = past_query.count()
        
        return {
            "accepted": accepted_count,
            "rejected": rejected_count,
            "pending": pending_count,
            "past": past_count,
            "total": accepted_count + rejected_count + pending_count
        }
    
    def get_request_details(
        self,
        current_user: CurrentUser,
        request_id: UUID
    ) -> AppointmentRequest:
        """
        Get appointment request details
        
        Args:
            current_user: Current user (doctor or patient)
            request_id: Request ID
            
        Returns:
            AppointmentRequest object
        """
        request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.id == request_id,
            AppointmentRequest.deleted_at.is_(None)
        ).first()
        
        if not request:
            raise NotFoundException(
                message="Appointment request not found",
                errors={"request_id": ["Request does not exist"]}
            )
        
        # Validate ownership
        # Compare as strings to avoid UUID type mismatch issues
        current_user_id_str = str(current_user.id).lower().strip()
        
        if current_user.role == UserRole.DOCTOR.value:
            doctor_id_str = str(request.doctor_id).lower().strip()
            if doctor_id_str != current_user_id_str:
                raise ForbiddenException(
                    message="Access denied",
                    errors={"request_id": ["You can only view your own appointment requests"]}
                )
        elif current_user.role == UserRole.PATIENT.value:
            patient_id_str = str(request.patient_id).lower().strip()
            if patient_id_str != current_user_id_str:
                raise ForbiddenException(
                    message="Access denied",
                    errors={"request_id": ["You can only view your own appointment requests"]}
                )
        else:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors and patients can view appointment requests"]}
            )
        
        return request
    
    def accept_request(
        self,
        current_user: CurrentUser,
        request_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        waiver_percent: Optional[int] = None,
    ) -> AppointmentRequest:
        """
        Accept an appointment request
        
        Rules:
        - Only assigned doctor can accept
        - Re-validates availability
        - Locks the slot
        - Updates status to ACCEPTED
        - Locks pricing
        - When waiver_doctor_decides is True, waiver_percent (0, 25, 50, 75, 100) is required and stored
        
        Args:
            current_user: Current doctor user
            request_id: Request ID
            ip_address: Request IP address
            user_agent: Request user agent
            waiver_percent: Optional waiver (0, 25, 50, 75, 100) when admin has waiver_doctor_decides enabled
            
        Returns:
            Updated AppointmentRequest object
        """
        # Validate doctor role
        if current_user.role != UserRole.DOCTOR.value:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors can accept appointment requests"]}
            )
        
        # Get request
        request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.id == request_id,
            AppointmentRequest.deleted_at.is_(None)
        ).first()
        
        if not request:
            raise NotFoundException(
                message="Appointment request not found",
                errors={"request_id": ["Request does not exist"]}
            )
        
        # Validate ownership
        # Compare as strings to avoid UUID type mismatch issues
        # current_user.id is string, request.doctor_id is UUID object
        try:
            # Convert both to strings and normalize
            current_user_id_str = str(current_user.id).strip()
            doctor_id_str = str(request.doctor_id).strip()
            
            # Remove any hyphens and compare (in case of formatting differences)
            current_user_id_clean = current_user_id_str.replace('-', '').lower()
            doctor_id_clean = doctor_id_str.replace('-', '').lower()
            
            # Also compare as-is (case-insensitive)
            ids_match = (
                current_user_id_str.lower() == doctor_id_str.lower() or
                current_user_id_clean == doctor_id_clean
            )
            
            # Debug logging
            logger.info(
                f"Accept request ownership check: request_id={request_id}, "
                f"current_user.id={current_user.id} (type: {type(current_user.id)}), "
                f"request.doctor_id={request.doctor_id} (type: {type(request.doctor_id)}), "
                f"current_user_id_str={current_user_id_str}, doctor_id_str={doctor_id_str}, "
                f"ids_match={ids_match}"
            )
            
            if not ids_match:
                logger.warning(
                    f"Ownership validation failed for request {request_id}: "
                    f"doctor_id={doctor_id_str}, current_user_id={current_user_id_str}, "
                    f"doctor_id_clean={doctor_id_clean}, current_user_id_clean={current_user_id_clean}"
                )
                raise ForbiddenException(
                    message="Access denied",
                    errors={"request_id": ["You can only accept your own appointment requests"]}
                )
        except Exception as e:
            logger.error(f"Error in ownership validation: {str(e)}", exc_info=True)
            raise ForbiddenException(
                message="Access denied",
                errors={"request_id": ["Error validating request ownership"]}
            )
        
        # Validate status
        if request.status != 'PENDING':
            raise BadRequestException(
                message="Request cannot be accepted",
                errors={"status": [f"Request is already {request.status.lower()}. Only pending requests can be accepted."]}
            )
        
        # Waiver: when admin has waiver_doctor_decides enabled, doctor must set waiver (0, 25, 50, 75, 100)
        waiver_enabled, _, waiver_doctor_decides = get_waiver_settings_full(self.db)
        if waiver_doctor_decides and waiver_enabled:
            if waiver_percent is None:
                raise BadRequestException(
                    message="Waiver percentage required",
                    errors={"waiver_percent": ["When waiver is set to doctor-decides, you must provide waiver_percent (0, 25, 50, 75, or 100)"]}
                )
            if waiver_percent not in (0, 25, 50, 75, 100):
                raise BadRequestException(
                    message="Invalid waiver percentage",
                    errors={"waiver_percent": ["waiver_percent must be one of 0, 25, 50, 75, 100"]}
                )
            request.waiver_percent = waiver_percent
        else:
            # Admin waiver mode: leave request.waiver_percent unset (set at payment init if applicable)
            request.waiver_percent = None
        
        # Re-validate availability (race condition check)
        start_datetime = datetime.combine(request.preferred_date, request.preferred_time)
        end_datetime = start_datetime + timedelta(minutes=request.duration_minutes)
        
        if not self.slot_generator.is_slot_available(
            doctor_id=request.doctor_id,
            service_id=request.service_id,
            slot_start=start_datetime,
            slot_end=end_datetime,
            consultation_mode=request.consultation_mode
        ):
            raise BadRequestException(
                message="Time slot no longer available",
                errors={
                    "preferred_time": ["The selected time slot is no longer available. Please reject this request."]
                }
            )
        
        # Check for conflicting appointments/requests
        existing_appointment = self.db.query(Appointment).filter(
            Appointment.doctor_id == request.doctor_id,
            Appointment.appointment_date == request.preferred_date,
            Appointment.start_time == request.preferred_time,
            Appointment.status.in_(['SCHEDULED', 'CONFIRMED']),
            Appointment.deleted_at.is_(None)
        ).first()
        
        if existing_appointment:
            raise BadRequestException(
                message="Time slot already booked",
                errors={
                    "preferred_time": ["This time slot has been booked by another appointment."]
                }
            )
        
        existing_request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.id != request_id,
            AppointmentRequest.doctor_id == request.doctor_id,
            AppointmentRequest.preferred_date == request.preferred_date,
            AppointmentRequest.preferred_time == request.preferred_time,
            AppointmentRequest.status.in_(['PENDING', 'ACCEPTED']),
            AppointmentRequest.deleted_at.is_(None)
        ).first()
        
        if existing_request:
            raise BadRequestException(
                message="Time slot has conflicting request",
                errors={
                    "preferred_time": ["This time slot has another pending or accepted request."]
                }
            )
        
        # Update status to ACCEPTED
        request.status = 'ACCEPTED'
        # Lock pricing (ensure price_amount is set)
        if request.price_amount is None:
            # Re-calculate if not set
            try:
                price_amount, currency, pricing_source = self.pricing_resolver.resolve_price(
                    doctor_id=request.doctor_id,
                    service_id=request.service_id,
                    doctor_service_availability_id=request.doctor_service_availability_id,
                    consultation_mode=request.consultation_mode,
                    currency=request.currency
                )
                request.price_amount = price_amount
                request.currency = currency
                request.pricing_source = pricing_source
            except BadRequestException:
                raise BadRequestException(
                    message="Pricing unavailable",
                    errors={"price": ["Unable to determine price for this appointment"]}
                )
        
        self.db.commit()
        self.db.refresh(request)
        
        # Audit log: Request accepted (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=current_user.id,
            action="APPOINTMENT_REQUEST_ACCEPTED",
            entity_type="appointment_request",
            entity_id=request.id,
            audit_metadata={
                "appointment_request_id": str(request.id),
                "patient_id": str(request.patient_id),
                "service_id": str(request.service_id),
                "consultation_mode": request.consultation_mode,
                "price_amount": float(request.price_amount) if request.price_amount else None,
                "currency": request.currency
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Appointment request {request_id} accepted by doctor {current_user.id}")
        
        # Trigger notification to patient (async, don't wait)
        try:
            patient = self.db.query(User).filter(User.id == request.patient_id).first()
            if patient:
                import asyncio
                import concurrent.futures
                
                # Get service name for email
                service = self.db.query(Service).filter(Service.id == request.service_id).first()
                service_name = service.name if service else "Appointment"
                
                # Store values needed for notification (don't pass db session to thread)
                patient_id_str = str(request.patient_id)
                request_id_str = str(request_id)
                doctor_name_str = current_user.name if hasattr(current_user, 'name') else "Doctor"
                appointment_date_str = request.preferred_date.isoformat()
                appointment_time_str = request.preferred_time.isoformat()
                price_amount_float = float(request.price_amount) if request.price_amount else 0.0
                currency_str = request.currency
                consultation_mode_str = request.consultation_mode
                
                # Run async notification in thread pool to avoid event loop conflicts
                def run_patient_notification():
                    try:
                        # Create new database session for this thread
                        from app.core.database import SessionLocal
                        db = SessionLocal()
                        try:
                            # Create new event loop for this thread
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(
                                    send_appointment_acceptance_notification(
                                        db=db,
                                        patient_id=patient_id_str,
                                        request_id=request_id_str,
                                        doctor_name=doctor_name_str,
                                        appointment_date=appointment_date_str,
                                        appointment_time=appointment_time_str,
                                        price_amount=price_amount_float,
                                        currency=currency_str,
                                        service_name=service_name,
                                        consultation_mode=consultation_mode_str
                                    )
                                )
                            finally:
                                loop.close()
                        finally:
                            db.close()
                    except Exception as e:
                        logger.error(f"Error in patient notification thread: {str(e)}", exc_info=True)
                
                # Run in background thread (don't wait for completion)
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                executor.submit(run_patient_notification)
                executor.shutdown(wait=False)  # Don't wait for completion
        except Exception as e:
            logger.warning(f"Failed to trigger patient notification: {str(e)}", exc_info=True)
        
        return request
    
    def reject_request(
        self,
        current_user: CurrentUser,
        request_id: UUID,
        rejection_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AppointmentRequest:
        """
        Reject an appointment request
        
        Rules:
        - Only assigned doctor can reject
        - Updates status to REJECTED
        - Closes request permanently
        
        Args:
            current_user: Current doctor user
            request_id: Request ID
            rejection_reason: Optional rejection reason
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated AppointmentRequest object
        """
        # Validate doctor role
        if current_user.role != UserRole.DOCTOR.value:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors can reject appointment requests"]}
            )
        
        # Get request
        request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.id == request_id,
            AppointmentRequest.deleted_at.is_(None)
        ).first()
        
        if not request:
            raise NotFoundException(
                message="Appointment request not found",
                errors={"request_id": ["Request does not exist"]}
            )
        
        # Validate ownership
        # Compare as strings to avoid UUID type mismatch issues
        # current_user.id is string, request.doctor_id is UUID object
        try:
            # Convert both to strings and normalize
            current_user_id_str = str(current_user.id).strip()
            doctor_id_str = str(request.doctor_id).strip()
            
            # Remove any hyphens and compare (in case of formatting differences)
            current_user_id_clean = current_user_id_str.replace('-', '').lower()
            doctor_id_clean = doctor_id_str.replace('-', '').lower()
            
            # Also compare as-is (case-insensitive)
            ids_match = (
                current_user_id_str.lower() == doctor_id_str.lower() or
                current_user_id_clean == doctor_id_clean
            )
            
            # Debug logging
            logger.info(
                f"Reject request ownership check: request_id={request_id}, "
                f"current_user.id={current_user.id} (type: {type(current_user.id)}), "
                f"request.doctor_id={request.doctor_id} (type: {type(request.doctor_id)}), "
                f"current_user_id_str={current_user_id_str}, doctor_id_str={doctor_id_str}, "
                f"ids_match={ids_match}"
            )
            
            if not ids_match:
                logger.warning(
                    f"Ownership validation failed for request {request_id}: "
                    f"doctor_id={doctor_id_str}, current_user_id={current_user_id_str}, "
                    f"doctor_id_clean={doctor_id_clean}, current_user_id_clean={current_user_id_clean}"
                )
                raise ForbiddenException(
                    message="Access denied",
                    errors={"request_id": ["You can only reject your own appointment requests"]}
                )
        except Exception as e:
            logger.error(f"Error in ownership validation: {str(e)}", exc_info=True)
            raise ForbiddenException(
                message="Access denied",
                errors={"request_id": ["Error validating request ownership"]}
            )
        
        # Validate status
        if request.status != 'PENDING':
            raise BadRequestException(
                message="Request cannot be rejected",
                errors={"status": [f"Request is already {request.status.lower()}. Only pending requests can be rejected."]}
            )
        
        # Update status to REJECTED
        request.status = 'REJECTED'
        request.rejection_reason = rejection_reason
        
        self.db.commit()
        self.db.refresh(request)
        
        # Audit log: Request rejected (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=current_user.id,
            action="APPOINTMENT_REQUEST_REJECTED",
            entity_type="appointment_request",
            entity_id=request.id,
            audit_metadata={
                "appointment_request_id": str(request.id),
                "patient_id": str(request.patient_id),
                "service_id": str(request.service_id),
                "has_rejection_reason": rejection_reason is not None
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Appointment request {request_id} rejected by doctor {current_user.id}")
        
        # Trigger notification to patient (async, don't wait)
        import asyncio
        try:
            patient = self.db.query(User).filter(User.id == request.patient_id).first()
            if patient:
                # Get service name if available
                service_name = None
                if request.service:
                    service_name = request.service.name
                
                asyncio.create_task(
                    send_appointment_rejection_notification(
                        db=self.db,
                        patient_id=str(request.patient_id),
                        request_id=str(request_id),
                        doctor_name=current_user.name if hasattr(current_user, 'name') else "Doctor",
                        appointment_date=request.preferred_date.isoformat(),
                        appointment_time=request.preferred_time.isoformat(),
                        rejection_reason=rejection_reason,
                        service_name=service_name
                    )
                )
        except Exception as e:
            logger.warning(f"Failed to trigger patient notification: {str(e)}")
        
        return request
    
    def mark_notification_as_read(
        self,
        current_user: CurrentUser,
        appointment_request_id: UUID
    ) -> Dict[str, Any]:
        """
        Mark a notification as read for the current user
        
        Args:
            current_user: Current user
            appointment_request_id: Appointment request ID (notification ID)
            
        Returns:
            Dictionary with success status and read timestamp
        """
        # Verify appointment request exists
        request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.id == appointment_request_id,
            AppointmentRequest.deleted_at.is_(None)
        ).first()
        
        if not request:
            raise NotFoundException(
                message="Appointment request not found",
                errors={"appointment_request_id": ["Appointment request does not exist"]}
            )
        
        # Verify user has access to this notification
        # For doctors: must be the doctor assigned to the request
        # For patients: must be the patient who created the request
        # Convert UUIDs to strings for comparison (current_user.id is a string)
        if current_user.role == UserRole.DOCTOR.value:
            if str(request.doctor_id) != str(current_user.id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"appointment_request_id": ["You don't have access to this notification"]}
                )
        elif current_user.role == UserRole.PATIENT.value:
            if str(request.patient_id) != str(current_user.id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"appointment_request_id": ["You don't have access to this notification"]}
                )
        else:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors and patients can mark notifications as read"]}
            )
        
        # Check if already marked as read
        existing_read = self.db.query(NotificationRead).filter(
            NotificationRead.user_id == current_user.id,
            NotificationRead.appointment_request_id == appointment_request_id
        ).first()
        
        if existing_read:
            # Already read, return existing record
            return {
                "success": True,
                "read_at": existing_read.read_at.isoformat() if existing_read.read_at else None,
                "already_read": True
            }
        
        # Create new read record
        notification_read = NotificationRead(
            user_id=current_user.id,
            appointment_request_id=appointment_request_id
        )
        self.db.add(notification_read)
        self.db.commit()
        self.db.refresh(notification_read)
        
        return {
            "success": True,
            "read_at": notification_read.read_at.isoformat() if notification_read.read_at else None,
            "already_read": False
        }
    
    def mark_all_notifications_as_read(
        self,
        current_user: CurrentUser
    ) -> Dict[str, Any]:
        """
        Mark all notifications as read for the current user
        
        Args:
            current_user: Current user
            
        Returns:
            Dictionary with success status and count of marked notifications
        """
        from datetime import timezone
        
        # Get all appointment requests that the user has access to
        if current_user.role == UserRole.DOCTOR.value:
            # Get all appointment requests for this doctor
            requests = self.db.query(AppointmentRequest).filter(
                AppointmentRequest.doctor_id == current_user.id,
                AppointmentRequest.deleted_at.is_(None)
            ).all()
        elif current_user.role == UserRole.PATIENT.value:
            # Get all appointment requests for this patient
            requests = self.db.query(AppointmentRequest).filter(
                AppointmentRequest.patient_id == current_user.id,
                AppointmentRequest.deleted_at.is_(None)
            ).all()
        else:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors and patients can mark notifications as read"]}
            )
        
        # Get already read notification IDs
        already_read_ids = set(
            self.db.query(NotificationRead.appointment_request_id).filter(
                NotificationRead.user_id == current_user.id
            ).all()
        )
        already_read_ids = {req_id[0] for req_id in already_read_ids}
        
        # Mark unread notifications as read
        new_reads = []
        for request in requests:
            if request.id not in already_read_ids:
                notification_read = NotificationRead(
                    user_id=current_user.id,
                    appointment_request_id=request.id
                )
                self.db.add(notification_read)
                new_reads.append(notification_read)
        
        self.db.commit()
        
        return {
            "success": True,
            "marked_count": len(new_reads),
            "total_notifications": len(requests),
            "already_read_count": len(already_read_ids)
        }
    
    def get_unread_notification_count(
        self,
        current_user: CurrentUser
    ) -> Dict[str, Any]:
        """
        Get unread notification count for the current user
        
        Args:
            current_user: Current user
            
        Returns:
            Dictionary with unread count and total count
        """
        # Get all appointment requests that the user has access to
        if current_user.role == UserRole.DOCTOR.value:
            # Get all appointment requests for this doctor
            requests = self.db.query(AppointmentRequest).filter(
                AppointmentRequest.doctor_id == current_user.id,
                AppointmentRequest.deleted_at.is_(None)
            ).all()
        elif current_user.role == UserRole.PATIENT.value:
            # Get all appointment requests for this patient
            requests = self.db.query(AppointmentRequest).filter(
                AppointmentRequest.patient_id == current_user.id,
                AppointmentRequest.deleted_at.is_(None)
            ).all()
        else:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors and patients can view notification counts"]}
            )
        
        # Get already read notification IDs
        already_read_ids = set(
            self.db.query(NotificationRead.appointment_request_id).filter(
                NotificationRead.user_id == current_user.id
            ).all()
        )
        already_read_ids = {req_id[0] for req_id in already_read_ids}
        
        # Calculate unread count
        total_count = len(requests)
        unread_count = sum(1 for req in requests if req.id not in already_read_ids)
        read_count = total_count - unread_count
        
        return {
            "unread_count": unread_count,
            "read_count": read_count,
            "total_count": total_count
        }