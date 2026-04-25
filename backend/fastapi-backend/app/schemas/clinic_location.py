"""
Clinic Location schemas
Pydantic models for request/response validation
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class ClinicLocationBase(BaseModel):
    """Base schema for clinic location"""
    name: str = Field(..., min_length=1, max_length=255, description="Branch/location name")
    branch_type: Optional[str] = Field(None, max_length=100, description="Type of branch")
    address: Optional[str] = Field(None, description="Full address")
    country_id: UUID = Field(..., description="Country ID")
    state_id: UUID = Field(..., description="State ID")
    city_id: UUID = Field(..., description="City ID")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    is_primary: bool = Field(False, description="Is this the primary location?")


class ClinicLocationCreate(ClinicLocationBase):
    """Schema for creating a new clinic location"""
    pass


class ClinicLocationUpdate(BaseModel):
    """Schema for updating a clinic location"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Branch/location name")
    branch_type: Optional[str] = Field(None, max_length=100, description="Type of branch")
    address: Optional[str] = Field(None, description="Full address")
    country_id: Optional[UUID] = Field(None, description="Country ID")
    state_id: Optional[UUID] = Field(None, description="State ID")
    city_id: Optional[UUID] = Field(None, description="City ID")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    is_primary: Optional[bool] = Field(None, description="Is this the primary location?")


class ClinicLocationResponse(BaseModel):
    """Schema for clinic location response"""
    id: UUID
    name: str
    branch_type: Optional[str]
    address: Optional[str]
    building_name: Optional[str]
    street_name: Optional[str]
    pincode: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    country: Optional[str]
    state: Optional[str]
    city: Optional[str]
    country_id: Optional[UUID]
    state_id: Optional[UUID]
    city_id: Optional[UUID]
    latitude: Optional[float]
    longitude: Optional[float]
    is_primary: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ClinicLocationListResponse(BaseModel):
    """Schema for list of clinic locations"""
    status: bool = True
    message: str = "Locations retrieved successfully"
    data: dict
    
    class Config:
        from_attributes = True


class ClinicLocationSingleResponse(BaseModel):
    """Schema for single clinic location response"""
    status: bool = True
    message: str
    data: dict
    
    class Config:
        from_attributes = True


class ClinicLocationDeleteResponse(BaseModel):
    """Schema for location deletion response"""
    status: bool = True
    message: str = "Location deleted successfully"
    
    class Config:
        from_attributes = True
