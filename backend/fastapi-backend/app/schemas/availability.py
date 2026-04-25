"""
Doctor Availability Schemas
Pydantic schemas for doctor availability and time-off operations
"""

from typing import Optional, List, Union
from datetime import time, datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, field_serializer


# ============================================================================
# AVAILABILITY SCHEMAS
# ============================================================================


class AvailabilityBase(BaseModel):
    """Base schema for availability"""
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week: 0=Monday, 1=Tuesday, ..., 6=Sunday")
    start_time: time = Field(..., description="Start time (HH:MM:SS)")
    end_time: time = Field(..., description="End time (HH:MM:SS)")
    is_active: bool = Field(default=True, description="Whether this availability slot is active")
    
    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def parse_time(cls, v: Union[str, time]) -> time:
        """
        Parse time string, handling timezone-aware formats
        Strips timezone information to ensure timezone-naive time objects
        """
        if isinstance(v, time):
            # If already a time object, ensure it's timezone-naive
            if v.tzinfo is not None:
                # Convert to naive time by replacing tzinfo with None
                return v.replace(tzinfo=None)
            return v
        
        if isinstance(v, str):
            # Handle ISO format with timezone (e.g., "02:00:00.027Z" or "02:00:00+00:00")
            # Strip timezone part and parse as naive time
            # Remove 'Z' suffix (UTC timezone indicator)
            if v.endswith('Z'):
                v = v[:-1]
            
            # Remove timezone offset (+HH:MM or -HH:MM)
            if '+' in v:
                v = v.split('+')[0]
            elif '-' in v and v.count('-') > 1:
                # Handle negative timezone offset (e.g., "02:00:00-05:00")
                # Find the last '-' that's followed by a colon (timezone separator)
                parts = v.rsplit('-', 1)
                if len(parts) == 2 and ':' in parts[1] and len(parts[1].split(':')) == 2:
                    v = parts[0]
            
            # Remove milliseconds if present (e.g., "02:00:00.027")
            if '.' in v:
                v = v.split('.')[0]
            
            # Parse as time (HH:MM:SS or HH:MM)
            try:
                if len(v.split(':')) == 3:
                    hours, minutes, seconds = map(int, v.split(':'))
                    return time(hours, minutes, seconds)
                elif len(v.split(':')) == 2:
                    hours, minutes = map(int, v.split(':'))
                    return time(hours, minutes, 0)
                else:
                    raise ValueError(f"Invalid time format: {v}")
            except (ValueError, AttributeError) as e:
                raise ValueError(f"Invalid time format: {v}. Expected HH:MM:SS or HH:MM")
        
        return v
    
    @model_validator(mode='after')
    def validate_times(self):
        """Validate that end_time is after start_time"""
        if self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        return self


class AvailabilityCreate(AvailabilityBase):
    """Schema for creating availability"""
    clinic_id: UUID = Field(..., description="Clinic ID")


class AvailabilityUpdate(BaseModel):
    """Schema for updating availability"""
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week: 0=Monday, 1=Tuesday, ..., 6=Sunday")
    start_time: Optional[time] = Field(None, description="Start time (HH:MM:SS)")
    end_time: Optional[time] = Field(None, description="End time (HH:MM:SS)")
    is_active: Optional[bool] = Field(None, description="Whether this availability slot is active")
    
    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def parse_time(cls, v: Union[str, time, None]) -> Optional[time]:
        """
        Parse time string, handling timezone-aware formats
        Strips timezone information to ensure timezone-naive time objects
        """
        if v is None:
            return None
        
        if isinstance(v, time):
            # If already a time object, ensure it's timezone-naive
            if v.tzinfo is not None:
                # Convert to naive time by replacing tzinfo with None
                return v.replace(tzinfo=None)
            return v
        
        if isinstance(v, str):
            # Handle ISO format with timezone (e.g., "02:00:00.027Z" or "02:00:00+00:00")
            # Strip timezone part and parse as naive time
            # Remove 'Z' suffix (UTC timezone indicator)
            if v.endswith('Z'):
                v = v[:-1]
            
            # Remove timezone offset (+HH:MM or -HH:MM)
            if '+' in v:
                v = v.split('+')[0]
            elif '-' in v and v.count('-') > 1:
                # Handle negative timezone offset (e.g., "02:00:00-05:00")
                # Find the last '-' that's followed by a colon (timezone separator)
                parts = v.rsplit('-', 1)
                if len(parts) == 2 and ':' in parts[1] and len(parts[1].split(':')) == 2:
                    v = parts[0]
            
            # Remove milliseconds if present (e.g., "02:00:00.027")
            if '.' in v:
                v = v.split('.')[0]
            
            # Parse as time (HH:MM:SS or HH:MM)
            try:
                if len(v.split(':')) == 3:
                    hours, minutes, seconds = map(int, v.split(':'))
                    return time(hours, minutes, seconds)
                elif len(v.split(':')) == 2:
                    hours, minutes = map(int, v.split(':'))
                    return time(hours, minutes, 0)
                else:
                    raise ValueError(f"Invalid time format: {v}")
            except (ValueError, AttributeError) as e:
                raise ValueError(f"Invalid time format: {v}. Expected HH:MM:SS or HH:MM")
        
        return v
    
    @model_validator(mode='after')
    def validate_times(self):
        """Validate that end_time is after start_time if both are provided"""
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        return self


