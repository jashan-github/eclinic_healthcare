"""
Language schemas
Request/response models for language endpoints
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class LanguageResponse(BaseModel):
    """Language response schema"""
    id: UUID
    language_name: Optional[str] = None
    language_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# LIST RESPONSE SCHEMAS (Laravel compatible)
# ============================================================================


class LanguagesListResponse(BaseModel):
    """Languages list response (Laravel compatible)"""
    success: bool = True
    message: str = "Languages retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Languages retrieved successfully",
                "data": {
                    "languages": [
                        {
                            "id": "a734ef5c-5653-444c-825e-ac8629e7eaf0",
                            "language_name": "English",
                            "language_code": "en"
                        },
                        {
                            "id": "8c8d3fb2-e9a4-45c2-9c24-7e6edc5b9642",
                            "language_name": "French",
                            "language_code": "fr"
                        }
                    ]
                },
                "errors": None
            }
        }

