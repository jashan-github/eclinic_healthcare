"""
Pydantic schemas for notification settings
Laravel-compatible request/response schemas
"""

from typing import Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class SmtpConfigUpdate(BaseModel):
    """
    Schema for updating SMTP email configuration
    
    Dedicated endpoint: PUT /admin/notifications/email/smtp
    """
    
    enabled: Optional[bool] = Field(None, description="Enable/disable email notifications")
    host: str = Field(..., min_length=1, max_length=255, description="SMTP server host (e.g., smtp.gmail.com)")
    port: int = Field(..., ge=1, le=65535, description="SMTP server port (e.g., 587, 465, 2525)")
    username: str = Field(..., min_length=1, max_length=255, description="SMTP username/email")
    password: str = Field(..., min_length=1, description="SMTP password or app password")
    from_email: str = Field(..., min_length=1, max_length=255, description="Sender email address")
    from_name: Optional[str] = Field("eClinic", max_length=255, description="Sender display name")
    use_tls: Optional[bool] = Field(True, description="Use TLS encryption (default: true)")
    
    @validator('host')
    def validate_host(cls, v):
        """Validate SMTP host"""
        if not v or not v.strip():
            raise ValueError("SMTP host is required")
        return v.strip()
    
    @validator('username')
    def validate_username(cls, v):
        """Validate SMTP username"""
        if not v or not v.strip():
            raise ValueError("SMTP username is required")
        return v.strip()
    
    @validator('from_email')
    def validate_from_email(cls, v):
        """Validate from email format"""
        if not v or not v.strip():
            raise ValueError("From email is required")
        # Basic email validation
        if '@' not in v:
            raise ValueError("From email must be a valid email address")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "host": "smtp.gmail.com",
                "port": 587,
                "username": "your_email@gmail.com",
                "password": "your_app_password",
                "from_email": "noreply@eclinic.local",
                "from_name": "eClinic",
                "use_tls": True
            }
        }


class NotificationChannelUpdate(BaseModel):
    """
    Schema for updating notification channel settings
    
    Laravel compatible:
    PUT /admin/notifications/{channel}
    """
    
    enabled: Optional[bool] = Field(None, description="Enable/disable the channel")
    provider: Optional[str] = Field(None, description="Provider name (twilio, smtp, etc.)")
    config: Optional[Dict[str, Any]] = Field(None, description="Provider configuration (will be encrypted)")
    
    @validator('provider')
    def validate_provider(cls, v):
        """Validate provider name"""
        if v is not None:
            v = v.lower().strip()
            if not v:
                raise ValueError("Provider name cannot be empty")
        return v
    
    @validator('config')
    def validate_config(cls, v):
        """Validate configuration is a dictionary"""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Config must be a dictionary")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "provider": "twilio",
                "config": {
                    "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "auth_token": "your_auth_token_here",
                    "phone_number": "+1234567890"
                }
            }
        }


class NotificationChannelToggle(BaseModel):
    """
    Schema for toggling notification channel
    
    Laravel compatible:
    PATCH /admin/notifications/{channel}/toggle
    """
    
    enabled: bool = Field(..., description="Enable or disable the channel")
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled": False
            }
        }


class NotificationKeyRotation(BaseModel):
    """
    Schema for rotating provider keys
    
    Laravel compatible:
    POST /admin/notifications/{channel}/rotate-keys
    """
    
    config: Dict[str, Any] = Field(..., description="New provider configuration (will be encrypted)")
    
    @validator('config')
    def validate_config(cls, v):
        """Validate configuration is not empty"""
        if not v or not isinstance(v, dict):
            raise ValueError("Config must be a non-empty dictionary")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "config": {
                    "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "auth_token": "new_auth_token_here",
                    "phone_number": "+1234567890"
                }
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class NotificationChannelResponse(BaseModel):
    """
    Response schema for notification channel settings
    
    Laravel compatible response
    """
    
    id: UUID = Field(..., description="Setting ID")
    channel: str = Field(..., description="Channel name (sms, email, whatsapp)")
    enabled: bool = Field(..., description="Whether channel is enabled")
    provider: Optional[str] = Field(None, description="Provider name")
    has_config: bool = Field(..., description="Whether configuration exists (config never returned)")
    updated_by: Optional[UUID] = Field(None, description="User who last updated")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "channel": "sms",
                "enabled": True,
                "provider": "twilio",
                "has_config": True,
                "updated_by": "660e8400-e29b-41d4-a716-446655440000",
                "updated_at": "2025-12-23T10:00:00Z",
                "created_at": "2025-12-20T15:00:00Z"
            }
        }


class NotificationChannelListResponse(BaseModel):
    """
    Response schema for list of notification channels
    """
    
    success: bool = True
    message: str = "Notification channels retrieved successfully"
    data: list[NotificationChannelResponse]
    errors: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Notification channels retrieved successfully",
                "data": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "channel": "sms",
                        "enabled": True,
                        "provider": "twilio",
                        "has_config": True,
                        "updated_by": "660e8400-e29b-41d4-a716-446655440000",
                        "updated_at": "2025-12-23T10:00:00Z",
                        "created_at": "2025-12-20T15:00:00Z"
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "channel": "email",
                        "enabled": False,
                        "provider": "smtp",
                        "has_config": False,
                        "updated_by": None,
                        "updated_at": None,
                        "created_at": "2025-12-20T15:00:00Z"
                    }
                ],
                "errors": None
            }
        }


class NotificationChannelSingleResponse(BaseModel):
    """
    Response schema for single notification channel
    """
    
    success: bool = True
    message: str = "Notification channel updated successfully"
    data: NotificationChannelResponse
    errors: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Notification channel updated successfully",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "channel": "sms",
                    "enabled": True,
                    "provider": "twilio",
                    "has_config": True,
                    "updated_by": "660e8400-e29b-41d4-a716-446655440000",
                    "updated_at": "2025-12-23T10:00:00Z",
                    "created_at": "2025-12-20T15:00:00Z"
                },
                "errors": None
            }
        }


# ============================================================================
# INTERNAL SCHEMAS (for service layer)
# ============================================================================


class NotificationDispatchRequest(BaseModel):
    """
    Internal schema for dispatching notifications
    Not exposed via API
    """
    
    channel: Literal["sms", "email", "whatsapp"]
    recipient: str
    message: str
    subject: Optional[str] = None
    clinic_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationDispatchResponse(BaseModel):
    """
    Internal schema for notification dispatch result
    """
    
    success: bool
    channel: str
    message: Optional[str] = None
    error: Optional[str] = None
