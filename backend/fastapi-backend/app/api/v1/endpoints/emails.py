"""
Email API Endpoints
Endpoints for sending emails via SendGrid
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, timedelta, timezone
import secrets

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.security import CurrentUser
from app.core.config import settings
from app.core.exceptions import laravel_response, BadRequestException, ValidationException, NotFoundException
from app.services.email_service import EmailService
from app.repositories.user_repository import UserRepository
from app.models.user import User
from loguru import logger


router = APIRouter(prefix="/emails", tags=["Emails"])


# Request Schemas
class ResetPasswordEmailRequest(BaseModel):
    """Request schema for sending reset password email"""
    email: EmailStr = Field(..., description="User email address to send password reset")


class ResetPasswordRequest(BaseModel):
    """Request schema for resetting password with token"""
    token: str = Field(..., description="Password reset token from email", min_length=10)
    password: str = Field(..., description="New password", min_length=8)
    confirm_password: str = Field(..., description="Confirm new password", min_length=8)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class NewAppointmentEmailRequest(BaseModel):
    """Request schema for sending new appointment email"""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    recipient_name: str = Field(..., description="Recipient name")
    doctor_name: str = Field(..., description="Doctor name")
    appointment_date: str = Field(..., description="Appointment date (formatted string, e.g., 'January 15, 2025')")
    appointment_time: str = Field(..., description="Appointment time (formatted string, e.g., '10:00 AM')")
    service_name: str = Field(..., description="Service name")
    consultation_mode: str = Field(..., description="Consultation mode (IN_CLINIC or TELECONSULTATION)")
    appointment_id: Optional[str] = Field(None, description="Appointment ID (optional)")


class AppointmentConfirmedEmailRequest(BaseModel):
    """Request schema for sending appointment confirmed email"""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    recipient_name: str = Field(..., description="Recipient name")
    doctor_name: str = Field(..., description="Doctor name")
    appointment_date: str = Field(..., description="Appointment date (formatted string, e.g., 'January 15, 2025')")
    appointment_time: str = Field(..., description="Appointment time (formatted string, e.g., '10:00 AM')")
    service_name: str = Field(..., description="Service name")
    consultation_mode: str = Field(..., description="Consultation mode (IN_CLINIC or TELECONSULTATION)")
    appointment_id: Optional[str] = Field(None, description="Appointment ID (optional)")


# Response Schema
class EmailResponse(BaseModel):
    """Email response schema"""
    success: bool = True
    message: str = "Email sent successfully"
    data: Optional[dict] = None
    errors: Optional[dict] = None


@router.post(
    "/reset-password",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send reset password email",
    description="Send password reset email to user via SendGrid"
)
async def send_reset_password_email(
    request_data: ResetPasswordEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Send password reset email (Forgot Password)
    
    **Public endpoint** (can be called without authentication for password reset flow)
    
    Verifies if the email exists in the system. If it exists, generates a secure reset token,
    stores it with expiration (1 hour), and sends a password reset email with the reset link.
    
    **Security Note:**
    - Returns error if email doesn't exist
    - Reset token expires in 1 hour
    - Only one active reset token per user (previous tokens are invalidated)
    
    **Request Body:**
    - **email**: User email address
    
    **Returns:**
    - Success message (always, for security - doesn't reveal if email exists)
    """
    try:
        user_repo = UserRepository(db)
        
        # Get user by email (case-insensitive)
        user = db.query(User).filter(
            User.email.ilike(request_data.email.lower()),
            User.deleted_at.is_(None)
        ).first()
        
        # Check if user exists
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {request_data.email}")
            raise NotFoundException(
                message="Email not found",
                errors={"email": ["No account found with this email address"]}
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Password reset requested for inactive user: {user.id}")
            raise BadRequestException(
                message="Account is inactive",
                errors={"account": ["This account has been deactivated. Please contact support."]}
            )
        
        # Generate secure reset token (32 bytes = 43 characters in URL-safe base64)
        reset_token = secrets.token_urlsafe(32)
        
        # Set token expiration (1 hour from now)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Store reset token in user record
        user = user_repo.set_reset_token(user, reset_token, expires_at)
        
        # Check admin setting: allow sending password reset email
        from app.services.admin_settings_service import AdminSettingsService
        admin_settings = AdminSettingsService(db).get_settings()
        if not getattr(admin_settings, "email_notify_password_reset", True):
            logger.info(f"Password reset email disabled by admin; token stored for user_id={user.id}")
            return laravel_response(
                success=True,
                message="Password reset email sent successfully",
                data={"email": user.email}
            )
        
        # Get user name for email
        recipient_name = user.name
        
        # Initialize email service
        try:
            email_service = EmailService()
        except ValueError as e:
            logger.error(f"Email service configuration error: {str(e)}")
            raise BadRequestException(
                message="Email service not configured",
                errors={"configuration": [str(e)]}
            )
        
        # Send email with reset token
        try:
            await email_service.send_reset_password_email(
                recipient_email=user.email,
                recipient_name=recipient_name,
                reset_token=reset_token,
                reset_url=None  # Will be constructed from BASE_URL
            )
        except Exception as email_error:
            # Log the actual SendGrid error for debugging
            logger.error(f"SendGrid email sending failed: {str(email_error)}", exc_info=True)
            raise BadRequestException(
                message="Failed to send password reset email",
                errors={"email": [str(email_error)]}
            )
        
        logger.info(f"Password reset email sent to {user.email} (user_id: {user.id})")
        
        return laravel_response(
            success=True,
            message="Password reset email sent successfully",
            data={"email": user.email}
        )
    
    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to send reset password email: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Failed to send reset password email",
            errors={"email": [str(e)]}
        )


