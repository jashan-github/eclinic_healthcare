"""
Admin Settings Service
Business logic for managing system-wide admin configuration settings
"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from loguru import logger
from datetime import date, datetime
import pytz

from app.models.admin_settings import AdminSettings
from app.core.exceptions import NotFoundException, BadRequestException
from app.core.security import CurrentUser, UserRole

# EST timezone (UTC-05:00, handles EST/EDT automatically)
EST = pytz.timezone('America/New_York')

def get_est_date() -> date:
    """Get current date in EST timezone"""
    return datetime.now(EST).date()


class AdminSettingsService:
    """Service for admin settings operations"""
    
    def __init__(self, db: Session):
        """
        Initialize admin settings service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_settings(self) -> AdminSettings:
        """
        Get the current admin settings (singleton pattern)
        
        Returns:
            AdminSettings object (creates default if none exists)
        """
        settings = self.db.query(AdminSettings).filter(
            AdminSettings.deleted_at.is_(None)
        ).first()
        
        if not settings:
            # Create default settings if none exist
            logger.info("No admin settings found, creating default settings")
            settings = AdminSettings(
                auto_approve_appointments=False,
                allow_same_day_booking=False,
                booking_window_days=30,
                email_notify_password_reset=True,
                email_notify_new_appointment_request=True,
                email_notify_appointment_accepted=True,
                waiver_enabled=False,
                waiver_percent=0,
                waiver_doctor_decides=False,
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        
        return settings
    
    def update_settings(
        self,
        current_user: CurrentUser,
        auto_approve_appointments: Optional[bool] = None,
        allow_same_day_booking: Optional[bool] = None,
        booking_window_days: Optional[int] = None,
        email_notify_password_reset: Optional[bool] = None,
        email_notify_new_appointment_request: Optional[bool] = None,
        email_notify_appointment_accepted: Optional[bool] = None,
        email_notify_appointment_rejected: Optional[bool] = None,
        waiver_enabled: Optional[bool] = None,
        waiver_percent: Optional[int] = None,
        waiver_doctor_decides: Optional[bool] = None,
    ) -> AdminSettings:
        """
        Update admin settings (admin only)
        
        Args:
            current_user: Current user (must be admin)
            auto_approve_appointments: Optional auto-approve setting
            allow_same_day_booking: Optional same-day booking setting
            booking_window_days: Optional booking window in days
            
        Returns:
            Updated AdminSettings object
        """
        # Validate admin role
        if current_user.role not in [UserRole.SUPER_ADMIN.value, UserRole.CLINIC_ADMIN.value]:
            raise BadRequestException(
                message="Access denied",
                errors={"role": ["Only admins can update system settings"]}
            )
        
        # Get existing settings
        settings = self.get_settings()
        
        # Update fields if provided
        if auto_approve_appointments is not None:
            settings.auto_approve_appointments = auto_approve_appointments
            logger.info(f"Admin {current_user.id} updated auto_approve_appointments to {auto_approve_appointments}")
        
        if allow_same_day_booking is not None:
            settings.allow_same_day_booking = allow_same_day_booking
            logger.info(f"Admin {current_user.id} updated allow_same_day_booking to {allow_same_day_booking}")
        
        if booking_window_days is not None:
            if booking_window_days < 1:
                raise BadRequestException(
                    message="Invalid booking window",
                    errors={"booking_window_days": ["Booking window must be at least 1 day"]}
                )
            settings.booking_window_days = booking_window_days
            logger.info(f"Admin {current_user.id} updated booking_window_days to {booking_window_days}")
        
        if email_notify_password_reset is not None:
            settings.email_notify_password_reset = email_notify_password_reset
            logger.info(f"Admin {current_user.id} updated email_notify_password_reset to {email_notify_password_reset}")
        if email_notify_new_appointment_request is not None:
            settings.email_notify_new_appointment_request = email_notify_new_appointment_request
            logger.info(f"Admin {current_user.id} updated email_notify_new_appointment_request to {email_notify_new_appointment_request}")
        if email_notify_appointment_accepted is not None:
            settings.email_notify_appointment_accepted = email_notify_appointment_accepted
            logger.info(f"Admin {current_user.id} updated email_notify_appointment_accepted to {email_notify_appointment_accepted}")
        if email_notify_appointment_rejected is not None:
            settings.email_notify_appointment_rejected = email_notify_appointment_rejected
            logger.info(f"Admin {current_user.id} updated email_notify_appointment_rejected to {email_notify_appointment_rejected}")

        if waiver_enabled is not None:
            settings.waiver_enabled = waiver_enabled
            logger.info(f"Admin {current_user.id} updated waiver_enabled to {waiver_enabled}")
        if waiver_percent is not None:
            if not (0 <= waiver_percent <= 100):
                raise BadRequestException(
                    message="Invalid waiver percent",
                    errors={"waiver_percent": ["Must be between 0 and 100"]}
                )
            settings.waiver_percent = waiver_percent
            logger.info(f"Admin {current_user.id} updated waiver_percent to {waiver_percent}")
        if waiver_doctor_decides is not None:
            settings.waiver_doctor_decides = waiver_doctor_decides
            logger.info(f"Admin {current_user.id} updated waiver_doctor_decides to {waiver_doctor_decides}")

        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        
        return settings
    
    def validate_booking_date(self, preferred_date: Any) -> tuple[bool, Optional[str]]:
        """
        Validate if a booking date is allowed based on current settings
        
        Args:
            preferred_date: Date object or date string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        from datetime import date, datetime, timedelta
        
        # Convert to date if needed
        if isinstance(preferred_date, str):
            try:
                preferred_date = datetime.fromisoformat(preferred_date).date()
            except (ValueError, AttributeError):
                try:
                    preferred_date = datetime.strptime(preferred_date, "%Y-%m-%d").date()
                except ValueError:
                    return False, "Invalid date format"
        elif isinstance(preferred_date, datetime):
            preferred_date = preferred_date.date()
        
        if not isinstance(preferred_date, date):
            return False, "Invalid date type"
        
        settings = self.get_settings()
        today = get_est_date()
        
        # Check if same-day booking is allowed
        if preferred_date == today and not settings.allow_same_day_booking:
            return False, "Same-day booking is not allowed. Please select a future date."
        
        # Check if date is in the past
        if preferred_date < today:
            return False, "Cannot book appointments in the past. Please select a future date."
        
        # Check booking window
        max_booking_date = today + timedelta(days=settings.booking_window_days)
        if preferred_date > max_booking_date:
            return False, f"Appointments can only be booked up to {settings.booking_window_days} days in advance. Maximum booking date: {max_booking_date.isoformat()}."
        
        return True, None
