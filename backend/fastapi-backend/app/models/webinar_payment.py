"""
Webinar Payment model
Tracks Sentoo payment transactions and webhook events for webinar registrations
"""

from typing import Optional
from decimal import Decimal
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, CheckConstraint, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from sqlalchemy import func
from app.models.base import Base


class WebinarPayment(Base):
    """
    Webinar Payment model
    
    Tracks:
    - Payment intent creation for webinar registrations
    - Sentoo webhook events
    - Payment status
    - Idempotency keys
    """
    
    __tablename__ = "webinar_payments"
    
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
    webinar_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Webinar ID (from webinar service)"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="User ID who registered/paid for the webinar"
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
    
    # Payment amount (locked from webinar price; after waiver if applied)
    amount = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Payment amount (locked from webinar price; after waiver if applied)"
    )

    waiver_percent = Column(
        Integer,
        nullable=True,
        comment="Waiver percentage applied (0-100) at registration",
    )
    amount_before_waiver = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Original price before waiver",
    )

    currency = Column(
        String(3),
        nullable=False,
        default='INR',
        server_default='INR',
        comment="Currency code (ISO 4217)"
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
    user = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="select"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='webinar_payments_status_check'
        ),
        CheckConstraint(
            'amount >= 0',
            name='webinar_payments_amount_check'
        ),
        CheckConstraint(
            'LENGTH(currency) = 3',
            name='webinar_payments_currency_check'
        ),
        # Unique constraint: one payment per user per webinar
        # (user can only pay once per webinar)
    )
    
    def __repr__(self) -> str:
        return f"<WebinarPayment(id={self.id}, webinar_id={self.webinar_id}, user_id={self.user_id}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """
        Convert payment to dictionary
        
        Returns:
            Dictionary representation of payment
        """
        return {
            "id": str(self.id),
            "webinar_id": str(self.webinar_id),
            "user_id": str(self.user_id),
            "sentoo_payment_id": self.sentoo_payment_id,
            "payment_url": self.payment_url,
            "amount": float(self.amount) if self.amount else None,
            "currency": self.currency,
            "status": self.status,
            "sentoo_webhook_id": self.sentoo_webhook_id,
            "webhook_received_at": self.webhook_received_at.isoformat() if self.webhook_received_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
