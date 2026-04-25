"""
Video Session Audit Log Model
HIPAA-compliant immutable audit trail
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base


class VideoSessionAuditLog(Base):
    """
    Audit log for video sessions
    
    Immutable log of all video session events for HIPAA compliance
    """
    
    __tablename__ = "video_session_audit_logs"
    
    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4(), nullable=False)
    
    # Session reference
    session_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True,
                        comment="Video session ID")
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True,
                       comment="Event type (join_attempt, join_success, join_failure, etc.)")
    
    event_description = Column(Text, nullable=True,
                              comment="Human-readable event description")
    
    # User who triggered event
    user_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True,
                    comment="User who triggered the event")
    
    user_role = Column(String(50), nullable=True,
                      comment="User role (doctor, patient)")
    
    # State information
    previous_status = Column(String(50), nullable=True,
                            comment="Previous session status")
    
    new_status = Column(String(50), nullable=True,
                       comment="New session status")
    
    # Timing
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True,
                            server_default=func.now(),
                            comment="Event timestamp (UTC)")
    
    # Additional data (using audit_metadata as attribute name to avoid SQLAlchemy reserved word conflict)
    audit_metadata = Column(JSONB, nullable=True, name="metadata",
                            comment="Additional event metadata (error codes, durations, etc.)")
    
    # IP address and device info (for security)
    ip_address = Column(String(45), nullable=True,
                       comment="IP address of user (IPv6 support)")
    
    user_agent = Column(String(500), nullable=True,
                       comment="User agent string")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        {"comment": "HIPAA-compliant audit log for video sessions"}
    )
