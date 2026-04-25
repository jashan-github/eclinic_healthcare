"""
Admin Settings model
Stores system-wide admin configuration settings
"""

from sqlalchemy import Column, Boolean, Integer, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class AdminSettings(BaseModel):
    """
    Admin Settings model
    
    Stores system-wide configuration settings that control:
    - Auto-approval of appointments
    - Same-day booking restrictions
    - Booking window (advance booking limit)
    
    Only one settings record should exist (singleton pattern enforced at application level)
    """
    
    __tablename__ = "admin_settings"
    
    # Auto-approve appointments setting
    auto_approve_appointments = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="If enabled, appointment requests are automatically approved without doctor action"
    )
    
    # Same-day booking setting
    allow_same_day_booking = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="If enabled, patients can book appointments for the same day"
    )
    
    # Booking window setting (in days)
    booking_window_days = Column(
        Integer,
        nullable=False,
        default=30,
        comment="Maximum number of days in advance patients can book appointments (e.g., 30 days from today)"
    )
    
    # Email notification toggles (admin can disable specific notifications)
    email_notify_password_reset = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="If enabled, send password reset email when user requests reset",
    )
    email_notify_new_appointment_request = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="If enabled, send email to doctor when patient creates appointment request",
    )
    email_notify_appointment_accepted = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="If enabled, send email to patient when doctor accepts appointment request",
    )
    email_notify_appointment_rejected = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="If enabled, send email to patient when doctor rejects appointment request",
    )

    # Waiver settings: enable/disable and single percentage (0-100%)
    waiver_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="If enabled, waiver feature is available; admin sets allowed percentage (0-100%)",
    )
    waiver_percent = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Allowed waiver percentage (0-100); ignored when waiver_doctor_decides is True",
    )
    waiver_doctor_decides = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="If True (and waiver_enabled), doctor sets waiver at accept (0,25,50,75,100%%); admin waiver_percent ignored",
    )

    __table_args__ = (
        CheckConstraint(
            "waiver_percent >= 0 AND waiver_percent <= 100",
            name="admin_settings_waiver_percent_range",
        ),
        {"comment": "System-wide admin configuration settings"},
    )
