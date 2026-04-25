"""
User management endpoints
Laravel-compatible user management API
"""

from typing import Optional, Union
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, Path, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger

from app.core.dependencies import get_db, get_current_user, AdminUser, get_client_ip
from app.core.security import CurrentUser
from app.core.exceptions import laravel_response
from app.core.config import settings
from app.services.user_service import UserService
from app.services.notification.dispatcher import get_notification_dispatcher
from app.utils.encryption import get_encryption_service
from app.services.audit_service import AuditService
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserListResponse,
    UserDetailResponse,
    UserCreateResponse,
    UserUpdateResponse,
    UserDeleteResponse,
    ActivateDeactivateRequest,
    ActivateDeactivateResponse,
    ChangeRoleRequest,
    ChangeRoleResponse,
    RolesListResponse,
    UserStatsResponse
)

router = APIRouter()


@router.get("", response_model=UserListResponse, status_code=200, include_in_schema=False)
@router.get("/", response_model=UserListResponse, status_code=200)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role (e.g. doctor, patient, clinic_admin, super_admin, nurse, staff, receptionist)"),
    by_role: Optional[str] = Query(None, alias="by_role", description="Filter by role (same as role)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID (UUID)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get list of users (admin only)
    
    **Laravel-compatible endpoint**
    
    Query parameters:
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **role** / **by_role**: Filter by role (doctor, patient, clinic_admin, super_admin, nurse, staff, receptionist)
    - **is_active**: Filter by active status
    - **search**: Search by name or email
    - **clinic_id**: Filter by clinic ID (super admin only)
    
    Requires admin authentication.
    """
    user_service = UserService(db)
    role_filter = role or by_role
    
    result = user_service.get_all_users(
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        current_user_clinic_id=current_user.clinic_id,
        page=page,
        per_page=per_page,
        role_filter=role_filter,
        is_active_filter=is_active,
        search=search,
        clinic_id_filter=clinic_id
    )
    
    return laravel_response(
        success=True,
        message="Users retrieved successfully",
        data=result
    )


@router.get("/statistics", response_model=UserStatsResponse, status_code=200)
async def get_user_statistics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get user statistics (admin only)
    
    **Laravel-compatible endpoint**
    
    Returns statistics about users including:
    - Total users
    - Active/inactive counts
    - Distribution by role
    
    Requires admin authentication.
    """
    user_service = UserService(db)
    
    stats = user_service.get_user_statistics(
        current_user_role=current_user.role,
        current_user_clinic_id=current_user.clinic_id
    )
    
    return laravel_response(
        success=True,
        message="Statistics retrieved successfully",
        data=stats
    )


@router.get("/{user_id}", response_model=UserDetailResponse, status_code=200)
async def get_user(
    user_id: UUID = Path(..., description="User ID (UUID)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get user by ID
    
    **Laravel-compatible endpoint**
    
    Path parameters:
    - **user_id**: User ID
    
    Users can view their own profile. Admins can view any user.
    """
    user_service = UserService(db)
    
    user = user_service.get_user_by_id(
        user_id=user_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        current_user_clinic_id=current_user.clinic_id
    )
    
    return laravel_response(
        success=True,
        message="User retrieved successfully",
        data=user
    )


async def _send_welcome_email_task(
    db: Session,
    user_email: str,
    user_name: str,
    password: str
) -> None:
    """
    Background task to send welcome email to newly created user
    
    Args:
        db: Database session
        user_email: User email address
        user_name: User name
        password: Plain text password
    """
    try:
        # Get notification dispatcher
        encryption_service = get_encryption_service()
        dispatcher = get_notification_dispatcher(db, encryption_service)
        
        # Check if email channel is enabled
        if not dispatcher.is_channel_enabled("email"):
            logger.warning(f"Email channel is disabled. Skipping welcome email to {user_email}")
            return
        
        # Prepare email content
        subject = f"Welcome to {settings.SMTP_FROM_NAME or 'eClinic'} - Your Account Details"
        
        # HTML email template
        message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Welcome to {settings.SMTP_FROM_NAME or 'eClinic'}!</h2>
                
                <p>Hello {user_name or 'User'},</p>
                
                <p>Your account has been created successfully. Please use the following credentials to log in and complete your profile:</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Email:</strong> {user_email}</p>
                    <p style="margin: 5px 0;"><strong>Password:</strong> {password}</p>
                </div>
                
                <p><strong>Important:</strong> Please log in and complete your profile. The following fields are required:</p>
                <ul>
                    <li>Name (First Name, Last Name)</li>
                    <li>Gender</li>
                    <li>Date of Birth</li>
                </ul>
                
                <p>For security reasons, we recommend changing your password after your first login.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>{settings.SMTP_FROM_NAME or 'eClinic Team'}</p>
            </div>
        </body>
        </html>
        """
        
        # Send email
        await dispatcher.send_email(
            email=user_email,
            message=message,
            subject=subject
        )
        
        logger.info(f"Welcome email sent successfully to {user_email}")
        
    except Exception as e:
        # Log error but don't raise - user creation should succeed even if email fails
        logger.error(f"Failed to send welcome email to {user_email}: {str(e)}")


@router.post("", response_model=UserCreateResponse, status_code=201, include_in_schema=False)
@router.post("/", response_model=UserCreateResponse, status_code=201)
async def create_user(
    request: UserCreate,
    client_request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create new user (admin only)
    
    **Laravel-compatible endpoint**
    
    Request body:
    - **email**: User email
    - **password**: User password (min 8 chars)
    - **name**: User full name
    - **phone**: Phone number (optional)
    - **role**: User role
    - **clinic_id**: Clinic ID (optional)
    - **assigned_doctor_id**: Assigned doctor ID (required for staff role)
    - **is_active**: Active status (default: true)
    - **education**: Doctor education (required when role is doctor; e.g. MBBS, MD)
    - **years_of_experience**: Doctor years of experience (required when role is doctor)
    - **specializations**: List of medical service UUIDs (required when role is doctor; at least one)
    
    Requires admin authentication.
    
    **Email Notification:**
    - Automatically sends welcome email with login credentials if email channel is enabled
    - Email includes: email, password, and instructions to complete profile
    """
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    user = user_service.create_user(
        email=request.email,
        password=request.password,
        name=request.name,
        role=request.role,
        phone=request.phone,
        clinic_id=request.clinic_id,
        assigned_doctor_id=request.assigned_doctor_id,
        is_active=request.is_active,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        current_user_clinic_id=current_user.clinic_id,
        education=request.education,
        years_of_experience=request.years_of_experience,
        specializations=request.specializations,
    )
    
    # Create audit log
    audit_service.create_audit_log_from_request(
        request=client_request,
        actor_user_id=current_user.id,
        action="create",
        entity_type="user",
        entity_id=user.get("id"),
        audit_metadata={
            "email": request.email,
            "role": request.role,
            "clinic_id": str(request.clinic_id) if request.clinic_id else None
        }
    )
    
    # Add background task to send welcome email
    background_tasks.add_task(
        _send_welcome_email_task,
        db=db,
        user_email=user.get("email"),
        user_name=user.get("name"),
        password=request.password
    )
    
    return laravel_response(
        success=True,
        message="User created successfully",
        data=user
    )


@router.put("/{user_id}", response_model=UserUpdateResponse, status_code=200)
@router.patch("/{user_id}", response_model=UserUpdateResponse, status_code=200)
async def update_user(
    request: UserUpdate,
    client_request: Request,
    user_id: UUID = Path(..., description="User ID (UUID)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update user (admin only)
    
    **Laravel-compatible endpoint**
    
    Path parameters:
    - **user_id**: User ID to update
    
    Request body (all optional):
    - **email**: User email
    - **name**: User full name
    - **phone**: Phone number
    - **role**: User role
    - **clinic_id**: Clinic ID (super admin only)
    - **assigned_doctor_id**: Assigned doctor ID (required for staff role)
    - **is_active**: Active status
    - **education**: Doctor education (e.g. MBBS, MD); applied when user is a doctor
    - **years_of_experience**: Doctor years of experience; applied when user is a doctor
    - **specializations**: List of medical service UUIDs; replaces existing when user is a doctor
    
    Requires admin authentication.
    """
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    user = user_service.update_user(
        user_id=user_id,
        email=request.email,
        name=request.name,
        phone=request.phone,
        role=request.role,
        clinic_id=request.clinic_id,
        assigned_doctor_id=request.assigned_doctor_id,
        is_active=request.is_active,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        current_user_clinic_id=current_user.clinic_id,
        education=request.education,
        years_of_experience=request.years_of_experience,
        specializations=request.specializations,
    )
    
    # Create audit log
    audit_service.create_audit_log_from_request(
        request=client_request,
        actor_user_id=current_user.id,
        action="update",
        entity_type="user",
        entity_id=user_id,
        audit_metadata={
            "updated_fields": {k: v for k, v in request.model_dump(exclude_unset=True).items() if v is not None}
        }
    )
    
    return laravel_response(
        success=True,
        message="User updated successfully",
        data=user
    )


@router.delete("/{user_id}", response_model=UserDeleteResponse, status_code=200)
async def delete_user(
    client_request: Request,
    user_id: UUID = Path(..., description="User ID (UUID)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete user (soft delete, admin only)
    
    **Laravel-compatible endpoint**
    
    Path parameters:
    - **user_id**: User ID to delete
    
    Performs soft delete (sets deleted_at timestamp).
    Users cannot delete themselves.
    
    Requires admin authentication.
    """
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    user_service.delete_user(
        user_id=user_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        current_user_clinic_id=current_user.clinic_id
    )
    
    # Create audit log
    audit_service.create_audit_log_from_request(
        request=client_request,
        actor_user_id=current_user.id,
        action="delete",
        entity_type="user",
        entity_id=user_id,
        audit_metadata={"soft_delete": True}
    )
    
    return laravel_response(
        success=True,
        message="User deleted successfully",
        data=None
    )


@router.post("/{user_id}/activate", response_model=ActivateDeactivateResponse, status_code=200)
@router.post("/{user_id}/deactivate", response_model=ActivateDeactivateResponse, status_code=200)
async def activate_deactivate_user(
    request: ActivateDeactivateRequest,
    client_request: Request,
    user_id: UUID = Path(..., description="User ID (UUID)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Activate or deactivate user (admin only)
    
    **Laravel-compatible endpoint**
    
    Path parameters:
    - **user_id**: User ID
    
    Request body:
    - **is_active**: Active status (true/false)
    - **reason**: Reason for status change (optional)
    
    Audit log includes reason and IP address.
    
    Requires admin authentication.
    """
    user_service = UserService(db)
    
    user = user_service.activate_deactivate_user(
        user_id=user_id,
        is_active=request.is_active,
        reason=request.reason,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        current_user_clinic_id=current_user.clinic_id,
        ip_address=ip_address
    )
    
    message = "User activated successfully" if request.is_active else "User deactivated successfully"
    
    return laravel_response(
        success=True,
        message=message,
        data=user
    )


@router.post("/{user_id}/change-role", response_model=ChangeRoleResponse, status_code=200)
async def change_user_role(
    request: ChangeRoleRequest,
    client_request: Request,
    user_id: UUID = Path(..., description="User ID (UUID)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Change user role (admin only)
    
    **Laravel-compatible endpoint**
    
    Path parameters:
    - **user_id**: User ID
    
    Request body:
    - **role**: New role
    - **reason**: Reason for role change (optional)
    
    Audit log includes reason and IP address.
    
    Requires admin authentication.
    """
    user_service = UserService(db)
    
    user = user_service.change_user_role(
        user_id=user_id,
        new_role=request.role,
        reason=request.reason,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        current_user_clinic_id=current_user.clinic_id,
        ip_address=ip_address
    )
    
    return laravel_response(
        success=True,
        message="Role changed successfully",
        data=user
    )


@router.get("/roles/list", response_model=RolesListResponse, status_code=200)
async def list_roles(db: Session = Depends(get_db)):
    """
    Get list of available roles
    
    **Laravel-compatible endpoint**
    
    Returns all available roles from the database.
    Public endpoint (no authentication required).
    """
    from app.models.auth import Role
    
    # Fetch all active roles from database
    db_roles = db.query(Role).filter(
        Role.deleted_at.is_(None)
    ).order_by(Role.name).all()
    
    # Map database roles to response format (all from database, no hardcoded values)
    roles = []
    for role in db_roles:
        # Generate display_name from name if not in database (simple string transformation)
        display_name = role.display_name if role.display_name else role.name.replace("_", " ").title()
        
        roles.append({
            "name": role.name,
            "display_name": display_name,
            "description": role.description or "",  # Empty string if not set in database
            "permissions": role.permissions if role.permissions is not None else []  # Empty list if not set
        })
    
    return laravel_response(
        success=True,
        message="Roles retrieved successfully",
        data={"roles": roles}
    )
