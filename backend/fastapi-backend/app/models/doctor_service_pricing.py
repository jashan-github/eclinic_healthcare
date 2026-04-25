"""
Doctor Service Pricing model
Pricing for doctor-service combinations
"""

from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, CheckConstraint, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from app.models.base import Base


class DoctorServicePricing(Base):
    """
    Doctor Service Pricing model
    
    Defines pricing for a doctor-service combination.
    Each doctor can set their own price for each service they offer.
    """
    
    __tablename__ = "doctor_service_pricing"
    
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
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Record creation timestamp (UTC)"
    )
    
    # Relationships
    doctor = relationship(
        "User",
        foreign_keys=[doctor_id],
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
            'doctor_id',
            'service_id',
            name='doctor_service_pricing_doctor_service_unique'
        ),
        CheckConstraint(
            'price_amount > 0',
            name='doctor_service_pricing_price_check'
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
    
    def __repr__(self) -> str:
        return f"<DoctorServicePricing(id={self.id}, doctor_id={self.doctor_id}, service_id={self.service_id}, price={self.price_amount} {self.currency})>"
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary
        
        Returns:
            Dictionary representation
        """
        return {
            "id": str(self.id),
            "doctor_id": str(self.doctor_id),
            "service_id": str(self.service_id),
            "price_amount": float(self.price_amount) if self.price_amount else None,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
