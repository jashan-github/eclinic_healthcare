"""
Doctor Appointments API Endpoints
Routes for doctors to view their appointments
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import DoctorUser, require_feature
from app.services.appointment_service import AppointmentService
from app.schemas.appointment_booking import DoctorAppointmentsGroupedResponse
from app.core.exceptions import laravel_response, BadRequestException
from loguru import logger


router = APIRouter(
    prefix="/doctor/appointments",
    tags=["Doctor - Appointments"],
    dependencies=[Depends(require_feature("appointments"))],
)


@router.get(
    "/grouped",
    status_code=status.HTTP_200_OK,
    summary="Get doctor's appointments grouped by status",
    description="""
    Get doctor's appointments grouped into three categories with pagination:
    
    **Today Appointments:**
    - Appointments scheduled for today (appointment_date == today)
    - Ordered by start_time (earliest first)
    
    **Upcoming Appointments:**
    - Appointments scheduled for future dates (appointment_date > today)
    - Ordered by appointment_date (soonest first), then start_time
    
    **Completed Appointments:**
    - Appointments that have passed (appointment_date < today) OR status = 'COMPLETED'
    - Ordered by appointment_date descending (most recent first), then start_time
    
    **Doctor Only Endpoint**
    - Only authenticated doctors can access their own appointments
    
    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **type**: Filter by type - 'today', 'upcoming', or 'completed' (optional)
    - **search**: Search by patient name (optional)
    
    Returns a Laravel-compatible response with three arrays: today, upcoming, and completed.
    Each appointment includes patient details, service information, and appointment details.
    """
)
async def get_doctor_appointments_grouped(
    current_user: DoctorUser,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    type: Optional[str] = Query(None, description="Filter by type: 'today', 'upcoming', or 'completed'"),
    search: Optional[str] = Query(None, description="Search by patient name"),
    db: Session = Depends(get_db)
):
    """
    Get appointments grouped by status for the authenticated doctor with pagination
    
    Groups appointments into:
    - **Today**: Appointments scheduled for today
    - **Upcoming**: Appointments scheduled for future dates
    - **Completed**: Appointments from past dates or with COMPLETED status
    
    **Authentication Required**: Yes (Doctor role)
    
    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **type**: Optional filter by type ('today', 'upcoming', 'completed')
    - **search**: Optional search by patient name
    
    Note: DoctorUser dependency already enforces doctor role, so no additional role check needed.
    """

    appointment_service = AppointmentService(db)

    try:
        grouped = appointment_service.list_doctor_appointments_grouped(
            current_user=current_user,
            page=page,
            per_page=per_page,
            appointment_type=type,
            search=search
        )
        return laravel_response(
            success=True,
            message="Doctor appointments retrieved successfully",
            data=grouped
        )
    except Exception as e:
        logger.error(f"Error retrieving doctor appointments: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving doctor appointments",
            errors={"general": [str(e)]}
        )
