"""
Medical Service model
Stores medical services offered by the clinic
"""

from sqlalchemy import Column, String, Boolean, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class MedicalService(Base):
    """
    Medical Service model
    Stores medical services with hierarchical structure (parent-child relationships)
    """
    
    __tablename__ = "medical_services"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.text('uuid_generate_v4()'), nullable=False, index=True)
    parent = Column(String(255), nullable=False, server_default='0', comment='Parent service ID (for hierarchical structure, default "0" for root)')
    name = Column(String(50), nullable=True, comment='Service name')
    image = Column(String(200), nullable=True, comment='Service image path/URL')
    status = Column(Boolean(), nullable=False, server_default=func.text('false'), comment='Service status (0=inactive, 1=active)')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_medical_services_parent', 'parent'),
        Index('ix_medical_services_status', 'status'),
    )
    
    def __repr__(self):
        return f"<MedicalService(id={self.id}, name='{self.name}', parent='{self.parent}')>"

