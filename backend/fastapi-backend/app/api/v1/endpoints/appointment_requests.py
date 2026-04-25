"""
Appointment Request endpoints
API endpoints for appointment request → approval → payment flow
"""

from decimal import Decimal
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, Query, Request, Path
from fastapi import Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_db, get_current_user, get_client_ip, require_feature
from app.utils.waiver_helper import get_request_price_display
from app.core.security import CurrentUser, UserRole
from app.core.exceptions import laravel_response, BadRequestException, NotFoundException, ForbiddenException
from app.services.appointment_request_service import AppointmentRequestService
from app.services.admin_settings_service import AdminSettingsService
from app.schemas.appointment_request import (
    ACCEPT_WAIVER_CHOICES,
    AppointmentRequestAccept,
    AppointmentRequestCreate,
    AppointmentRequestReject,
    AppointmentRequestResponse,
    AppointmentRequestListResponse,
    AppointmentRequestSingleResponse,
    AppointmentNotificationListResponse,
    AppointmentRequestStatisticsResponse,
    AppointmentRequestStatisticsSingleResponse,
    PaymentDetailsResponse,
    PaymentDetailsSingleResponse,
    VisitResponse,
    VisitSingleResponse,
    UnreadNotificationCountResponse,
    UnreadNotificationCountSingleResponse,
)
from app.services.payment_service import PaymentService
from app.services.appointment_service import AppointmentService
from app.models.appointment_payment import AppointmentPayment
from app.models.appointment import Appointment
from app.core.config import settings
from loguru import logger

router = APIRouter()




@router.get(
    "/requests/waiver-settings",
    status_code=200,
    summary="Get waiver settings relevant for doctors",
    description="Returns whether waiver is enabled and if doctor must decide the waiver at accept time.",
)
async def get_doctor_waiver_settings(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Doctor-accessible waiver settings.

    Returns:
    - waiver_enabled: whether waiver feature is enabled
    - waiver_doctor_decides: when True, doctor must choose waiver at accept
    - waiver_choices: allowed waiver percentages for doctor (0, 25, 50, 75, 100)
    """
    if current_user.role != UserRole.DOCTOR.value:
        raise ForbiddenException(
            message="Access denied",
            errors={"role": ["Only doctors can view doctor waiver settings"]},
        )

    settings = AdminSettingsService(db).get_settings()
    data = {
        "waiver_enabled": bool(settings.waiver_enabled),
        "waiver_doctor_decides": bool(getattr(settings, "waiver_doctor_decides", False)),
        "waiver_choices": list(ACCEPT_WAIVER_CHOICES),
    }
    return laravel_response(
        success=True,
        message="Doctor waiver settings retrieved successfully",
        data=data,
    )



@router.post(
    "/requests",
    response_model=AppointmentRequestSingleResponse,
    status_code=201,
    summary="Create appointment request",
    description="Create an appointment request (status: PENDING). Does NOT create confirmed appointment or payment intent."
)
async def create_appointment_request(
    request_data: AppointmentRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Create an appointment request
    
    Creates a request with status PENDING. Doctor must accept before payment.
    
    Request Body:
    - **doctor_id**: Doctor user ID (required)
    - **service_id**: Service ID (required)
    - **consultation_mode**: Consultation mode - IN_CLINIC or TELECONSULTATION (required)
    - **preferred_date**: Preferred appointment date (required)
    - **preferred_time**: Preferred appointment time in HH:MM format (required)
    - **reason**: Optional reason/symptoms for appointment (HIPAA-protected, never logged)
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
    "/requests",
    response_model=AppointmentRequestListResponse,
    status_code=200,
    summary="List appointment requests",
    description="List appointment requests for the authenticated user (doctor or patient)"
)
async def list_appointment_requests(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, ACCEPTED, REJECTED)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List appointment requests
    
    For doctors: Returns incoming requests (default: PENDING only)
    For patients: Returns own requests
    
    Query Parameters:
    - **status**: Optional status filter (PENDING, ACCEPTED, REJECTED)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    """
    request_service = AppointmentRequestService(db)
    
    try:
        if current_user.role == UserRole.DOCTOR.value:
            result = request_service.list_doctor_requests(
                current_user=current_user,
                status=status,
                page=page,
                limit=limit
            )
        else:
            # For patients, list their own requests
            # TODO: Implement patient request listing if needed
            raise BadRequestException(
                message="Not implemented",
                errors={"role": ["Patient request listing not yet implemented"]}
            )
        
        return laravel_response(
            success=True,
            message="Appointment requests retrieved successfully",
            data=result
        )
    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"Error listing appointment requests: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving appointment requests",
            errors={"general": [str(e)]}
        )


