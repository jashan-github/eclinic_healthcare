"""
Patient Doctor Search endpoints
API endpoints for patients to search for doctors
"""

from typing import Optional
from datetime import datetime, timezone, date as date_type
from fastapi import APIRouter, Depends, Query, Request, Path
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_db, get_current_user_optional, get_client_ip
from app.core.security import CurrentUser
from app.core.exceptions import laravel_response, BadRequestException, NotFoundException
from app.services.doctor_search_service import DoctorSearchService
from app.services.audit_service import AuditService
from app.schemas.doctor_search import DoctorSearchResponse
from app.schemas.availability import PatientTimeOffListResponse, PatientTimeOffResponse
from app.models.availability import DoctorTimeOff
from app.models.user import User
from loguru import logger

router = APIRouter()


@router.get(
    "/search",
    response_model=DoctorSearchResponse,
    status_code=200,
    summary="Search for doctors",
    description="Search for doctors with optional filters for specialty, availability day, and availability time"
)
async def search_doctors(
    request: Request,
    specialty: Optional[UUID] = Query(None, alias="specialty_id", description="Filter by medical service/specialty ID"),
    availability_day: Optional[str] = Query(None, description="Filter by availability day (Mon, Tue, Wed, Thu, Fri, Sat, Sun)"),
    availability_time: Optional[str] = Query(None, description="Filter by availability time (HH:MM format)"),
    date: Optional[date_type] = Query(None, description="Optional. If provided, only services available on this date are returned; if omitted, services are not filtered by day."),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
    ip_address: str = Depends(get_client_ip)
):
    """
    Search for doctors (patient endpoint)
    
    **Laravel-compatible endpoint**
    
    Allows patients to search for doctors with optional filters:
    - **specialty**: Filter by medical service/specialty (UUID)
    - **availability_day**: Filter by day of week (Mon, Tue, Wed, etc.)
    - **availability_time**: Filter by time (HH:MM format)
    
    Supports pagination with `page` and `limit` parameters.
    
    Returns only active doctors with:
    - Doctor ID, name, profile image
    - Specialty, qualifications, rating, years of experience
    - Lowest consultation fee (IN_CLINIC preferred) and currency
    - Available days (max 5, sorted Monday-Sunday)
    
    Query Parameters:
    - **specialty**: Optional. UUID of medical service/specialty
    - **availability_day**: Optional. Day name (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
    - **availability_time**: Optional. Time in HH:MM format (e.g., "14:30")
    - **page**: Page number (default: 1, minimum: 1)
    - **limit**: Items per page (default: 20, minimum: 1, maximum: 100)
    
    Returns:
    - List of doctors matching the search criteria
    - Pagination information
    - Empty list with 200 OK if no doctors match
    """
    # Validate availability_day format
    if availability_day:
        day_lower = availability_day.lower().strip()
        valid_days = ["mon", "monday", "tue", "tuesday", "wed", "wednesday",
                     "thu", "thursday", "fri", "friday", "sat", "saturday",
                     "sun", "sunday"]
        if day_lower not in valid_days:
            raise BadRequestException(
                message="Invalid availability_day",
                errors={
                    "availability_day": [
                        "Must be one of: Mon, Tue, Wed, Thu, Fri, Sat, Sun (or full day names)"
                    ]
                }
            )
    
    # Validate availability_time format
    if availability_time:
        try:
            parts = availability_time.strip().split(":")
            if len(parts) != 2:
                raise ValueError("Invalid format")
            hour = int(parts[0])
            minute = int(parts[1])
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError("Invalid time range")
        except (ValueError, IndexError):
            raise BadRequestException(
                message="Invalid availability_time format",
                errors={
                    "availability_time": [
                        "Must be in HH:MM format (e.g., '14:30')"
                    ]
                }
            )
    
    # Initialize service and perform search
    search_service = DoctorSearchService(db)
    
    try:
        result = search_service.search_doctors(
            specialty_id=specialty,
            availability_day=availability_day,
            availability_time=availability_time,
            availability_date=date,
            page=page,
            limit=limit
        )
        
        # Audit log: Patient search activity (NO PHI)
        audit_service = AuditService(db)
        actor_user_id = current_user.id if current_user else None
        user_agent = request.headers.get("user-agent")
        
        audit_service.create_audit_log(
            actor_user_id=actor_user_id,
            action="DOCTOR_SEARCH",
            entity_type="doctor",
            entity_id=None,
            audit_metadata={
                "has_specialty_filter": specialty is not None,
                "has_day_filter": availability_day is not None,
                "has_time_filter": availability_time is not None,
                "availability_date": str(date) if date else None,
                "results_count": len(result.get("doctors", [])),
                "page": page,
                "limit": limit
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return laravel_response(
            success=True,
            message="Doctors retrieved successfully",
            data=result
        )
    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"Error searching doctors: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error searching doctors",
            errors={"search": [str(e)]}
        )


@router.get(
    "/{doctor_id}/time-off",
    response_model=PatientTimeOffListResponse,
    status_code=200,
    summary="Get doctor time-off periods",
    description="Get upcoming time-off periods for a specific doctor. Only shows future time-off periods."
)
async def get_doctor_time_off(
    doctor_id: UUID = Path(..., description="Doctor ID"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
    ip_address: str = Depends(get_client_ip)
):
    """
    Get doctor's upcoming time-off periods (patient endpoint)
    
    **Laravel-compatible endpoint**
    
    Returns only future time-off periods for the specified doctor.
    Does NOT include the reason (private information for doctors only).
    
    **Access:**
    - Public endpoint (authentication optional)
    - Useful for patients to know when a doctor is unavailable
    
    **Returns:**
    - List of upcoming time-off periods with:
      - id, doctor_id, clinic_id
      - start_datetime, end_datetime
    - Does NOT include: reason (private)
    
    **Filters:**
    - Only shows time-off periods that end AFTER the current time
    - Sorted by start_datetime ascending (nearest first)
    """
    try:
        # Verify doctor exists and is active
        doctor = db.query(User).filter(
            User.id == doctor_id,
            User.deleted_at.is_(None),
            User.is_active == True
        ).first()
        
        if not doctor:
            raise NotFoundException(
                message="Doctor not found",
                errors={"doctor_id": ["Doctor with this ID does not exist or is inactive"]}
            )
        
        # Verify user has doctor role
        if doctor.role != 'doctor':
            raise NotFoundException(
                message="Doctor not found",
                errors={"doctor_id": ["The specified user is not a doctor"]}
            )
        
        # Get current time (UTC)
        now = datetime.now(timezone.utc)
        
        # Query upcoming time-off periods (end_datetime > now)
        time_off_list = db.query(DoctorTimeOff).filter(
            DoctorTimeOff.doctor_id == doctor_id,
            DoctorTimeOff.deleted_at.is_(None),
            DoctorTimeOff.end_datetime > now  # Only future/ongoing time-off
        ).order_by(
            DoctorTimeOff.start_datetime.asc()  # Nearest first
        ).all()
        
        # Convert to response format (without reason)
        response_data = [
            PatientTimeOffResponse(
                id=time_off.id,
                doctor_id=time_off.doctor_id,
                clinic_id=time_off.clinic_id,
                start_datetime=time_off.start_datetime,
                end_datetime=time_off.end_datetime
            )
            for time_off in time_off_list
        ]
        
        # Audit log (optional - for analytics)
        audit_service = AuditService(db)
        actor_user_id = current_user.id if current_user else None
        
        audit_service.create_audit_log(
            actor_user_id=actor_user_id,
            action="VIEW_DOCTOR_TIME_OFF",
            entity_type="doctor_time_off",
            entity_id=doctor_id,
            audit_metadata={
                "doctor_id": str(doctor_id),
                "time_off_count": len(response_data)
            },
            ip_address=ip_address,
            user_agent=None
        )
        
        # Get booking_window_days from admin settings
        from app.services.admin_settings_service import AdminSettingsService
        admin_settings_service = AdminSettingsService(db)
        settings = admin_settings_service.get_settings()
        
        return PatientTimeOffListResponse(
            success=True,
            message=f"Found {len(response_data)} upcoming time-off period(s)",
            data=response_data,
            errors=None,
            booking_window_days=settings.booking_window_days
        )
    
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error getting doctor time-off: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving doctor time-off",
            errors={"time_off": [str(e)]}
        )