@router.post(
    "/new-appointment",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send new appointment email",
    description="Send new appointment notification email via SendGrid"
)
async def send_new_appointment_email(
    request_data: NewAppointmentEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Send new appointment notification email
    
    **Authenticated endpoint**
    
    Sends a notification email when a new appointment is scheduled.
    
    **Request Body:**
    - **recipient_email**: Recipient email address
    - **recipient_name**: Recipient name
    - **doctor_name**: Doctor name
    - **appointment_date**: Appointment date (formatted string)
    - **appointment_time**: Appointment time (formatted string)
    - **service_name**: Service name
    - **consultation_mode**: Consultation mode (IN_CLINIC or TELECONSULTATION)
    - **appointment_id**: (Optional) Appointment ID
    
    **Returns:**
    - Success message if email sent successfully
    """
    try:
        # Validate consultation mode
        if request_data.consultation_mode not in ["IN_CLINIC", "TELECONSULTATION"]:
            raise ValidationException(
                message="Invalid consultation mode",
                errors={"consultation_mode": ["Must be either 'IN_CLINIC' or 'TELECONSULTATION'"]}
            )
        
        # Initialize email service
        email_service = EmailService()
        
        # Send email
        await email_service.send_new_appointment_email(
            recipient_email=request_data.recipient_email,
            recipient_name=request_data.recipient_name,
            doctor_name=request_data.doctor_name,
            appointment_date=request_data.appointment_date,
            appointment_time=request_data.appointment_time,
            service_name=request_data.service_name,
            consultation_mode=request_data.consultation_mode,
            appointment_id=request_data.appointment_id
        )
        
        logger.info(f"New appointment email sent to {request_data.recipient_email}")
        
        return laravel_response(
            success=True,
            message="New appointment email sent successfully",
            data={"email": request_data.recipient_email}
        )
    
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Failed to send new appointment email: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Failed to send new appointment email",
            errors={"email": [str(e)]}
        )


@router.post(
    "/appointment-confirmed",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send appointment confirmed email",
    description="Send appointment confirmed notification email via SendGrid"
)
async def send_appointment_confirmed_email(
    request_data: AppointmentConfirmedEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Send appointment confirmed email
    
    **Authenticated endpoint**
    
    Sends a confirmation email when an appointment is confirmed.
    
    **Request Body:**
    - **recipient_email**: Recipient email address
    - **recipient_name**: Recipient name
    - **doctor_name**: Doctor name
    - **appointment_date**: Appointment date (formatted string)
    - **appointment_time**: Appointment time (formatted string)
    - **service_name**: Service name
    - **consultation_mode**: Consultation mode (IN_CLINIC or TELECONSULTATION)
    - **appointment_id**: (Optional) Appointment ID
    
    **Returns:**
    - Success message if email sent successfully
    """
    try:
        # Validate consultation mode
        if request_data.consultation_mode not in ["IN_CLINIC", "TELECONSULTATION"]:
            raise ValidationException(
                message="Invalid consultation mode",
                errors={"consultation_mode": ["Must be either 'IN_CLINIC' or 'TELECONSULTATION'"]}
            )
        
        # Initialize email service
        email_service = EmailService()
        
        # Send email
        await email_service.send_appointment_confirmed_email(
            recipient_email=request_data.recipient_email,
            recipient_name=request_data.recipient_name,
            doctor_name=request_data.doctor_name,
            appointment_date=request_data.appointment_date,
            appointment_time=request_data.appointment_time,
            service_name=request_data.service_name,
            consultation_mode=request_data.consultation_mode,
            appointment_id=request_data.appointment_id
        )
        
        logger.info(f"Appointment confirmed email sent to {request_data.recipient_email}")
        
        return laravel_response(
            success=True,
            message="Appointment confirmed email sent successfully",
            data={"email": request_data.recipient_email}
        )
    
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Failed to send appointment confirmed email: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Failed to send appointment confirmed email",
            errors={"email": [str(e)]}
        )


