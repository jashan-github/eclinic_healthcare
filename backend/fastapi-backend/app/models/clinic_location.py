"""
Clinic Location models
Manage clinic branches and locations
"""

from sqlalchemy import Column, String, Text, Boolean, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ClinicLocation(BaseModel):
    """
    Clinic Location model
    Stores branch/location information for clinics
    """
    
    __tablename__ = "clinic_locations"
    
    clinic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to clinics table"
    )
    name = Column(String(255), nullable=False, comment="Branch/location name")
    branch_type = Column(String(100), nullable=True, comment="Type of branch (Main Branch, Sub Branch, etc.)")
    address = Column(Text, nullable=True, comment="Full address")
    building_name = Column(String(255), nullable=True, comment="Building name or number")
    street_name = Column(String(255), nullable=True, comment="Street name")
    pincode = Column(String(20), nullable=True, comment="Postal/ZIP code")
    phone = Column(String(50), nullable=True, comment="Contact phone number")
    email = Column(String(255), nullable=True, comment="Contact email")
    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to countries table"
    )
    state_id = Column(
        UUID(as_uuid=True),
        ForeignKey("states.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to states table"
    )
    city_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to cities table"
    )
    latitude = Column(Numeric(10, 8), nullable=True, comment="Geographic latitude")
    longitude = Column(Numeric(11, 8), nullable=True, comment="Geographic longitude")
    is_primary = Column(Boolean, nullable=False, default=False, server_default='false', comment="Is this the primary location?")
    
    # Relationships
    clinic = relationship("Clinic", foreign_keys=[clinic_id], lazy="select")
    country = relationship("Country", foreign_keys=[country_id], lazy="select")
    state = relationship("State", foreign_keys=[state_id], lazy="select")
    city = relationship("City", foreign_keys=[city_id], lazy="select")
    
    # Indexes
    __table_args__ = (
        Index('clinic_locations_clinic_id_index', 'clinic_id'),
        Index('clinic_locations_country_id_index', 'country_id'),
        Index('clinic_locations_state_id_index', 'state_id'),
        Index('clinic_locations_city_id_index', 'city_id'),
        Index('clinic_locations_is_primary_index', 'is_primary'),
        Index('clinic_locations_created_at_index', 'created_at'),
        Index('clinic_locations_deleted_at_index', 'deleted_at'),
    )
    
    def __repr__(self):
        return f"<ClinicLocation(id={self.id}, name='{self.name}', clinic_id={self.clinic_id})>"
