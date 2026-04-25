"""
SOAP Notes Schemas
Request/response models for SOAP notes
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class SoapNoteCreate(BaseModel):
    """Request to create a SOAP note"""
    appointment_id: UUID = Field(..., description="Appointment ID")
    patient_id: UUID = Field(..., description="Patient user ID")
    subjective: Optional[str] = Field(None, description="Subjective: Patient's symptoms, feelings, concerns")
    objective: Optional[str] = Field(None, description="Objective: Observable findings, measurements, test results")
    assessment: Optional[str] = Field(None, description="Assessment: Diagnosis, evaluation, clinical impression")
    plan: Optional[str] = Field(None, description="Plan: Treatment plan, medications, follow-up actions")


class SoapNoteUpdate(BaseModel):
    """Request to update a SOAP note"""
    subjective: Optional[str] = Field(None, description="Subjective: Patient's symptoms, feelings, concerns")
    objective: Optional[str] = Field(None, description="Objective: Observable findings, measurements, test results")
    assessment: Optional[str] = Field(None, description="Assessment: Diagnosis, evaluation, clinical impression")
    plan: Optional[str] = Field(None, description="Plan: Treatment plan, medications, follow-up actions")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class SoapNoteResponse(BaseModel):
    """SOAP note response schema"""
    id: str = Field(..., description="SOAP note ID")
    appointment_id: str = Field(..., description="Appointment ID")
    subjective: Optional[str] = Field(None, description="Subjective notes")
    objective: Optional[str] = Field(None, description="Objective notes")
    assessment: Optional[str] = Field(None, description="Assessment notes")
    plan: Optional[str] = Field(None, description="Plan notes")
    appointment_date: str = Field(..., description="Appointment date (YYYY-MM-DD)")
    appointment_time: Optional[str] = Field(None, description="Appointment time (HH:MM AM/PM)")
    appointment_datetime: str = Field(..., description="Appointment datetime (ISO format)")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO format)")
    can_edit: bool = Field(..., description="Whether this SOAP note can be edited")
    
    class Config:
        from_attributes = True


# ============================================================================
# LARAVEL-COMPATIBLE RESPONSE WRAPPERS
# ============================================================================


class SoapNoteSingleResponse(BaseModel):
    """Laravel-compatible SOAP note response"""
    success: bool = True
    message: str = "SOAP note retrieved successfully"
    data: SoapNoteResponse
    errors: Optional[dict] = None


class SoapNoteListResponse(BaseModel):
    """Laravel-compatible SOAP note list response"""
    success: bool = True
    message: str = "SOAP notes retrieved successfully"
    data: dict  # Contains list of SOAP notes and pagination
    errors: Optional[dict] = None
