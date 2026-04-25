"""
Appointment Request schemas
Request/response models for appointment request flow
"""

from typing import Optional, List
from uuid import UUID
from datetime import date, time
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class AppointmentRequestCreate(BaseModel):
    """Request to create an appointment request"""
    doctor_id: UUID = Field(..., description="Doctor user ID")
    service_id: UUID = Field(..., description="Service ID")
    consultation_mode: str = Field(..., description="Consultation mode: IN_CLINIC or TELECONSULTATION")
    preferred_date: date = Field(..., description="Preferred appointment date")
    preferred_time: time = Field(..., description="Preferred appointment time (HH:MM)")
    reason: Optional[str] = Field(None, max_length=1000, description="Reason/symptoms for appointment (optional)")
    doctor_service_availability_id: Optional[UUID] = Field(None, description="Doctor service availability assignment ID (if applicable)")


class AppointmentRequestReject(BaseModel):
    """Request to reject an appointment request"""
    rejection_reason: Optional[str] = Field(None, max_length=500, description="Reason for rejection")


# Allowed waiver percentages when admin has waiver_doctor_decides enabled
ACCEPT_WAIVER_CHOICES = (0, 25, 50, 75, 100)


class AppointmentRequestAccept(BaseModel):
    """Request body for accepting an appointment request (optional doctor-set waiver)."""
    waiver_percent: Optional[int] = Field(
        None,
        description="Waiver percentage (0, 25, 50, 75, or 100). Required when admin has waiver_doctor_decides enabled; ignored otherwise.",
    )

    @field_validator("waiver_percent")
    @classmethod
    def waiver_percent_must_be_choice(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v not in ACCEPT_WAIVER_CHOICES:
            raise ValueError("waiver_percent must be one of 0, 25, 50, 75, 100")
        return v


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class AppointmentRequestResponse(BaseModel):
    """Appointment request response schema"""
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    service_id: UUID
    clinic_id: UUID
    preferred_date: date
    preferred_time: time
    consultation_mode: str
    duration_minutes: int
    status: str
    price_amount: Optional[float] = None  # amount after waiver (what patient pays)
    amount_before_waiver: Optional[float] = None  # original price for tracking
    waiver_percent: Optional[int] = None  # admin waiver % applied (0-100)
    currency: Optional[str] = None
    pricing_source: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: Optional[str] = None  # ISO format datetime string
    updated_at: Optional[str] = None  # ISO format datetime string
    
    class Config:
        from_attributes = True


# ============================================================================
# LARAVEL-COMPATIBLE RESPONSE WRAPPERS
# ============================================================================


class AppointmentRequestSingleResponse(BaseModel):
    """Laravel-compatible appointment request response"""
    success: bool = True
    message: str = "Appointment request retrieved successfully"
    data: AppointmentRequestResponse
    errors: Optional[dict] = None


class AppointmentRequestListResponse(BaseModel):
    """Laravel-compatible appointment request list response"""
    success: bool = True
    message: str = "Appointment requests retrieved successfully"
    data: dict  # Contains list of AppointmentRequestResponse objects
    errors: Optional[dict] = None


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================


class PaymentInitializeResponse(BaseModel):
    """Payment initialization response schema"""
    payment_id: UUID
    sentoo_payment_id: str
    payment_url: str
    amount: float
    currency: str
    status: str
    
    class Config:
        from_attributes = True


class PaymentInitializeSingleResponse(BaseModel):
    """Laravel-compatible payment initialization response"""
    success: bool = True
    message: str = "Payment initialized successfully"
    data: PaymentInitializeResponse
    errors: Optional[dict] = None


# ============================================================================
# APPOINTMENT NOTIFICATION SCHEMAS
# ============================================================================


class AppointmentNotificationItem(BaseModel):
    """Single appointment notification item"""
    id: str
    type: str = Field(..., description="Notification type: NEW_REQUEST, REQUEST_ACCEPTED, REQUEST_REJECTED")
    title: str
    message: str
    status: str
    is_read: bool = Field(False, description="Whether the notification has been read")
    read_at: Optional[str] = Field(None, description="Timestamp when notification was marked as read (ISO format)")
    appointment_request: dict
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AppointmentNotificationListResponse(BaseModel):
    """Laravel-compatible appointment notification list response"""
    success: bool = True
    message: str = "Appointment notifications retrieved successfully"
    data: dict  # Contains list of AppointmentNotificationItem objects and pagination
    errors: Optional[dict] = None


class UnreadNotificationCountResponse(BaseModel):
    """Unread notification count response schema"""
    unread_count: int = Field(..., description="Number of unread notifications")
    read_count: int = Field(..., description="Number of read notifications")
    total_count: int = Field(..., description="Total number of notifications")


class UnreadNotificationCountSingleResponse(BaseModel):
    """Laravel-compatible unread notification count response"""
    success: bool = True
    message: str = "Unread notification count retrieved successfully"
    data: UnreadNotificationCountResponse
    errors: Optional[dict] = None


class AppointmentRequestStatisticsResponse(BaseModel):
    """Appointment request statistics response schema"""
    accepted: int = Field(..., description="Count of accepted requests")
    rejected: int = Field(..., description="Count of rejected requests")
    pending: int = Field(..., description="Count of pending requests")
    past: int = Field(..., description="Count of past requests")
    total: int = Field(..., description="Total count of all requests")


class AppointmentRequestStatisticsSingleResponse(BaseModel):
    """Laravel-compatible appointment request statistics response"""
    success: bool = True
    message: str = "Appointment request statistics retrieved successfully"
    data: AppointmentRequestStatisticsResponse
    errors: Optional[dict] = None


# ============================================================================
# PAYMENT DETAILS SCHEMAS
# ============================================================================


class PaymentDetailsResponse(BaseModel):
    """Payment details response schema"""
    payment_id: Optional[UUID] = None
    stripe_payment_intent_id: Optional[str] = None
    client_secret: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    request_id: UUID
    request_status: str
    price_amount: Optional[float] = None  # amount after waiver (what patient pays)
    amount_before_waiver: Optional[float] = None
    waiver_percent: Optional[int] = None
    needs_payment: bool = Field(..., description="Whether payment needs to be initialized")


class PaymentDetailsSingleResponse(BaseModel):
    """Laravel-compatible payment details response"""
    success: bool = True
    message: str = "Payment details retrieved successfully"
    data: PaymentDetailsResponse
    errors: Optional[dict] = None


# ============================================================================
# VISIT SCHEMAS
# ============================================================================


class VisitResponse(BaseModel):
    """Visit response schema"""
    appointment_id: UUID
    status: str
    doctor_id: UUID
    patient_id: UUID
    appointment_date: date
    start_time: time
    consultation_mode: str


class VisitSingleResponse(BaseModel):
    """Laravel-compatible visit response"""
    success: bool = True
    message: str
    data: VisitResponse
    errors: Optional[dict] = None
