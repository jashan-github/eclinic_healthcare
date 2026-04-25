"""
Notification settings model
Manages notification channel configurations with encrypted settings
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class NotificationSetting(BaseModel):
    """
    Notification settings model
    Stores encrypted configuration for notification channels (SMS, Email, WhatsApp)
    
    Design principles:
    - Encrypted config: Only encrypted configuration stored
    - Admin-only: Access controlled at application level
    - Auditable: All changes tracked via audit logs
    """
    
    __tablename__ = "notification_settings"
    
    # Channel type
    channel = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Notification channel: 'sms', 'email', 'whatsapp'"
    )
    
    # Status
    enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether this notification channel is enabled"
    )
    
    # Provider information
    provider = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Provider name (e.g., 'twilio', 'sendgrid', 'twilio_whatsapp')"
    )
    
    # Encrypted configuration (JSONB)
    # Note: Configuration should be encrypted before storing
    config_encrypted = Column(
        JSONB,
        nullable=True,
        comment="Encrypted configuration data (JSONB format). Must be encrypted before storage."
    )
    
    # Change tracking
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who last updated this setting (FK to users.id)"
    )
    
    # Relationships
    updater = relationship("User", foreign_keys=[updated_by], backref="notification_settings_updated")
    
    # Indexes for performance
    __table_args__ = (
        Index('notification_settings_channel_index', 'channel'),
        Index('notification_settings_enabled_index', 'enabled'),
        Index('notification_settings_provider_index', 'provider'),
        Index('notification_settings_updated_by_index', 'updated_by'),
    )
    
    def __repr__(self):
        return f"<NotificationSetting(id={self.id}, channel='{self.channel}', enabled={self.enabled}, provider='{self.provider}')>"
    
    def to_dict(self, include_deleted: bool = False, include_encrypted: bool = False):
        """
        Convert notification setting to dictionary
        
        Args:
            include_deleted: Include deleted_at field
            include_encrypted: Include encrypted config (admin-only)
        
        Returns:
            Dictionary representation of notification setting
        """
        data = super().to_dict(include_deleted=include_deleted)
        
        data.update({
            "channel": self.channel,
            "enabled": self.enabled,
            "provider": self.provider,
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        })
        
        # Only include encrypted config if explicitly requested (admin-only)
        if include_encrypted:
            data["config_encrypted"] = self.config_encrypted
        
        return data

