"""
Appointment Request model
Stores appointment requests in pending/accepted/rejected states before payment
"""

from typing import Optional
from datetime import date, time
from decimal import Decimal
from sqlalchemy import Column, String, Integer, Date, Time, DateTime, ForeignKey, Numeric, CheckConstraint, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.core.security import ConsultationMode


class AppointmentRequest(BaseModel):
    """
    Appointment Request model
    
    Supports flow:
    1. Patient creates request (status: PENDING)
    2. Doctor accepts/rejects (status: ACCEPTED/REJECTED)
    3. Patient pays (converts to confirmed appointment)
    
    HIPAA: reason/symptoms stored but never logged in audit metadata
    """
    
    __tablename__ = "appointment_requests"
    
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
    
    # Request details
    preferred_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Preferred appointment date"
    )
    
    preferred_time = Column(
        Time,
        nullable=False,
        comment="Preferred appointment time"
    )
    
    consultation_mode = Column(
        String(20),
        nullable=False,
        server_default=ConsultationMode.default(),
        index=True,
        comment="Consultation mode: IN_CLINIC or TELECONSULTATION"
    )
    
    duration_minutes = Column(
        Integer,
        nullable=False,
        comment="Slot duration in minutes"
    )
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        server_default='PENDING',
        index=True,
        comment="Request status: PENDING, ACCEPTED, REJECTED"
    )
    
    # Reason/symptoms (HIPAA: stored but never logged)
    reason = Column(
        Text,
        nullable=True,
        comment="Patient reason/symptoms (HIPAA-protected, never logged)"
    )
    
    # Rejection reason
    rejection_reason = Column(
        String(500),
        nullable=True,
        comment="Doctor rejection reason (if rejected)"
    )
    
    # Pricing (calculated at request time, locked after acceptance)
    price_amount = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Calculated price (locked after acceptance)"
    )
    
    currency = Column(
        String(3),
        nullable=False,
        comment="Currency code (ISO 4217). Set from resolved pricing."
    )
    
    pricing_source = Column(
        String(50),
        nullable=True,
        comment="Source of price: availability, doctor, or global"
    )

    waiver_percent = Column(
        Integer,
        nullable=True,
        comment="Waiver percentage applied (0-100) when payment was initialized; for tracking",
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
            "status IN ('PENDING', 'ACCEPTED', 'REJECTED')",
            name='appointment_requests_status_check'
        ),
        CheckConstraint(
            f"consultation_mode IN ('{ConsultationMode.IN_CLINIC.value}', '{ConsultationMode.TELECONSULTATION.value}')",
            name='appointment_requests_consultation_mode_check'
        ),
        CheckConstraint(
            'duration_minutes >= 5 AND duration_minutes <= 360',
            name='appointment_requests_duration_check'
        ),
        CheckConstraint(
            'price_amount IS NULL OR price_amount > 0',
            name='appointment_requests_price_check'
        ),
    )
    
    def __repr__(self) -> str:
        return f"<AppointmentRequest(id={self.id}, doctor_id={self.doctor_id}, patient_id={self.patient_id}, status={self.status})>"
    
    def to_dict(self, include_deleted: bool = False) -> dict:
        """
        Convert appointment request to dictionary
        
        Args:
            include_deleted: Include deleted_at field in output
            
        Returns:
            Dictionary representation of appointment request
        """
        data = super().to_dict(include_deleted=include_deleted)
        data.update({
            "doctor_id": str(self.doctor_id) if self.doctor_id else None,
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "service_id": str(self.service_id) if self.service_id else None,
            "clinic_id": str(self.clinic_id) if self.clinic_id else None,
            "doctor_service_availability_id": str(self.doctor_service_availability_id) if self.doctor_service_availability_id else None,
            "preferred_date": self.preferred_date.isoformat() if self.preferred_date else None,
            "preferred_time": str(self.preferred_time) if self.preferred_time else None,
            "consultation_mode": self.consultation_mode,
            "duration_minutes": self.duration_minutes,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "price_amount": float(self.price_amount) if self.price_amount else None,
            "currency": self.currency,
            "pricing_source": self.pricing_source,
            "waiver_percent": self.waiver_percent,
            # NOTE: reason/symptoms NOT included in to_dict (HIPAA protection)
        })
        return data
    
    @property
    def can_be_accepted(self) -> bool:
        """Check if request can be accepted"""
        return self.status == 'PENDING'
    
    @property
    def can_be_rejected(self) -> bool:
        """Check if request can be rejected"""
        return self.status == 'PENDING'
    
    @property
    def can_initiate_payment(self) -> bool:
        """Check if payment can be initiated"""
        return self.status == 'ACCEPTED' and self.price_amount is not None
