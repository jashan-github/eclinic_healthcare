"""
Doctor Service Selection API Endpoints
Routes for doctors to manage their service offerings
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, status, Response
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import CurrentUser
from app.services.doctor_service_service import DoctorServiceSelectionService
from app.schemas.doctor_service import (
    DoctorServiceCreate,
    DoctorServiceUpdate,
    DoctorServiceResponse,
    DoctorServiceListResponse,
    DoctorServiceSingleResponse,
    AvailableServiceResponse,
    AvailableServiceListResponse
)
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    ConflictException,
    BadRequestException
)
from app.models.doctor_service import DoctorService
from loguru import logger


router = APIRouter(prefix="/doctor/services", tags=["Doctor - Services"])


def _extract_request_info(request: Request) -> tuple:
    """
    Extract IP address and user agent from request
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Tuple of (ip_address, user_agent)
    """
    ip_address = None
    if request.client:
        ip_address = request.client.host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    
    user_agent = request.headers.get("user-agent")
    
    return ip_address, user_agent


@router.get(
    "/available",
    response_model=AvailableServiceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get available services",
    description="Get services available for doctor to select from (active & bookable in doctor's clinic)"
)
async def get_available_services(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get available services for doctor
    
    **Doctor only endpoint**
    
    Returns services that are:
    - In the doctor's clinic
    - Active and bookable
    - Not yet assigned to this doctor
    
    Returns:
        List of available services
    """
    try:
        service = DoctorServiceSelectionService(db)
        services = service.get_available_services(current_user)
        
        data = [
            AvailableServiceResponse(
                id=svc.id,
                name=svc.name,
                nickname=svc.nickname,
                service_mode=svc.service_mode,
                appointment_type=svc.appointment_type,
                advance_booking_days=svc.advance_booking_days,
                minimum_notice_minutes=svc.minimum_notice_minutes,
                payment_type=svc.payment_type,
                price=float(svc.price) if svc.price else None
            )
            for svc in services
        ]
        
        return AvailableServiceListResponse(
            success=True,
            message=f"Found {len(data)} available services",
            data=data,
            errors=None
        )
    
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Failed to get available services: {str(e)}")
        raise


