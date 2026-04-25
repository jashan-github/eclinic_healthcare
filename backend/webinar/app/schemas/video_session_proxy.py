"""
Proxy schemas for Video Sessions (webinar service)

These mirror the backend video session schemas to provide OpenAPI
request/response documentation in the webinar service.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class VideoSessionCreateRequest(BaseModel):
    """Request to create a video session"""
    patient_id: Optional[UUID] = Field(None, description="Patient user ID (null for webinars)")
    appointment_id: Optional[UUID] = Field(None, description="Associated appointment ID")
    webinar_id: Optional[UUID] = Field(None, description="Associated webinar ID")
    session_type: Optional[str] = Field("appointment", description="Session type: appointment, webinar, emergency")
    scheduled_start_time: Optional[datetime] = Field(None, description="Scheduled start time (ISO 8601)")
    scheduled_end_time: Optional[datetime] = Field(None, description="Scheduled end time (ISO 8601)")
    recording_enabled: Optional[bool] = Field(False, description="Whether recording is enabled")

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


class VideoSessionJoinRequest(BaseModel):
    """Request to join video session (no body fields required)"""

    class Config:
        json_schema_extra = {"example": {}}


class JoinSuccessRequest(BaseModel):
    """Confirm join success (no body required)"""

    class Config:
        json_schema_extra = {"example": {}}


class JoinFailureRequest(BaseModel):
    """Report join failure"""
    error: str = Field(..., description="Error message")
    error_code: str = Field("JOIN_FAILED", description="Error code")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Network timeout",
                "error_code": "JOIN_FAILED"
            }
        }


class VideoSessionRetryRequest(BaseModel):
    """Request to retry failed call"""
    previous_session_id: UUID = Field(..., description="Previous failed session ID")

    class Config:
        json_schema_extra = {
            "example": {
                "previous_session_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
