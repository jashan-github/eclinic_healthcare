"""
Pydantic schemas for doctor service pricing
Doctors can set their own prices for services
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class DoctorServicePricingCreate(BaseModel):
    """
    Schema for setting doctor service price
    
    POST /doctor/service-pricing
    
    Currency is REQUIRED - no defaults, must be explicitly provided.
    """
    
    service_id: UUID = Field(..., description="Service ID")
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
                "service_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "price_amount": 500.00,
                "currency": "USD"
            }
        }


class DoctorServicePricingUpdate(BaseModel):
    """
    Schema for updating doctor service price
    
    PATCH /doctor/service-pricing/{id}
    
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


class DoctorServicePricingResponse(BaseModel):
    """
    Schema for doctor service pricing response
    """
    
    id: UUID
    doctor_id: UUID
    service_id: UUID
    price_amount: float
    currency: str
    created_at: datetime
    # Include related details
    service_name: Optional[str] = None
    service_mode: Optional[str] = None
    global_price: Optional[float] = None  # From services table
    
    class Config:
        from_attributes = True


class DoctorServicePricingListResponse(BaseModel):
    """
    Laravel-compatible list response
    """
    
    success: bool = True
    message: str = "Doctor service pricing retrieved successfully"
    data: List[DoctorServicePricingResponse]
    errors: Optional[dict] = None


class DoctorServicePricingSingleResponse(BaseModel):
    """
    Laravel-compatible single response
    """
    
    success: bool = True
    message: str = "Doctor service pricing retrieved successfully"
    data: Optional[DoctorServicePricingResponse] = None
    errors: Optional[dict] = None
