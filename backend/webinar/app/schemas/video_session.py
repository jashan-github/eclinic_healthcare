"""
Video Session Schemas
Pydantic models for video session API
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class VideoSessionCreateRequest(BaseModel):
    """Request to create video session"""
    patient_id: Optional[UUID] = Field(None, description="Patient user ID (null for webinars)")
    appointment_id: Optional[UUID] = Field(None, description="Associated appointment ID")
    webinar_id: Optional[UUID] = Field(None, description="Associated webinar ID")
    session_type: Optional[str] = Field("appointment", description="Session type: appointment, webinar, emergency")
    scheduled_start_time: Optional[datetime] = Field(None, description="Scheduled start time")
    scheduled_end_time: Optional[datetime] = Field(None, description="Scheduled end time")
    recording_enabled: Optional[bool] = Field(False, description="Whether recording is enabled")
    doctor_display_name: Optional[str] = Field(None, description="Doctor name for channel label (doctor/patient/datetime)")
    patient_display_name: Optional[str] = Field(None, description="Patient name for channel label (doctor/patient/datetime)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "appointment_id": "123e4567-e89b-12d3-a456-426614174000",
                "session_type": "appointment",
                "scheduled_start_time": "2025-01-15T10:00:00Z",
                "scheduled_end_time": "2025-01-15T10:30:00Z",
                "recording_enabled": False
            }
        }


class VideoSessionCreateResponse(BaseModel):
    """Response after creating video session"""
    session_id: UUID
    channel_name: str
    status: str
    session_type: str


class VideoSessionJoinRequest(BaseModel):
    """Request to join video session"""
    pass  # No additional fields needed, user_id from auth
    
    class Config:
        # Allow empty body
        json_schema_extra = {
            "example": {}
        }


class VideoSessionJoinResponse(BaseModel):
    """Response after join request"""
    status: str
    token: Optional[str] = None
    channel_name: str
    waiting_room: bool
    message: str
    doctor_joined: Optional[bool] = None
    watchdog_expires_at: Optional[str] = None


class VideoSessionStatusResponse(BaseModel):
    """Video session status response"""
    status: str
    waiting_room: bool
    doctor_joined: bool
    token: Optional[str] = None
    channel_name: str
    message: str


class VideoSessionRetryRequest(BaseModel):
    """Request to retry failed call"""
    previous_session_id: UUID = Field(..., description="Previous failed session ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "previous_session_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class VideoSessionRetryResponse(BaseModel):
    """Response after retry"""
    session_id: UUID
    channel_name: str
    retry_count: int
