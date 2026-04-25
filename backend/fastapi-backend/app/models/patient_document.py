"""
Patient Document models
Manage patient medical documents, photos, and files
"""

from sqlalchemy import Column, String, Text, BigInteger, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PatientDocument(BaseModel):
    """
    Patient Document model
    Stores patient medical documents and files
    """
    
    __tablename__ = "patient_documents"
    
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient user ID"
    )
    document_type = Column(String(100), nullable=False, comment="Type of document (Blood Test Report, X-Ray, etc.)")
    file_name = Column(String(255), nullable=False, comment="Original file name")
    file_path = Column(String(500), nullable=False, comment="Relative path to file")
    file_size = Column(BigInteger, nullable=False, comment="File size in bytes")
    file_extension = Column(String(10), nullable=False, comment="File extension (pdf, jpg, png, etc.)")
    mime_type = Column(String(100), nullable=False, comment="MIME type of the file")
    issued_by = Column(String(255), nullable=True, comment="Doctor/issuer name")
    issued_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Doctor user ID"
    )
    issued_date = Column(Date, nullable=True, comment="Date document was issued")
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who uploaded the document"
    )
    notes = Column(Text, nullable=True, comment="Additional notes about the document")
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], lazy="select")
    issuer = relationship("User", foreign_keys=[issued_by_id], lazy="select")
    uploader = relationship("User", foreign_keys=[uploaded_by], lazy="select")
    
    # Indexes
    __table_args__ = (
        Index('patient_documents_patient_id_index', 'patient_id'),
        Index('patient_documents_issued_by_id_index', 'issued_by_id'),
        Index('patient_documents_uploaded_by_index', 'uploaded_by'),
        Index('patient_documents_document_type_index', 'document_type'),
        Index('patient_documents_file_extension_index', 'file_extension'),
        Index('patient_documents_issued_date_index', 'issued_date'),
        Index('patient_documents_created_at_index', 'created_at'),
        Index('patient_documents_deleted_at_index', 'deleted_at'),
    )
    
    def __repr__(self):
        return f"<PatientDocument(id={self.id}, patient_id={self.patient_id}, type='{self.document_type}')>"