@router.post(
    "/reset-password-confirm",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with token",
    description="Reset user password using the token received via email"
)
async def reset_password_with_token(
    request_data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reset password with token
    
    **Public endpoint** (no authentication required)
    
    This endpoint is called from the frontend reset password page after the user
    enters their new password.
    
    **Request Body:**
    - **token**: Password reset token from email
    - **password**: New password (minimum 8 characters)
    - **confirm_password**: Password confirmation (must match password)
    
    **Returns:**
    - Success message if password reset successfully
    
    **Errors:**
    - 404: Token not found or user doesn't exist
    - 400: Token expired, user inactive, or passwords don't match
    """
    try:
        # Get user by reset token
        user = db.query(User).filter(
            User.reset_token == request_data.token,
            User.deleted_at.is_(None)
        ).first()
        
        # Check if token exists
        if not user:
            logger.warning(f"Password reset failed: token not found")
            raise NotFoundException(
                message="Invalid or expired reset token",
                errors={"token": ["The reset token is invalid or has expired"]}
            )
        
        # Check if token is expired (use timezone-aware datetime)
        current_time = datetime.now(timezone.utc)
        if not user.reset_token_expires_at or user.reset_token_expires_at < current_time:
            logger.warning(f"Password reset failed: token expired for user {user.id}")
            raise BadRequestException(
                message="Reset token has expired",
                errors={"token": ["The reset token has expired. Please request a new password reset."]}
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Password reset failed: user {user.id} is inactive")
            raise BadRequestException(
                message="Account is inactive",
                errors={"account": ["Your account is inactive. Please contact support."]}
            )
        
        # Update password using repository
        user_repo = UserRepository(db)
        user_repo.update_password(user, request_data.password)
        
        # Clear reset token after successful password reset
        user_repo.clear_reset_token(user)
        
        logger.info(f"Password reset successfully for user {user.id} (email: {user.email})")
        
        return laravel_response(
            success=True,
            message="Password reset successfully. You can now login with your new password.",
            data={"email": user.email}
        )
    
    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to reset password: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Failed to reset password",
            errors={"general": [str(e)]}
        )


@router.get(
    "/reset-password",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Verify reset password token and redirect",
    description="Verifies the password reset token and redirects to frontend reset password page or error page"
)
async def verify_reset_password_token(
    token: str = Query(..., description="Password reset token"),
    db: Session = Depends(get_db)
):
    """
    Verify reset password token and redirect
    
    **Public endpoint** (no authentication required)
    
    This endpoint is called when a user clicks on the password reset link in their email.
    It verifies the token and redirects to the appropriate frontend page.
    
    **Query Parameters:**
    - **token**: Password reset token from email link
    
    **Redirects:**
    - If token is valid: Redirects to `FRONTEND_URL/auth/reset-password?token={token}`
    - If token is invalid/expired: Redirects to `FRONTEND_URL/auth/reset-password-verification-failed`
    
    **Token Validation:**
    - Token must exist in user record
    - Token must not be expired (reset_token_expires_at > current time)
    - User must be active
    """
    try:
        # Get user by reset token
        user = db.query(User).filter(
            User.reset_token == token,
            User.deleted_at.is_(None)
        ).first()
        
        # Check if token exists
        if not user:
            logger.warning(f"Password reset token verification failed: token not found")
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            return RedirectResponse(
                url=f"{frontend_url}/auth/reset-password-verification-failed",
                status_code=307
            )
        
        # Check if token is expired
        if not user.reset_token_expires_at or user.reset_token_expires_at < datetime.utcnow():
            logger.warning(f"Password reset token verification failed: token expired for user {user.id}")
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            return RedirectResponse(
                url=f"{frontend_url}/auth/reset-password-verification-failed",
                status_code=307
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Password reset token verification failed: user {user.id} is inactive")
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            return RedirectResponse(
                url=f"{frontend_url}/auth/reset-password-verification-failed",
                status_code=307
            )
        
        # Token is valid - redirect to frontend reset password page with token
        logger.info(f"Password reset token verified successfully for user {user.id}")
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(
            url=f"{frontend_url}/auth/reset-password?token={token}",
            status_code=307
        )
    
    except Exception as e:
        logger.error(f"Error verifying reset password token: {str(e)}", exc_info=True)
        # On any error, redirect to failure page
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(
            url=f"{frontend_url}/auth/reset-password-verification-failed",
            status_code=307
        )


@router.post(
    "/test",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Test email sending",
    description="Test endpoint to verify email sending functionality (for debugging)"
)
async def test_email(
    recipient_email: EmailStr = Query(..., description="Recipient email address to test"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Test email sending functionality
    
    **Public endpoint** (for debugging)
    
    Sends a test email to verify SendGrid configuration and email delivery.
    
    **Query Parameters:**
    - **recipient_email**: Email address to send test email to
    
    **Returns:**
    - Success message with email details
    """
    try:
        # Initialize email service
        email_service = EmailService()
        
        # Send test email
        await email_service.send_new_appointment_email(
            recipient_email=recipient_email,
            recipient_name="Test User",
            doctor_name="Dr. Test Doctor",
            appointment_date="January 20, 2026",
            appointment_time="10:00 AM",
            service_name="Test Appointment",
            consultation_mode="IN_CLINIC",
            appointment_id="test-123"
        )
        
        logger.info(f"Test email sent successfully to {recipient_email}")
        
        return laravel_response(
            success=True,
            message=f"Test email sent successfully to {recipient_email}. Please check your inbox (and spam folder).",
            data={
                "recipient_email": recipient_email,
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Failed to send test email",
            errors={"email": [str(e)]}
        )
