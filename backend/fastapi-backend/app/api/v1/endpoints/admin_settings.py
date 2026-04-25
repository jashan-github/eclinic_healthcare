"""
Admin Settings API Endpoints
Admin-only routes for managing system-wide configuration settings
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.core.security import CurrentUser
from app.services.admin_settings_service import AdminSettingsService
from app.core.exceptions import laravel_response
from loguru import logger


router = APIRouter(prefix="/admin/settings", tags=["Admin - Settings"])


class AdminSettingsResponse(BaseModel):
    """Admin settings response schema"""
    id: str
    auto_approve_appointments: bool
    allow_same_day_booking: bool
    booking_window_days: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AdminSettingsUpdateRequest(BaseModel):
    """Admin settings update request schema"""
    auto_approve_appointments: bool | None = Field(None, description="Enable/disable auto-approval of appointments")
    allow_same_day_booking: bool | None = Field(None, description="Enable/disable same-day appointment booking")
    booking_window_days: int | None = Field(None, ge=1, description="Maximum days in advance for booking (e.g., 30 days)")


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get admin settings",
    description="""Get current system-wide admin settings (Admin only)

**Returns:**
- `auto_approve_appointments`: If enabled, appointment requests are automatically approved
- `allow_same_day_booking`: If enabled, patients can book appointments for the same day
- `booking_window_days`: Maximum number of days in advance patients can book (e.g., 30 days)

**Note:** Only one settings record exists (singleton pattern). Default settings are created automatically if none exist.
"""
)
async def get_admin_settings(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """Get current admin settings"""
    try:
        settings_service = AdminSettingsService(db)
        settings = settings_service.get_settings()
        
        response_data = AdminSettingsResponse(
            id=str(settings.id),
            auto_approve_appointments=settings.auto_approve_appointments,
            allow_same_day_booking=settings.allow_same_day_booking,
            booking_window_days=settings.booking_window_days,
            created_at=settings.created_at.isoformat() if settings.created_at else None,
            updated_at=settings.updated_at.isoformat() if settings.updated_at else None
        )
        
        return laravel_response(
            success=True,
            message="Admin settings retrieved successfully",
            data=response_data
        )
    except Exception as e:
        logger.error(f"Error retrieving admin settings: {str(e)}", exc_info=True)
        raise


@router.put(
    "",
    status_code=status.HTTP_200_OK,
    summary="Update admin settings",
    description="""Update system-wide admin settings (Admin only)

**Settings:**
- `auto_approve_appointments`: If enabled, appointment requests are automatically approved without doctor action
- `allow_same_day_booking`: If enabled, patients can book appointments for the same day
- `booking_window_days`: Maximum number of days in advance patients can book (must be >= 1)

**Note:** Only provide the fields you want to update. Omitted fields will remain unchanged.
"""
)
async def update_admin_settings(
    request_data: AdminSettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """Update admin settings"""
    try:
        settings_service = AdminSettingsService(db)
        settings = settings_service.update_settings(
            current_user=current_user,
            auto_approve_appointments=request_data.auto_approve_appointments,
            allow_same_day_booking=request_data.allow_same_day_booking,
            booking_window_days=request_data.booking_window_days,
        )
        
        response_data = AdminSettingsResponse(
            id=str(settings.id),
            auto_approve_appointments=settings.auto_approve_appointments,
            allow_same_day_booking=settings.allow_same_day_booking,
            booking_window_days=settings.booking_window_days,
            created_at=settings.created_at.isoformat() if settings.created_at else None,
            updated_at=settings.updated_at.isoformat() if settings.updated_at else None
        )
        
        return laravel_response(
            success=True,
            message="Admin settings updated successfully",
            data=response_data
        )
    except Exception as e:
        logger.error(f"Error updating admin settings: {str(e)}", exc_info=True)
        raise
