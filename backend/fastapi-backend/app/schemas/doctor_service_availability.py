"""
Pydantic schemas for doctor service availability
Assigns services to specific availability blocks with custom durations
"""

from typing import Optional, List
from datetime import datetime, time
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from app.core.security import ConsultationMode


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class DoctorServiceAvailabilityCreate(BaseModel):
    """
    Schema for assigning a service to an availability block
    
    POST /doctor/availability-services
    """
    
    availability_id: UUID = Field(..., description="Availability block ID")
    service_id: UUID = Field(..., description="Service ID to assign")
    slot_duration_minutes: int = Field(
        ...,
        ge=5,
        le=360,
        description="Duration of appointment slot in minutes (5-360)"
    )
    consultation_mode: Optional[str] = Field(
        None,
        description=f"If omitted, uses the admin-configured service mode for this service. Otherwise: {ConsultationMode.IN_CLINIC.value} or {ConsultationMode.TELECONSULTATION.value}"
    )
    
    @field_validator('slot_duration_minutes')
    @classmethod
    def validate_slot_duration(cls, v: int) -> int:
        """Validate slot duration range"""
        if v < 5 or v > 360:
            raise ValueError("Slot duration must be between 5 and 360 minutes")
        return v
    
    @field_validator('consultation_mode')
    @classmethod
    def validate_consultation_mode(cls, v: Optional[str]) -> Optional[str]:
        """Validate consultation mode using enum (when provided)"""
        if v is None:
            return v
        try:
            mode = ConsultationMode(v)
            return mode.value
        except ValueError:
            valid_modes = [mode.value for mode in ConsultationMode]
            raise ValueError(f"consultation_mode must be one of {valid_modes}, got: {v}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "availability_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "service_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "slot_duration_minutes": 30,
                "consultation_mode": None
            }
        }


class DoctorServiceAvailabilityUpdate(BaseModel):
    """
    Schema for updating service assignment duration and service properties
    
    PATCH /doctor/availability-services/{id}
    """
    
    slot_duration_minutes: Optional[int] = Field(
        None,
        ge=5,
        le=360,
        description="Duration of appointment slot in minutes (5-360)"
    )
    consultation_mode: Optional[str] = Field(
        None,
        description=f"Consultation mode: {ConsultationMode.IN_CLINIC.value} or {ConsultationMode.TELECONSULTATION.value}"
    )
    # Service properties that can be updated
    payment_type: Optional[str] = Field(
        None,
        description="Payment type: PREPAID or POSTPAID"
    )
    advance_booking_days: Optional[int] = Field(
        None,
        ge=0,
        description="Number of days in advance bookings can be made"
    )
    minimum_notice_minutes: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum notice required in minutes"
    )
    is_bookable: Optional[bool] = Field(
        None,
        description="Whether service is available for booking"
    )
    appointment_type: Optional[str] = Field(
        None,
        description="Appointment type: REGULAR or FOLLOW_UP"
    )
    
    @field_validator('slot_duration_minutes')
    @classmethod
    def validate_slot_duration(cls, v: Optional[int]) -> Optional[int]:
        """Validate slot duration range"""
        if v is not None and (v < 5 or v > 360):
            raise ValueError("Slot duration must be between 5 and 360 minutes")
        return v
    
    @field_validator('consultation_mode')
    @classmethod
    def validate_consultation_mode(cls, v: Optional[str]) -> Optional[str]:
        """Validate consultation mode using enum"""
        if v is not None:
            try:
                mode = ConsultationMode(v)
                return mode.value
            except ValueError:
                valid_modes = [mode.value for mode in ConsultationMode]
                raise ValueError(f"consultation_mode must be one of {valid_modes}, got: {v}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "slot_duration_minutes": 45,
                "consultation_mode": ConsultationMode.TELECONSULTATION.value
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class DoctorServiceAvailabilityResponse(BaseModel):
    """
    Schema for service availability assignment response
    """
    
    id: UUID
    availability_id: UUID
    service_id: UUID
    slot_duration_minutes: int
    consultation_mode: str
    created_at: datetime
    # Include related details
    service_name: Optional[str] = None
    service_mode: Optional[str] = None
    availability_day: Optional[int] = None
    availability_start_time: Optional[str] = None
    availability_end_time: Optional[str] = None
    
    class Config:
        from_attributes = True


class DoctorServiceAvailabilityListResponse(BaseModel):
    """
    Laravel-compatible list response
    """
    
    success: bool = True
    message: str = "Service availability assignments retrieved successfully"
    data: List[DoctorServiceAvailabilityResponse]
    errors: Optional[dict] = None


class DoctorServiceAvailabilitySingleResponse(BaseModel):
    """
    Laravel-compatible single response
    """
    
    success: bool = True
    message: str = "Service availability assignment retrieved successfully"
    data: Optional[DoctorServiceAvailabilityResponse] = None
    errors: Optional[dict] = None
