"""
Doctor Service Availability Pricing model
Availability-specific pricing for appointments
"""

from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, CheckConstraint, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from app.models.base import Base
from app.core.security import ConsultationMode


class DoctorServiceAvailabilityPricing(Base):
    """
    Doctor Service Availability Pricing model
    
    Defines availability-specific pricing for appointments.
    Allows doctors to set different prices for the same service
    on different availability blocks.
    """
    
    __tablename__ = "doctor_service_availability_pricing"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.text('uuid_generate_v4()'),
        nullable=False,
        index=True,
        comment="Primary key (UUID)"
    )
    
    # Foreign key to doctor_service_availability
    doctor_service_availability_id = Column(
        UUID(as_uuid=True),
        ForeignKey("doctor_service_availability.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to doctor service availability assignment"
    )
    
    # Pricing fields
    price_amount = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Price amount (must be > 0)"
    )
    
    currency = Column(
        String(3),
        nullable=False,
        comment="Currency code (ISO 4217). Always required."
    )
    
    # Consultation mode for mode-aware pricing
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
    doctor_service_availability = relationship(
        "DoctorServiceAvailability",
        foreign_keys=[doctor_service_availability_id],
        lazy="select"
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            'doctor_service_availability_id',
            'consultation_mode',
            name='doctor_service_availability_pricing_avail_mode_unique'
        ),
        CheckConstraint(
            'price_amount > 0',
            name='doctor_service_availability_pricing_price_check'
        ),
        CheckConstraint(
            f"consultation_mode IN ('{ConsultationMode.IN_CLINIC.value}', '{ConsultationMode.TELECONSULTATION.value}')",
            name='doctor_service_availability_pricing_consultation_mode_check'
        ),
    )
    
    @validates('price_amount')
    def validate_price_amount(self, key: str, value: Decimal) -> Decimal:
        """
        Validate price amount
        
        Args:
            key: Column name
            value: Price amount
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If value is not positive
        """
        if value <= 0:
            raise ValueError("price_amount must be greater than 0")
        return value
    
    @validates('currency')
    def validate_currency(self, key: str, value: str) -> str:
        """
        Validate currency code
        
        Args:
            key: Column name
            value: Currency code
            
        Returns:
            Validated value (uppercase)
            
        Raises:
            ValueError: If value is not 3 characters
        """
        if value and len(value) != 3:
            raise ValueError("currency must be a 3-character ISO 4217 code")
        return value.upper() if value else value
    
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
        try:
            mode = ConsultationMode(value)
            return mode.value
        except ValueError:
            valid_modes = [mode.value for mode in ConsultationMode]
            raise ValueError(
                f"consultation_mode must be one of {valid_modes}, got: {value}"
            )
    
    def __repr__(self) -> str:
        return f"<DoctorServiceAvailabilityPricing(id={self.id}, avail_id={self.doctor_service_availability_id}, mode={self.consultation_mode}, price={self.price_amount} {self.currency})>"
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary
        
        Returns:
            Dictionary representation
        """
        return {
            "id": str(self.id),
            "doctor_service_availability_id": str(self.doctor_service_availability_id),
            "price_amount": float(self.price_amount) if self.price_amount else None,
            "currency": self.currency,
            "consultation_mode": self.consultation_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
