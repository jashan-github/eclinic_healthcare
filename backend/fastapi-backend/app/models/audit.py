"""
Audit log model
HIPAA-compliant audit trail - append-only, immutable records
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class AuditLog(Base):
    """
    Audit log model
    HIPAA-compliant audit trail for tracking all user actions
    
    Design principles:
    - Append-only: Records cannot be updated or deleted
    - Immutable: Once created, records are never modified
    - Indexed: Fast lookups by actor_user_id and created_at
    - HIPAA-safe: Captures all necessary audit information
    """
    
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.text('uuid_generate_v4()'),
        nullable=False,
        index=True,
        comment="Primary key (UUID)"
    )
    
    # Actor (who performed the action)
    actor_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # Nullable in case user is deleted
        index=True,
        comment="User who performed the action (FK to users.id)"
    )
    
    # Action details
    action = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Action performed (e.g., 'create', 'update', 'delete', 'view', 'login', 'logout')"
    )
    
    # Entity details (what was affected)
    entity_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of entity affected (e.g., 'user', 'appointment', 'prescription', 'patient')"
    )
    
    entity_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID of the affected entity (UUID)"
    )
    
    # Additional metadata (JSONB for flexible storage)
    # Note: Using 'audit_metadata' instead of 'metadata' because 'metadata' is reserved in SQLAlchemy
    audit_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional audit data (JSONB format for flexible storage)"
    )
    
    # Request context
    ip_address = Column(
        String(45),
        nullable=True,
        index=True,
        comment="IP address of the request (IPv6 support)"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="User agent string from the request"
    )
    
    # Timestamp (UTC)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When the action occurred (UTC timestamp)"
    )
    
    # Relationships
    actor = relationship("User", foreign_keys=[actor_user_id], backref="audit_logs")
    
    # Indexes for performance
    __table_args__ = (
        Index('audit_logs_actor_user_id_created_at_idx', 'actor_user_id', 'created_at'),
        Index('audit_logs_entity_type_entity_id_idx', 'entity_type', 'entity_id'),
        Index('audit_logs_action_idx', 'action'),
        Index('audit_logs_created_at_idx', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', entity_type='{self.entity_type}', created_at={self.created_at})>"
    
    def to_dict(self) -> dict:
        """
        Convert audit log to dictionary
        
        Returns:
            Dictionary representation of audit log
        """
        return {
            "id": str(self.id),
            "actor_user_id": str(self.actor_user_id) if self.actor_user_id else None,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "metadata": self.audit_metadata,  # Exposed as 'metadata' in API
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

