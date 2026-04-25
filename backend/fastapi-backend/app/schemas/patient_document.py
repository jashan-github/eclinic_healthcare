"""
Patient Document schemas
Pydantic models for request/response validation
"""

from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field


class PatientDocumentUpload(BaseModel):
    """Schema for uploading a patient document"""
    document_type: str = Field(..., description="Type of document")
    issued_by: Optional[str] = Field(None, description="Doctor/issuer name")
    issued_date: Optional[date] = Field(None, description="Date document was issued")
    notes: Optional[str] = Field(None, description="Additional notes")


class PatientDocumentResponse(BaseModel):
    """Schema for patient document response"""
    id: UUID
    patient_id: UUID
    document_type: str
    file_name: str
    file_path: str
    file_size: int
    file_extension: str
    mime_type: str
    issued_by: Optional[str]
    issued_by_id: Optional[UUID]
    issued_date: Optional[str]
    uploaded_by: Optional[UUID]
    notes: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    
    # Computed fields
    file_size_mb: Optional[str] = None
    download_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class PatientDocumentListResponse(BaseModel):
    """Schema for list of patient documents"""
    status: bool = True
    message: str = "Documents retrieved successfully"
    data: dict
    
    class Config:
        from_attributes = True


class PatientDocumentSingleResponse(BaseModel):
    """Schema for single patient document response"""
    status: bool = True
    message: str
    data: dict
    
    class Config:
        from_attributes = True


class PatientDocumentDeleteResponse(BaseModel):
    """Schema for document deletion response"""
    status: bool = True
    message: str = "Document deleted successfully"
    
    class Config:
        from_attributes = True
