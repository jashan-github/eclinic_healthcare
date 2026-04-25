"""
RX Template models
Manage prescription templates for doctors at clinic locations
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class RxTemplate(BaseModel):
    """
    RX Template model
    Stores prescription templates for doctors at specific clinic locations
    """
    
    __tablename__ = "rx_templates"
    
    doctor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to users table (doctor)"
    )
    clinic_location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinic_locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to clinic_locations table"
    )
    letterhead_image_path = Column(
        String(500),
        nullable=True,
        comment="Path to uploaded letterhead image. NULL means use default letterhead."
    )
    template_name = Column(
        String(255),
        nullable=True,
        comment="Optional name for the template"
    )
    is_default = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default='false',
        comment="Is this the default template for this doctor at this clinic location?"
    )
    
    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id], lazy="select")
    clinic_location = relationship("ClinicLocation", foreign_keys=[clinic_location_id], lazy="select")
    
    # Indexes and constraints
    # Note: Partial unique index is created in migration
    __table_args__ = (
        Index('rx_templates_doctor_id_index', 'doctor_id'),
        Index('rx_templates_clinic_location_id_index', 'clinic_location_id'),
        Index('rx_templates_is_default_index', 'is_default'),
        Index('rx_templates_created_at_index', 'created_at'),
        Index('rx_templates_deleted_at_index', 'deleted_at'),
    )
    
    def __repr__(self):
        return f"<RxTemplate(id={self.id}, doctor_id={self.doctor_id}, clinic_location_id={self.clinic_location_id}, is_default={self.is_default})>"
