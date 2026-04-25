"""
Payment endpoints
API endpoints for payment initialization and webhook handling
"""

from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from loguru import logger
import time
from datetime import datetime, timezone

from app.core.dependencies import get_db, get_current_user, get_client_ip
from app.core.security import CurrentUser, UserRole
from app.core.exceptions import laravel_response, BadRequestException, NotFoundException, ForbiddenException
from app.services.payment_service import PaymentService
from app.schemas.appointment_request import (
    PaymentInitializeResponse,
    PaymentInitializeSingleResponse
)
from app.core.config import settings
from app.models.webhook_log import WebhookLog

router = APIRouter()


@router.post(
    "/initialize",
    response_model=PaymentInitializeSingleResponse,
    status_code=200,
    summary="Initialize payment",
    description="Initialize Sentoo payment for an accepted appointment request"
)
async def initialize_payment(
    request_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Initialize payment for an accepted appointment request
    
    Creates Sentoo payment and returns payment_url for frontend.
    Only works if request status is ACCEPTED.
    
    Query Parameters:
    - **request_id**: Appointment request ID (required)
    
    Returns:
    - Payment details including payment_url for Sentoo checkout
    """
    # Check if Sentoo is configured
    if not settings.SENTOO_MERCHANT_ID or not settings.SENTOO_MERCHANT_SECRET:
        raise BadRequestException(
            message="Payment service not configured",
            errors={"payment": ["Sentoo payment gateway is not configured. Please contact support."]}
        )
    
    payment_service = PaymentService(
        db,
        sentoo_merchant_id=settings.SENTOO_MERCHANT_ID,
        sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET
    )
    
    try:
        payment_data = payment_service.initialize_payment(
            current_user=current_user,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent")
        )
        
        response_data = PaymentInitializeResponse(
            payment_id=UUID(payment_data["payment_id"]),
            sentoo_payment_id=payment_data["sentoo_payment_id"],
            payment_url=payment_data["payment_url"],
            amount=payment_data["amount"],
            currency=payment_data["currency"],
            status=payment_data["status"]
        )
        
        return laravel_response(
            success=True,
            message="Payment initialized successfully",
            data=response_data
        )
    except (BadRequestException, NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error initializing payment: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error initializing payment",
            errors={"general": [str(e)]}
        )


@router.post(
    "/webhook",
    status_code=200,
    summary="Sentoo webhook handler (single URL for all payment types)",
    description="Handle Sentoo webhook events for appointment and webinar payments. Set this as the only webhook URL in Sentoo."
)
async def sentoo_webhook(
    request: Request,
    db: Session = Depends(get_db),
    sentoo_signature: str = Header(None, alias="X-Sentoo-Signature")
):
    """
    Handle Sentoo webhook events (single endpoint for appointment and webinar payments).
    
    Sentoo sends webhooks as form-encoded data with transaction_id.
    We look up the transaction in appointment_payments first, then webinar_payments,
    and dispatch to the appropriate service. Always return {"success": true} to prevent retries.
    """
    from fastapi.responses import JSONResponse
    from app.models.appointment_payment import AppointmentPayment
    from app.models.webinar_payment import WebinarPayment
    from app.services.webinar_payment_service import WebinarPaymentService
    
    start_time = time.time()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    webhook_log = None
    transaction_id = None
    payment_type = None  # "appointment" | "webinar"
    
    # Helper to return success response
    def success_response():
        return JSONResponse(content={"success": True}, status_code=200)
    
    try:
        # Parse form data
        form_data = await request.form()
        logger.info(f"=== WEBHOOK RECEIVED ===")
        logger.info(f"Form data: {dict(form_data)}")
        logger.info(f"========================")
        
        # Extract transaction_id
        transaction_id = form_data.get('transaction_id')
        if transaction_id:
            transaction_id = transaction_id.strip('"\'')
        
        if not transaction_id:
            logger.warning("Webhook missing transaction_id")
            return success_response()
        
        logger.info(f"Processing webhook for transaction: {transaction_id}")
        
        # Create webhook log
        webhook_log = WebhookLog(
            source="sentoo",
            event_type="payment.update",
            webhook_id=transaction_id,
            raw_payload=dict(form_data),
            headers=dict(request.headers),
            processing_status="pending",
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Find payment: try appointment first, then webinar (single webhook URL in Sentoo)
        appointment_payment = db.query(AppointmentPayment).filter(
            AppointmentPayment.sentoo_payment_id == transaction_id
        ).first()
        
        if appointment_payment:
            payment_type = "appointment"
            webhook_log.payment_id = appointment_payment.id
            webhook_log.appointment_request_id = appointment_payment.appointment_request_id
            webhook_log.event_type = "payment.update"
            logger.info(f"Found appointment payment: {appointment_payment.id}")
        else:
            webinar_payment = db.query(WebinarPayment).filter(
                WebinarPayment.sentoo_payment_id == transaction_id
            ).first()
            if webinar_payment:
                payment_type = "webinar"
                webhook_log.payment_id = webinar_payment.id
                webhook_log.event_type = "webinar_payment.update"
                logger.info(f"Found webinar payment: {webinar_payment.id}")
            else:
                logger.warning(f"Payment not found for transaction: {transaction_id} (checked appointment and webinar)")
        
        db.add(webhook_log)
        db.commit()
        db.refresh(webhook_log)
        
    except Exception as e:
        logger.error(f"Error parsing webhook: {str(e)}", exc_info=True)
        return success_response()
    
    # Check Sentoo config
    if not settings.SENTOO_MERCHANT_ID or not settings.SENTOO_MERCHANT_SECRET:
        logger.error("Sentoo not configured")
        if webhook_log:
            webhook_log.processing_status = "error"
            webhook_log.error_message = "Sentoo not configured"
            db.commit()
        return success_response()
    
    # Dispatch to appropriate service
    try:
        if payment_type == "appointment":
            payment_service = PaymentService(
                db,
                sentoo_merchant_id=settings.SENTOO_MERCHANT_ID,
                sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET
            )
            result = payment_service.process_webhook_by_transaction_id(
                transaction_id=transaction_id,
                webhook_id=transaction_id
            )
        elif payment_type == "webinar":
            webinar_payment_service = WebinarPaymentService(
                db,
                sentoo_merchant_id=settings.SENTOO_MERCHANT_ID,
                sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET
            )
            result = webinar_payment_service.process_webhook_by_transaction_id(
                transaction_id=transaction_id,
                webhook_id=transaction_id
            )
        else:
            result = {"status": "payment_not_found"}
        
        processing_time = (time.time() - start_time) * 1000
        
        # Update webhook log
        if webhook_log:
            if result.get("status") == "error":
                webhook_log.processing_status = "error"
            elif result.get("status") == "payment_not_found" or payment_type is None:
                webhook_log.processing_status = "ignored"
            else:
                webhook_log.processing_status = "success"
            webhook_log.response_status = "200"
            webhook_log.response_body = {"success": True, "result": result, "payment_type": payment_type or "unknown"}
            webhook_log.processing_time_ms = f"{processing_time:.2f}"
            db.commit()
        
        logger.info(f"Webhook processed ({payment_type or 'none'}): {result}")
        
        # CRITICAL: Return success to Sentoo
        return success_response()
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        
        if webhook_log:
            webhook_log.processing_status = "error"
            webhook_log.error_message = str(e)
            webhook_log.response_status = "200"
            db.commit()
        
        # Still return success to prevent retries
        return success_response()


@router.get(
    "/{payment_id}",
    summary="Get payment details",
    description="Retrieve payment details by payment ID"
)
async def get_payment_details(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get payment details by ID
    
    Path Parameters:
    - **payment_id**: Payment ID (UUID)
    
    Returns:
    - Payment details
    """
    from app.models.appointment_payment import AppointmentPayment
    from app.models.appointment_request import AppointmentRequest
    
    payment = db.query(AppointmentPayment).filter(
        AppointmentPayment.id == payment_id
    ).first()
    
    if not payment:
        raise NotFoundException(
            message="Payment not found",
            errors={"payment_id": ["Payment with this ID does not exist"]}
        )
    
    # Check access - must be patient who owns the request or doctor
    request = db.query(AppointmentRequest).filter(
        AppointmentRequest.id == payment.appointment_request_id
    ).first()
    
    if not request:
        raise NotFoundException(
            message="Appointment request not found",
            errors={"request_id": ["Associated appointment request not found"]}
        )
    
    if not (current_user.id == request.patient_id or 
            current_user.id == request.doctor_id or 
            current_user.has_role(UserRole.ADMIN)):
        raise ForbiddenException(
            message="Access denied",
            errors={"access": ["You do not have permission to view this payment"]}
        )
    
    return laravel_response(
        success=True,
        message="Payment details retrieved successfully",
        data={
            "payment": {
                "id": str(payment.id),
                "appointment_request_id": str(payment.appointment_request_id),
                "sentoo_payment_id": payment.sentoo_payment_id,
                "payment_url": payment.payment_url,
                "amount": float(payment.amount) if payment.amount else None,
                "currency": payment.currency,
                "status": payment.status,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "updated_at": payment.updated_at.isoformat() if payment.updated_at else None
            }
        }
    )