class AvailabilityResponse(BaseModel):
    """Schema for availability response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    doctor_id: UUID
    clinic_id: UUID
    day_of_week: int
    start_time: str  # ISO format time string
    end_time: str  # ISO format time string
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# TIME-OFF SCHEMAS
# ============================================================================


class TimeOffCreate(BaseModel):
    """Schema for creating time-off"""
    clinic_id: UUID = Field(..., description="Clinic ID")
    start_datetime: datetime = Field(..., description="Start datetime for time-off")
    end_datetime: datetime = Field(..., description="End datetime for time-off")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for time-off")
    
    @model_validator(mode='after')
    def validate_datetimes(self):
        """Validate that end_datetime is after start_datetime"""
        if self.end_datetime <= self.start_datetime:
            raise ValueError('end_datetime must be after start_datetime')
        return self


class TimeOffResponse(BaseModel):
    """Schema for time-off response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    doctor_id: UUID
    clinic_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str]
    created_at: datetime
    
    @field_serializer('start_datetime', 'end_datetime', 'created_at')
    def serialize_datetime(self, dt: datetime, _info) -> str:
        """
        Serialize datetime to string format: YYYY-MM-DD HH:MM:SS
        Removes milliseconds and timezone information
        """
        if dt is None:
            return None
        
        # If timezone-aware, convert to UTC then remove timezone
        if dt.tzinfo is not None:
            from datetime import timezone
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        
        # Format as YYYY-MM-DD HH:MM:SS (no milliseconds, no timezone)
        # strftime automatically truncates microseconds
        return dt.strftime('%Y-%m-%d %H:%M:%S')


# ============================================================================
# LARAVEL-COMPATIBLE RESPONSE SCHEMAS
# ============================================================================


class AvailabilityListResponse(BaseModel):
    """Laravel-compatible list response"""
    success: bool
    message: str
    data: List[AvailabilityResponse]
    errors: Optional[dict] = None


class AvailabilitySingleResponse(BaseModel):
    """Laravel-compatible single response"""
    success: bool
    message: str
    data: AvailabilityResponse
    errors: Optional[dict] = None


class TimeOffListResponse(BaseModel):
    """Laravel-compatible list response for time-off"""
    success: bool
    message: str
    data: List[TimeOffResponse]
    errors: Optional[dict] = None
    booking_window_days: Optional[int] = None  # Admin setting: maximum days in advance for booking


class TimeOffSingleResponse(BaseModel):
    """Laravel-compatible single response for time-off"""
    success: bool
    message: str
    data: TimeOffResponse
    errors: Optional[dict] = None


# ============================================================================
# PATIENT-FACING TIME-OFF SCHEMAS (without private details)
# ============================================================================


class PatientTimeOffResponse(BaseModel):
    """
    Schema for time-off response for patients
    Does NOT include reason (private for doctors only)
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    doctor_id: UUID
    clinic_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    # Note: reason is NOT included - private for doctors
    
    @field_serializer('start_datetime', 'end_datetime')
    def serialize_datetime(self, dt: datetime, _info) -> str:
        """
        Serialize datetime to string format: YYYY-MM-DD HH:MM:SS
        Removes milliseconds and timezone information
        """
        if dt is None:
            return None
        
        # If timezone-aware, convert to UTC then remove timezone
        if dt.tzinfo is not None:
            from datetime import timezone
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        
        # Format as YYYY-MM-DD HH:MM:SS (no milliseconds, no timezone)
        return dt.strftime('%Y-%m-%d %H:%M:%S')


class PatientTimeOffListResponse(BaseModel):
    """Laravel-compatible list response for patient-facing time-off"""
    success: bool
    message: str
    data: List[PatientTimeOffResponse]
    errors: Optional[dict] = None
    booking_window_days: Optional[int] = None  # Admin setting: maximum days in advance for booking