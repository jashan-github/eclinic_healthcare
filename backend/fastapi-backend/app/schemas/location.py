"""
Location schemas
Request/response models for location endpoints
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class CountryResponse(BaseModel):
    """Country response schema"""
    id: UUID
    shortname: str
    name: str
    phonecode: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StateResponse(BaseModel):
    """State response schema"""
    id: UUID
    name: str
    icon: Optional[str] = None
    sortcode: Optional[str] = None
    country_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CityResponse(BaseModel):
    """City response schema"""
    id: UUID
    name: str
    icon: str
    state_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# LIST RESPONSE SCHEMAS (Laravel compatible)
# ============================================================================


class CountriesListResponse(BaseModel):
    """Countries list response (Laravel compatible)"""
    success: bool = True
    message: str = "Countries retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Countries retrieved successfully",
                "data": {
                    "countries": [
                        {
                            "id": "f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c",
                            "shortname": "SX",
                            "name": "Sint Maarten",
                            "phonecode": 1721
                        }
                    ]
                },
                "errors": None
            }
        }


class StatesListResponse(BaseModel):
    """States list response (Laravel compatible)"""
    success: bool = True
    message: str = "States retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "States retrieved successfully",
                "data": {
                    "states": [
                        {
                            "id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
                            "name": "Philipsburg",
                            "country_id": "f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"
                        }
                    ]
                },
                "errors": None
            }
        }


class CitiesListResponse(BaseModel):
    """Cities list response (Laravel compatible)"""
    success: bool = True
    message: str = "Cities retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Cities retrieved successfully",
                "data": {
                    "cities": [
                        {
                            "id": "b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7",
                            "name": "Cole Bay",
                            "state_id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"
                        }
                    ]
                },
                "errors": None
            }
        }

