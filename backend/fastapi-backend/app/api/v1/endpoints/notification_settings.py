"""
Admin notification settings API
Email notification toggles only: password reset, new appointment request (to doctor), appointment accepted (to patient).
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


router = APIRouter(prefix="/admin/notification-settings", tags=["Admin - Notification Settings"])


# Display labels for each setting key (frontend can use without hardcoding)
NOTIFICATION_SETTING_LABELS = {
    "email_notify_password_reset": "Password reset email",
    "email_notify_new_appointment_request": "New appointment request (email to doctor)",
    "email_notify_appointment_accepted": "Appointment accepted (email to patient)",
    "email_notify_appointment_rejected": "Appointment rejected (email to patient)",
}


class NotificationSettingsResponse(BaseModel):
    """Email notification settings response (admin only)."""
    email_notify_password_reset: bool = True
    email_notify_new_appointment_request: bool = True
    email_notify_appointment_accepted: bool = True
    email_notify_appointment_rejected: bool = True
    labels: dict | None = Field(None, description="Display labels for each setting key")

    class Config:
        from_attributes = True


class NotificationSettingsUpdateRequest(BaseModel):
    """Update only email notification toggles."""
    email_notify_password_reset: bool | None = Field(None, description="Enable/disable password reset email")
    email_notify_new_appointment_request: bool | None = Field(None, description="Enable/disable new appointment request email to doctor")
    email_notify_appointment_accepted: bool | None = Field(None, description="Enable/disable appointment accepted email to patient")
    email_notify_appointment_rejected: bool | None = Field(None, description="Enable/disable appointment rejected email to patient")


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get email notification settings",
    description="Get admin email notification toggles (Admin only). Controls: password reset, new appointment request (to doctor), appointment accepted (to patient).",
)
async def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Get email notification settings only."""
    try:
        settings_service = AdminSettingsService(db)
        settings = settings_service.get_settings()
        data = {
            "email_notify_password_reset": getattr(settings, "email_notify_password_reset", True),
            "email_notify_new_appointment_request": getattr(settings, "email_notify_new_appointment_request", True),
            "email_notify_appointment_accepted": getattr(settings, "email_notify_appointment_accepted", True),
            "email_notify_appointment_rejected": getattr(settings, "email_notify_appointment_rejected", True),
            "labels": NOTIFICATION_SETTING_LABELS,
        }
        return laravel_response(
            success=True,
            message="Notification settings retrieved",
            data=data,
        )
    except Exception as e:
        logger.error("Error retrieving notification settings: {}", str(e), exc_info=True)
        raise


@router.put(
    "",
    status_code=status.HTTP_200_OK,
    summary="Update email notification settings",
    description="Update email notification toggles only (Admin only). Omitted fields remain unchanged.",
)
async def update_notification_settings(
    request_data: NotificationSettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Update only email notification settings."""
    try:
        settings_service = AdminSettingsService(db)
        settings = settings_service.update_settings(
            current_user=current_user,
            email_notify_password_reset=request_data.email_notify_password_reset,
            email_notify_new_appointment_request=request_data.email_notify_new_appointment_request,
            email_notify_appointment_accepted=request_data.email_notify_appointment_accepted,
            email_notify_appointment_rejected=request_data.email_notify_appointment_rejected,
        )
        data = {
            "email_notify_password_reset": getattr(settings, "email_notify_password_reset", True),
            "email_notify_new_appointment_request": getattr(settings, "email_notify_new_appointment_request", True),
            "email_notify_appointment_accepted": getattr(settings, "email_notify_appointment_accepted", True),
            "email_notify_appointment_rejected": getattr(settings, "email_notify_appointment_rejected", True),
            "labels": NOTIFICATION_SETTING_LABELS,
        }
        return laravel_response(
            success=True,
            message="Notification settings updated",
            data=data,
        )
    except Exception as e:
        logger.error("Error updating notification settings: {}", str(e), exc_info=True)
        raise
