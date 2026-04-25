"""
FCM token model
Stores Firebase Cloud Messaging registration tokens per user for push notifications
"""

from sqlalchemy import Column, String, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class FCMToken(BaseModel):
    """
    Firebase Cloud Messaging registration token.
    One user can have multiple tokens (e.g. web, Android, iOS).
    """

    __tablename__ = "fcm_tokens"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this token",
    )
    token = Column(
        String(512),
        nullable=False,
        comment="FCM registration token",
    )
    platform = Column(
        String(32),
        nullable=True,
        comment="Platform: web, android, ios",
    )
    device_label = Column(
        String(255),
        nullable=True,
        comment="Optional label e.g. Chrome on Desktop",
    )

    __table_args__ = (
        UniqueConstraint("token", name="fcm_tokens_token_unique"),
        Index("fcm_tokens_user_id_index", "user_id"),
        Index("fcm_tokens_token_index", "token"),
    )

    def __repr__(self):
        return f"<FCMToken(id={self.id}, user_id={self.user_id})>"
