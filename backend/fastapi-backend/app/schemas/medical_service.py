"""
Medical Service schemas
Request/response models for medical service endpoints
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# REQUEST SCHEMAS (Admin CRUD)
# ============================================================================


class MedicalServiceCreate(BaseModel):
    """Schema for creating a medical service (admin only)."""
    name: Optional[str] = Field(None, max_length=50, description="Service name")
    parent: str = Field(default="0", max_length=255, description="Parent ID for hierarchy (default '0' for root)")
    image: Optional[str] = Field(None, max_length=200, description="Image path/URL")
    status: bool = Field(default=True, description="Active (true) or inactive (false)")


class MedicalServiceUpdate(BaseModel):
    """Schema for updating a medical service (admin only)."""
    name: Optional[str] = Field(None, max_length=50, description="Service name")
    parent: Optional[str] = Field(None, max_length=255, description="Parent ID for hierarchy")
    image: Optional[str] = Field(None, max_length=200, description="Image path/URL")
    status: Optional[bool] = Field(None, description="Active (true) or inactive (false)")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class MedicalServiceResponse(BaseModel):
    """Medical Service response schema"""
    id: UUID
    parent: str
    name: Optional[str] = None
    image: Optional[str] = None
    status: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# LIST RESPONSE SCHEMAS (Laravel compatible)
# ============================================================================


class MedicalServicesListResponse(BaseModel):
    """Medical Services list response (Laravel compatible)"""
    success: bool = True
    message: str = "Medical services retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Medical services retrieved successfully",
                "data": {
                    "medical_services": [
                        {
                            "id": "9cdf3788-f630-47d5-8e11-a49d84409d21",
                            "parent": "0",
                            "name": "Lungs",
                            "image": "https://portal.orvo.app/storage/service_image/jinej5316w.png",
                            "status": True
                        },
                        {
                            "id": "9cdf3789-00dd-40fd-9932-3ed703e12a44",
                            "parent": "0",
                            "name": "Heart",
                            "image": "https://portal.orvo.app/storage/service_image/d3n1wobffg.png",
                            "status": True
                        }
                    ]
                },
                "errors": None
            }
        }

