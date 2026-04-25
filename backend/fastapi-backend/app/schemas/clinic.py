"""
Clinic schemas
Pydantic models for clinic data validation and serialization
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ClinicResponse(BaseModel):
    """Clinic response model"""
    id: UUID
    name: str
    code: str
    timezone: str
    country_id: Optional[UUID] = None
    country_name: Optional[str] = None
    status: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClinicsListResponse(BaseModel):
    """Response model for list of clinics"""
    success: bool
    message: str
    data: Dict[str, List[ClinicResponse]]
    errors: Optional[Dict[str, List[str]]] = None


class ClinicSingleResponse(BaseModel):
    """Response model for single clinic"""
    success: bool
    message: str
    data: Dict[str, ClinicResponse]
    errors: Optional[Dict[str, List[str]]] = None

