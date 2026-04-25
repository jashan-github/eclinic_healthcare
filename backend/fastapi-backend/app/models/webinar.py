"""
Webinar models
Manage webinars and online events
"""

from sqlalchemy import Column, String, Text, Integer, Date, Time, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Webinar(BaseModel):
    """
    Webinar model
    Stores webinar/online event information
    """
    
    __tablename__ = "webinars"
    
    title = Column(String(255), nullable=False, comment="Webinar title")
    description = Column(Text, nullable=True, comment="Webinar description")
    webinar_date = Column(Date, nullable=False, comment="Date of the webinar")
    start_time = Column(Time, nullable=False, comment="Start time")
    end_time = Column(Time, nullable=False, comment="End time")
    pricing_type = Column(String(20), nullable=False, default='free', server_default='free', comment="Pricing type: free or paid")
    price = Column(Numeric(10, 2), nullable=False, default=0.00, server_default='0.00', comment="Price for paid webinars")
    participant_limit = Column(Integer, nullable=True, comment="Maximum number of participants")
    host_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Host user ID"
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
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
    
    # Relationships
    host = relationship("User", foreign_keys=[host_id], lazy="select")
    creator = relationship("User", foreign_keys=[created_by], lazy="select")
    
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
