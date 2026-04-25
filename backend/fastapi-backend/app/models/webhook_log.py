"""
Webhook log model
Stores all webhook requests for debugging and audit purposes
"""

from sqlalchemy import Column, String, Text, DateTime, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base


class WebhookLog(Base):
    """
    Webhook log model
    Stores all webhook requests from payment gateways (e.g., Sentoo)
    
    This table provides:
    - Complete audit trail of all webhook attempts
    - Raw payload storage for debugging
    - Processing status tracking
    - Error logging
    """
    
    __tablename__ = "webhook_logs"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.text('uuid_generate_v4()'),
        nullable=False,
        index=True,
        comment="Primary key (UUID)"
    )
    
    # Webhook source
    source = Column(
        String(50),
        nullable=False,
        index=True,
        default="sentoo",
        comment="Webhook source (e.g., 'sentoo', 'stripe', etc.)"
    )
    
    # Event details
    event_type = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Event type (e.g., 'payment.succeeded', 'payment.failed')"
    )
    
    webhook_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Webhook event ID from payment gateway"
    )
    
    # Raw webhook data
    raw_payload = Column(
        JSONB,
        nullable=True,
        comment="Raw webhook payload (JSONB format)"
    )
    
    headers = Column(
        JSONB,
        nullable=True,
        comment="HTTP headers received with webhook"
    )
    
    # Processing details
    processing_status = Column(
        String(50),
        nullable=False,
        index=True,
        default="pending",
        comment="Processing status: pending, success, error, ignored"
    )
    
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if processing failed"
    )
    
    # Related entities
    payment_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Related payment ID (FK to appointment_payments.id)"
    )
    
    appointment_request_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Related appointment request ID (FK to appointment_requests.id)"
    )
    
    # Request metadata
    ip_address = Column(
        String(45),
        nullable=True,
        index=True,
        comment="IP address of webhook sender (IPv6 support)"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="User agent string from webhook request"
    )
    
    # Response details
    response_status = Column(
        String(50),
        nullable=True,
        comment="HTTP response status sent back (e.g., '200', '400')"
    )
    
    response_body = Column(
        JSONB,
        nullable=True,
        comment="Response body sent back to webhook sender"
    )
    
    # Processing metrics
    processing_time_ms = Column(
        String(20),
        nullable=True,
        comment="Processing time in milliseconds"
    )
    
    # Timestamp (UTC)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When the webhook was received (UTC timestamp)"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('webhook_logs_source_created_at_idx', 'source', 'created_at'),
        Index('webhook_logs_event_type_idx', 'event_type'),
        Index('webhook_logs_webhook_id_idx', 'webhook_id'),
        Index('webhook_logs_payment_id_idx', 'payment_id'),
        Index('webhook_logs_processing_status_idx', 'processing_status'),
        Index('webhook_logs_created_at_idx', 'created_at'),
    )
    
    def __repr__(self):
        return f"<WebhookLog(id={self.id}, source='{self.source}', event_type='{self.event_type}', status='{self.processing_status}', created_at={self.created_at})>"
    
    def to_dict(self) -> dict:
        """
        Convert webhook log to dictionary
        """
        return {
            "id": str(self.id),
            "source": self.source,
            "event_type": self.event_type,
            "webhook_id": self.webhook_id,
            "raw_payload": self.raw_payload,
            "headers": self.headers,
            "processing_status": self.processing_status,
            "error_message": self.error_message,
            "payment_id": str(self.payment_id) if self.payment_id else None,
            "appointment_request_id": str(self.appointment_request_id) if self.appointment_request_id else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "response_status": self.response_status,
            "response_body": self.response_body,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
