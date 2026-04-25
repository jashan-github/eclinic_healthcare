"""
Webinar models
Manage webinars and online events
"""

from sqlalchemy import Column, String, Text, Integer, Date, Time, Numeric, ForeignKey, Index, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.session import Base


class Webinar(Base):
    """
    Webinar model
    Stores webinar/online event information
    """
    
    __tablename__ = "webinars"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    title = Column(String(255), nullable=False, comment="Webinar title")
    description = Column(Text, nullable=True, comment="Webinar description")
    webinar_date = Column(Date, nullable=False, comment="Date of the webinar")
    start_time = Column(Time, nullable=False, comment="Start time")
    end_time = Column(Time, nullable=False, comment="End time")
    pricing_type = Column(String(20), nullable=False, default='free', server_default='free', comment="Pricing type: free or paid")
    price = Column(Numeric(10, 2), nullable=False, default=0.00, server_default='0.00', comment="Price for paid webinars")
    participant_limit = Column(Integer, nullable=True, comment="Maximum number of participants")
    # Use plain UUID fields to avoid cross-service FK constraints (users table lives in backend service)
    host_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Host user ID"
    )
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Creator user ID"
    )
    status = Column(String(20), nullable=False, default='draft', server_default='draft', comment="Status: draft, scheduled, live, completed, cancelled")
    visibility = Column(String(20), nullable=False, default='public', server_default='public', comment="Visibility: public or private")
    agora_channel_name = Column(String(255), nullable=True, comment="Agora channel name for live streaming")
    agora_token = Column(String(500), nullable=True, comment="Agora token for authentication")
    registered_count = Column(Integer, nullable=False, default=0, server_default='0', comment="Number of registered participants")
    attended_count = Column(Integer, nullable=False, default=0, server_default='0', comment="Number of attended participants")
    agenda = Column(Text, nullable=True, comment="Webinar agenda")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Note: Relationships to users table are not defined here since users table is in shared database
    # We'll query users directly when needed
    
    # Indexes
    __table_args__ = (
        Index('webinars_host_id_index', 'host_id'),
        Index('webinars_created_by_index', 'created_by'),
        Index('webinars_status_index', 'status'),
        Index('webinars_visibility_index', 'visibility'),
        Index('webinars_webinar_date_index', 'webinar_date'),
        Index('webinars_pricing_type_index', 'pricing_type'),
        Index('webinars_created_at_index', 'created_at'),
        Index('webinars_deleted_at_index', 'deleted_at'),
    )
    
    def __repr__(self):
        return f"<Webinar(id={self.id}, title='{self.title}', date={self.webinar_date})>"
