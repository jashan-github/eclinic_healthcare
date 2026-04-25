"""
Waiver Settings API
Admin-only: enable/disable waiver and set single waiver percentage (0-100%).
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


router = APIRouter(prefix="/admin/waiver-settings", tags=["Admin - Waiver Settings"])


class WaiverSettingsResponse(BaseModel):
    """Waiver settings response."""
    waiver_enabled: bool = Field(..., description="Whether waiver feature is enabled")
    waiver_percent: int = Field(..., ge=0, le=100, description="Allowed waiver percentage (0-100); ignored when waiver_doctor_decides is True")
    waiver_doctor_decides: bool = Field(..., description="When True, doctor sets waiver (0,25,50,75,100%) at accept; admin waiver_percent ignored")


class WaiverSettingsUpdateRequest(BaseModel):
    """Waiver settings update request."""
    waiver_enabled: bool | None = Field(None, description="Enable or disable waiver feature")
    waiver_percent: int | None = Field(None, ge=0, le=100, description="Allowed waiver percentage (0-100); ignored when waiver_doctor_decides is True")
    waiver_doctor_decides: bool | None = Field(None, description="When True, doctor sets waiver at accept (0,25,50,75,100%); admin waiver_percent ignored")


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get waiver settings (admin)",
    description="Get current waiver settings: enabled/disabled and waiver percentage (0-100%).",
)
async def get_waiver_settings(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Get waiver settings (admin only)."""
    try:
        settings_service = AdminSettingsService(db)
        settings = settings_service.get_settings()
        data = {
            "waiver_enabled": settings.waiver_enabled,
            "waiver_percent": settings.waiver_percent,
            "waiver_doctor_decides": getattr(settings, "waiver_doctor_decides", False),
        }
        return laravel_response(
            success=True,
            message="Waiver settings retrieved successfully",
            data=data,
        )
    except Exception as e:
        logger.error(f"Error retrieving waiver settings: {str(e)}", exc_info=True)
        raise


@router.put(
    "",
    status_code=status.HTTP_200_OK,
    summary="Update waiver settings (admin)",
    description="Enable/disable waiver and set waiver percentage (0-100%).",
)
async def update_waiver_settings(
    request_data: WaiverSettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Update waiver settings (admin only)."""
    try:
        settings_service = AdminSettingsService(db)
        settings = settings_service.update_settings(
            current_user=current_user,
            waiver_enabled=request_data.waiver_enabled,
            waiver_percent=request_data.waiver_percent,
            waiver_doctor_decides=request_data.waiver_doctor_decides,
        )
        data = {
            "waiver_enabled": settings.waiver_enabled,
            "waiver_percent": settings.waiver_percent,
            "waiver_doctor_decides": getattr(settings, "waiver_doctor_decides", False),
        }
        return laravel_response(
            success=True,
            message="Waiver settings updated successfully",
            data=data,
        )
    except Exception as e:
        logger.error(f"Error updating waiver settings: {str(e)}", exc_info=True)
        raise
