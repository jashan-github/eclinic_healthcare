"""
Doctor Payments schemas
Request/response models for doctor payment transactions
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class DoctorPaymentTransactionResponse(BaseModel):
    """Payment transaction response schema for doctor payments"""
    id: UUID = Field(..., description="Payment ID")
    serial_number: int = Field(..., description="Serial number for display")
    patient_details: dict = Field(..., description="Patient information (id, name, phone)")
    contact_number: Optional[str] = Field(None, description="Patient contact number")
    service: dict = Field(..., description="Service information (id, name)")
    amount: float = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    paymode: str = Field(..., description="Payment mode/status")
    receipt_number: str = Field(..., description="Receipt number (payment ID or sentoo payment ID)")
    created_at: str = Field(..., description="Payment creation timestamp (ISO format)")
    
    class Config:
        from_attributes = True


class DoctorPaymentStatsResponse(BaseModel):
    """Payment statistics for doctor"""
    total_earned: float = Field(0.0, description="Total amount earned from completed payments")
    growth: float = Field(0.0, description="Growth percentage compared to previous period")
    currency: str = Field("USD", description="Currency code")
    
    class Config:
        from_attributes = True


class DoctorPaymentsListResponse(BaseModel):
    """Laravel-compatible doctor payments list response"""
    success: bool = True
    message: str = "Doctor payments retrieved successfully"
    data: dict = Field(..., description="Contains stats, transactions, and pagination")
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Doctor payments retrieved successfully",
                "data": {
                    "stats": {
                        "total_earned": 5000.00,
                        "growth": 15.5,
                        "currency": "USD"
                    },
                    "transactions": [
                        {
                            "id": "a42068a3-8109-4d07-b71e-3c1826ea41ab",
                            "serial_number": 1,
                            "patient_details": {
                                "id": "b88ea1a7-1747-43fe-b737-19678f6baa96",
                                "name": "John Doe",
                                "phone": "+1234567890"
                            },
                            "contact_number": "+1234567890",
                            "service": {
                                "id": "9cdf3788-f630-47d5-8e11-a49d84409d21",
                                "name": "General Consultation"
                            },
                            "amount": 100.00,
                            "currency": "USD",
                            "paymode": "COMPLETED",
                            "receipt_number": "05ff9a72-b698-4d4f-a83b-cbaa98c2c8b4",
                            "created_at": "2026-01-16T09:13:44.019420+00:00"
                        }
                    ],
                    "pagination": {
                        "current_page": 1,
                        "per_page": 20,
                        "total": 50,
                        "total_pages": 3
                    }
                },
                "errors": None
            }
        }
