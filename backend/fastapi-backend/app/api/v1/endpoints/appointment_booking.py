"""
Patient Appointment Booking endpoints
API endpoints for patient appointment booking flow
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, Request
from fastapi import Request
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date, time, datetime, timezone

from app.core.dependencies import get_db, get_current_user_optional, get_current_user, get_client_ip
from app.core.security import CurrentUser, UserRole
from app.core.exceptions import laravel_response, BadRequestException, NotFoundException, ForbiddenException
from app.services.appointment_booking_service import AppointmentBookingService
from app.services.appointment_request_service import AppointmentRequestService
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.schemas.appointment_booking import (
    AppointmentBookingRequest,
    DoctorSummaryResponse,
    ConsultationTypesListResponse,
    AvailableTimeSlotsListResponse,
    AppointmentBookingSingleResponse,
    AppointmentBookingResponse,
    PatientAppointmentsGroupedResponse,
    PaymentConfirmationResponse,
    PaymentConfirmationSingleResponse
)
from app.schemas.appointment_request import (
    AppointmentRequestResponse,
    AppointmentRequestSingleResponse
)
from app.utils.waiver_helper import get_request_price_display
from loguru import logger

router = APIRouter()


@router.get(
    "/doctors/{doctor_id}/summary",
    response_model=dict,
    status_code=200,
    summary="Get doctor summary for booking",
    description="Get doctor details and pricing for appointment booking"
)
async def get_doctor_summary(
    doctor_id: UUID = Path(..., description="Doctor user ID"),
    service_id: UUID = Query(..., description="Service ID"),
    date: Optional[date] = Query(None, description="Date for pricing/availability (default: today)"),
    consultation_mode: Optional[str] = Query(None, description="Consultation mode (IN_CLINIC or TELECONSULTATION)"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Get doctor summary for appointment booking
    
    Returns doctor details including:
    - Name, profile image, specialty, years of experience, rating
    - Consultation fee, intake fee, total fee (resolved for the given date when possible)
    - Pricing based on selected consultation mode and date
    
    Query Parameters:
    - **service_id**: Service ID (required)
    - **date**: Optional date for pricing (default: today). Price is resolved for this date when the doctor has availability-specific pricing for that day.
    - **consultation_mode**: Optional consultation mode (defaults to IN_CLINIC)
    """
    booking_service = AppointmentBookingService(db)
    
    try:
        summary = booking_service.get_doctor_summary(
            doctor_id=doctor_id,
            service_id=service_id,
            consultation_mode=consultation_mode,
            booking_date=date
        )
        
        return laravel_response(
            success=True,
            message="Doctor summary retrieved successfully",
            data=summary
        )
    except Exception as e:
        logger.error(f"Error getting doctor summary: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving doctor summary",
            errors={"general": [str(e)]}
        )


