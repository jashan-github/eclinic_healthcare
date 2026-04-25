"""
Vital Name model
Stores vital sign names that can be managed by admin
"""

from sqlalchemy import Column, String, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class VitalName(BaseModel):
    """
    Vital Name model
    Stores configurable vital sign names that admins can manage
    """
    
    __tablename__ = "vital_names"
    
    name = Column(String(255), nullable=False, unique=True, index=True, comment="Vital sign name (e.g., 'Weight (lbs)', 'BP Systolic')")
    unit = Column(String(50), nullable=True, comment="Unit of measurement (e.g., 'lbs', 'mmHg', 'per min')")
    display_order = Column(String(10), nullable=True, default="0", comment="Display order for sorting")
    is_active = Column(Boolean, default=True, nullable=False, index=True, comment="Whether this vital name is active")
    data_type = Column(String(50), nullable=True, default="number", comment="Data type: number, text, select, etc.")
    options = Column(String(500), nullable=True, comment="JSON string for select options (if data_type is 'select')")
    max_entries_per_day = Column(String(10), nullable=True, default="1", comment="Maximum number of entries allowed per day (e.g., '1', '2', '4', '6'). Default is 1.")
    
    # Indexes
    __table_args__ = (
        Index('ix_vital_names_name', 'name'),
        Index('ix_vital_names_is_active', 'is_active'),
        Index('ix_vital_names_display_order', 'display_order'),
    )
    
    def __repr__(self):
        return f"<VitalName(id={self.id}, name='{self.name}', unit='{self.unit}')>"

