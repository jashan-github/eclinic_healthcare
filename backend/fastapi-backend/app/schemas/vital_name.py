"""
Vital Name schemas
Request/response models for vital name endpoints
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class VitalNameCreate(BaseModel):
    """Vital Name creation schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Vital sign name (e.g., 'Weight (lbs)', 'BP Systolic')")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement (e.g., 'lbs', 'mmHg', 'per min')")
    display_order: Optional[str] = Field("0", max_length=10, description="Display order for sorting")
    is_active: Optional[bool] = Field(True, description="Whether this vital name is active")
    data_type: Optional[str] = Field("number", max_length=50, description="Data type: number, text, select, etc.")
    options: Optional[str] = Field(None, max_length=500, description="JSON string for select options (if data_type is 'select')")
    # Note: max_entries_per_day is handled in backend and defaults to "1"
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Weight (lbs)",
                "unit": "lbs",
                "display_order": "1",
                "is_active": True,
                "data_type": "number",
                "options": None
            }
        }


class VitalNameUpdate(BaseModel):
    """Vital Name update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Vital sign name")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    display_order: Optional[str] = Field(None, max_length=10, description="Display order for sorting")
    is_active: Optional[bool] = Field(None, description="Whether this vital name is active")
    data_type: Optional[str] = Field(None, max_length=50, description="Data type: number, text, select, etc.")
    options: Optional[str] = Field(None, max_length=500, description="JSON string for select options")
    # Note: max_entries_per_day is handled in backend and defaults to "1"


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class VitalNameResponse(BaseModel):
    """Vital Name response schema"""
    id: UUID
    name: str
    unit: Optional[str] = None
    display_order: Optional[str] = None
    is_active: bool
    data_type: Optional[str] = None
    options: Optional[str] = None
    max_entries_per_day: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# LIST RESPONSE SCHEMAS (Laravel compatible)
# ============================================================================


class VitalNameListResponse(BaseModel):
    """Vital Names list response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital names retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Vital names retrieved successfully",
                "data": {
                    "vital_names": [
                        {
                            "id": "9cdf3788-f630-47d5-8e11-a49d84409d21",
                            "name": "Weight (lbs)",
                            "unit": "lbs",
                            "display_order": "1",
                            "is_active": True,
                            "data_type": "number"
                        }
                    ]
                },
                "errors": None
            }
        }


class VitalNameSingleResponse(BaseModel):
    """Single Vital Name response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital name retrieved successfully"
    data: VitalNameResponse
    errors: Optional[dict] = None


class VitalNameCreateResponse(BaseModel):
    """Vital Name creation response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital name created successfully"
    data: VitalNameResponse
    errors: Optional[dict] = None


class VitalNameUpdateResponse(BaseModel):
    """Vital Name update response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital name updated successfully"
    data: VitalNameResponse
    errors: Optional[dict] = None


class VitalNameDeleteResponse(BaseModel):
    """Vital Name deletion response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital name deleted successfully"
    data: Optional[dict] = None
    errors: Optional[dict] = None

