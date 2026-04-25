"""
Doctor Availability API Endpoints
Laravel-compatible routes for availability and time-off management
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin_user
from app.core.security import CurrentUser
from app.models.user import User
from app.services.audit_service import AuditService
from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilityListResponse,
    AvailabilitySingleResponse,
    TimeOffCreate,
    TimeOffListResponse,
    TimeOffSingleResponse
)
from app.services.availability_service import get_availability_service, AvailabilityService
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from loguru import logger


router = APIRouter(tags=["Doctor Availability"])


def _create_audit_log(
    db: Session,
    user: CurrentUser,
    action: str,
    entity_type: str,
    entity_id: UUID,
    request: Request,
    metadata: dict = None
):
    """
    Create audit log entry for availability operations
    
    Args:
        db: Database session
        user: Current user
        action: Action type
        entity_type: Entity type (availability or time_off)
        entity_id: Entity ID
        request: HTTP request
        metadata: Additional metadata
    """
    try:
        audit_service = AuditService(db)
        audit_service.create_audit_log_from_request(
            request=request,
            actor_user_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            audit_metadata=metadata or {}
        )
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        # Don't fail the operation if audit logging fails


# ============================================================================
# AVAILABILITY ENDPOINTS
# ============================================================================


@router.get(
    "/doctors/{doctor_id}/availability",
    response_model=AvailabilityListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get doctor availability",
    description="Retrieve availability slots for a doctor"
)
async def get_doctor_availability(
    doctor_id: UUID,
    request: Request,
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """
    Get doctor availability slots
    
    **Laravel compatible:**
    - Same endpoint path: GET /doctors/{id}/availability
    - Same response format
    
    **Permissions:**
    - Doctor: Can view own availability
    - Admin: Can view any doctor's availability
    
    Args:
        doctor_id: Doctor ID
        clinic_id: Optional clinic ID filter (query parameter)
    
    Returns:
        List of availability slots
    """
    try:
        # Get availability
        availability_list = availability_service.get_availability(
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            current_user=current_user
        )
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="AVAILABILITY_VIEWED",
            entity_type="doctor_availability",
            entity_id=doctor_id,
            request=request,
            metadata={
                "doctor_id": str(doctor_id),
                "clinic_id": str(clinic_id) if clinic_id else None,
                "slot_count": len(availability_list)
            }
        )
        
        return AvailabilityListResponse(
            success=True,
            message="Availability retrieved successfully",
            data=availability_list,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve availability: {str(e)}")
        raise


@router.post(
    "/doctors/{doctor_id}/availability",
    response_model=AvailabilitySingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create doctor availability",
    description="Create a new availability slot for a doctor"
)
async def create_doctor_availability(
    doctor_id: UUID,
    availability_data: AvailabilityCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """
    Create a new availability slot for a doctor
    
    **Laravel compatible:**
    - Same endpoint path: POST /doctors/{id}/availability
    - Same request payload
    - Same response format
    
    **Permissions:**
    - Doctor: Can create own availability
    - Admin: Can create availability for any doctor
    
    **Business Rules:**
    - Prevents overlapping slots
    - Enforces clinic isolation
    
    Args:
        doctor_id: Doctor ID
        availability_data: Availability data
    
    Returns:
        Created availability slot
    """
    try:
        # Create availability
        availability = availability_service.create_availability(
            doctor_id=doctor_id,
            availability_data=availability_data,
            current_user=current_user
        )
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="AVAILABILITY_CREATED",
            entity_type="doctor_availability",
            entity_id=availability.id,
            request=request,
            metadata={
                "doctor_id": str(doctor_id),
                "clinic_id": str(availability_data.clinic_id),
                "day_of_week": availability_data.day_of_week,
                "start_time": availability_data.start_time.isoformat(),
                "end_time": availability_data.end_time.isoformat()
            }
        )
        
        logger.info(f"User {current_user.id} created availability for doctor {doctor_id}")
        
        return AvailabilitySingleResponse(
            success=True,
            message="Availability created successfully",
            data=availability,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, ConflictException):
        raise
    except Exception as e:
        logger.error(f"Failed to create availability: {str(e)}")
        raise


@router.put(
    "/availability/{availability_id}",
    response_model=AvailabilitySingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update availability slot",
    description="Update an existing availability slot"
)
async def update_availability(
    availability_id: UUID,
    availability_data: AvailabilityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """
    Update an availability slot
    
    **Laravel compatible:**
    - Same endpoint path: PUT /availability/{id}
    - Same request payload
    - Same response format
    
    **Permissions:**
    - Doctor: Can update own availability
    - Admin: Can update any doctor's availability
    
    **Business Rules:**
    - Prevents overlapping slots
    - Enforces clinic isolation
    
    Args:
        availability_id: Availability slot ID
        availability_data: Updated availability data
    
    Returns:
        Updated availability slot
    """
    try:
        # Update availability
        availability = availability_service.update_availability(
            availability_id=availability_id,
            availability_data=availability_data,
            current_user=current_user
        )
        
        # Create audit log
        update_fields = availability_data.model_dump(exclude_unset=True)
        _create_audit_log(
            db=db,
            user=current_user,
            action="AVAILABILITY_UPDATED",
            entity_type="doctor_availability",
            entity_id=availability_id,
            request=request,
            metadata={
                "doctor_id": str(availability.doctor_id),
                "clinic_id": str(availability.clinic_id),
                "updated_fields": list(update_fields.keys())
            }
        )
        
        logger.info(f"User {current_user.id} updated availability {availability_id}")
        
        return AvailabilitySingleResponse(
            success=True,
            message="Availability updated successfully",
            data=availability,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, ConflictException):
        raise
    except Exception as e:
        logger.error(f"Failed to update availability: {str(e)}")
        raise


@router.delete(
    "/availability/{availability_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete availability slot",
    description="Delete (soft delete) an availability slot"
)
async def delete_availability(
    availability_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """
    Delete an availability slot
    
    **Laravel compatible:**
    - Same endpoint path: DELETE /availability/{id}
    - Same response format
    
    **Permissions:**
    - Doctor: Can delete own availability
    - Admin: Can delete any doctor's availability
    
    Args:
        availability_id: Availability slot ID
    
    Returns:
        Success message
    """
    try:
        # Get availability before deletion for audit log
        from app.models.availability import DoctorAvailability
        availability = db.query(DoctorAvailability).filter(
            DoctorAvailability.id == availability_id,
            DoctorAvailability.deleted_at.is_(None)
        ).first()
        
        if not availability:
            raise NotFoundException(
                message="Availability slot not found",
                errors={"availability_id": ["Availability slot with this ID does not exist"]}
            )
        
        # Delete availability
        availability_service.delete_availability(
            availability_id=availability_id,
            current_user=current_user
        )
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="AVAILABILITY_DELETED",
            entity_type="doctor_availability",
            entity_id=availability_id,
            request=request,
            metadata={
                "doctor_id": str(availability.doctor_id),
                "clinic_id": str(availability.clinic_id),
                "day_of_week": availability.day_of_week
            }
        )
        
        logger.info(f"User {current_user.id} deleted availability {availability_id}")
        
        return {
            "success": True,
            "message": "Availability deleted successfully",
            "data": None,
            "errors": None
        }
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to delete availability: {str(e)}")
        raise


# ============================================================================
# TIME-OFF ENDPOINTS
# ============================================================================


@router.get(
    "/doctors/{doctor_id}/time-off",
    response_model=TimeOffListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get doctor time-off",
    description="Retrieve time-off periods for a doctor"
)
async def get_doctor_time_off(
    doctor_id: UUID,
    request: Request,
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """
    Get doctor time-off periods
    
    **Laravel compatible:**
    - Same endpoint path: GET /doctors/{id}/time-off
    - Same response format
    
    **Permissions:**
    - Doctor: Can view own time-off
    - Admin: Can view any doctor's time-off
    
    Args:
        doctor_id: Doctor ID
        clinic_id: Optional clinic ID filter (query parameter)
    
    Returns:
        List of time-off periods
    """
    try:
        # Get time-off
        time_off_list = availability_service.get_time_off(
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            current_user=current_user
        )
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="TIME_OFF_VIEWED",
            entity_type="doctor_time_off",
            entity_id=doctor_id,
            request=request,
            metadata={
                "doctor_id": str(doctor_id),
                "clinic_id": str(clinic_id) if clinic_id else None,
                "time_off_count": len(time_off_list)
            }
        )
        
        # Get booking_window_days from admin settings
        from app.services.admin_settings_service import AdminSettingsService
        admin_settings_service = AdminSettingsService(db)
        settings = admin_settings_service.get_settings()
        
        return TimeOffListResponse(
            success=True,
            message="Time-off retrieved successfully",
            data=time_off_list,
            errors=None,
            booking_window_days=settings.booking_window_days
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve time-off: {str(e)}")
        raise


@router.post(
    "/doctors/{doctor_id}/time-off",
    response_model=TimeOffSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create doctor time-off",
    description="Create a new time-off period for a doctor"
)
async def create_doctor_time_off(
    doctor_id: UUID,
    time_off_data: TimeOffCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """
    Create a new time-off period for a doctor
    
    **Laravel compatible:**
    - Same endpoint path: POST /doctors/{id}/time-off
    - Same request payload
    - Same response format
    
    **Permissions:**
    - Doctor: Can create own time-off
    - Admin: Can create time-off for any doctor
    
    **Business Rules:**
    - Prevents overlapping time-off periods
    - Time-off overrides availability
    
    Args:
        doctor_id: Doctor ID
        time_off_data: Time-off data
    
    Returns:
        Created time-off period
    """
    try:
        # Create time-off
        time_off = availability_service.create_time_off(
            doctor_id=doctor_id,
            time_off_data=time_off_data,
            current_user=current_user
        )
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="TIME_OFF_ADDED",
            entity_type="doctor_time_off",
            entity_id=time_off.id,
            request=request,
            metadata={
                "doctor_id": str(doctor_id),
                "clinic_id": str(time_off_data.clinic_id),
                "start_datetime": time_off_data.start_datetime.isoformat(),
                "end_datetime": time_off_data.end_datetime.isoformat(),
                "reason": time_off_data.reason
            }
        )
        
        logger.info(f"User {current_user.id} created time-off for doctor {doctor_id}")
        
        return TimeOffSingleResponse(
            success=True,
            message="Time-off created successfully",
            data=time_off,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, ConflictException):
        raise
    except Exception as e:
        logger.error(f"Failed to create time-off: {str(e)}")
        raise


@router.delete(
    "/time-off/{time_off_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete time-off period",
    description="Delete (soft delete) a time-off period"
)
async def delete_time_off(
    time_off_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """
    Delete a time-off period
    
    **Laravel compatible:**
    - Same endpoint path: DELETE /time-off/{id}
    - Same response format
    
    **Permissions:**
    - Doctor: Can delete own time-off
    - Admin: Can delete any doctor's time-off
    
    Args:
        time_off_id: Time-off period ID
    
    Returns:
        Success message
    """
    try:
        # Get time-off before deletion for audit log
        from app.models.availability import DoctorTimeOff
        time_off = db.query(DoctorTimeOff).filter(
            DoctorTimeOff.id == time_off_id,
            DoctorTimeOff.deleted_at.is_(None)
        ).first()
        
        if not time_off:
            raise NotFoundException(
                message="Time-off period not found",
                errors={"time_off_id": ["Time-off period with this ID does not exist"]}
            )
        
        # Delete time-off
        availability_service.delete_time_off(
            time_off_id=time_off_id,
            current_user=current_user
        )
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="TIME_OFF_DELETED",
            entity_type="doctor_time_off",
            entity_id=time_off_id,
            request=request,
            metadata={
                "doctor_id": str(time_off.doctor_id),
                "clinic_id": str(time_off.clinic_id)
            }
        )
        
        logger.info(f"User {current_user.id} deleted time-off {time_off_id}")
        
        return {
            "success": True,
            "message": "Time-off deleted successfully",
            "data": None,
            "errors": None
        }
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to delete time-off: {str(e)}")
        raise
