"""
Authentication schemas (Pydantic models)
Request/response models for auth endpoints
"""

from typing import Optional
from datetime import date
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, model_validator


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")
    role: Optional[str] = Field(None, description="Expected user role (optional, validates against user's actual role)")
    
    @validator('role')
    def validate_role(cls, v):
        """Validate role value if provided"""
        if v is not None:
            v = v.lower()
            valid_roles = ['super_admin', 'clinic_admin', 'doctor', 'patient', 'staff']
            if v not in valid_roles:
                raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@yopmail.com",
                "password": "password",
                "role": "doctor"
            }
        }


class LoginResponse(BaseModel):
    """Login response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Login successful"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Login successful",
                "data": {
                    "user": {
                        "id": 1,
                        "email": "doctor@example.com",
                        "name": "Dr. John Doe",
                        "role": "doctor",
                        "clinic_id": 1
                    },
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "token_type": "bearer",
                    "expires_in": 1800
                },
                "errors": None
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
            }
        }


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Token refreshed successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Token refreshed successfully",
                "data": {
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "token_type": "bearer",
                    "expires_in": 1800
                },
                "errors": None
            }
        }


class LogoutResponse(BaseModel):
    """Logout response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Logged out successfully"
    data: Optional[dict] = None
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Logged out successfully",
                "data": None,
                "errors": None
            }
        }


class UserProfileResponse(BaseModel):
    """User profile response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Profile retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Profile retrieved successfully",
                "data": {
                    "id": 1,
                    "email": "doctor@example.com",
                    "name": "Dr. John Doe",
                    "role": "doctor",
                    "clinic_id": 1,
                    "phone": "+1234567890",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                "errors": None
            }
        }


class UpdateProfileRequest(BaseModel):
    """Update profile request schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Name cannot be empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Dr. John Doe Updated",
                "phone": "+1234567890"
            }
        }


class UpdateProfileResponse(BaseModel):
    """Update profile response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Profile updated successfully"
    data: dict
    errors: Optional[dict] = None


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)
    new_password_confirmation: str = Field(..., min_length=8)
    
    @validator('new_password_confirmation')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword123",
                "new_password_confirmation": "newpassword123"
            }
        }


class ChangePasswordResponse(BaseModel):
    """Change password response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Password changed successfully"
    data: Optional[dict] = None
    errors: Optional[dict] = None


class RegisterRequest(BaseModel):
    """
    Patient registration request schema
    Matches Figma design for patient registration form
    
    Only patients can register themselves via this endpoint.
    Other roles must be created by admins.
    """
    # Title (optional)
    title: Optional[str] = Field(None, max_length=10, description="Title (Dr, Mr, Mrs, Ms, etc.)", examples=["Mr"])
    
    # Name fields (required)
    first_name: str = Field(..., min_length=1, max_length=255, description="First name (required)", examples=["John"])
    middle_name: Optional[str] = Field(None, max_length=255, description="Middle name (optional)", examples=["Michael"])
    last_name: str = Field(..., min_length=1, max_length=255, description="Last name (required)", examples=["Doe"])
    
    # Date of birth (required)
    date_of_birth: date = Field(..., description="Date of birth (required)", examples=["1990-01-15"])
    
    # Gender (required)
    gender: str = Field(..., max_length=20, description="Gender (required)", examples=["male"])
    
    # Email (required)
    email: EmailStr = Field(..., description="User email address")
    
    # Password (required)
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    password_confirmation: str = Field(..., min_length=8, description="Password confirmation")
    
    # Mobile number (optional) - with country code
    # Format: Enter 10-digit number (area code + exchange + subscriber)
    # Example: For "+1 (721) 544-2275", enter "7215442275" (10 digits)
    # The system will automatically format it as "+1 (721) 544-2275" using the selected country's phone code
    country_id: Optional[UUID] = Field(None, description="Country ID for phone code (required if mobile_number is provided)", examples=["f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"])
    mobile_number: Optional[str] = Field(None, max_length=10, description="10-digit mobile number without country code (area code + exchange + subscriber). Example: For '+1 (721) 544-2275', enter '7215442275'", examples=["7215442275"])
    
    @validator('password_confirmation')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """Validate gender value (required field)"""
        if v is None:
            raise ValueError("Gender is required")
        v = v.lower()
        valid_genders = ['male', 'female', 'other']
        if v not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
        return v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth is not in future (required field)"""
        if v is None:
            raise ValueError("Date of birth is required")
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title value"""
        if v is not None:
            v = v.strip()
        return v
    
    @model_validator(mode='after')
    def validate_mobile_number_with_country(self):
        """Validate that country_id is provided when mobile_number is provided"""
        if self.mobile_number is not None and self.mobile_number.strip():
            if not self.country_id:
                raise ValueError("Country ID is required when mobile number is provided")
        return self
    
    @classmethod
    def model_json_schema(cls, **kwargs):
        """Override to ensure example is in correct order matching Figma design"""
        from collections import OrderedDict
        schema = super().model_json_schema(**kwargs)
        
        # Build example in EXACT field order (matching Figma design)
        # Order: title, first_name, middle_name, last_name, date_of_birth, gender, email, password, password_confirmation, country_id, mobile_number
        example = OrderedDict([
            ("title", "Mr"),
            ("first_name", "John"),
            ("middle_name", "Michael"),
            ("last_name", "Doe"),
            ("date_of_birth", "1990-01-15"),
            ("gender", "male"),
            ("email", "patient@example.com"),
            ("password", "password123"),
            ("password_confirmation", "password123"),
            ("country_id", "f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"),
            ("mobile_number", "7215442275")
        ])
        schema['example'] = dict(example)
        return schema
    
    class Config:
        pass


class RegisterResponse(BaseModel):
    """User registration response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Registration successful"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Registration successful",
                "data": {
                    "user": {
                        "id": 1,
                        "email": "newuser@example.com",
                        "name": "John Doe",
                        "role": "patient",
                        "clinic_id": 1
                    },
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "token_type": "bearer",
                    "expires_in": 1800
                },
                "errors": None
            }
        }
