"""
Doctor Service Availability API Endpoints
Routes for doctors to assign services to availability blocks
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import CurrentUser
from app.services.doctor_service_availability_service import DoctorServiceAvailabilityService
from app.schemas.doctor_service_availability import (
    DoctorServiceAvailabilityCreate,
    DoctorServiceAvailabilityUpdate,
    DoctorServiceAvailabilityResponse,
    DoctorServiceAvailabilityListResponse,
    DoctorServiceAvailabilitySingleResponse
)
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException
)
from loguru import logger


router = APIRouter(prefix="/doctor/availability-services", tags=["Doctor - Availability Services"])


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


def _build_response(assignment) -> DoctorServiceAvailabilityResponse:
    """
    Build response object with related details
    
    Args:
        assignment: DoctorServiceAvailability object
        
    Returns:
        DoctorServiceAvailabilityResponse
    """
    return DoctorServiceAvailabilityResponse(
        id=assignment.id,
        availability_id=assignment.availability_id,
        service_id=assignment.service_id,
        slot_duration_minutes=assignment.slot_duration_minutes,
        consultation_mode=assignment.consultation_mode,
        created_at=assignment.created_at,
        service_name=assignment.service.name if assignment.service else None,
        service_mode=assignment.service.service_mode if assignment.service else None,
        availability_day=assignment.availability.day_of_week if assignment.availability else None,
        availability_start_time=str(assignment.availability.start_time) if assignment.availability else None,
        availability_end_time=str(assignment.availability.end_time) if assignment.availability else None
    )


@router.get(
    "",
    response_model=DoctorServiceAvailabilityListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get service availability assignments",
    description="Get doctor's service assignments to availability blocks"
)
async def get_availability_services(
    availability_id: Optional[UUID] = Query(None, description="Filter by availability ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get doctor's service availability assignments
    
    **Doctor only endpoint**
    
    Returns all service-to-availability assignments for the doctor.
    Optionally filter by availability_id.
    
    Returns:
        List of service availability assignments
    """
    try:
        service = DoctorServiceAvailabilityService(db)
        assignments = service.get_availability_services(current_user, availability_id)
        
        data = [_build_response(a) for a in assignments]
        
        return DoctorServiceAvailabilityListResponse(
            success=True,
            message=f"Found {len(data)} service availability assignments",
            data=data,
            errors=None
        )
    
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Failed to get availability services: {str(e)}")
        raise


@router.post(
    "",
    response_model=DoctorServiceAvailabilitySingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign service to availability",
    description="Assign a service to an availability block with custom slot duration"
)
async def assign_service(
    data: DoctorServiceAvailabilityCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Assign a service to an availability block
    
    **Doctor only endpoint**
    
    Allows doctors to assign services to their availability windows with custom durations and consultation modes.
    
    Rules:
    - Doctor can assign same service to multiple availability blocks
    - Doctor can assign same service twice if consultation mode differs
    - Cannot duplicate same service + consultation mode in same availability
    - Duration must be between 5 and 360 minutes
    
    Args:
        data: Service availability assignment data (includes consultation_mode)
        
    Returns:
        Created service availability assignment
    """
    try:
        service = DoctorServiceAvailabilityService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        assignment = service.assign_service(
            current_user=current_user,
            availability_id=data.availability_id,
            service_id=data.service_id,
            slot_duration_minutes=data.slot_duration_minutes,
            consultation_mode=data.consultation_mode,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return DoctorServiceAvailabilitySingleResponse(
            success=True,
            message="Service assigned to availability successfully",
            data=_build_response(assignment),
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to assign service to availability: {str(e)}")
        raise


@router.patch(
    "/{assignment_id}",
    response_model=DoctorServiceAvailabilitySingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update service availability assignment",
    description="Update the slot duration for a service availability assignment"
)
async def update_assignment(
    assignment_id: UUID,
    data: DoctorServiceAvailabilityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update a service availability assignment
    
    **Doctor only endpoint**
    
    Update the slot duration for an existing assignment.
    
    Args:
        assignment_id: Assignment ID
        data: Update data
        
    Returns:
        Updated service availability assignment
    """
    try:
        service = DoctorServiceAvailabilityService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        assignment = service.update_assignment(
            current_user=current_user,
            assignment_id=assignment_id,
            slot_duration_minutes=data.slot_duration_minutes,
            consultation_mode=data.consultation_mode,
            payment_type=data.payment_type,
            advance_booking_days=data.advance_booking_days,
            minimum_notice_minutes=data.minimum_notice_minutes,
            is_bookable=data.is_bookable,
            appointment_type=data.appointment_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return DoctorServiceAvailabilitySingleResponse(
            success=True,
            message="Service availability assignment updated successfully",
            data=_build_response(assignment),
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to update service availability assignment: {str(e)}")
        raise


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove service from availability",
    description="Remove a service assignment from an availability block"
)
async def remove_assignment(
    assignment_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Remove a service from an availability block
    
    **Doctor only endpoint**
    
    Permanently removes the service assignment from the availability block.
    
    Args:
        assignment_id: Assignment ID
        
    Returns:
        Success message
    """
    try:
        service = DoctorServiceAvailabilityService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        service.remove_assignment(
            current_user=current_user,
            assignment_id=assignment_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "message": "Service removed from availability successfully",
            "data": None,
            "errors": None
        }
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to remove service from availability: {str(e)}")
        raise
