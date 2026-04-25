"""
Role feature permissions API
Admin: GET/PUT role-permissions (doctor/staff tab visibility).
Doctor/Staff: GET /me/permissions for tab visibility.
"""

from typing import Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user, get_current_user
from app.core.security import CurrentUser, UserRole
from app.services.role_permission_service import RolePermissionService
from app.core.exceptions import laravel_response
from loguru import logger

router = APIRouter(tags=["Role Permissions"])


# ---- Admin: list and update role permissions ----

class RolePermissionsResponse(BaseModel):
    """Response: doctor and staff permission maps."""
    doctor: Dict[str, bool] = Field(..., description="Doctor tab permissions")
    staff: Dict[str, bool] = Field(..., description="Staff tab permissions")


class RolePermissionsUpdateRequest(BaseModel):
    """Request body for updating role permissions."""
    doctor: Dict[str, bool] | None = Field(None, description="Doctor tab permissions (only provided keys updated)")
    staff: Dict[str, bool] | None = Field(None, description="Staff tab permissions (only provided keys updated)")


@router.get(
    "/admin/role-permissions",
    status_code=status.HTTP_200_OK,
    summary="Get role permissions (admin)",
    description="Get doctor and staff tab/feature permissions. Used by admin to show/hide tabs per role.",
)
async def get_role_permissions(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Admin: get all role permissions."""
    try:
        service = RolePermissionService(db)
        data = service.get_all()
        return laravel_response(
            success=True,
            message="Role permissions retrieved",
            data=data,
        )
    except Exception as e:
        logger.error(f"Error retrieving role permissions: {str(e)}", exc_info=True)
        raise


@router.api_route(
    "/admin/role-permissions",
    methods=["PUT", "PATCH"],
    status_code=status.HTTP_200_OK,
    summary="Update role permissions (admin)",
    description="Update doctor and/or staff tab permissions. Only provided roles and keys are updated.",
)
async def update_role_permissions(
    request_data: RolePermissionsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Admin: update role permissions."""
    try:
        payload = {}
        if request_data.doctor is not None:
            payload["doctor"] = request_data.doctor
        if request_data.staff is not None:
            payload["staff"] = request_data.staff
        if not payload:
            service = RolePermissionService(db)
            data = service.get_all()
            return laravel_response(
                success=True,
                message="No changes provided",
                data=data,
            )
        service = RolePermissionService(db)
        data = service.update_bulk(payload)
        return laravel_response(
            success=True,
            message="Role permissions updated",
            data=data,
        )
    except Exception as e:
        logger.error(f"Error updating role permissions: {str(e)}", exc_info=True)
        raise


# ---- Doctor/Staff: get my permissions (for tab visibility) ----

@router.get(
    "/me/permissions",
    status_code=status.HTTP_200_OK,
    summary="Get my tab permissions",
    description="Returns the current user's tab/feature permissions. Doctor and staff only; others get empty or all true.",
)
async def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Doctor/Staff: returns { "appointments": true, "patients": true, ... } for tab visibility.
    Admin/Patient: returns null or empty so frontend shows all allowed tabs for that role.
    """
    try:
        service = RolePermissionService(db)
        permissions = service.get_for_current_user(current_user.role)
        if permissions is None:
            # Admin, patient, etc. - no tab filtering; frontend can show all for that role
            return laravel_response(
                success=True,
                message="No tab restrictions for this role",
                data={},
            )
        return laravel_response(
            success=True,
            message="Permissions retrieved",
            data=permissions,
        )
    except Exception as e:
        logger.error(f"Error retrieving my permissions: {str(e)}", exc_info=True)
        raise
