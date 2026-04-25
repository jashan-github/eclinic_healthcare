"""
Pydantic schemas for doctor service selection
Doctor can select from admin-created services
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class DoctorServiceCreate(BaseModel):
    """
    Schema for doctor selecting a service
    
    POST /doctor/services
    
    Doctor sends only service_id (and optionally day_of_week). Backend fetches the
    admin-configured service and creates the assignment using admin data (service
    mode, appointment type, etc. come from the linked service; slot duration
    uses a default when not stored on the service).
    
    Notes:
    - day_of_week = NULL: Default for all days
    - day_of_week = 0-6: Day-specific (0=Sunday, 6=Saturday)
    - Only ONE record allowed where day_of_week IS NULL per service
    - Multiple records allowed for same service if day_of_week differs
    """
    
    service_id: UUID = Field(..., description="Service ID to add (admin-created service)")
    day_of_week: Optional[int] = Field(
        None,
        ge=0,
        le=6,
        description="Day of week (0=Sunday, 6=Saturday). NULL = default for all days"
    )
    
    @field_validator('day_of_week')
    @classmethod
    def validate_day_of_week(cls, v: Optional[int]) -> Optional[int]:
        """Validate day of week range"""
        if v is not None and (v < 0 or v > 6):
            raise ValueError("Day of week must be between 0 (Sunday) and 6 (Saturday)")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "day_of_week": None
            }
        }


class DoctorServiceUpdate(BaseModel):
    """
    Schema for updating doctor service assignment
    
    PATCH /doctor/services/{id}
    
    Note: day_of_week cannot be changed after creation.
    To change day_of_week, remove and re-add the assignment.
    """
    
    slot_duration_minutes: Optional[int] = Field(
        None,
        ge=5,
        le=360,
        description="Duration of appointment slot in minutes (5-360)"
    )
    is_active: Optional[bool] = Field(None, description="Whether assignment is active")
    
    @field_validator('slot_duration_minutes')
    @classmethod
    def validate_slot_duration(cls, v: Optional[int]) -> Optional[int]:
        """Validate slot duration range"""
        if v is not None and (v < 5 or v > 360):
            raise ValueError("Slot duration must be between 5 and 360 minutes")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "slot_duration_minutes": 45,
                "is_active": True
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class AvailableServiceResponse(BaseModel):
    """
    Schema for available service (admin-created, bookable)
    """
    
    id: UUID
    name: str
    nickname: Optional[str] = None
    service_mode: str
    appointment_type: str
    advance_booking_days: int
    minimum_notice_minutes: int
    payment_type: str
    price: Optional[float] = None
    
    class Config:
        from_attributes = True


class AvailableServiceListResponse(BaseModel):
    """
    Laravel-compatible list response for available services
    """
    
    success: bool = True
    message: str = "Available services retrieved successfully"
    data: List[AvailableServiceResponse]
    errors: Optional[dict] = None


class DoctorServiceResponse(BaseModel):
    """
    Schema for doctor service assignment response
    """
    
    id: UUID
    doctor_id: UUID
    service_id: UUID
    clinic_id: UUID
    day_of_week: Optional[int] = None
    day_name: Optional[str] = None
    is_default: bool = True
    slot_duration_minutes: int
    is_active: bool
    created_at: datetime
    # Include service details
    service_name: Optional[str] = None
    service_mode: Optional[str] = None
    appointment_type: Optional[str] = None
    
    class Config:
        from_attributes = True


class DoctorServiceListResponse(BaseModel):
    """
    Laravel-compatible list response for doctor services
    """
    
    success: bool = True
    message: str = "Doctor services retrieved successfully"
    data: List[DoctorServiceResponse]
    errors: Optional[dict] = None


class DoctorServiceSingleResponse(BaseModel):
    """
    Laravel-compatible single response for doctor service
    """
    
    success: bool = True
    message: str = "Doctor service retrieved successfully"
    data: Optional[DoctorServiceResponse] = None
    errors: Optional[dict] = None
