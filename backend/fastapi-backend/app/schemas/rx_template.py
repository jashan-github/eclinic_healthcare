"""
RX Template schemas
Request and response models for RX template API
"""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class RxTemplateBase(BaseModel):
    """Base schema for RX template"""
    clinic_location_id: UUID = Field(..., description="Clinic location ID")
    template_name: Optional[str] = Field(None, description="Optional template name")
    use_default_letterhead: bool = Field(False, description="Use default letterhead instead of uploaded image")


class RxTemplateCreate(RxTemplateBase):
    """Schema for creating RX template"""
    pass


class RxTemplateUpdate(BaseModel):
    """Schema for updating RX template"""
    template_name: Optional[str] = Field(None, description="Optional template name")
    use_default_letterhead: Optional[bool] = Field(None, description="Use default letterhead instead of uploaded image")


class RxTemplateResponse(BaseModel):
    """Schema for RX template response"""
    id: UUID
    doctor_id: UUID
    clinic_location_id: UUID
    clinic_location_name: Optional[str] = None
    letterhead_image_path: Optional[str] = None
    letterhead_image_url: Optional[str] = None
    template_name: Optional[str] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RxTemplateListResponse(BaseModel):
    """Schema for list of RX templates"""
    status: bool = True
    message: str = "RX templates retrieved successfully"
    data: dict = Field(..., description="Response data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": True,
                "message": "RX templates retrieved successfully",
                "data": {
                    "templates": [
                        {
                            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "doctor_id": "7cf36af4-23b5-4a50-aa71-f99e1dd1ed3d",
                            "clinic_location_id": "93f951f4-3d45-4395-aa18-c2115656d633",
                            "clinic_location_name": "Pure Health BV",
                            "letterhead_image_path": "uploads/rx-templates/7cf36af4-23b5-4a50-aa71-f99e1dd1ed3d/93f951f4-3d45-4395-aa18-c2115656d633/letterhead.jpg",
                            "letterhead_image_url": "https://portal.salutogenahealthcareltd.com/backend/api-fast/uploads/rx-templates/7cf36af4-23b5-4a50-aa71-f99e1dd1ed3d/93f951f4-3d45-4395-aa18-c2115656d633/letterhead.jpg",
                            "template_name": "Main Clinic Template",
                            "is_default": True,
                            "created_at": "2026-01-09T06:43:00Z",
                            "updated_at": "2026-01-09T06:43:00Z"
                        }
                    ]
                }
            }
        }


class RxTemplateSingleResponse(BaseModel):
    """Schema for single RX template response"""
    status: bool = True
    message: str
    data: RxTemplateResponse
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": True,
                "message": "RX template created successfully",
                "data": {
                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "doctor_id": "7cf36af4-23b5-4a50-aa71-f99e1dd1ed3d",
                    "clinic_location_id": "93f951f4-3d45-4395-aa18-c2115656d633",
                    "clinic_location_name": "Pure Health BV",
                    "letterhead_image_path": "uploads/rx-templates/7cf36af4-23b5-4a50-aa71-f99e1dd1ed3d/93f951f4-3d45-4395-aa18-c2115656d633/letterhead.jpg",
                    "letterhead_image_url": "https://portal.salutogenahealthcareltd.com/backend/api-fast/uploads/rx-templates/7cf36af4-23b5-4a50-aa71-f99e1dd1ed3d/93f951f4-3d45-4395-aa18-c2115656d633/letterhead.jpg",
                    "template_name": "Main Clinic Template",
                    "is_default": True,
                    "created_at": "2026-01-09T06:43:00Z",
                    "updated_at": "2026-01-09T06:43:00Z"
                }
            }
        }


class RxTemplateDeleteResponse(BaseModel):
    """Schema for delete response"""
    status: bool = True
    message: str = "RX template deleted successfully"
    data: Optional[dict] = None
