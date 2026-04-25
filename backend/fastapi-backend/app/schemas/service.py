"""
Pydantic schemas for service catalog
Admin-only service management
"""

from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from app.core.security import ConsultationMode


# ============================================================================
# ENUMS / LITERALS
# ============================================================================

ServiceMode = Literal[ConsultationMode.IN_CLINIC.value, ConsultationMode.TELECONSULTATION.value]
AppointmentType = Literal["REGULAR", "FOLLOW_UP"]
PaymentType = Literal["PREPAID", "POSTPAID"]


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class ServiceCreate(BaseModel):
    """
    Schema for creating a new service
    
    POST /admin/services
    
    Currency Rules:
    - When price is provided and currency is omitted, currency defaults to XCG
    - currency is optional when price is NULL
    """
    
    clinic_id: UUID = Field(..., description="Clinic ID for the service")
    name: str = Field(..., min_length=1, max_length=255, description="Service name")
    nickname: Optional[str] = Field(None, max_length=255, description="Service nickname (optional)")
    service_mode: ServiceMode = Field(
        default=ConsultationMode.default(),
        description=f"Service mode: {ConsultationMode.IN_CLINIC.value} or {ConsultationMode.TELECONSULTATION.value}"
    )
    appointment_type: AppointmentType = Field(..., description="Appointment type: REGULAR or FOLLOW_UP")
    is_bookable: bool = Field(True, description="Whether service is available for booking")
    advance_booking_days: int = Field(30, ge=0, description="Number of days in advance bookings can be made")
    minimum_notice_minutes: int = Field(60, ge=0, description="Minimum notice required in minutes")
    payment_type: PaymentType = Field(..., description="Payment type: PREPAID or POSTPAID")
    price: Optional[Decimal] = Field(None, ge=0, description="Service price (nullable)")
    currency: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="Currency code (ISO 4217, 3 characters). Defaults to XCG when price is provided."
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate service name"""
        if not v or not v.strip():
            raise ValueError("Service name is required")
        return v.strip()
    
    @field_validator('nickname')
    @classmethod
    def validate_nickname(cls, v: Optional[str]) -> Optional[str]:
        """Validate service nickname"""
        if v:
            return v.strip()
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency code format"""
        if v is not None:
            v = v.strip().upper()
            if len(v) != 3:
                raise ValueError("Currency must be a 3-character ISO 4217 code")
        return v
    
    def model_post_init(self, __context) -> None:
        """Default currency to XCG when price is provided and currency is not"""
        if self.price is not None and self.currency is None:
            object.__setattr__(self, "currency", "XCG")
    
    class Config:
        json_schema_extra = {
            "example": {
                "clinic_id": "4a2c23c9-b31e-4ab5-9819-c4e69ac27879",
                "name": "General Consultation",
                "nickname": "GP Visit",
                "service_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_type": "REGULAR",
                "is_bookable": True,
                "advance_booking_days": 30,
                "minimum_notice_minutes": 60,
                "payment_type": "PREPAID",
                "price": 50.00,
                "currency": "XCG"
            }
        }


class ServiceUpdate(BaseModel):
    """
    Schema for updating a service
    
    PATCH /admin/services/{id}
    
    Currency Rules:
    - When updating price without currency, currency defaults to XCG
    - currency can be updated independently
    """
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Service name")
    nickname: Optional[str] = Field(None, max_length=255, description="Service nickname")
    service_mode: Optional[ServiceMode] = Field(
        None,
        description=f"Service mode: {ConsultationMode.IN_CLINIC.value} or {ConsultationMode.TELECONSULTATION.value}"
    )
    appointment_type: Optional[AppointmentType] = Field(None, description="Appointment type: REGULAR or FOLLOW_UP")
    is_bookable: Optional[bool] = Field(None, description="Whether service is available for booking")
    advance_booking_days: Optional[int] = Field(None, ge=0, description="Number of days in advance bookings can be made")
    minimum_notice_minutes: Optional[int] = Field(None, ge=0, description="Minimum notice required in minutes")
    payment_type: Optional[PaymentType] = Field(None, description="Payment type: PREPAID or POSTPAID")
    price: Optional[Decimal] = Field(None, ge=0, description="Service price (nullable)")
    currency: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="Currency code (ISO 4217, 3 characters)"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate service name"""
        if v is not None:
            if not v.strip():
                raise ValueError("Service name cannot be empty")
            return v.strip()
        return v
    
    @field_validator('nickname')
    @classmethod
    def validate_nickname(cls, v: Optional[str]) -> Optional[str]:
        """Validate service nickname"""
        if v is not None:
            return v.strip() if v else None
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency code format"""
        if v is not None:
            v = v.strip().upper()
            if len(v) != 3:
                raise ValueError("Currency must be a 3-character ISO 4217 code")
        return v
    
    def model_post_init(self, __context) -> None:
        """Default currency to XCG when price is provided and currency is not"""
        if self.price is not None and self.currency is None:
            object.__setattr__(self, "currency", "XCG")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "General Consultation Updated",
                "is_bookable": False,
                "price": 75.00,
                "currency": "XCG"
            }
        }


class ServiceFilter(BaseModel):
    """
    Schema for filtering services
    
    GET /admin/services
    """
    
    clinic_id: Optional[UUID] = Field(None, description="Filter by clinic ID")
    service_mode: Optional[ServiceMode] = Field(None, description="Filter by service mode")
    appointment_type: Optional[AppointmentType] = Field(None, description="Filter by appointment type")
    is_bookable: Optional[bool] = Field(None, description="Filter by bookable status")
    payment_type: Optional[PaymentType] = Field(None, description="Filter by payment type")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class ServiceResponse(BaseModel):
    """
    Schema for service response
    
    Pricing fields:
    - price: Backward compatibility (maps to base_price)
    - base_price: Normalized field (logical mapping from price column)
    - currency: Currency code (ISO 4217), can be None if price is not set
    """
    
    id: UUID
    clinic_id: UUID
    name: str
    nickname: Optional[str] = None
    service_mode: str
    appointment_type: str
    is_bookable: bool
    advance_booking_days: int
    minimum_notice_minutes: int
    payment_type: str
    # Backward compatibility: keep price field
    price: Optional[float] = None
    # Normalized pricing fields
    base_price: Optional[float] = Field(None, description="Base price (logical mapping from price)")
    currency: Optional[str] = Field(None, description="Currency code (ISO 4217). Present when price is set.")
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """
    Laravel-compatible list response
    """
    
    success: bool = True
    message: str = "Services retrieved successfully"
    data: List[ServiceResponse]
    errors: Optional[dict] = None


class ServiceSingleResponse(BaseModel):
    """
    Laravel-compatible single response
    """
    
    success: bool = True
    message: str = "Service retrieved successfully"
    data: Optional[ServiceResponse] = None
    errors: Optional[dict] = None


class ServiceDeleteResponse(BaseModel):
    """
    Laravel-compatible delete response
    """
    
    success: bool = True
    message: str = "Service deleted successfully"
    data: Optional[dict] = None
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Service deleted successfully",
                "data": None,
                "errors": None
            }
        }
