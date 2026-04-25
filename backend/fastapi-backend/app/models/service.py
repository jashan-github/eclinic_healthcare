"""
Service model for admin-managed service catalog
Multi-clinic support with UUID primary keys
"""

from typing import Optional
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.core.security import ConsultationMode


class Service(BaseModel):
    """
    Service model for service catalog
    
    Admin-managed services that can be booked by patients.
    Supports multi-clinic architecture.
    """
    
    __tablename__ = "services"
    
    # Multi-clinic support
    clinic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Clinic ID for multi-clinic support (UUID)"
    )
    
    # Service identification
    name = Column(
        String(255),
        nullable=False,
        comment="Service name"
    )
    
    nickname = Column(
        String(255),
        nullable=True,
        comment="Service nickname (optional)"
    )
    
    # Service configuration
    service_mode = Column(
        String(50),
        nullable=False,
        server_default=ConsultationMode.default(),
        index=True,
        comment=f"Service mode: {ConsultationMode.IN_CLINIC.value} or {ConsultationMode.TELECONSULTATION.value}"
    )
    
    appointment_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Appointment type: REGULAR or FOLLOW_UP"
    )
    
    # Booking configuration
    is_bookable = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether service is available for booking"
    )
    
    advance_booking_days = Column(
        Integer,
        nullable=False,
        default=30,
        comment="Number of days in advance bookings can be made"
    )
    
    minimum_notice_minutes = Column(
        Integer,
        nullable=False,
        default=60,
        comment="Minimum notice required in minutes"
    )
    
    # Payment configuration
    payment_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Payment type: PREPAID or POSTPAID"
    )
    
    price = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Service price (nullable)"
    )
    
    currency = Column(
        String(3),
        nullable=True,  # Nullable, but required when price is set (enforced by CHECK constraint)
        comment="Currency code (ISO 4217). Required when price is set."
    )
    
    # Audit trail
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Admin user ID who created the service"
    )
    
    # Relationships
    clinic = relationship("Clinic", foreign_keys=[clinic_id], lazy="select")
    creator = relationship("User", foreign_keys=[created_by], lazy="select")
    
    # Table-level constraints
    __table_args__ = (
        CheckConstraint(
            f"service_mode IN ('{ConsultationMode.IN_CLINIC.value}', '{ConsultationMode.TELECONSULTATION.value}')",
            name='services_service_mode_check'
        ),
        CheckConstraint(
            "appointment_type IN ('REGULAR', 'FOLLOW_UP')",
            name='services_appointment_type_check'
        ),
        CheckConstraint(
            "payment_type IN ('PREPAID', 'POSTPAID')",
            name='services_payment_type_check'
        ),
        CheckConstraint(
            'advance_booking_days >= 0',
            name='services_advance_booking_days_check'
        ),
        CheckConstraint(
            'minimum_notice_minutes >= 0',
            name='services_minimum_notice_minutes_check'
        ),
        CheckConstraint(
            'price IS NULL OR price >= 0',
            name='services_price_check'
        ),
        CheckConstraint(
            'LENGTH(currency) = 3',
            name='services_currency_length_check'
        ),
    )
    
    @property
    def base_price(self) -> Optional[float]:
        """
        Get base price (logical mapping from price column)
        
        Returns:
            Base price as float, or None if price is None
        """
        return float(self.price) if self.price is not None else None
    
    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name='{self.name}', clinic_id={self.clinic_id})>"
    
    def to_dict(self, include_deleted: bool = False) -> dict:
        """
        Convert service to dictionary
        
        Args:
            include_deleted: Include deleted_at field in output
            
        Returns:
            Dictionary representation of service
        """
        data = super().to_dict(include_deleted=include_deleted)
        price_value = float(self.price) if self.price is not None else None
        data.update({
            "clinic_id": str(self.clinic_id) if self.clinic_id else None,
            "name": self.name,
            "nickname": self.nickname,
            "service_mode": self.service_mode,
            "appointment_type": self.appointment_type,
            "is_bookable": self.is_bookable,
            "advance_booking_days": self.advance_booking_days,
            "minimum_notice_minutes": self.minimum_notice_minutes,
            "payment_type": self.payment_type,
            # Backward compatibility: keep price field
            "price": price_value,
            # Normalized pricing fields
            "base_price": price_value,  # Logical mapping from price
            "currency": self.currency,
            "created_by": str(self.created_by) if self.created_by else None,
        })
        return data