@router.get(
    "/requests/{request_id}",
    response_model=AppointmentRequestSingleResponse,
    status_code=200,
    summary="Get appointment request details",
    description="Get appointment request details by ID"
)
async def get_appointment_request(
    request_id: UUID = Path(..., description="Appointment request ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get appointment request details
    
    Returns request details. Only accessible by the assigned doctor or patient.
    """
    request_service = AppointmentRequestService(db)
    
    try:
        appointment_request = request_service.get_request_details(
            current_user=current_user,
            request_id=request_id
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
            message="Appointment request retrieved successfully",
            data=response_data
        )
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving appointment request: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving appointment request",
            errors={"general": [str(e)]}
        )


@router.post(
    "/requests/{request_id}/accept",
    response_model=AppointmentRequestSingleResponse,
    status_code=200,
    summary="Accept appointment request",
    description="Accept an appointment request (doctor only). When admin has waiver_doctor_decides enabled, doctor may set waiver (0, 25, 50, 75, 100%)."
)
async def accept_appointment_request(
    request_id: UUID = Path(..., description="Appointment request ID"),
    request_body: Optional[AppointmentRequestAccept] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Accept an appointment request
    
    Only the assigned doctor can accept. Re-validates availability and locks the slot.
    When admin has waiver_doctor_decides enabled, pass waiver_percent (0, 25, 50, 75, or 100) in the body.
    """
    request_service = AppointmentRequestService(db)
    
    try:
        waiver_percent = request_body.waiver_percent if request_body else None
        appointment_request = request_service.accept_request(
            current_user=current_user,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            waiver_percent=waiver_percent,
        )
        
        # Build response (NO PHI); use request.waiver_percent when doctor-set for display
        price_after, amount_before, waiver_pct = get_request_price_display(
            db,
            float(appointment_request.price_amount) if appointment_request.price_amount else None,
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
            message="Appointment request accepted successfully",
            data=response_data
        )
    except (BadRequestException, NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error accepting appointment request: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error accepting appointment request",
            errors={"general": [str(e)]}
        )


@router.post(
    "/requests/{request_id}/reject",
    response_model=AppointmentRequestSingleResponse,
    status_code=200,
    summary="Reject appointment request",
    description="Reject an appointment request (doctor only). Updates status to REJECTED and closes the request."
)
async def reject_appointment_request(
    request_id: UUID = Path(..., description="Appointment request ID"),
    request_data: AppointmentRequestReject = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Reject an appointment request
    
    Only the assigned doctor can reject. Updates status to REJECTED and closes the request permanently.
    """
    request_service = AppointmentRequestService(db)
    
    try:
        appointment_request = request_service.reject_request(
            current_user=current_user,
            request_id=request_id,
            rejection_reason=request_data.rejection_reason if request_data else None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        # Build response (NO PHI); apply waiver for display
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
            message="Appointment request rejected successfully",
            data=response_data
        )
    except (BadRequestException, NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error rejecting appointment request: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error rejecting appointment request",
            errors={"general": [str(e)]}
        )


# Create separate routers for notifications to ensure proper tag registration
notifications_router = APIRouter(
    tags=["Appointment Notifications - Doctor"],
    dependencies=[Depends(require_feature("requests"))],
)
patient_notifications_router = APIRouter(tags=["Appointment Notifications - Patient"])


@notifications_router.get(
    "/doctor/notifications",
    response_model=AppointmentNotificationListResponse,
    status_code=200,
    summary="List appointment notifications",
    description="List appointment notifications for the authenticated doctor"
)
async def list_appointment_notifications(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, ACCEPTED, REJECTED)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List appointment notifications for doctors
    
    Returns appointment requests formatted as notifications with:
    - Notification type (NEW_REQUEST, REQUEST_ACCEPTED, REQUEST_REJECTED)
    - Patient information
    - Appointment details
    - Status
    
    **Doctor only endpoint**
    
    Query Parameters:
    - **status**: Optional status filter (PENDING, ACCEPTED, REJECTED). If not provided, returns all statuses.
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    
    Returns:
    - List of appointment notifications with pagination
    """
    # Validate current user is a doctor
    if current_user.role != UserRole.DOCTOR.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only doctors can view appointment notifications"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        result = request_service.list_doctor_appointment_notifications(
            current_user=current_user,
            status=status,
            page=page,
            limit=limit
        )
        
        return laravel_response(
            success=True,
            message="Appointment notifications retrieved successfully",
            data=result
        )
    except (BadRequestException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error listing appointment notifications: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving appointment notifications",
            errors={"general": [str(e)]}
        )


@notifications_router.get(
    "/doctor/notifications/unread-count",
    response_model=UnreadNotificationCountSingleResponse,
    status_code=200,
    summary="Get unread notification count",
    description="Get the count of unread appointment notifications for the authenticated doctor"
)
async def get_doctor_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get unread notification count for doctors
    
    Returns:
    - unread_count: Number of unread notifications
    - read_count: Number of read notifications
    - total_count: Total number of notifications
    
    **Doctor only endpoint**
    """
    # Validate current user is a doctor
    if current_user.role != UserRole.DOCTOR.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only doctors can view notification counts"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        result = request_service.get_unread_notification_count(
            current_user=current_user
        )
        
        response_data = UnreadNotificationCountResponse(
            unread_count=result["unread_count"],
            read_count=result["read_count"],
            total_count=result["total_count"]
        )
        
        return laravel_response(
            success=True,
            message="Unread notification count retrieved successfully",
            data=response_data
        )
    except (BadRequestException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving unread notification count: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving unread notification count",
            errors={"general": [str(e)]}
        )


@patient_notifications_router.get(
    "/patient/notifications",
    response_model=AppointmentNotificationListResponse,
    status_code=200,
    summary="List appointment notifications",
    description="List appointment notifications for the authenticated patient"
)
async def list_patient_appointment_notifications(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, ACCEPTED, REJECTED)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List appointment notifications for patients
    
    Returns appointment requests formatted as notifications with:
    - Notification type (REQUEST_ACCEPTED, REQUEST_REJECTED)
    - Doctor information
    - Appointment details
    - Status
    
    **Patient only endpoint**
    
    Query Parameters:
    - **status**: Optional status filter (PENDING, ACCEPTED, REJECTED). If not provided, returns all statuses.
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    
    Returns:
    - List of appointment notifications with pagination
    """
    # Validate current user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only patients can view appointment notifications"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        result = request_service.list_patient_appointment_notifications(
            current_user=current_user,
            status=status,
            page=page,
            limit=limit
        )
        
        return laravel_response(
            success=True,
            message="Appointment notifications retrieved successfully",
            data=result
        )
    except (BadRequestException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error listing patient appointment notifications: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving appointment notifications",
            errors={"general": [str(e)]}
        )


@patient_notifications_router.get(
    "/patient/notifications/unread-count",
    response_model=UnreadNotificationCountSingleResponse,
    status_code=200,
    summary="Get unread notification count",
    description="Get the count of unread appointment notifications for the authenticated patient"
)
async def get_patient_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get unread notification count for patients
    
    Returns:
    - unread_count: Number of unread notifications
    - read_count: Number of read notifications
    - total_count: Total number of notifications
    
    **Patient only endpoint**
    """
    # Validate current user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only patients can view notification counts"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        result = request_service.get_unread_notification_count(
            current_user=current_user
        )
        
        response_data = UnreadNotificationCountResponse(
            unread_count=result["unread_count"],
            read_count=result["read_count"],
            total_count=result["total_count"]
        )
        
        return laravel_response(
            success=True,
            message="Unread notification count retrieved successfully",
            data=response_data
        )
    except (BadRequestException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving unread notification count: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving unread notification count",
            errors={"general": [str(e)]}
        )


@patient_notifications_router.get(
    "/requests/statistics",
    response_model=AppointmentRequestStatisticsSingleResponse,
    status_code=200,
    summary="Get appointment request statistics",
    description="Get statistics about patient's appointment requests (counts of accepted, rejected, pending, and past requests)"
)
async def get_patient_request_statistics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get appointment request statistics for patients
    
    Returns counts of:
    - Accepted requests
    - Rejected requests
    - Pending requests
    - Past requests (where preferred_date + preferred_time is in the past)
    
    **Patient only endpoint**
    
    Returns:
    - Statistics object with counts for each category
    """
    # Validate current user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only patients can view appointment request statistics"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        statistics = request_service.get_patient_request_statistics(
            current_user=current_user
        )
        
        response_data = AppointmentRequestStatisticsResponse(
            accepted=statistics["accepted"],
            rejected=statistics["rejected"],
            pending=statistics["pending"],
            past=statistics["past"],
            total=statistics["total"]
        )
        
        return laravel_response(
            success=True,
            message="Appointment request statistics retrieved successfully",
            data=response_data
        )
    except (BadRequestException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving appointment request statistics: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving appointment request statistics",
            errors={"general": [str(e)]}
        )