@router.get(
    "",
    response_model=DoctorServiceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my services",
    description="Get doctor's current service assignments"
)
async def get_my_services(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get doctor's service assignments
    
    **Doctor only endpoint**
    
    Returns all services the doctor has selected, including day-specific durations.
    
    Returns:
        List of doctor's service assignments
    """
    try:
        service = DoctorServiceSelectionService(db)
        assignments = service.get_doctor_services(current_user)
        
        data = [
            DoctorServiceResponse(
                id=a.id,
                doctor_id=a.doctor_id,
                service_id=a.service_id,
                clinic_id=a.clinic_id,
                day_of_week=a.day_of_week,
                day_name=a.day_name,
                is_default=a.is_default,
                slot_duration_minutes=a.slot_duration_minutes,
                is_active=a.is_active,
                created_at=a.created_at,
                service_name=a.service.name if a.service else None,
                service_mode=a.service.service_mode if a.service else None,
                appointment_type=a.service.appointment_type if a.service else None
            )
            for a in assignments
        ]
        
        return DoctorServiceListResponse(
            success=True,
            message=f"Found {len(data)} service assignments",
            data=data,
            errors=None
        )
    
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Failed to get doctor services: {str(e)}")
        raise


@router.post(
    "",
    response_model=DoctorServiceSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a service",
    description="Add a service to doctor's offerings. Send only service_id (and optional day_of_week); backend fetches the admin-configured service and sets all data from admin into the doctor assignment. If already configured, returns existing with 200."
)
async def add_service(
    data: DoctorServiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Add a service to doctor's offerings
    
    **Doctor only endpoint**
    
    Doctors can only select from admin-created services that are:
    - In their clinic
    - Active and bookable
    
    **Request:** Only service_id required; optional day_of_week. All other data (service mode, appointment type, etc.) is taken from the admin-configured service.
    **Day-specific:** day_of_week = NULL for default; 0-6 for a specific day. One default per service; multiple records allowed per service for different days.
    
    **Idempotent behavior:**
    - If service is already configured for the same doctor and day_of_week, returns existing assignment with 200 status
    - No duplicate records are created
    
    Args:
        data: Service selection data
        
    Returns:
        Created or existing service assignment (200 if exists, 201 if created)
    """
    try:
        service = DoctorServiceSelectionService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        # Check if assignment already exists before creating
        doctor = service._get_doctor_user(current_user)
        existing = None
        
        if data.day_of_week is None:
            existing = db.query(DoctorService).filter(
                DoctorService.doctor_id == doctor.id,
                DoctorService.service_id == data.service_id,
                DoctorService.day_of_week.is_(None)
            ).first()
        else:
            existing = db.query(DoctorService).filter(
                DoctorService.doctor_id == doctor.id,
                DoctorService.service_id == data.service_id,
                DoctorService.day_of_week == data.day_of_week
            ).first()
        
        # If exists, return 200 with existing assignment
        if existing:
            response_data = DoctorServiceSingleResponse(
                success=True,
                message="Service is already configured",
                data=DoctorServiceResponse(
                    id=existing.id,
                    doctor_id=existing.doctor_id,
                    service_id=existing.service_id,
                    clinic_id=existing.clinic_id,
                    day_of_week=existing.day_of_week,
                    day_name=existing.day_name,
                    is_default=existing.is_default,
                    slot_duration_minutes=existing.slot_duration_minutes,
                    is_active=existing.is_active,
                    created_at=existing.created_at,
                    service_name=existing.service.name if existing.service else None,
                    service_mode=existing.service.service_mode if existing.service else None,
                    appointment_type=existing.service.appointment_type if existing.service else None
                ),
                errors=None
            )
            # Return with 200 status code
            return Response(
                content=response_data.model_dump_json(),
                status_code=status.HTTP_200_OK,
                media_type="application/json"
            )
        
        # Create new assignment
        assignment = service.add_service(
            current_user=current_user,
            service_id=data.service_id,
            day_of_week=data.day_of_week,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return DoctorServiceSingleResponse(
            success=True,
            message="Service assigned successfully",
            data=DoctorServiceResponse(
                id=assignment.id,
                doctor_id=assignment.doctor_id,
                service_id=assignment.service_id,
                clinic_id=assignment.clinic_id,
                day_of_week=assignment.day_of_week,
                day_name=assignment.day_name,
                is_default=assignment.is_default,
                slot_duration_minutes=assignment.slot_duration_minutes,
                is_active=assignment.is_active,
                created_at=assignment.created_at,
                service_name=assignment.service.name if assignment.service else None,
                service_mode=assignment.service.service_mode if assignment.service else None,
                appointment_type=assignment.service.appointment_type if assignment.service else None
            ),
            errors=None
        )
    
    except (ForbiddenException, ValidationException, ConflictException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to add service: {str(e)}")
        raise


@router.patch(
    "/{assignment_id}",
    response_model=DoctorServiceSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update service assignment",
    description="Update a doctor's service assignment"
)
async def update_service(
    assignment_id: UUID,
    data: DoctorServiceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update a service assignment
    
    **Doctor only endpoint**
    
    Doctors can update:
    - Slot duration (5-360 minutes)
    - Active status
    
    Note: day_of_week cannot be changed. To modify day_of_week, 
    remove and re-add the assignment.
    
    Args:
        assignment_id: Service assignment ID
        data: Update data
        
    Returns:
        Updated service assignment
    """
    try:
        service = DoctorServiceSelectionService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        assignment = service.update_service(
            current_user=current_user,
            assignment_id=assignment_id,
            slot_duration_minutes=data.slot_duration_minutes,
            is_active=data.is_active,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return DoctorServiceSingleResponse(
            success=True,
            message="Service assignment updated successfully",
            data=DoctorServiceResponse(
                id=assignment.id,
                doctor_id=assignment.doctor_id,
                service_id=assignment.service_id,
                clinic_id=assignment.clinic_id,
                day_of_week=assignment.day_of_week,
                day_name=assignment.day_name,
                is_default=assignment.is_default,
                slot_duration_minutes=assignment.slot_duration_minutes,
                is_active=assignment.is_active,
                created_at=assignment.created_at,
                service_name=assignment.service.name if assignment.service else None,
                service_mode=assignment.service.service_mode if assignment.service else None,
                appointment_type=assignment.service.appointment_type if assignment.service else None
            ),
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, ValidationException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to update service assignment: {str(e)}")
        raise


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove service",
    description="Remove a service from doctor's offerings"
)
async def remove_service(
    assignment_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Remove a service from doctor's offerings
    
    **Doctor only endpoint**
    
    Permanently removes the service assignment.
    
    Args:
        assignment_id: Service assignment ID
        
    Returns:
        Success message
    """
    try:
        service = DoctorServiceSelectionService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        service.remove_service(
            current_user=current_user,
            assignment_id=assignment_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "message": "Service removed successfully",
            "data": None,
            "errors": None
        }
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to remove service: {str(e)}")
        raise
