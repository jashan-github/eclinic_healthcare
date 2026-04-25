"""
Patient Dashboard API Endpoints
Routes for patient dashboard data
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import CurrentUser, UserRole
from app.services.patient_dashboard_service import PatientDashboardService
from app.schemas.patient_dashboard import PatientDashboardResponse
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    laravel_response
)


router = APIRouter(prefix="/patient/dashboard", tags=["Patient - Dashboard"])


@router.get(
    "",
    response_model=PatientDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient dashboard data",
    description="""Get comprehensive dashboard data for the authenticated patient

**Returns:**
- Summary statistics:
  - Upcoming appointments count
  - Documents uploaded count
  - Pending approvals count
- Upcoming appointments list (with doctor details, specialty, date/time)
- Recent activity feed (appointment confirmations, document uploads)

**Patient only endpoint**

**Example Response:**
```json
{
  "success": true,
  "message": "Dashboard data retrieved successfully",
  "data": {
    "summary": {
      "upcoming_appointments": 1,
      "documents_uploaded": 5,
      "pending_approvals": 0
    },
    "upcoming_appointments": [
      {
        "id": "...",
        "doctor": {
          "id": "...",
          "name": "Dr. Sarah Johnson",
          "specialty": "General Physician",
          "profile_image": "..."
        },
        "service": {
          "id": "...",
          "name": "General Consultation"
        },
        "appointment_date": "2025-08-25",
        "appointment_time": "10:00 AM",
        "appointment_datetime": "2025-08-25T10:00:00",
        "status": "CONFIRMED",
        "consultation_mode": "IN_CLINIC"
      }
    ],
    "recent_activity": [
      {
        "id": "...",
        "type": "appointment_confirmed",
        "icon": "checkmark",
        "message": "Your appointment with Dr. Sarah Johnson has been confirmed for Jan 25.",
        "created_at": "2026-01-12T08:00:00Z",
        "metadata": {
          "appointment_request_id": "...",
          "doctor_id": "...",
          "doctor_name": "Dr. Sarah Johnson",
          "service_name": "General Consultation",
          "appointment_date": "2026-01-25"
        }
      },
      {
        "id": "...",
        "type": "document_uploaded",
        "icon": "upload",
        "message": "Lab report uploaded successfully.",
        "created_at": "2026-01-11T10:00:00Z",
        "metadata": {
          "document_id": "...",
          "document_type": "Lab report",
          "file_name": "lab_results.pdf"
        }
      }
    ]
  }
}
```"""
)
async def get_patient_dashboard(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get patient dashboard data
    
    **Patient only endpoint**
    
    Returns comprehensive dashboard data including:
    - Summary statistics (counts)
    - Upcoming appointments with doctor details
    - Recent activity feed
    """
    # Validate current user is a patient
    if current_user.role != UserRole.PATIENT.value:
        raise ForbiddenException(
            message="Access denied",
            errors={"role": ["Only patients can access the dashboard"]}
        )
    
    try:
        dashboard_service = PatientDashboardService(db)
        dashboard_data = dashboard_service.get_dashboard_data(current_user)
        
        return laravel_response(
            success=True,
            message="Dashboard data retrieved successfully",
            data=dashboard_data
        )
    except (BadRequestException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving patient dashboard: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving dashboard data",
            errors={"general": [str(e)]}
        )
