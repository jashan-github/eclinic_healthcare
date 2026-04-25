"""
Webinar Payment Service
Handles Sentoo payment creation and webhook processing for webinar registrations

PAYMENT FLOW:
1. User registers for webinar -> Creates payment record if paid (15 min expiry)
2. User completes payment on Sentoo
3. Either:
   a) Success redirect -> Verify status from API -> Mark registration complete if paid
   b) Webhook received -> Verify status from API -> Mark registration complete if paid
4. Both paths check for existing payment to prevent duplicates
"""

from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger
from datetime import datetime, timezone, timedelta

from app.models.webinar_payment import WebinarPayment
from app.models.user import User
from app.services.audit_service import AuditService
from app.core.security import CurrentUser, UserRole, create_access_token, create_webinar_redirect_token
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException
)
from app.utils.sentoo_client import SentooClient
from app.core.config import settings
import httpx


# Payment expiry time in minutes
PAYMENT_EXPIRY_MINUTES = 15


class WebinarPaymentService:
    """Service for webinar payment operations using Sentoo"""
    
    def __init__(self, db: Session, sentoo_merchant_id: Optional[str] = None, sentoo_merchant_secret: Optional[str] = None):
        """Initialize webinar payment service"""
        self.db = db
        self.audit_service = AuditService(db)
        
        # Initialize Sentoo client
        if sentoo_merchant_id and sentoo_merchant_secret:
            self.sentoo_client = SentooClient(
                merchant_id=sentoo_merchant_id,
                merchant_secret=sentoo_merchant_secret,
                api_url=settings.SENTOO_API_URL
            )
        else:
            if settings.SENTOO_MERCHANT_ID and settings.SENTOO_MERCHANT_SECRET:
                self.sentoo_client = SentooClient(
                    merchant_id=settings.SENTOO_MERCHANT_ID,
                    merchant_secret=settings.SENTOO_MERCHANT_SECRET,
                    api_url=settings.SENTOO_API_URL
                )
            else:
                logger.warning("Sentoo credentials not configured")
                self.sentoo_client = None
    
    def _get_webinar_from_service(self, webinar_id: UUID) -> Dict[str, Any]:
        """
        Get webinar details from webinar service
        
        Returns:
            Webinar details dict with pricing_type, price, title, etc.
        """
        try:
            # Generate JWT token for admin to authenticate the request
            # The webinar service will validate this token
            # Use a system admin user ID (00000000-0000-0000-0000-000000000000) for internal service calls
            token_data = {
                "sub": "00000000-0000-0000-0000-000000000000",
                "user_id": "00000000-0000-0000-0000-000000000000",
                "role": UserRole.SUPER_ADMIN.value,
                "email": "system@internal"
            }
            access_token = create_access_token(data=token_data)
            
            # Make HTTP request to webinar-service
            webinar_service_url = getattr(settings, 'WEBINAR_SERVICE_URL', 'http://localhost:8002')
            url = f"{webinar_service_url}/api/v1/admin/webinars/{webinar_id}"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") and result.get("data"):
                        return result.get("data")
                    else:
                        raise NotFoundException(
                            message="Webinar not found",
                            errors={"webinar_id": ["Webinar data not available"]}
                        )
                elif response.status_code == 404:
                    raise NotFoundException(
                        message="Webinar not found",
                        errors={"webinar_id": ["Webinar with this ID does not exist"]}
                    )
                else:
                    logger.error(f"Failed to fetch webinar: HTTP {response.status_code} - {response.text}")
                    raise BadRequestException(
                        message="Unable to fetch webinar details",
                        errors={"webinar": ["Webinar service unavailable"]}
                    )
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching webinar {webinar_id} from webinar-service")
            raise BadRequestException(
                message="Webinar service timeout",
                errors={"webinar": ["Webinar service did not respond"]}
            )
        except httpx.RequestError as e:
            logger.error(f"Request error fetching webinar {webinar_id}: {str(e)}")
            raise BadRequestException(
                message="Unable to fetch webinar",
                errors={"webinar": [f"Error connecting to webinar service: {str(e)}"]}
            )
        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching webinar {webinar_id}: {str(e)}", exc_info=True)
            raise BadRequestException(
                message="Error fetching webinar",
                errors={"webinar": [str(e)]}
            )
    
    def _update_webinar_registered_count(self, webinar_id: UUID, increment: int = 1) -> None:
        """
        Update registered_count in webinar service
        
        Args:
            webinar_id: Webinar ID
            increment: Amount to increment (default: 1, use -1 to decrement)
        """
        try:
            # Generate JWT token for admin to authenticate the request
            token_data = {
                "sub": "00000000-0000-0000-0000-000000000000",
                "user_id": "00000000-0000-0000-0000-000000000000",
                "role": UserRole.SUPER_ADMIN.value,
                "email": "system@internal"
            }
            access_token = create_access_token(data=token_data)
            
            webinar_service_url = getattr(settings, 'WEBINAR_SERVICE_URL', 'http://localhost:8002')
            url = f"{webinar_service_url}/api/v1/admin/webinars/{webinar_id}/registered-count"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    url,
                    json={"increment": increment},
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Updated registered_count for webinar {webinar_id} by {increment}")
                else:
                    logger.warning(
                        f"Failed to update registered_count for webinar {webinar_id}: "
                        f"HTTP {response.status_code} - {response.text}"
                    )
        except Exception as e:
            logger.warning(f"Error updating webinar registered_count: {e}")
            # Don't fail the payment if this fails
    
    def register_for_webinar(
        self,
        current_user: CurrentUser,
        webinar_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register user for a webinar
        
        For free webinars: Immediately registers
        For paid webinars: Creates payment intent
        
        Returns:
            Registration result with payment details if paid
        """
        # Allow patients and doctors to register (doctors can attend webinars they are not hosting)
        if not current_user.has_role(UserRole.PATIENT) and not current_user.has_role(UserRole.DOCTOR):
            raise ForbiddenException(
                message="Access denied",
                errors={"access": [f"Only patients and doctors can register for webinars. Your role: {current_user.role}"]}
            )
        
        # Get webinar details from webinar service
        webinar = self._get_webinar_from_service(webinar_id)
        
        if not webinar:
            raise NotFoundException(
                message="Webinar not found",
                errors={"webinar_id": ["Webinar with this ID does not exist"]}
            )
        
        # Check if webinar is deleted or cancelled
        if webinar.get("deleted_at") or webinar.get("status") == "cancelled":
            raise BadRequestException(
                message="Webinar not available",
                errors={"webinar": ["This webinar is no longer available"]}
            )
        
        # Check if already registered (has completed payment)
        existing_payment = self.db.query(WebinarPayment).filter(
            WebinarPayment.webinar_id == webinar_id,
            WebinarPayment.user_id == current_user.id,
            WebinarPayment.status == 'COMPLETED'
        ).first()
        
        if existing_payment:
            return {
                "webinar_id": str(webinar_id),
                "user_id": str(current_user.id),
                "registered": True,
                "payment_required": False,
                "payment": None,
                "message": "You are already registered for this webinar"
            }
        
        # Handle free webinars
        pricing_type = webinar.get("pricing_type", "free")
        if pricing_type == "free":
            # For free webinars, create a COMPLETED payment record for tracking
            existing_pending = self.db.query(WebinarPayment).filter(
                WebinarPayment.webinar_id == webinar_id,
                WebinarPayment.user_id == current_user.id
            ).first()
            
            if existing_pending:
                if existing_pending.status != 'COMPLETED':
                    existing_pending.status = 'COMPLETED'
                    self.db.commit()
            else:
                free_payment = WebinarPayment(
                    webinar_id=webinar_id,
                    user_id=current_user.id,
                    amount=Decimal("0.00"),
                    currency="XCG",
                    status='COMPLETED'
                )
                self.db.add(free_payment)
                self.db.commit()
                self.db.refresh(free_payment)
            
            # Update registered count
            self._update_webinar_registered_count(webinar_id, increment=1)
            
            # Audit log
            self.audit_service.create_audit_log(
                actor_user_id=current_user.id,
                action="WEBINAR_REGISTERED",
                entity_type="webinar_payment",
                entity_id=free_payment.id if not existing_pending else existing_pending.id,
                audit_metadata={
                    "webinar_id": str(webinar_id),
                    "pricing_type": "free",
                    "amount": 0.00
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "webinar_id": str(webinar_id),
                "user_id": str(current_user.id),
                "registered": True,
                "payment_required": False,
                "payment": None,
                "message": "Successfully registered for free webinar"
            }
        
        # Handle paid webinars - initialize payment
        price = Decimal(str(webinar.get("price", 0)))
        if price <= 0:
            raise BadRequestException(
                message="Invalid webinar price",
                errors={"price": ["Paid webinar must have a price greater than 0"]}
            )
        
        # Check if payment already exists
        existing_payment = self.db.query(WebinarPayment).filter(
            WebinarPayment.webinar_id == webinar_id,
            WebinarPayment.user_id == current_user.id
        ).first()
        
        if existing_payment:
            # If payment is COMPLETED, return success
            if existing_payment.status == 'COMPLETED':
                return {
                    "webinar_id": str(webinar_id),
                    "user_id": str(current_user.id),
                    "registered": True,
                    "payment_required": False,
                    "payment": None,
                    "message": "You are already registered for this webinar"
                }
            
            # Check if payment is expired
            if existing_payment.created_at:
                expiry_time = existing_payment.created_at + timedelta(minutes=PAYMENT_EXPIRY_MINUTES)
                if datetime.now(timezone.utc) > expiry_time.replace(tzinfo=timezone.utc):
                    logger.info(f"Payment {existing_payment.id} expired, creating new payment")
                    existing_payment.status = 'EXPIRED'
                    self.db.commit()
                elif existing_payment.payment_url:
                    # Payment still valid, return existing
                    return {
                        "webinar_id": str(webinar_id),
                        "user_id": str(current_user.id),
                        "registered": False,
                        "payment_required": True,
                        "payment": {
                            "payment_id": str(existing_payment.id),
                            "sentoo_payment_id": existing_payment.sentoo_payment_id,
                            "payment_url": existing_payment.payment_url,
                            "amount": float(existing_payment.amount),
                            "currency": existing_payment.currency,
                            "status": existing_payment.status,
                            "webinar_id": str(webinar_id),
                            "webinar_title": webinar.get("title")
                        },
                        "message": "Payment already initialized. Please complete payment."
                    }
        
        # Check Sentoo client is configured
        if not self.sentoo_client:
            raise BadRequestException(
                message="Payment service not configured",
                errors={"payment": ["Sentoo payment gateway is not configured"]}
            )
        
        # Create Sentoo payment
        try:
            base_url = settings.BASE_URL.rstrip('/')
            redirect_token = create_webinar_redirect_token(current_user.id, webinar_id, expires_minutes=15)
            return_url = f"{base_url}/api/v1/patient/webinars/payment-success?webinar_id={str(webinar_id)}&redirect_token={redirect_token}"
            cancel_url = f"{base_url}/api/v1/patient/webinars/payment-cancelled?webinar_id={str(webinar_id)}&redirect_token={redirect_token}"
            description = f"Webinar registration - {webinar.get('title', 'Webinar')[:50]}"
            
            sentoo_response = self.sentoo_client.create_payment(
                amount=float(price),
                currency="XCG",
                reference_id=str(webinar_id),
                return_url=return_url,
                cancel_url=cancel_url,
                description=description,
                metadata={
                    "webinar_id": str(webinar_id),
                    "user_id": str(current_user.id),
                    "type": "webinar_registration"
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
        
        try:
            if isinstance(sentoo_response, dict) and 'success' in sentoo_response:
                success_obj = sentoo_response['success']
                if isinstance(success_obj, dict):
                    sentoo_payment_id = success_obj.get('message')
                    data_obj = success_obj.get('data', {})
                    if isinstance(data_obj, dict):
                        payment_url = data_obj.get('url')
        except Exception as e:
            logger.error(f"Error parsing Sentoo response: {str(e)}")
        
        # Create or update payment record
        if existing_payment and existing_payment.status == 'EXPIRED':
            # Update existing expired payment
            existing_payment.sentoo_payment_id = sentoo_payment_id
            existing_payment.payment_url = payment_url
            existing_payment.status = 'PENDING'
            existing_payment.idempotency_key = f"{webinar_id}_{current_user.id}_{sentoo_payment_id}" if sentoo_payment_id else f"{webinar_id}_{current_user.id}_pending"
            payment = existing_payment
        else:
            # Create new payment record
            payment = WebinarPayment(
                webinar_id=webinar_id,
                user_id=current_user.id,
                sentoo_payment_id=sentoo_payment_id,
                payment_url=payment_url,
                amount=price,
                currency="XCG",
                status='PENDING',
                idempotency_key=f"{webinar_id}_{current_user.id}_{sentoo_payment_id}" if sentoo_payment_id else f"{webinar_id}_{current_user.id}_pending"
            )
            self.db.add(payment)
        
        self.db.commit()
        self.db.refresh(payment)
        
        # Audit log
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=PAYMENT_EXPIRY_MINUTES)
        self.audit_service.create_audit_log(
            actor_user_id=current_user.id,
            action="WEBINAR_PAYMENT_INITIALIZED",
            entity_type="webinar_payment",
            entity_id=payment.id,
            audit_metadata={
                "webinar_id": str(webinar_id),
                "amount": float(price),
                "currency": "XCG",
                "expires_at": expiry_time.isoformat()
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Webinar payment initialized: {payment.id}, expires at {expiry_time}")
        
        return {
            "webinar_id": str(webinar_id),
            "user_id": str(current_user.id),
            "registered": False,
            "payment_required": True,
            "payment": {
                "payment_id": str(payment.id),
                "sentoo_payment_id": payment.sentoo_payment_id,
                "payment_url": payment.payment_url,
                "amount": float(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
                "webinar_id": str(webinar_id),
                "webinar_title": webinar.get("title")
            },
            "message": "Payment initialized. Please complete payment to register."
        }
    
    def verify_and_complete_payment(
        self,
        current_user: CurrentUser,
        webinar_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify payment status from Sentoo API and complete registration if paid
        
        Called after user returns from Sentoo payment page.
        """
        # Get payment record
        payment = self.db.query(WebinarPayment).filter(
            WebinarPayment.webinar_id == webinar_id,
            WebinarPayment.user_id == current_user.id
        ).first()
        
        if not payment:
            raise NotFoundException(
                message="Payment not found",
                errors={"webinar_id": ["No payment found for this webinar"]}
            )
        
        # Check user has access
        if str(current_user.id) != str(payment.user_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"access": ["You can only verify payment for your own registrations"]}
            )
        
        # If payment is already completed, return success
        if payment.status == 'COMPLETED':
            return {
                "status": "success",
                "payment_status": "COMPLETED",
                "is_paid": True,
                "webinar_id": str(webinar_id),
                "message": "Payment completed. You are registered for the webinar."
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
        
        # If paid, complete payment and update registration
        if is_paid or new_status == 'COMPLETED':
            old_status = payment.status
            payment.status = 'COMPLETED'
            payment.sentoo_webhook_id = payment.sentoo_payment_id
            payment.webhook_received_at = datetime.now(timezone.utc)
            self.db.commit()
            
            # Update registered count
            self._update_webinar_registered_count(webinar_id, increment=1)
            
            # Audit log
            self.audit_service.create_audit_log(
                actor_user_id=current_user.id,
                action="WEBINAR_PAYMENT_COMPLETED",
                entity_type="webinar_payment",
                entity_id=payment.id,
                audit_metadata={
                    "webinar_id": str(webinar_id),
                    "old_status": old_status,
                    "new_status": "COMPLETED",
                    "transaction_id": payment.sentoo_payment_id
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Webinar payment {payment.id} completed for webinar {webinar_id}")
            
            return {
                "status": "success",
                "payment_status": "COMPLETED",
                "is_paid": True,
                "webinar_id": str(webinar_id),
                "message": "Payment verified. You are now registered for the webinar."
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
            "webinar_id": str(webinar_id),
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
        Completes registration if payment is successful.
        
        Returns:
            Processing result
        """
        logger.info(f"Processing webinar webhook for transaction: {transaction_id}")
        
        # Find payment
        payment = self.db.query(WebinarPayment).filter(
            WebinarPayment.sentoo_payment_id == transaction_id
        ).first()
        
        if not payment:
            logger.warning(f"Webinar payment not found for transaction: {transaction_id}")
            return {"status": "payment_not_found"}
        
        # Check if already processed (idempotency)
        if payment.status == 'COMPLETED' and payment.sentoo_webhook_id == transaction_id:
            logger.info(f"Webhook already processed for transaction: {transaction_id}")
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
        
        # If paid, complete payment and update registration
        if is_paid or api_status.upper() in ['COMPLETED', 'SUCCEEDED', 'PAID']:
            old_status = payment.status
            payment.status = 'COMPLETED'
            payment.sentoo_webhook_id = transaction_id
            payment.webhook_received_at = datetime.now(timezone.utc)
            self.db.commit()
            
            # Update registered count
            self._update_webinar_registered_count(payment.webinar_id, increment=1)
            
            logger.info(f"Webinar webhook processed successfully: payment={payment.id}, webinar={payment.webinar_id}")
            return {
                "status": "success",
                "payment_id": str(payment.id),
                "webinar_id": str(payment.webinar_id)
            }
        
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
        payment.webhook_received_at = datetime.now(timezone.utc)
        self.db.commit()
        logger.info(f"Payment {payment.id} status updated: {old_status} -> {api_status}")
        
        return {"status": "updated", "payment_status": api_status}