@router.get(
    "/doctors/{doctor_id}/consultation-types",
    response_model=ConsultationTypesListResponse,
    status_code=200,
    summary="Get available consultation types",
    description="Get available consultation modes for a doctor-service combination"
)
async def get_consultation_types(
    doctor_id: UUID = Path(..., description="Doctor user ID"),
    service_id: UUID = Query(..., description="Service ID"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Get available consultation types for booking
    
    Returns list of available consultation modes (IN_CLINIC, TELECONSULTATION)
    with pricing for each mode.
    
    Query Parameters:
    - **service_id**: Service ID (required)
    """
    booking_service = AppointmentBookingService(db)
    
    try:
        modes = booking_service.get_available_consultation_modes(
            doctor_id=doctor_id,
            service_id=service_id
        )
        
        return laravel_response(
            success=True,
            message="Consultation types retrieved successfully",
            data={"consultation_types": modes}
        )
    except Exception as e:
        logger.error(f"Error getting consultation types: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving consultation types",
            errors={"general": [str(e)]}
        )


@router.get(
    "/doctors/{doctor_id}/time-slots",
    response_model=AvailableTimeSlotsListResponse,
    status_code=200,
    summary="Get available time slots",
    description="Get available time slots for a specific date and consultation mode"
)
async def get_available_time_slots(
    doctor_id: UUID = Path(..., description="Doctor user ID"),
    service_id: UUID = Query(..., description="Service ID"),
    preferred_date: date = Query(..., description="Preferred appointment date (YYYY-MM-DD)"),
    consultation_mode: str = Query(..., description="Consultation mode (IN_CLINIC or TELECONSULTATION)"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Get available time slots for booking
    
    Returns list of available time slots for the specified date and consultation mode.
    Only returns bookable times based on doctor availability and service duration.
    
    Query Parameters:
    - **service_id**: Service ID (required)
    - **preferred_date**: Preferred appointment date in YYYY-MM-DD format (required)
    - **consultation_mode**: Consultation mode - IN_CLINIC or TELECONSULTATION (required)
    """
    booking_service = AppointmentBookingService(db)
    
    try:
        slots = booking_service.get_available_time_slots(
            doctor_id=doctor_id,
            service_id=service_id,
            preferred_date=preferred_date,
            consultation_mode=consultation_mode
        )
        
        return laravel_response(
            success=True,
            message="Available time slots retrieved successfully",
            data={"time_slots": slots}
        )
    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"Error getting time slots: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving time slots",
            errors={"general": [str(e)]}
        )


@router.post(
    "/appointments/request",
    response_model=AppointmentRequestSingleResponse,
    status_code=201,
    summary="Create appointment request",
    description="Create an appointment request (status: PENDING). Doctor must accept before appointment is created."
)
async def create_appointment_request(
    request_data: AppointmentBookingRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Create an appointment request
    
    Creates a request with status PENDING in the appointment_requests table.
    Doctor must accept the request before an appointment entry is created.
    Notification is sent to the doctor when request is created.
    
    Request Body:
    - **doctor_id**: Doctor user ID (required)
    - **service_id**: Service ID (required)
    - **consultation_mode**: Consultation mode - IN_CLINIC or TELECONSULTATION (required)
    - **preferred_date**: Preferred appointment date (required)
    - **preferred_time**: Preferred appointment time in HH:MM format (required)
    - **reason**: Optional reason/symptoms for appointment
    - **doctor_service_availability_id**: Optional availability assignment ID
    
    Returns:
    - Appointment request details with ID, status, and pricing
    """
    # Validate current user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only patients can create appointment requests"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        appointment_request = request_service.create_request(
            current_user=current_user,
            doctor_id=request_data.doctor_id,
            service_id=request_data.service_id,
            consultation_mode=request_data.consultation_mode,
            preferred_date=request_data.preferred_date,
            preferred_time=request_data.preferred_time,
            reason=request_data.reason,
            doctor_service_availability_id=request_data.doctor_service_availability_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent")
        )
        
        # Build response (NO PHI, no reason/symptoms); apply waiver for display
        price_after, amount_before, waiver_pct = get_request_price_display(
            db, float(appointment_request.price_amount) if appointment_request.price_amount else None,
            doctor_waiver_percent=appointment_request.waiver_percent,
        )
        response_data = AppointmentRequestResponse(
            id=appointment_request.id,
            doctor_id=appointment_request.doctor_id,
            patient_id=appointment_request.patient_id,
            service_id=appointment_request.service_id,
            clinic_id=appointment_request.clinic_id,
            preferred_date=appointment_request.preferred_date,
            preferred_time=appointment_request.preferred_time,
            consultation_mode=appointment_request.consultation_mode,
            duration_minutes=appointment_request.duration_minutes,
            status=appointment_request.status,
            price_amount=price_after,
            amount_before_waiver=amount_before,
            waiver_percent=waiver_pct,
            currency=appointment_request.currency,
            pricing_source=appointment_request.pricing_source,
            rejection_reason=appointment_request.rejection_reason,
            created_at=appointment_request.created_at.isoformat() if appointment_request.created_at else None,
            updated_at=appointment_request.updated_at.isoformat() if appointment_request.updated_at else None
        )
        
        return laravel_response(
            success=True,
            message="Appointment request created successfully",
            data=response_data
        )
    except (BadRequestException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Error creating appointment request: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error creating appointment request",
            errors={"general": [str(e)]}
        )


@router.get(
    "/appointments/grouped",
    status_code=200,
    summary="Get patient's appointments grouped by status",
    description="""
    Get patient's appointments and appointment requests grouped into three categories:
    
    **Upcoming Appointments:**
    - Appointments that have been accepted by the doctor and confirmed (appointment_date >= today)
    - Appointment requests with status ACCEPTED that haven't been paid yet (preferred_date >= today)
    - These are appointments/requests that are scheduled for future dates
    
    **Pending Appointments:**
    - Appointment requests with status PENDING (not yet accepted by the doctor)
    - These are requests waiting for doctor approval
    
    **Past Appointments:**
    - Appointments whose appointment_date has passed (appointment_date < today)
    - Only includes confirmed appointments, not requests
    
    **Patient Only Endpoint**
    - Only authenticated patients can access their own appointments
    
    Returns a Laravel-compatible response with three arrays: upcoming, pending, and past.
    """
)
async def get_patient_appointments_grouped(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get appointments grouped by status for the authenticated patient
    
    Groups appointments and appointment requests into:
    - **Upcoming**: Accepted/confirmed appointments for future dates, plus ACCEPTED requests awaiting payment
    - **Pending**: Appointment requests waiting for doctor acceptance (status: PENDING)
    - **Past**: Appointments from previous dates
    
    **Authentication Required**: Yes (Patient role)
    """
    # Ensure user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only patients can view their appointments"]}
        )

    appointment_service = AppointmentService(db)

    try:
        grouped = appointment_service.list_patient_appointments_grouped(current_user=current_user)
        return laravel_response(
            success=True,
            message="Patient appointments retrieved successfully",
            data=grouped
        )
    except Exception as e:
        logger.error(f"Error retrieving patient appointments: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving patient appointments",
            errors={"general": [str(e)]}
        )


@router.post(
    "/appointments/{appointment_request_id}/pay",
    status_code=200,
    summary="Initialize payment for appointment",
    description="""
    Initialize Sentoo payment for an accepted appointment request.
    
    **Patient Only Endpoint**
    
    **Requirements:**
    - The appointment request must belong to the authenticated patient
    - The appointment request must have status ACCEPTED (doctor has approved)
    - The appointment request must have a valid price amount
    
    **Payment Flow:**
    1. Call this endpoint to get payment URL and QR code
    2. Redirect patient to `payment_url` or display QR code
    3. Patient completes payment on Sentoo page
    4. **AUTOMATIC**: Sentoo sends webhook → Appointment is created automatically
    5. Patient is redirected back to your app
    6. Frontend can poll `/appointments/payment-status/{payment_id}` to check status
    
    **Response:**
    - **payment_id**: Our internal payment ID (use for status checks)
    - **sentoo_payment_id**: Sentoo's payment ID
    - **payment_url**: URL to redirect patient for payment
    - **qr_code**: QR code URL/data for payment (if available)
    - **amount**: Payment amount
    - **currency**: Currency code
    - **status**: Current payment status (PENDING)
    
    **Note:** The appointment is created AUTOMATICALLY when Sentoo sends the payment
    success webhook. The frontend should poll the payment status endpoint to know
    when the appointment is confirmed.
    
    **Error Cases:**
    - Request not found: Returns 404
    - Request doesn't belong to patient: Returns 403
    - Request not ACCEPTED: Returns 400
    - Invalid price: Returns 400
    - Payment already completed: Returns 400
    """
)
async def process_payment_for_appointment(
    request: Request,
    appointment_request_id: UUID = Path(..., description="Appointment request ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Initialize Sentoo payment for an accepted appointment request
    
    This endpoint initializes a Sentoo payment and returns the payment URL and QR code
    for the patient to complete the payment.
    
    **Patient only endpoint**
    
    Requirements:
    - Appointment request must belong to the authenticated patient
    - Appointment request must be in ACCEPTED status
    - Appointment request must have a valid price
    
    Path Parameters:
    - **appointment_request_id**: The ID of the appointment request to pay for
    
    Returns:
    - Payment details with payment_url and qr_code for Sentoo checkout
    """
    from app.services.payment_service import PaymentService
    from app.core.config import settings
    
    # Ensure user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only patients can process payments"]}
        )
    
    user_agent = request.headers.get("user-agent") if request else None
    
    # Check if Sentoo is configured
    if not settings.SENTOO_MERCHANT_ID or not settings.SENTOO_MERCHANT_SECRET:
        raise BadRequestException(
            message="Payment service not configured",
            errors={"payment": ["Payment gateway is not configured. Please contact support."]}
        )
    
    try:
        payment_service = PaymentService(
            db,
            sentoo_merchant_id=settings.SENTOO_MERCHANT_ID,
            sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET
        )
        
        payment_data = payment_service.initialize_payment(
            current_user=current_user,
            request_id=appointment_request_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return laravel_response(
            success=True,
            message="Payment initialized successfully. Please complete the payment.",
            data={
                "payment_id": payment_data["payment_id"],
                "sentoo_payment_id": payment_data["sentoo_payment_id"],
                "payment_url": payment_data["payment_url"],
                "qr_code": payment_data.get("qr_code"),
                "amount": payment_data["amount"],
                "currency": payment_data["currency"],
                "status": payment_data["status"],
                "appointment_request_id": str(appointment_request_id),
                "instructions": "Complete the payment using the payment_url or scan the QR code. After payment, call /appointments/verify-payment/{payment_id} to verify and confirm your appointment."
            }
        )
    except (NotFoundException, ForbiddenException, BadRequestException) as e:
        raise
    except Exception as e:
        # Get full error details
        import traceback
        error_type = type(e).__name__
        error_message = str(e)
        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        
        # Log with full traceback
        logger.error(
            f"ERROR initializing payment for appointment request {appointment_request_id}",
            exc_info=True
        )
        logger.error(f"Error type: {error_type}, Message: {error_message}")
        logger.error(f"Full traceback:\n{tb_str}")
        
        # Print to stderr as well (will show in server logs)
        import sys
        print(f"CRITICAL ERROR in payment endpoint: {error_type}: {error_message}", file=sys.stderr)
        print(f"Traceback:\n{tb_str}", file=sys.stderr)
        
        # Re-raise as BadRequestException with full error details for debugging
        raise BadRequestException(
            message=f"Error initializing payment: {error_type}: {error_message}",
            errors={
                "general": [f"{error_type}: {error_message}"], 
                "error_type": [error_type], 
                "error_message": [error_message],
                "traceback": [tb_str[:1000]]
            }
        )


@router.get(
    "/appointments/payment-success",
    status_code=200,
    summary="Payment redirect handler (handles all attempt types)",
    description="""
    Handle redirect from Sentoo after payment attempt.
    
    Sentoo redirects with ?attempt=success|pending|cancelled|rejected
    This endpoint ALWAYS verifies payment status via API (never trusts URL parameter).
    
    Query Parameters:
    - **payment_id**: Appointment request ID (used to find the payment)
    - **attempt**: Sentoo attempt status (success, pending, cancelled, rejected) - NOT TRUSTED, only for logging
    """
)
async def payment_success_redirect(
    payment_id: str = Query(..., description="Appointment request ID (may have suffix appended by Sentoo)"),
    attempt: Optional[str] = Query(None, description="Sentoo attempt status (not trusted, only for logging)"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Handle payment redirect from Sentoo
    
    CRITICAL: This endpoint ALWAYS verifies payment status from Sentoo API.
    The 'attempt' parameter in the URL is NOT trusted.
    
    Flow:
    1. Extract payment_id from URL
    2. Verify payment status from Sentoo API
    3. Create appointment if payment is successful
    4. Redirect to frontend with actual status
    """
    from app.services.payment_service import PaymentService
    from app.core.config import settings
    from fastapi.responses import RedirectResponse
    from app.models.appointment_payment import AppointmentPayment
    
    logger.info(f"Payment redirect received: payment_id={payment_id}, attempt={attempt}")
    
    # Clean payment_id (remove suffixes Sentoo might append)
    clean_payment_id = payment_id
    for suffix in ['success', 'pending', 'cancelled', 'cancel', 'rejected']:
        if payment_id.endswith(suffix):
            clean_payment_id = payment_id[:-len(suffix)]
            break
    
    # Validate UUID
    try:
        request_uuid = UUID(clean_payment_id)
    except ValueError:
        logger.error(f"Invalid payment_id format: {payment_id}")
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/app/payment/failure?reason=invalid_payment_id")
    
    # Check Sentoo config
    if not settings.SENTOO_MERCHANT_ID or not settings.SENTOO_MERCHANT_SECRET:
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/app/payment/failure?reason=service_not_configured")
    
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    
    try:
        # Get payment
        payment = db.query(AppointmentPayment).filter(
            AppointmentPayment.appointment_request_id == request_uuid
        ).first()
        
        if not payment:
            logger.warning(f"Payment not found for request: {request_uuid}")
            return RedirectResponse(url=f"{frontend_url}/app/payment/failure?payment_id={str(request_uuid)}&reason=payment_not_found")
        
        # Use PaymentService to verify and create appointment
        payment_service = PaymentService(
            db,
            sentoo_merchant_id=settings.SENTOO_MERCHANT_ID,
            sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET
        )
        
        # Process the redirect - this verifies status and creates appointment if paid
        result = payment_service.process_payment_success_redirect(payment, db)
        
        is_paid = result.get('is_paid', False)
        status = result.get('status', 'UNKNOWN')
        appointment_id = result.get('appointment_id')
        
        logger.info(f"Redirect processed: is_paid={is_paid}, status={status}, appointment_id={appointment_id}")
        
        # Redirect based on result
        if is_paid:
            redirect_url = f"{frontend_url}/app/payment/success?payment_id={str(request_uuid)}&status=COMPLETED"
            if appointment_id:
                redirect_url += f"&appointment_id={appointment_id}"
            logger.info(f"Payment successful - redirecting to: {redirect_url}")
            return RedirectResponse(url=redirect_url)
        elif status in ['FAILED', 'CANCELLED', 'EXPIRED']:
            logger.info(f"Payment {status} - redirecting to failure page")
            return RedirectResponse(url=f"{frontend_url}/app/payment/failure?payment_id={str(request_uuid)}&status={status}")
        else:
            logger.info(f"Payment pending ({status}) - redirecting to processing page")
            return RedirectResponse(url=f"{frontend_url}/app/payment/processing?payment_id={str(request_uuid)}&status={status}")
            
    except Exception as e:
        logger.error(f"Error handling payment redirect: {str(e)}", exc_info=True)
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/app/payment/failure?payment_id={payment_id}&reason=verification_failed")


@router.get(
    "/appointments/payment-cancelled",
    status_code=200,
    summary="Payment cancelled redirect handler",
    description="""
    Handle redirect from Sentoo when payment is cancelled.
    
    Query Parameters:
    - **payment_id**: Appointment request ID
    """
)
async def payment_cancelled_redirect(
    payment_id: str = Query(..., description="Appointment request ID (may have suffix appended by Sentoo)"),
    db: Session = Depends(get_db)
):
    """
    Handle payment cancelled redirect from Sentoo
    """
    from app.core.config import settings
    from fastapi.responses import RedirectResponse
    
    # Handle Sentoo appending suffixes to the payment_id
    # Remove common suffixes if present
    clean_payment_id = payment_id
    for suffix in ['success', 'cancelled', 'cancel']:
        if payment_id.endswith(suffix):
            clean_payment_id = payment_id[:-len(suffix)]
            break
    
    # Validate UUID format
    try:
        request_uuid = UUID(clean_payment_id)
    except ValueError:
        logger.error(f"Invalid payment_id format: {payment_id}")
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/app/payment/failure?payment_id={payment_id}&reason=invalid_payment_id")
    
    return RedirectResponse(url=f"{settings.BASE_URL.rstrip('/')}/payment-cancelled?payment_id={str(request_uuid)}")


@router.get(
    "/appointments/payment-status/{request_id}",
    status_code=200,
    summary="Get payment status for frontend",
    description="""
    Get current payment status for an appointment request.
    
    This endpoint is used by the frontend to:
    - Display appropriate UI based on payment status
    - Determine if retry button should be shown
    - Check if payment is still pending (for polling)
    
    Returns:
    - payment_status: COMPLETED, PENDING, FAILED, CANCELLED, etc.
    - is_paid: Boolean indicating if payment is complete
    - can_retry: Boolean indicating if user can retry payment
    - appointment_id: ID of created appointment (if payment successful)
    """
)
async def get_payment_status(
    request_id: UUID = Path(..., description="Appointment request ID"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Get payment status for frontend display
    
    This endpoint:
    1. Fetches payment record
    2. Verifies status from Sentoo API (if sentoo_payment_id exists)
    3. Returns status information for frontend UI
    """
    from app.services.payment_service import PaymentService
    from app.core.config import settings
    from app.models.appointment_payment import AppointmentPayment
    from app.models.appointment import Appointment
    from app.models.appointment_request import AppointmentRequest
    
    # Get payment record
    payment = db.query(AppointmentPayment).filter(
        AppointmentPayment.appointment_request_id == request_id
    ).first()
    
    if not payment:
        return laravel_response(
            success=False,
            message="Payment not found",
            errors={"payment": ["No payment record found for this appointment request"]}
        )
    
    # Get appointment request to check access
    request = db.query(AppointmentRequest).filter(
        AppointmentRequest.id == request_id
    ).first()
    
    if not request:
        return laravel_response(
            success=False,
            message="Appointment request not found",
            errors={"request": ["Appointment request not found"]}
        )
    
    # Check access (patient or doctor)
    if current_user:
        if str(current_user.id) != str(request.patient_id) and str(current_user.id) != str(request.doctor_id):
            if not current_user.has_role(UserRole.ADMIN):
                return laravel_response(
                    success=False,
                    message="Access denied",
                    errors={"access": ["You do not have permission to view this payment"]}
                )
    
    # Verify payment status from Sentoo API if available
    actual_status = payment.status
    is_paid = (payment.status == 'COMPLETED')
    sentoo_raw_status = None
    
    if payment.sentoo_payment_id and settings.SENTOO_MERCHANT_ID and settings.SENTOO_MERCHANT_SECRET:
        try:
            payment_service = PaymentService(
                db,
                sentoo_merchant_id=settings.SENTOO_MERCHANT_ID,
                sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET
            )
            sentoo_status = payment_service.sentoo_client.verify_transaction_status(payment.sentoo_payment_id)
            sentoo_raw_status = sentoo_status.get('status', 'UNKNOWN')
            is_paid = sentoo_status.get('is_paid', False)
            
            logger.info(f"Sentoo API response for payment {payment.id}: status={sentoo_raw_status}, is_paid={is_paid}")
            
            # Map Sentoo status to our database status
            status_mapping = {
                'COMPLETED': 'COMPLETED',
                'SUCCEEDED': 'COMPLETED',
                'PAID': 'COMPLETED',
                'PENDING': 'PENDING',
                'PROCESSING': 'PENDING',
                'FAILED': 'FAILED',
                'CANCELLED': 'FAILED',
                'CANCELED': 'FAILED',
                'REJECTED': 'FAILED'
            }
            
            # Use is_paid flag as primary indicator
            if is_paid:
                new_status = 'COMPLETED'
            else:
                new_status = status_mapping.get(sentoo_raw_status.upper() if sentoo_raw_status else 'UNKNOWN', 'PENDING')
            
            actual_status = new_status
            
            # Update database status if it changed
            if payment.status != new_status:
                old_status = payment.status
                payment.status = new_status
                db.commit()
                logger.info(f"Updated payment {payment.id} status from {old_status} to {new_status} (Sentoo: {sentoo_raw_status}, is_paid: {is_paid})")
            else:
                logger.info(f"Payment {payment.id} status unchanged: {payment.status} (Sentoo: {sentoo_raw_status}, is_paid: {is_paid})")
        except Exception as e:
            logger.error(f"Failed to verify payment status from API: {str(e)}", exc_info=True)
            # Use database status as fallback
            logger.warning(f"Using database status as fallback: {payment.status}")
    
    # Determine if retry is allowed
    # TC003: Can retry if payment is cancelled/rejected/failed
    # TC001, TC002: Cannot retry if payment is pending or completed
    can_retry = actual_status in ['FAILED', 'CANCELLED', 'CANCELED', 'REJECTED']
    
    # Check if appointment was created
    appointment_id = None
    if is_paid:
        appointment = db.query(Appointment).filter(
            Appointment.doctor_id == request.doctor_id,
            Appointment.patient_id == request.patient_id,
            Appointment.appointment_date == request.preferred_date,
            Appointment.start_time == request.preferred_time,
            Appointment.deleted_at.is_(None)
        ).first()
        if appointment:
            appointment_id = str(appointment.id)
    
    return laravel_response(
        success=True,
        message="Payment status retrieved successfully",
        data={
            "payment_status": actual_status,
            "is_paid": is_paid,
            "can_retry": can_retry,
            "appointment_id": appointment_id,
            "amount": float(payment.amount) if payment.amount else None,
            "currency": payment.currency,
            "payment_id": str(payment.id),
            "sentoo_payment_id": payment.sentoo_payment_id
        }
    )


@router.get(
    "/appointments/payment-success",
    status_code=200,
    summary="Payment success redirect handler",
    description="""
    Handle redirect from Sentoo after successful payment.
    
    This endpoint is called when Sentoo redirects the user back after payment.
    It verifies the payment status and redirects to the frontend success page.
    
    Query Parameters:
    - **payment_id**: Appointment request ID (used to find the payment)
    """
)
async def payment_success_redirect(
    payment_id: UUID = Query(..., description="Appointment request ID"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Handle payment success redirect from Sentoo
    
    This endpoint:
    1. Verifies the payment status from Sentoo API
    2. Creates the appointment if payment is successful
    3. Redirects to frontend success page
    """
    from app.services.payment_service import PaymentService
    from app.core.config import settings
    from fastapi.responses import RedirectResponse
    from app.models.appointment_payment import AppointmentPayment
    
    # Handle Sentoo appending "success" to the payment_id
    # Remove "success" if it's appended
    clean_payment_id = payment_id
    if payment_id.endswith('success'):
        clean_payment_id = payment_id[:-7]  # Remove "success" suffix
    
    # Validate UUID format
    try:
        request_uuid = UUID(clean_payment_id)
    except ValueError:
        logger.error(f"Invalid payment_id format: {payment_id}")
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/app/payment/failure?payment_id={payment_id}&reason=invalid_payment_id")
    
    # Check if Sentoo is configured
    if not settings.SENTOO_MERCHANT_ID or not settings.SENTOO_MERCHANT_SECRET:
        # Redirect to error page if payment service not configured
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/app/payment/failure?payment_id={str(request_uuid)}&reason=service_not_configured")
    
    try:
        payment_service = PaymentService(
            db,
            sentoo_merchant_id=settings.SENTOO_MERCHANT_ID,
            sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET
        )
        
        # Get payment by appointment_request_id
        payment = db.query(AppointmentPayment).filter(
            AppointmentPayment.appointment_request_id == request_uuid
        ).first()
        
        if not payment:
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            return RedirectResponse(url=f"{frontend_url}/app/payment/failure?payment_id={str(request_uuid)}&reason=payment_not_found")
        
        # Verify payment status if user is authenticated
        if current_user:
            try:
                result = payment_service.verify_and_complete_payment(
                    current_user=current_user,
                    payment_id=payment.id,
                    ip_address=None,
                    user_agent=None
                )
            except Exception as e:
                logger.error(f"Error verifying payment in redirect: {str(e)}")
                result = {"is_paid": payment.status == 'COMPLETED'}
        else:
            # If not authenticated, just check if payment is completed
            result = {"is_paid": payment.status == 'COMPLETED'}
        
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        if result.get("is_paid"):
            # Redirect to success page
            return RedirectResponse(url=f"{frontend_url}/app/payment/success?payment_id={str(request_uuid)}")
        else:
            # Redirect to processing page
            return RedirectResponse(url=f"{frontend_url}/app/payment/processing?payment_id={str(request_uuid)}")
            
    except Exception as e:
        logger.error(f"Error handling payment success redirect: {str(e)}", exc_info=True)
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/app/payment/failure?payment_id={payment_id}&reason=verification_failed")


@router.get(
    "/appointments/payment-cancelled",
    status_code=200,
    summary="Payment cancelled redirect handler",
    description="""
    Handle redirect from Sentoo when payment is cancelled.
    
    Query Parameters:
    - **payment_id**: Appointment request ID
    """
)
async def payment_cancelled_redirect(
    payment_id: str = Query(..., description="Appointment request ID (may have suffix appended by Sentoo)"),
    db: Session = Depends(get_db)
):
    """
    Handle payment cancelled redirect from Sentoo
    """
    from app.core.config import settings
    from fastapi.responses import RedirectResponse
    
    # Handle Sentoo appending suffixes to the payment_id
    # Remove common suffixes if present
    clean_payment_id = payment_id
    for suffix in ['success', 'cancelled', 'cancel']:
        if payment_id.endswith(suffix):
            clean_payment_id = payment_id[:-len(suffix)]
            break
    
    # Validate UUID format
    try:
        request_uuid = UUID(clean_payment_id)
    except ValueError:
        logger.error(f"Invalid payment_id format: {payment_id}")
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/app/payment/failure?payment_id={payment_id}&reason=invalid_payment_id")
    
    return RedirectResponse(url=f"{settings.BASE_URL.rstrip('/')}/payment-cancelled?payment_id={str(request_uuid)}")


@router.post(
    "/appointments/verify-payment/{payment_id}",
    status_code=200,
    summary="Manually verify payment (fallback)",
    description="""
    Manually verify payment status from Sentoo API - USE ONLY AS FALLBACK.
    
    **Patient Only Endpoint**
    
    **Note:** Normally, the appointment is created AUTOMATICALLY via webhook when
    payment succeeds. This endpoint is a FALLBACK for cases where:
    - Webhook delivery failed
    - Network issues prevented webhook processing
    - You need to manually trigger verification
    
    **Recommended Flow:**
    1. After payment, poll `/appointments/payment-status/{payment_id}` 
    2. If status is COMPLETED, appointment was created via webhook
    3. Only call this endpoint if webhook seems to have failed
    
    **Process:**
    1. Fetches actual payment status from Sentoo API
    2. If payment is completed but appointment doesn't exist:
       - Creates confirmed appointment
       - Sends confirmation notification
    3. Returns current status
    
    **Response:**
    - **status**: "success" | "pending" | "already_completed"
    - **payment_status**: COMPLETED | PENDING | FAILED | CANCELLED
    - **is_paid**: Boolean indicating if payment is complete
    - **appointment_id**: Appointment ID (if payment successful)
    - **message**: Human-readable status message
    """
)
async def verify_payment_and_confirm(
    request: Request,
    payment_id: UUID = Path(..., description="Payment ID (our internal ID, not Sentoo's)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Verify payment status from Sentoo API and confirm appointment if paid
    
    This endpoint should be called after the patient returns from Sentoo payment page.
    It verifies the actual payment status from Sentoo API (not URL parameters) and
    creates the confirmed appointment if payment is successful.
    
    **Patient only endpoint**
    
    Path Parameters:
    - **payment_id**: Our internal payment ID (returned from /appointments/{id}/pay)
    
    Returns:
    - Payment verification result with appointment details if successful
    """
    from app.services.payment_service import PaymentService
    from app.core.config import settings
    
    # Ensure user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only patients can verify payments"]}
        )
    
    user_agent = request.headers.get("user-agent") if request else None
    
    # Check if Sentoo is configured
    if not settings.SENTOO_MERCHANT_ID or not settings.SENTOO_MERCHANT_SECRET:
        raise BadRequestException(
            message="Payment service not configured",
            errors={"payment": ["Payment gateway is not configured. Please contact support."]}
        )
    
    try:
        payment_service = PaymentService(
            db,
            sentoo_merchant_id=settings.SENTOO_MERCHANT_ID,
            sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET
        )
        
        result = payment_service.verify_and_complete_payment(
            current_user=current_user,
            payment_id=payment_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Determine appropriate message based on status
        if result.get("is_paid"):
            message = "Payment verified successfully. Appointment confirmed."
        else:
            message = result.get("message", "Payment verification completed.")
        
        return laravel_response(
            success=result.get("is_paid", False),
            message=message,
            data=result
        )
    except (NotFoundException, ForbiddenException, BadRequestException) as e:
        raise
    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_message = str(e)
        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        
        logger.error(f"ERROR verifying payment {payment_id}", exc_info=True)
        
        raise BadRequestException(
            message=f"Error verifying payment: {error_type}: {error_message}",
            errors={
                "general": [f"{error_type}: {error_message}"],
                "traceback": [tb_str[:500]]
            }
        )


@router.get(
    "/appointments/payment-status/{payment_id}",
    status_code=200,
    summary="Get payment status (poll this after payment)",
    description="""
    Get current payment status and appointment info if created.
    
    **Patient Only Endpoint**
    
    **Recommended Usage:**
    Poll this endpoint after patient completes payment on Sentoo to check if
    the appointment has been created via webhook.
    
    **Response:**
    - **payment_id**: Our internal payment ID
    - **sentoo_payment_id**: Sentoo's payment ID
    - **status**: Current payment status (PENDING, COMPLETED, FAILED, CANCELLED)
    - **is_paid**: Boolean - true if payment completed
    - **appointment_id**: Appointment ID if created (null if not yet)
    - **appointment_confirmed**: Boolean - true if appointment exists
    - **amount**: Payment amount
    - **currency**: Currency code
    
    **Polling Strategy:**
    - Poll every 2-3 seconds after redirect
    - Stop polling when `is_paid` is true OR status is FAILED/CANCELLED
    - If `appointment_confirmed` is true, navigate to appointment details
    """
)
async def get_payment_status(
    payment_id: UUID = Path(..., description="Payment ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current payment status and appointment info
    
    **Patient only endpoint**
    
    Use this to poll for payment completion after redirect from Sentoo.
    """
    from app.models.appointment_payment import AppointmentPayment
    from app.models.appointment_request import AppointmentRequest
    from app.models.appointment import Appointment
    
    # Get payment
    payment = db.query(AppointmentPayment).filter(
        AppointmentPayment.id == payment_id
    ).first()
    
    if not payment:
        raise NotFoundException(
            message="Payment not found",
            errors={"payment_id": ["Payment with this ID does not exist"]}
        )
    
    # Get appointment request to verify ownership
    appointment_request = db.query(AppointmentRequest).filter(
        AppointmentRequest.id == payment.appointment_request_id
    ).first()
    
    if not appointment_request:
        raise NotFoundException(
            message="Appointment request not found",
            errors={"request_id": ["Associated appointment request not found"]}
        )
    
    # Check ownership
    if str(current_user.id) != str(appointment_request.patient_id):
        raise ForbiddenException(
            message="Access denied",
            errors={"access": ["You can only view your own payment status"]}
        )
    
    # Check if appointment was created (via webhook)
    appointment = None
    if payment.status == 'COMPLETED':
        appointment = db.query(Appointment).filter(
            Appointment.doctor_id == appointment_request.doctor_id,
            Appointment.patient_id == appointment_request.patient_id,
            Appointment.appointment_date == appointment_request.preferred_date,
            Appointment.start_time == appointment_request.preferred_time,
            Appointment.deleted_at.is_(None)
        ).first()
    
    is_paid = payment.status == 'COMPLETED'
    appointment_confirmed = appointment is not None
    
    response_data = {
        "payment_id": str(payment.id),
        "appointment_request_id": str(payment.appointment_request_id),
        "sentoo_payment_id": payment.sentoo_payment_id,
        "payment_url": payment.payment_url,
        "amount": float(payment.amount) if payment.amount else None,
        "currency": payment.currency,
        "status": payment.status,
        "is_paid": is_paid,
        "appointment_confirmed": appointment_confirmed,
        "appointment_id": str(appointment.id) if appointment else None,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "updated_at": payment.updated_at.isoformat() if payment.updated_at else None
    }
    
    # Add appointment details if exists
    if appointment:
        response_data["appointment"] = {
            "id": str(appointment.id),
            "appointment_date": appointment.appointment_date.isoformat(),
            "start_time": appointment.start_time.isoformat() if appointment.start_time else None,
            "end_time": appointment.end_time.isoformat() if appointment.end_time else None,
            "status": appointment.status,
            "consultation_mode": appointment.consultation_mode
        }
    
    return laravel_response(
        success=True,
        message="Payment completed. Appointment confirmed." if appointment_confirmed else "Payment status retrieved.",
        data=response_data
        )
