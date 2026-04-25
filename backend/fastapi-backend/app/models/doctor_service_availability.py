"""
Doctor Service Availability model
Links doctor availability slots to specific services with custom slot durations
"""

from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from app.models.base import Base
from app.core.security import ConsultationMode


class DoctorServiceAvailability(Base):
    """
    Doctor Service Availability model
    
    Links doctor availability slots to specific services with custom slot durations.
    This allows a doctor to offer different services with different durations
    on specific availability windows.
    
    Example:
    - Availability: Monday 9:00-12:00
    - Service A: 30 min slots
    - Service B: 60 min slots
    """
    
    __tablename__ = "doctor_service_availability"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.text('uuid_generate_v4()'),
        nullable=False,
        index=True,
        comment="Primary key (UUID)"
    )
    
    # Foreign key to doctor_availability
    availability_id = Column(
        UUID(as_uuid=True),
        ForeignKey("doctor_availability.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to doctor availability slot"
    )
    
    # Foreign key to services
    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to service"
    )
    
    # Slot duration for this availability-service combination
    slot_duration_minutes = Column(
        Integer,
        nullable=False,
        comment="Duration of appointment slot in minutes (5-360)"
    )
    
    # Consultation mode for this availability-service combination
    consultation_mode = Column(
        String(20),
        nullable=False,
        server_default=ConsultationMode.default(),
        index=True,
        comment=f"Consultation mode: {ConsultationMode.IN_CLINIC.value} or {ConsultationMode.TELECONSULTATION.value}"
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
    availability = relationship(
        "DoctorAvailability",
        foreign_keys=[availability_id],
        lazy="select"
    )
    service = relationship(
        "Service",
        foreign_keys=[service_id],
        lazy="select"
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            'availability_id',
            'service_id',
            'consultation_mode',
            name='doctor_service_availability_avail_service_mode_unique'
        ),
        CheckConstraint(
            'slot_duration_minutes >= 5 AND slot_duration_minutes <= 360',
            name='doctor_service_availability_duration_check'
        ),
        CheckConstraint(
            f"consultation_mode IN ('{ConsultationMode.IN_CLINIC.value}', '{ConsultationMode.TELECONSULTATION.value}')",
            name='doctor_service_availability_consultation_mode_check'
        ),
    )
    
    @validates('slot_duration_minutes')
    def validate_slot_duration(self, key: str, value: int) -> int:
        """
        Validate slot duration value
        
        Args:
            key: Column name
            value: Slot duration in minutes
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If value is not between 5 and 360
        """
        if value < 5 or value > 360:
            raise ValueError("slot_duration_minutes must be between 5 and 360")
        return value
    
    @validates('consultation_mode')
    def validate_consultation_mode(self, key: str, value: str) -> str:
        """
        Validate consultation mode value using enum
        
        Args:
            key: Column name
            value: Consultation mode string
            
        Returns:
            Validated consultation mode value
            
        Raises:
            ValueError: If value is not a valid ConsultationMode
        """
        # Convert string to enum for validation
        try:
            mode = ConsultationMode(value)
            return mode.value
        except ValueError:
            valid_modes = [mode.value for mode in ConsultationMode]
            raise ValueError(
                f"consultation_mode must be one of {valid_modes}, got: {value}"
            )
    
    def __repr__(self) -> str:
        return f"<DoctorServiceAvailability(id={self.id}, availability_id={self.availability_id}, service_id={self.service_id}, duration={self.slot_duration_minutes}min, mode={self.consultation_mode})>"
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary
        
        Returns:
            Dictionary representation
        """
        return {
            "id": str(self.id),
            "availability_id": str(self.availability_id),
            "service_id": str(self.service_id),
            "slot_duration_minutes": self.slot_duration_minutes,
            "consultation_mode": self.consultation_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
