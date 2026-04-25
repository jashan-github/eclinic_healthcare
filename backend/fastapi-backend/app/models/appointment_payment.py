"""
Appointment Payment model
Tracks Sentoo payment transactions and webhook events for appointment requests
"""

from typing import Optional
from decimal import Decimal
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, CheckConstraint, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from sqlalchemy import func
from app.models.base import Base


class AppointmentPayment(Base):
    """
    Appointment Payment model
    
    Tracks:
    - Payment intent creation
    - Stripe webhook events
    - Payment status
    - Idempotency keys
    """
    
    __tablename__ = "appointment_payments"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.text('uuid_generate_v4()'),
        nullable=False,
        index=True,
        comment="Primary key (UUID)"
    )
    
    # Foreign key to appointment_request
    appointment_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointment_requests.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
        comment="Appointment request ID (one payment per request)"
    )
    
    # Sentoo payment details
    sentoo_payment_id = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Sentoo Payment ID"
    )
    
    payment_url = Column(
        String(500),
        nullable=True,
        comment="Sentoo payment URL for customer"
    )
    
    # Payment amount (locked from request)
    amount = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Payment amount (locked from request price)"
    )
    
    # Commission at payment completion (only upcoming: rate changes do not affect past payments)
    commission_rate = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Commission rate (1-100) at time of payment completion; used for reporting only.",
    )
    commission_earned = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Commission amount earned at time of payment completion; used for reporting only.",
    )

    # Waiver tracking (admin waiver % applied at payment creation; 100% = free, no gateway)
    waiver_percent = Column(
        Integer,
        nullable=True,
        comment="Waiver percentage applied (0-100) at payment creation",
    )
    amount_before_waiver = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Original amount before waiver (request price_amount)",
    )

    currency = Column(
        String(3),
        nullable=False,
        comment="Currency code (ISO 4217). Locked from appointment request."
    )
    
    # Payment status
    status = Column(
        String(50),
        nullable=False,
        server_default='PENDING',
        index=True,
        comment="Payment status: PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED"
    )
    
    # Idempotency
    idempotency_key = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Idempotency key for webhook processing"
    )
    
    # Webhook tracking
    sentoo_webhook_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Sentoo webhook event ID (for idempotency)"
    )
    
    webhook_received_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Webhook event received timestamp"
    )
    
    # Error tracking
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if payment failed"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Payment creation timestamp (UTC)"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Payment update timestamp (UTC)"
    )
    
    # Relationships
    appointment_request = relationship(
        "AppointmentRequest",
        foreign_keys=[appointment_request_id],
        lazy="select"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='appointment_payments_status_check'
        ),
        CheckConstraint(
            'amount >= 0',
            name='appointment_payments_amount_check'
        ),
        CheckConstraint(
            'LENGTH(currency) = 3',
            name='appointment_payments_currency_check'
        ),
    )
    
    def __repr__(self) -> str:
        return f"<AppointmentPayment(id={self.id}, request_id={self.appointment_request_id}, status={self.status}, sentoo_id={self.sentoo_payment_id})>"
    
    def to_dict(self) -> dict:
        """
        Convert payment to dictionary
        
        Returns:
            Dictionary representation of payment
        """
        return {
            "id": str(self.id),
            "appointment_request_id": str(self.appointment_request_id),
            "sentoo_payment_id": self.sentoo_payment_id,
            "payment_url": self.payment_url,
            "amount": float(self.amount) if self.amount else None,
            "commission_rate": float(self.commission_rate) if self.commission_rate is not None else None,
            "commission_earned": float(self.commission_earned) if self.commission_earned is not None else None,
            "currency": self.currency,
            "status": self.status,
            "sentoo_webhook_id": self.sentoo_webhook_id,
            "webhook_received_at": self.webhook_received_at.isoformat() if self.webhook_received_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