# ============================================================================
# NOTIFICATION READ ENDPOINTS
# ============================================================================


@notifications_router.put(
    "/doctor/notifications/{notification_id}/read",
    status_code=200,
    summary="Mark notification as read",
    description="Mark a specific appointment notification as read for the authenticated doctor"
)
async def mark_notification_as_read(
    notification_id: UUID = Path(..., description="Notification ID (appointment request ID)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Mark a notification as read for doctors
    
    **Doctor only endpoint**
    
    Path Parameters:
    - **notification_id**: Appointment request ID (the notification ID)
    
    Returns:
    - Success status and read timestamp
    """
    # Validate current user is a doctor
    if current_user.role != UserRole.DOCTOR.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only doctors can mark notifications as read"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        result = request_service.mark_notification_as_read(
            current_user=current_user,
            appointment_request_id=notification_id
        )
        
        return laravel_response(
            success=True,
            message="Notification marked as read successfully",
            data=result
        )
    except (BadRequestException, NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error marking notification as read",
            errors={"general": [str(e)]}
        )


@notifications_router.put(
    "/doctor/notifications/read-all",
    status_code=200,
    summary="Mark all notifications as read",
    description="Mark all appointment notifications as read for the authenticated doctor"
)
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Mark all notifications as read for doctors
    
    **Doctor only endpoint**
    
    Returns:
    - Success status and count of marked notifications
    """
    # Validate current user is a doctor
    if current_user.role != UserRole.DOCTOR.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only doctors can mark notifications as read"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        result = request_service.mark_all_notifications_as_read(
            current_user=current_user
        )
        
        return laravel_response(
            success=True,
            message="All notifications marked as read successfully",
            data=result
        )
    except (BadRequestException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error marking all notifications as read",
            errors={"general": [str(e)]}
        )


@patient_notifications_router.put(
    "/patient/notifications/{notification_id}/read",
    status_code=200,
    summary="Mark notification as read",
    description="Mark a specific appointment notification as read for the authenticated patient"
)
async def mark_patient_notification_as_read(
    notification_id: UUID = Path(..., description="Notification ID (appointment request ID)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Mark a notification as read for patients
    
    **Patient only endpoint**
    
    Path Parameters:
    - **notification_id**: Appointment request ID (the notification ID)
    
    Returns:
    - Success status and read timestamp
    """
    # Validate current user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only patients can mark notifications as read"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        result = request_service.mark_notification_as_read(
            current_user=current_user,
            appointment_request_id=notification_id
        )
        
        return laravel_response(
            success=True,
            message="Notification marked as read successfully",
            data=result
        )
    except (BadRequestException, NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error marking notification as read",
            errors={"general": [str(e)]}
        )


@patient_notifications_router.put(
    "/patient/notifications/read-all",
    status_code=200,
    summary="Mark all notifications as read",
    description="Mark all appointment notifications as read for the authenticated patient"
)
async def mark_all_patient_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Mark all notifications as read for patients
    
    **Patient only endpoint**
    
    Returns:
    - Success status and count of marked notifications
    """
    # Validate current user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise BadRequestException(
            message="Access denied",
            errors={"role": ["Only patients can mark notifications as read"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    try:
        result = request_service.mark_all_notifications_as_read(
            current_user=current_user
        )
        
        return laravel_response(
            success=True,
            message="All notifications marked as read successfully",
            data=result
        )
    except (BadRequestException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error marking all notifications as read",
            errors={"general": [str(e)]}
        )


# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================


@patient_notifications_router.get(
    "/requests/{request_id}/payment",
    response_model=PaymentDetailsSingleResponse,
    status_code=200,
    summary="Get payment details for accepted appointment request",
    description="Get payment details for an accepted appointment request. Returns payment information if payment is initialized, or indicates that payment needs to be initialized."
)
async def get_payment_details(
    request_id: UUID = Path(..., description="Appointment request ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get payment details for an accepted appointment request
    
    Returns payment information including:
    - Payment ID and Stripe payment intent details (if payment initialized)
    - Amount and currency
    - Payment status
    - Whether payment needs to be initialized
    
    **Patient only endpoint**
    
    Path Parameters:
    - **request_id**: Appointment request ID (required)
    
    Returns:
    - Payment details including client_secret if payment is initialized
    - Indicates if payment needs to be initialized
    """
    # Validate current user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise ForbiddenException(
            message="Access denied",
            errors={"role": ["Only patients can view payment details"]}
        )
    
    request_service = AppointmentRequestService(db)
    
    # Get request
    from app.models.appointment_request import AppointmentRequest
    request = db.query(AppointmentRequest).filter(
        AppointmentRequest.id == request_id,
        AppointmentRequest.deleted_at.is_(None)
    ).first()
    
    if not request:
        raise NotFoundException(
            message="Appointment request not found",
            errors={"request_id": ["Request does not exist"]}
        )
    
    # Validate ownership
    if str(request.patient_id) != str(current_user.id):
        raise ForbiddenException(
            message="Access denied",
            errors={"request_id": ["You can only view payment details for your own appointment requests"]}
        )
    
    # Validate status - must be ACCEPTED
    if request.status != 'ACCEPTED':
        raise BadRequestException(
            message="Payment details not available",
            errors={"status": [f"Payment details are only available for ACCEPTED requests. Current status: {request.status}"]}
        )
    
    # Get payment if exists
    payment = db.query(AppointmentPayment).filter(
        AppointmentPayment.appointment_request_id == request_id
    ).first()
    
    # Waiver display: show amount after waiver as price_amount
    price_after, amount_before, waiver_pct = get_request_price_display(
        db, float(request.price_amount) if request.price_amount else None,
        doctor_waiver_percent=request.waiver_percent,
    )
    # Build response
    if payment:
        response_data = PaymentDetailsResponse(
            payment_id=payment.id,
            stripe_payment_intent_id=payment.stripe_payment_intent_id,
            client_secret=payment.stripe_client_secret,
            amount=float(payment.amount) if payment.amount else None,
            currency=payment.currency,
            status=payment.status,
            request_id=request_id,
            request_status=request.status,
            price_amount=price_after,
            amount_before_waiver=amount_before,
            waiver_percent=waiver_pct,
            needs_payment=payment.status != 'COMPLETED'
        )
    else:
        response_data = PaymentDetailsResponse(
            payment_id=None,
            stripe_payment_intent_id=None,
            client_secret=None,
            amount=None,
            currency=None,
            status=None,
            request_id=request_id,
            request_status=request.status,
            price_amount=price_after,
            amount_before_waiver=amount_before,
            waiver_percent=waiver_pct,
            needs_payment=True
        )
    
    return laravel_response(
        success=True,
        message="Payment details retrieved successfully",
        data=response_data
    )


# ============================================================================
# VISIT ENDPOINTS
# ============================================================================


# Create a new router for visit endpoints (doctor: start/complete visit)
visit_router = APIRouter(
    tags=["Appointment Visits"],
    dependencies=[Depends(require_feature("appointments"))],
)


@visit_router.post(
    "/appointments/{appointment_id}/start",
    response_model=VisitSingleResponse,
    status_code=200,
    summary="Start visit/consultation",
    description="Start a visit/consultation for a confirmed appointment. Only the assigned doctor can start the visit."
)
async def start_visit(
    appointment_id: UUID = Path(..., description="Appointment ID"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Start a visit/consultation for a confirmed appointment
    
    Rules:
    - Only assigned doctor can start visit
    - Appointment must be CONFIRMED (payment completed)
    - Updates appointment status to IN_PROGRESS
    
    **Doctor only endpoint**
    
    Path Parameters:
    - **appointment_id**: Appointment ID (required)
    
    Returns:
    - Updated appointment with IN_PROGRESS status
    """
    appointment_service = AppointmentService(db)
    
    try:
        appointment = appointment_service.start_visit(
            current_user=current_user,
            appointment_id=appointment_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        response_data = VisitResponse(
            appointment_id=appointment.id,
            status=appointment.status,
            doctor_id=appointment.doctor_id,
            patient_id=appointment.patient_id,
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
            consultation_mode=appointment.consultation_mode
        )
        
        return laravel_response(
            success=True,
            message="Visit started successfully",
            data=response_data
        )
    except (BadRequestException, NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error starting visit: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error starting visit",
            errors={"general": [str(e)]}
        )


@visit_router.post(
    "/appointments/{appointment_id}/complete",
    response_model=VisitSingleResponse,
    status_code=200,
    summary="Complete visit/consultation",
    description="Complete a visit/consultation. Only the assigned doctor can complete the visit."
)
async def complete_visit(
    appointment_id: UUID = Path(..., description="Appointment ID"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Complete a visit/consultation
    
    Rules:
    - Only assigned doctor can complete visit
    - Appointment must be IN_PROGRESS
    - Updates appointment status to COMPLETED
    
    **Doctor only endpoint**
    
    Path Parameters:
    - **appointment_id**: Appointment ID (required)
    
    Returns:
    - Updated appointment with COMPLETED status
    """
    appointment_service = AppointmentService(db)
    
    try:
        appointment = appointment_service.complete_visit(
            current_user=current_user,
            appointment_id=appointment_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        response_data = VisitResponse(
            appointment_id=appointment.id,
            status=appointment.status,
            doctor_id=appointment.doctor_id,
            patient_id=appointment.patient_id,
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
            consultation_mode=appointment.consultation_mode
        )
        
        return laravel_response(
            success=True,
            message="Visit completed successfully",
            data=response_data
        )
    except (BadRequestException, NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error completing visit: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error completing visit",
            errors={"general": [str(e)]}
        )
