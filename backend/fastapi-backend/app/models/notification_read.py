"""
Notification Read model
Tracks which appointment notifications have been read by users
"""

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class NotificationRead(Base):
    """
    Notification Read model
    
    Tracks which appointment request notifications have been read by users.
    This allows users to mark notifications as read and filter unread notifications.
    
    Design:
    - One record per user per appointment request
    - Tracks when the notification was marked as read
    - Supports both doctor and patient notifications
    """
    
    __tablename__ = "notification_reads"
    
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
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who read the notification"
    )
    
    appointment_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointment_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Appointment request ID (the notification)"
    )
    
    # Timestamp
    read_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Timestamp when notification was marked as read (UTC)"
    )
    
    # Relationships
    user = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="select"
    )
    
    appointment_request = relationship(
        "AppointmentRequest",
        foreign_keys=[appointment_request_id],
        lazy="select"
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            'user_id', 'appointment_request_id',
            name='notification_reads_user_request_unique'
        ),
        Index('notification_reads_user_id_index', 'user_id'),
        Index('notification_reads_appointment_request_id_index', 'appointment_request_id'),
        Index('notification_reads_read_at_index', 'read_at'),
    )
    
    def __repr__(self) -> str:
        return f"<NotificationRead(id={self.id}, user_id={self.user_id}, appointment_request_id={self.appointment_request_id}, read_at={self.read_at})>"
    
    def to_dict(self) -> dict:
        """
        Convert notification read to dictionary
        
        Returns:
            Dictionary representation of notification read
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "appointment_request_id": str(self.appointment_request_id),
            "read_at": self.read_at.isoformat() if self.read_at else None
        }
