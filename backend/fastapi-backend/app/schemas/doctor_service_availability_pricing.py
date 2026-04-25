"""
Pydantic schemas for doctor service availability pricing
Doctors can set availability-specific prices (highest priority)
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class DoctorServiceAvailabilityPricingCreate(BaseModel):
    """
    Schema for setting availability-specific price
    
    POST /doctor/availability-service-pricing
    
    Currency is REQUIRED - no defaults, must be explicitly provided.
    """
    
    doctor_service_availability_id: UUID = Field(..., description="Doctor service availability assignment ID")
    price_amount: Decimal = Field(
        ...,
        gt=0,
        description="Price amount (must be greater than 0, max 2 decimal places)"
    )
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Currency code (ISO 4217, 3 characters). Required."
    )
    
    @field_validator('price_amount')
    @classmethod
    def validate_price_amount(cls, v: Decimal) -> Decimal:
        """Validate price amount is positive and has max 2 decimal places"""
        if v <= 0:
            raise ValueError("Price amount must be greater than 0")
        # Check decimal places
        if v.as_tuple().exponent < -2:
            raise ValueError("Price amount can have at most 2 decimal places")
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format"""
        v = v.strip().upper()
        if len(v) != 3:
            raise ValueError("Currency must be a 3-character ISO 4217 code")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "doctor_service_availability_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "price_amount": 600.00,
                "currency": "USD"
            }
        }


class DoctorServiceAvailabilityPricingUpdate(BaseModel):
    """
    Schema for updating availability-specific price
    
    PATCH /doctor/availability-service-pricing/{id}
    
    Note: currency can be updated along with price_amount
    """
    
    price_amount: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Price amount (must be greater than 0, max 2 decimal places)"
    )
    currency: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="Currency code (ISO 4217, 3 characters)"
    )
    
    @field_validator('price_amount')
    @classmethod
    def validate_price_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate price amount is positive and has max 2 decimal places"""
        if v is not None:
            if v <= 0:
                raise ValueError("Price amount must be greater than 0")
            # Check decimal places
            if v.as_tuple().exponent < -2:
                raise ValueError("Price amount can have at most 2 decimal places")
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "price_amount": 750.00,
                "currency": "USD"
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class DoctorServiceAvailabilityPricingResponse(BaseModel):
    """
    Schema for availability-specific pricing response.
    When no price has been set yet, price_amount/currency/created_at may be null (placeholder).
    """
    
    id: Optional[UUID] = None  # Set to doctor_service_availability_id for placeholder
    doctor_service_availability_id: UUID
    price_amount: Optional[float] = None  # None when no price set yet
    currency: Optional[str] = None
    created_at: Optional[datetime] = None
    # Include related details
    service_id: Optional[UUID] = None
    service_name: Optional[str] = None
    availability_day: Optional[int] = None
    availability_start_time: Optional[str] = None
    availability_end_time: Optional[str] = None
    # Lower priority prices for comparison
    service_price: Optional[float] = None  # From doctor_service_pricing
    global_price: Optional[float] = None  # From services table
    
    class Config:
        from_attributes = True


class DoctorServiceAvailabilityPricingListResponse(BaseModel):
    """
    Laravel-compatible list response
    """
    
    success: bool = True
    message: str = "Availability pricing retrieved successfully"
    data: List[DoctorServiceAvailabilityPricingResponse]
    errors: Optional[dict] = None


class DoctorServiceAvailabilityPricingSingleResponse(BaseModel):
    """
    Laravel-compatible single response
    """
    
    success: bool = True
    message: str = "Availability pricing retrieved successfully"
    data: Optional[DoctorServiceAvailabilityPricingResponse] = None
    errors: Optional[dict] = None
