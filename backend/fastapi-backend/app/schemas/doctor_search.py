"""
Doctor Search schemas
Request/response models for patient doctor search endpoint
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class DoctorSearchResult(BaseModel):
    """Doctor search result item"""
    id: UUID
    name: str
    profile_image: Optional[str] = Field(None, alias="avatar", description="Profile image URL")
    specialty: Optional[str] = Field(None, description="Primary specialty name")
    qualifications: Optional[str] = Field(None, description="Education/qualifications")
    rating: Optional[float] = Field(None, description="Doctor rating (if available)")
    years_of_experience: Optional[int] = Field(None, description="Years of professional experience")
    lowest_consultation_fee: Optional[float] = Field(None, description="Lowest visible consultation fee (IN_CLINIC preferred)")
    currency: Optional[str] = Field(None, description="Currency code for consultation fee")
    available_days: List[str] = Field(default_factory=list, description="List of available days (max 5, sorted Monday-Sunday)")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class DoctorSearchResponse(BaseModel):
    """Doctor search response (Laravel compatible)"""
    success: bool = True
    message: str = "Doctors retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Doctors retrieved successfully",
                "data": {
                    "doctors": [
                        {
                            "id": "9cdf3788-f630-47d5-8e11-a49d84409d21",
                            "name": "Dr. John Doe",
                            "profile_image": "https://example.com/avatar.jpg",
                            "specialty": "Cardiology",
                            "qualifications": "MBBS, MD",
                            "rating": 4.5,
                            "years_of_experience": 10,
                            "lowest_consultation_fee": 500.00,
                            "currency": "USD",
                            "available_days": ["Mon", "Tue", "Wed", "Thu", "Fri"]
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
