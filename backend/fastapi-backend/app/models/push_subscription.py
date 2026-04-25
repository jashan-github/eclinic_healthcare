"""
Push subscription model
Stores browser Web Push API subscriptions per user for sending push notifications
"""

from sqlalchemy import Column, String, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import BaseModel


class PushSubscription(BaseModel):
    """
    Browser push subscription (Web Push API).
    One user can have multiple subscriptions (e.g. different devices/browsers).
    """

    __tablename__ = "push_subscriptions"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this subscription",
    )
    endpoint = Column(
        String(2048),
        nullable=False,
        comment="Push service endpoint URL (unique per subscription)",
    )
    p256dh = Column(
        String(255),
        nullable=False,
        comment="Client public key (base64url)",
    )
    auth = Column(
        String(255),
        nullable=False,
        comment="Auth secret (base64url)",
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="Browser user agent when subscribed (optional)",
    )
    device_label = Column(
        String(255),
        nullable=True,
        comment="Optional label e.g. Chrome on Desktop",
    )

    __table_args__ = (
        UniqueConstraint("endpoint", name="push_subscriptions_endpoint_unique"),
        Index("push_subscriptions_user_id_index", "user_id"),
        Index("push_subscriptions_endpoint_index", "endpoint"),
    )

    def __repr__(self):
        return f"<PushSubscription(id={self.id}, user_id={self.user_id})>"

    def to_subscription_info(self):
        """Return dict in format expected by pywebpush (endpoint + keys)."""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth,
            },
        }
