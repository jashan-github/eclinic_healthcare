"""
Appointment model
Appointments with immutable pricing snapshot at booking time
"""

from typing import Optional, Literal
from datetime import date, time, datetime
from decimal import Decimal
from sqlalchemy import Column, String, Integer, Date, Time, DateTime, ForeignKey, Numeric, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.core.security import ConsultationMode

# Pricing source types
PricingSource = Literal['availability', 'doctor', 'global']


class Appointment(BaseModel):
    """
    Appointment model
    
    Stores appointments with immutable snapshots at booking time.
    
    Snapshot fields (immutable after booking):
    - consultation_mode: Visit type (IN_CLINIC or TELECONSULTATION) - used for visit type & billing
    - duration_minutes: Slot duration in minutes
    - price_amount: Price at booking time
    - currency: Currency at booking time
    - pricing_source: Source of price (availability | doctor | global)
    
    These fields never change, even if:
    - Availability pricing changes
    - Doctor service pricing changes
    - Global service price changes
    - Appointment is rescheduled
    - Consultation mode settings change
    """
    
    __tablename__ = "appointments"
    
    # Foreign keys
    doctor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Doctor user ID"
    )
    
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Patient user ID"
    )
    
    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Service ID"
    )
    
    clinic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Clinic ID"
    )
    
    doctor_service_availability_id = Column(
        UUID(as_uuid=True),
        ForeignKey("doctor_service_availability.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Doctor service availability assignment ID (if applicable)"
    )
    
    # Appointment details
    appointment_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Appointment date"
    )
    
    start_time = Column(
        Time,
        nullable=False,
        comment="Appointment start time"
    )
    
    end_time = Column(
        Time,
        nullable=False,
        comment="Appointment end time"
    )
    
    status = Column(
        String(50),
        nullable=False,
        server_default='SCHEDULED',
        index=True,
        comment="Appointment status: SCHEDULED, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW"
    )
    
    # Pricing snapshot (immutable after booking)
    price_amount = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Price at booking time (snapshot, never changes)"
    )
    
    currency = Column(
        String(3),
        nullable=False,
        comment="Currency at booking time (snapshot, immutable)"
    )
    
    pricing_source = Column(
        String(50),
        nullable=False,
        comment="Source of price: availability, doctor, or global"
    )
    
    # Snapshot fields (immutable after booking)
    consultation_mode = Column(
        String(20),
        nullable=False,
        server_default=ConsultationMode.default(),
        index=True,
        comment="Consultation mode at booking time (snapshot, immutable). Used for visit type & billing."
    )
    
    duration_minutes = Column(
        Integer,
        nullable=False,
        comment="Slot duration in minutes at booking time (snapshot, immutable)"
    )
    
    # Relationships
    doctor = relationship(
        "User",
        foreign_keys=[doctor_id],
        lazy="select"
    )
    patient = relationship(
        "User",
        foreign_keys=[patient_id],
        lazy="select"
    )
    service = relationship(
        "Service",
        foreign_keys=[service_id],
        lazy="select"
    )
    clinic = relationship(
        "Clinic",
        foreign_keys=[clinic_id],
        lazy="select"
    )
    doctor_service_availability = relationship(
        "DoctorServiceAvailability",
        foreign_keys=[doctor_service_availability_id],
        lazy="select"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW')",
            name='appointments_status_check'
        ),
        CheckConstraint(
            'price_amount > 0',
            name='appointments_price_check'
        ),
        CheckConstraint(
            "pricing_source IN ('availability', 'doctor', 'global', 'service')",
            name='appointments_pricing_source_check'
        ),
        CheckConstraint(
            'end_time > start_time',
            name='appointments_time_check'
        ),
        CheckConstraint(
            f"consultation_mode IN ('{ConsultationMode.IN_CLINIC.value}', '{ConsultationMode.TELECONSULTATION.value}')",
            name='appointments_consultation_mode_check'
        ),
        CheckConstraint(
            'duration_minutes >= 5 AND duration_minutes <= 360',
            name='appointments_duration_check'
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, doctor_id={self.doctor_id}, patient_id={self.patient_id}, date={self.appointment_date}, status={self.status})>"
    
    def to_dict(self, include_deleted: bool = False) -> dict:
        """
        Convert appointment to dictionary
        
        Args:
            include_deleted: Include deleted_at field in output
            
        Returns:
            Dictionary representation of appointment
        """
        data = super().to_dict(include_deleted=include_deleted)
        data.update({
            "doctor_id": str(self.doctor_id) if self.doctor_id else None,
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "service_id": str(self.service_id) if self.service_id else None,
            "clinic_id": str(self.clinic_id) if self.clinic_id else None,
            "doctor_service_availability_id": str(self.doctor_service_availability_id) if self.doctor_service_availability_id else None,
            "appointment_date": self.appointment_date.isoformat() if self.appointment_date else None,
            "start_time": str(self.start_time) if self.start_time else None,
            "end_time": str(self.end_time) if self.end_time else None,
            "status": self.status,
            "price_amount": float(self.price_amount) if self.price_amount else None,
            "currency": self.currency,
            "pricing_source": self.pricing_source,
            "consultation_mode": self.consultation_mode,
            "duration_minutes": self.duration_minutes,
        })
        return data
    
    @property
    def is_pricing_immutable(self) -> bool:
        """
        Check if pricing is immutable (always true after creation)
        
        Returns:
            True (pricing never changes after booking)
        """
        return True
