"""
Doctor Availability models
SQLAlchemy ORM models for doctor availability and time-off management
"""

from sqlalchemy import Column, Integer, Time, Boolean, DateTime, String, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DoctorAvailability(BaseModel):
    """
    Doctor availability model
    Stores weekly availability slots for doctors at clinics
    """
    
    __tablename__ = "doctor_availability"
    
    # Foreign keys
    doctor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Doctor user ID"
    )
    clinic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Clinic ID"
    )
    
    # Availability fields
    day_of_week = Column(
        Integer,
        nullable=False,
        comment="Day of week: 0=Monday, 1=Tuesday, ..., 6=Sunday"
    )
    start_time = Column(
        Time,
        nullable=False,
        comment="Start time for availability slot"
    )
    end_time = Column(
        Time,
        nullable=False,
        comment="End time for availability slot"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether this availability slot is active"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='day_of_week_check'),
        CheckConstraint('end_time > start_time', name='time_check'),
    )
    
    # Relationships
    # doctor = relationship("User", back_populates="availabilities")
    # clinic = relationship("Clinic", back_populates="doctor_availabilities")
    
    def __repr__(self):
        return f"<DoctorAvailability(id={self.id}, doctor_id={self.doctor_id}, day={self.day_of_week}, time={self.start_time}-{self.end_time})>"
    
    def to_dict(self, include_deleted: bool = False) -> dict:
        """
        Convert availability to dictionary
        
        Args:
            include_deleted: Include deleted_at field in output
            
        Returns:
            Dictionary representation of availability
        """
        data = super().to_dict(include_deleted=include_deleted)
        data.update({
            "doctor_id": str(self.doctor_id),
            "clinic_id": str(self.clinic_id),
            "day_of_week": self.day_of_week,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_active": self.is_active,
        })
        return data


class DoctorTimeOff(BaseModel):
    """
    Doctor time-off model
    Stores time-off periods for doctors (overrides availability)
    """
    
    __tablename__ = "doctor_time_off"
    
    # Foreign keys
    doctor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Doctor user ID"
    )
    clinic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Clinic ID"
    )
    
    # Time-off fields
    start_datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Start datetime for time-off period"
    )
    end_datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="End datetime for time-off period"
    )
    reason = Column(
        String(500),
        nullable=True,
        comment="Reason for time-off"
    )
    
    # Note: No updated_at for time-off (immutable once created)
    # We don't define updated_at here, so it won't be included
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('end_datetime > start_datetime', name='datetime_check'),
    )
    
    # Relationships
    # doctor = relationship("User", back_populates="time_offs")
    # clinic = relationship("Clinic", back_populates="doctor_time_offs")
    
    def __repr__(self):
        return f"<DoctorTimeOff(id={self.id}, doctor_id={self.doctor_id}, period={self.start_datetime}-{self.end_datetime})>"
    
    def to_dict(self, include_deleted: bool = False) -> dict:
        """
        Convert time-off to dictionary
        
        Args:
            include_deleted: Include deleted_at field in output
            
        Returns:
            Dictionary representation of time-off
        """
        # Don't call super().to_dict() since we don't have updated_at
        data = {
            "id": str(self.id),
            "doctor_id": str(self.doctor_id),
            "clinic_id": str(self.clinic_id),
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_deleted:
            data["deleted_at"] = self.deleted_at.isoformat() if self.deleted_at else None
        
        return data
