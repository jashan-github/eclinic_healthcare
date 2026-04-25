"""
Webinar schemas
Pydantic models for request/response validation
"""

from typing import Optional
from uuid import UUID
from datetime import date, time
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class WebinarBase(BaseModel):
    """Base schema for webinar"""
    title: str = Field(..., min_length=1, max_length=255, description="Webinar title")
    description: Optional[str] = Field(None, description="Webinar description")
    webinar_date: date = Field(..., description="Date of the webinar")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    pricing_type: str = Field("free", description="Pricing type: free or paid")
    price: Decimal = Field(Decimal("0.00"), description="Price for paid webinars")
    participant_limit: Optional[int] = Field(None, description="Maximum number of participants")
    host_id: UUID = Field(..., description="Host user ID")
    status: str = Field("draft", description="Status: draft, scheduled, live, completed, cancelled")
    visibility: str = Field("public", description="Visibility: public or private")
    agenda: Optional[str] = Field(None, description="Webinar agenda")
    
    @validator('pricing_type')
    def validate_pricing_type(cls, v):
        if v not in ['free', 'paid']:
            raise ValueError('pricing_type must be either "free" or "paid"')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['draft', 'scheduled', 'live', 'completed', 'cancelled']:
            raise ValueError('status must be one of: draft, scheduled, live, completed, cancelled')
        return v
    
    @validator('visibility')
    def validate_visibility(cls, v):
        if v not in ['public', 'private']:
            raise ValueError('visibility must be either "public" or "private"')
        return v
    
    @validator('price')
    def validate_price(cls, v, values):
        if 'pricing_type' in values and values['pricing_type'] == 'paid' and v <= 0:
            raise ValueError('price must be greater than 0 for paid webinars')
        return v


class WebinarCreate(BaseModel):
    """Schema for creating a new webinar"""
    title: str
    description: Optional[str] = None
    webinar_date: date
    start_time: str  # Accept as string, will convert to time
    end_time: str  # Accept as string, will convert to time
    pricing_type: str = "free"
    price: Decimal = Decimal("0.00")
    participant_limit: Optional[int] = None
    host_id: UUID
    status: Optional[str] = None  # Optional - defaults to "scheduled" in endpoint if not provided
    visibility: str = "public"
    agenda: Optional[str] = None


class WebinarUpdate(BaseModel):
    """Schema for updating a webinar"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Webinar title")
    description: Optional[str] = Field(None, description="Webinar description")
    webinar_date: Optional[date] = Field(None, description="Date of the webinar")
    start_time: Optional[str] = Field(None, description="Start time")
    end_time: Optional[str] = Field(None, description="End time")
    pricing_type: Optional[str] = Field(None, description="Pricing type: free or paid")
    price: Optional[Decimal] = Field(None, description="Price for paid webinars")
    participant_limit: Optional[int] = Field(None, description="Maximum number of participants")
    host_id: Optional[UUID] = Field(None, description="Host user ID")
    status: Optional[str] = Field(None, description="Status: draft, scheduled, live, completed, cancelled")
    visibility: Optional[str] = Field(None, description="Visibility: public or private")
    agenda: Optional[str] = Field(None, description="Webinar agenda")


class WebinarResponse(BaseModel):
    """Schema for webinar response"""
    id: UUID
    title: str
    description: Optional[str]
    webinar_date: str
    start_time: str
    end_time: str
    pricing_type: str
    price: str
    participant_limit: Optional[int]
    host_id: Optional[UUID]
    host: Optional[dict]  # Host user details
    created_by: Optional[UUID]
    status: str
    visibility: str
    agora_channel_name: Optional[str]
    agora_token: Optional[str]
    registered_count: int
    attended_count: int
    agenda: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    
    class Config:
        from_attributes = True


class WebinarListResponse(BaseModel):
    """Schema for list of webinars"""
    status: bool = True
    message: str = "Webinars retrieved successfully"
    data: dict
    
    class Config:
        from_attributes = True


class WebinarSingleResponse(BaseModel):
    """Schema for single webinar response"""
    status: bool = True
    message: str
    data: dict
    
    class Config:
        from_attributes = True


class WebinarDeleteResponse(BaseModel):
    """Schema for webinar deletion response"""
    status: bool = True
    message: str = "Webinar deleted successfully"
    
    class Config:
        from_attributes = True
