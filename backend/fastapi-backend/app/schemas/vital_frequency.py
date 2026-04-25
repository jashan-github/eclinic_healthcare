"""
Vital Frequency schemas
Request/response models for vital frequency endpoints
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class VitalFrequencyCreate(BaseModel):
    """Vital Frequency creation schema"""
    patient_id: Optional[UUID] = Field(None, description="Patient user ID (NULL = applies to all patients or clinic/global default)")
    vital_name_id: Optional[UUID] = Field(None, description="Vital name ID (NULL = applies to all vital names)")
    clinic_id: Optional[UUID] = Field(None, description="Clinic ID (NULL = global default)")
    frequency_type: Optional[str] = Field("daily", description="Frequency type: 'daily', 'weekly', 'custom'")
    max_entries_per_day: int = Field(..., ge=1, description="Maximum number of entries allowed per day (e.g., 1, 2, 4, 6)")
    times_per_day: Optional[int] = Field(None, ge=1, description="Number of times per day (e.g., 2 = twice a day)")
    preferred_times: Optional[List[str]] = Field(None, description="Preferred times of day for recording (e.g., ['09:00', '17:00'])")
    is_active: bool = Field(True, description="Whether this frequency rule is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": None,
                "vital_name_id": None,
                "clinic_id": "4a2c23c9-b31e-4ab5-9819-c4e69ac27879",
                "frequency_type": "daily",
                "max_entries_per_day": 2,
                "times_per_day": 2,
                "preferred_times": ["09:00", "17:00"],
                "is_active": True
            }
        }


class VitalFrequencyUpdate(BaseModel):
    """Vital Frequency update schema"""
    frequency_type: Optional[str] = Field(None, description="Frequency type: 'daily', 'weekly', 'custom'")
    max_entries_per_day: Optional[int] = Field(None, ge=1, description="Maximum number of entries allowed per day")
    times_per_day: Optional[int] = Field(None, ge=1, description="Number of times per day")
    preferred_times: Optional[List[str]] = Field(None, description="Preferred times of day for recording")
    is_active: Optional[bool] = Field(None, description="Whether this frequency rule is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "frequency_type": "daily",
                "max_entries_per_day": 4,
                "times_per_day": 4,
                "preferred_times": ["08:00", "12:00", "16:00", "20:00"],
                "is_active": True
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class VitalFrequencyResponse(BaseModel):
    """Vital Frequency response schema"""
    id: UUID
    patient_id: Optional[UUID] = None
    vital_name_id: Optional[UUID] = None
    clinic_id: Optional[UUID] = None
    frequency_type: Optional[str] = None
    max_entries_per_day: int
    times_per_day: Optional[int] = None
    preferred_times: Optional[List[str]] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Include related entity names for convenience
    patient_name: Optional[str] = None
    vital_name: Optional[str] = None
    clinic_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# LIST RESPONSE SCHEMAS (Laravel compatible)
# ============================================================================


class VitalFrequencyListResponse(BaseModel):
    """Vital Frequency list response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital frequency rules retrieved successfully"
    data: dict
    errors: Optional[dict] = None


class VitalFrequencySingleResponse(BaseModel):
    """Single Vital Frequency response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital frequency rule retrieved successfully"
    data: VitalFrequencyResponse
    errors: Optional[dict] = None


class VitalFrequencyCreateResponse(BaseModel):
    """Vital Frequency creation response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital frequency rule created successfully"
    data: VitalFrequencyResponse
    errors: Optional[dict] = None


class VitalFrequencyUpdateResponse(BaseModel):
    """Vital Frequency update response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital frequency rule updated successfully"
    data: VitalFrequencyResponse
    errors: Optional[dict] = None


class VitalFrequencyDeleteResponse(BaseModel):
    """Vital Frequency deletion response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital frequency rule deleted successfully"
    data: Optional[dict] = None
    errors: Optional[dict] = None

