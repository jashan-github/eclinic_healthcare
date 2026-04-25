"""
Webinar Payment schemas
Request/response models for webinar payment flow
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class WebinarRegistrationRequest(BaseModel):
    """Request to register for a webinar (creates payment if paid)"""
    webinar_id: UUID = Field(..., description="Webinar ID to register for")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class WebinarPaymentResponse(BaseModel):
    """Webinar payment response schema"""
    id: UUID
    webinar_id: UUID
    user_id: UUID
    sentoo_payment_id: Optional[str] = None
    payment_url: Optional[str] = None
    amount: float
    currency: str
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None  # ISO format datetime string
    updated_at: Optional[str] = None  # ISO format datetime string
    
    class Config:
        from_attributes = True


class WebinarPaymentInitializeResponse(BaseModel):
    """Webinar payment initialization response schema"""
    payment_id: UUID
    sentoo_payment_id: str
    payment_url: str
    amount: float
    currency: str
    status: str
    webinar_id: UUID
    webinar_title: Optional[str] = None
    
    class Config:
        from_attributes = True


class WebinarRegistrationResponse(BaseModel):
    """Webinar registration response schema"""
    webinar_id: UUID
    user_id: UUID
    registered: bool = Field(..., description="Whether registration was successful")
    payment_required: bool = Field(..., description="Whether payment is required")
    payment: Optional[WebinarPaymentInitializeResponse] = Field(None, description="Payment details if payment required")
    message: str


# ============================================================================
# LARAVEL-COMPATIBLE RESPONSE WRAPPERS
# ============================================================================


class WebinarPaymentSingleResponse(BaseModel):
    """Laravel-compatible webinar payment response"""
    success: bool = True
    message: str = "Webinar payment retrieved successfully"
    data: WebinarPaymentResponse
    errors: Optional[dict] = None


class WebinarPaymentInitializeSingleResponse(BaseModel):
    """Laravel-compatible webinar payment initialization response"""
    success: bool = True
    message: str = "Webinar payment initialized successfully"
    data: WebinarPaymentInitializeResponse
    errors: Optional[dict] = None


class WebinarRegistrationSingleResponse(BaseModel):
    """Laravel-compatible webinar registration response"""
    success: bool = True
    message: str = "Webinar registration successful"
    data: WebinarRegistrationResponse
    errors: Optional[dict] = None


class WebinarPaymentListResponse(BaseModel):
    """Laravel-compatible webinar payment list response"""
    success: bool = True
    message: str = "Webinar payments retrieved successfully"
    data: dict  # Contains list of WebinarPaymentResponse objects
    errors: Optional[dict] = None
