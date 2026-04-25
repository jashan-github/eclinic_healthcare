"""
Authentication endpoints
Laravel-compatible auth API
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, get_client_ip
from app.core.security import CurrentUser
from app.core.exceptions import laravel_response, UnauthorizedException
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    UserProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    RegisterRequest,
    RegisterResponse
)

router = APIRouter()


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(
    request: LoginRequest,
    client_request: Request,
    db: Session = Depends(get_db),
    ip_address: str = Depends(get_client_ip)
):
    """
    User login
    
    **Laravel-compatible endpoint**
    
    - **email**: User email address
    - **password**: User password
    - **role**: (Optional) Expected user role. If provided, validates that the user's role matches the requested role.
    
    Returns user data and JWT tokens
    
    Note: All login attempts (successful and failed) are logged to login_attempts table.
    """
    auth_service = AuthService(db)
    
    # Extract user agent from request
    user_agent = client_request.headers.get("user-agent")
    
    try:
        result = auth_service.login(
            email=request.email,
            password=request.password,
            role=request.role,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return laravel_response(
            success=True,
            message="Login successful",
            data=result
        )
    except UnauthorizedException:
        # Login attempt already logged in auth_service.login()
        raise


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Patient registration
    
    **Laravel-compatible endpoint**
    
    **Only patients can register themselves via this endpoint.**
    Other roles (doctor, nurse, staff, etc.) must be created by admins.
    
    Required fields:
    - **first_name**: First name
    - **last_name**: Last name
    - **date_of_birth**: Date of birth (YYYY-MM-DD)
    - **gender**: Gender (male, female, other)
    - **email**: User email address
    - **password**: User password (minimum 8 characters)
    - **password_confirmation**: Password confirmation
    
    Optional fields:
    - **title**: Title (Dr, Mr, Mrs, Ms, etc.)
    - **middle_name**: Middle name
    - **country_id**: Country ID for phone code (required if mobile_number is provided)
    - **mobile_number**: Mobile number without country code (optional)
    
    Returns user data and JWT tokens
    """
    auth_service = AuthService(db)
    
    result = auth_service.register(
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        date_of_birth=request.date_of_birth,
        gender=request.gender,
        title=request.title,
        middle_name=request.middle_name,
        country_id=request.country_id,
        mobile_number=request.mobile_number
    )
    
    return laravel_response(
        success=True,
        message="Registration successful",
        data=result
    )


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=200)
async def refresh_token(
    request: RefreshTokenRequest,
    client_request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token
    
    **Laravel-compatible endpoint**
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token and refresh token
    """
    auth_service = AuthService(db)
    
    # Extract IP address and user agent for audit logging
    ip_address = None
    if client_request.client:
        ip_address = client_request.client.host
    forwarded_for = client_request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    
    user_agent = client_request.headers.get("user-agent")
    
    # Refresh tokens - HIPAA FIX 3: Audit logging is handled in auth_service.refresh_tokens()
    result = auth_service.refresh_tokens(
        request.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return laravel_response(
        success=True,
        message="Token refreshed successfully",
        data=result
    )


@router.post("/logout", response_model=LogoutResponse, status_code=200)
async def logout(
    authorization: Optional[str] = Header(None),
    refresh_token: Optional[str] = None,
    client_request: Request = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    User logout
    
    **Laravel-compatible endpoint**
    
    Blacklists the current access token and optionally the refresh token.
    Requires authentication.
    """
    auth_service = AuthService(db)
    
    # Extract access token from Authorization header
    access_token = None
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.replace("Bearer ", "")
    
    # Extract IP address and user agent for audit logging
    ip_address = None
    if client_request and client_request.client:
        ip_address = client_request.client.host
    forwarded_for = client_request.headers.get("X-Forwarded-For") if client_request else None
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    
    user_agent = client_request.headers.get("user-agent") if client_request else None
    
    # Logout (blacklist tokens) - HIPAA FIX 3: Pass user_id, IP, and user_agent for audit
    auth_service.logout(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return laravel_response(
        success=True,
        message="Logged out successfully",
        data=None
    )


@router.get("/profile", response_model=UserProfileResponse, status_code=200)
async def get_profile(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get user profile
    
    **Laravel-compatible endpoint**
    
    Returns authenticated user's profile data.
    Requires authentication.
    """
    auth_service = AuthService(db)
    
    profile = auth_service.get_profile(current_user.id)
    
    return laravel_response(
        success=True,
        message="Profile retrieved successfully",
        data=profile
    )


@router.put("/profile", response_model=UpdateProfileResponse, status_code=200)
@router.patch("/profile", response_model=UpdateProfileResponse, status_code=200)
async def update_profile(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update user profile
    
    **Laravel-compatible endpoint**
    
    - **name**: User full name (optional)
    - **phone**: Phone number (optional)
    
    Returns updated profile data.
    Requires authentication.
    """
    auth_service = AuthService(db)
    
    profile = auth_service.update_profile(
        user_id=current_user.id,
        name=request.name,
        phone=request.phone
    )
    
    return laravel_response(
        success=True,
        message="Profile updated successfully",
        data=profile
    )


@router.post("/change-password", response_model=ChangePasswordResponse, status_code=200)
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Change user password
    
    **Laravel-compatible endpoint**
    
    - **current_password**: Current password
    - **new_password**: New password
    - **new_password_confirmation**: New password confirmation
    
    Requires authentication.
    """
    auth_service = AuthService(db)
    
    auth_service.change_password(
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password
    )
    
    return laravel_response(
        success=True,
        message="Password changed successfully",
        data=None
    )


@router.get("/me", response_model=UserProfileResponse, status_code=200)
async def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current authenticated user
    
    **Laravel-compatible endpoint (alias for /profile)**
    
    Returns authenticated user's profile data.
    Requires authentication.
    """
    auth_service = AuthService(db)
    
    profile = auth_service.get_profile(current_user.id)
    
    return laravel_response(
        success=True,
        message="User retrieved successfully",
        data=profile
    )
