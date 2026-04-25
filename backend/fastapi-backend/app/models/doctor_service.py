"""
Doctor-Service assignment model
Links doctors to services they can provide with slot duration
Supports per-day duration configuration
"""

from typing import Optional
from sqlalchemy import Column, Integer, SmallInteger, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from app.models.base import Base


# Day of week constants (0=Sunday, 6=Saturday)
DAY_NAMES = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
}


class DoctorService(Base):
    """
    Doctor-Service assignment model
    
    Links doctors to services they can provide at a clinic.
    Each assignment specifies the slot duration for appointments.
    
    Supports per-day duration configuration:
    - day_of_week = NULL: Default duration for all days
    - day_of_week = 0-6: Day-specific duration (0=Sunday, 6=Saturday)
    
    A doctor can have:
    - One default assignment (day_of_week=NULL) for a service
    - Up to 7 day-specific assignments (day_of_week=0-6) for the same service
    """
    
    __tablename__ = "doctor_services"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.text('uuid_generate_v4()'),
        nullable=False,
        index=True,
        comment="Primary key (UUID)"
    )
    
    # Foreign keys
    doctor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Doctor user ID"
    )
    
    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Service ID"
    )
    
    clinic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Clinic ID"
    )
    
    # Day-specific configuration
    day_of_week = Column(
        SmallInteger,
        nullable=True,
        comment="Day of week (0=Sunday, 6=Saturday). NULL = default for all days"
    )
    
    # Assignment configuration
    slot_duration_minutes = Column(
        Integer,
        nullable=False,
        comment="Duration of appointment slot in minutes (5-360)"
    )
    
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether this assignment is active"
    )
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Record creation timestamp (UTC)"
    )
    
    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id], lazy="select")
    service = relationship("Service", foreign_keys=[service_id], lazy="select")
    clinic = relationship("Clinic", foreign_keys=[clinic_id], lazy="select")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('doctor_id', 'service_id', 'day_of_week', name='doctor_services_doctor_service_day_unique'),
        CheckConstraint(
            'slot_duration_minutes >= 5 AND slot_duration_minutes <= 360',
            name='doctor_services_slot_duration_check'
        ),
        CheckConstraint(
            'day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6)',
            name='doctor_services_day_of_week_check'
        ),
    )
    
    @validates('day_of_week')
    def validate_day_of_week(self, key: str, value: Optional[int]) -> Optional[int]:
        """
        Validate day_of_week value
        
        Args:
            key: Column name
            value: Day of week value (0-6 or None)
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If value is not None and not in range 0-6
        """
        if value is not None:
            if not isinstance(value, int) or value < 0 or value > 6:
                raise ValueError("day_of_week must be None or an integer between 0 and 6")
        return value
    
    @property
    def day_name(self) -> Optional[str]:
        """
        Get the name of the day
        
        Returns:
            Day name (e.g., "Monday") or None if day_of_week is NULL
        """
        if self.day_of_week is None:
            return None
        return DAY_NAMES.get(self.day_of_week)
    
    @property
    def is_default(self) -> bool:
        """
        Check if this is the default duration (applies to all days)
        
        Returns:
            True if day_of_week is NULL (default for all days)
        """
        return self.day_of_week is None
    
    def __repr__(self) -> str:
        day_info = f"day={self.day_of_week}" if self.day_of_week is not None else "default"
        return f"<DoctorService(id={self.id}, doctor_id={self.doctor_id}, service_id={self.service_id}, {day_info}, duration={self.slot_duration_minutes}min)>"
    
    def to_dict(self) -> dict:
        """
        Convert doctor-service assignment to dictionary
        
        Returns:
            Dictionary representation of assignment
        """
        return {
            "id": str(self.id),
            "doctor_id": str(self.doctor_id),
            "service_id": str(self.service_id),
            "clinic_id": str(self.clinic_id),
            "day_of_week": self.day_of_week,
            "day_name": self.day_name,
            "is_default": self.is_default,
            "slot_duration_minutes": self.slot_duration_minutes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
