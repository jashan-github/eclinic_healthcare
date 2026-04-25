"""
User management schemas
Request/response models for user management endpoints
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    role: str


class UserCreate(UserBase):
    """Create user request schema"""
    password: str = Field(..., min_length=8)
    clinic_id: Optional[UUID] = None
    assigned_doctor_id: Optional[UUID] = Field(None, description="Assigned doctor ID (required for staff role)")
    is_active: bool = True
    # Doctor-only fields (required when role is 'doctor'), same as doctor profile
    education: Optional[str] = Field(None, max_length=255, description="Education details (e.g. MBBS, MD). Required when role is doctor.")
    years_of_experience: Optional[int] = Field(None, ge=0, description="Years of experience. Required when role is doctor.")
    specializations: Optional[List[UUID]] = Field(None, description="List of medical service/specialization IDs. Required when role is doctor (at least one).")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed_roles = ['super_admin', 'clinic_admin', 'doctor', 'nurse', 'staff', 'receptionist', 'patient']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v
    
    @field_validator('assigned_doctor_id')
    @classmethod
    def validate_assigned_doctor(cls, v: Optional[UUID], info) -> Optional[UUID]:
        """Validate that assigned_doctor_id is provided when role is 'staff'"""
        role = info.data.get('role') if info.data else None
        if role == 'staff' and v is None:
            raise ValueError('assigned_doctor_id is required when role is "staff"')
        if role is not None and role != 'staff' and v is not None:
            raise ValueError('assigned_doctor_id can only be set when role is "staff"')
        return v
    
    @model_validator(mode='after')
    def validate_doctor_fields(self):
        """When role is doctor, education, years_of_experience and specializations are required."""
        if self.role != 'doctor':
            return self
        if not self.education or not str(self.education).strip():
            raise ValueError('education is required when role is "doctor"')
        if self.years_of_experience is None:
            raise ValueError('years_of_experience is required when role is "doctor"')
        if not self.specializations or len(self.specializations) == 0:
            raise ValueError('specializations is required when role is "doctor" (at least one medical service ID)')
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "doctor@example.com",
                "password": "password123",
                "name": "Dr. John Doe",
                "phone": "+1234567890",
                "role": "doctor",
                "education": "MBBS, MD in Cardiology",
                "years_of_experience": 10,
                "specializations": ["9cdf3788-f630-47d5-8e11-a49d84409d21"],
                "clinic_id": "4a2c23c9-b31e-4ab5-9819-c4e69ac27879",
                "is_active": True
            }
        }


class UserUpdate(BaseModel):
    """Update user request schema"""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    role: Optional[str] = None
    clinic_id: Optional[UUID] = None
    assigned_doctor_id: Optional[UUID] = Field(None, description="Assigned doctor ID (required for staff role)")
    is_active: Optional[bool] = None
    # Doctor-only fields (optional on update; applied when user is a doctor)
    education: Optional[str] = Field(None, max_length=255, description="Education details (e.g. MBBS, MD)")
    years_of_experience: Optional[int] = Field(None, ge=0, description="Years of experience")
    specializations: Optional[List[UUID]] = Field(None, description="List of medical service/specialization IDs (replaces existing)")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_roles = ['super_admin', 'clinic_admin', 'doctor', 'nurse', 'staff', 'receptionist', 'patient']
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v
    
    @field_validator('assigned_doctor_id')
    @classmethod
    def validate_assigned_doctor_update(cls, v: Optional[UUID], info) -> Optional[UUID]:
        """Validate that assigned_doctor_id is provided when role is 'staff'"""
        role = info.data.get('role') if info.data else None
        if role == 'staff' and v is None:
            raise ValueError('assigned_doctor_id is required when role is "staff"')
        if role is not None and role != 'staff' and v is not None:
            raise ValueError('assigned_doctor_id can only be set when role is "staff"')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Dr. John Doe Updated",
                "phone": "+1234567890",
                "role": "doctor",
                "education": "MBBS, MD in Cardiology",
                "years_of_experience": 12,
                "specializations": ["9cdf3788-f630-47d5-8e11-a49d84409d21"],
                "is_active": True
            }
        }


class UserResponse(BaseModel):
    """User response schema"""
    id: str  # UUID as string
    email: str
    name: str
    phone: Optional[str]
    role: str
    clinic_id: Optional[str]  # UUID as string
    assigned_doctor_id: Optional[str] = None  # UUID as string
    is_active: bool
    is_verified: bool
    email_verified_at: Optional[str]
    created_at: str
    updated_at: str
    last_login_at: Optional[str]
    avatar: Optional[str]
    # Doctor-only fields (from UserProfile and user_medical_services; present when role is doctor)
    education: Optional[str] = None
    years_of_experience: Optional[int] = None
    specializations: Optional[List[str]] = None  # List of medical service UUIDs as strings
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Users retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Users retrieved successfully",
                "data": {
                    "users": [
                        {
                            "id": 1,
                            "email": "doctor@example.com",
                            "name": "Dr. John Doe",
                            "role": "doctor",
                            "is_active": True
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "per_page": 20
                },
                "errors": None
            }
        }


class UserDetailResponse(BaseModel):
    """User detail response schema (Laravel compatible)"""
    success: bool = True
    message: str = "User retrieved successfully"
    data: UserResponse
    errors: Optional[dict] = None


class UserCreateResponse(BaseModel):
    """User create response schema (Laravel compatible)"""
    success: bool = True
    message: str = "User created successfully"
    data: UserResponse
    errors: Optional[dict] = None


class UserUpdateResponse(BaseModel):
    """User update response schema (Laravel compatible)"""
    success: bool = True
    message: str = "User updated successfully"
    data: UserResponse
    errors: Optional[dict] = None


class UserDeleteResponse(BaseModel):
    """User delete response schema (Laravel compatible)"""
    success: bool = True
    message: str = "User deleted successfully"
    data: Optional[dict] = None
    errors: Optional[dict] = None


class ActivateDeactivateRequest(BaseModel):
    """Activate/deactivate user request"""
    is_active: bool = Field(..., description="User active status")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for status change")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_active": False,
                "reason": "Account suspended due to policy violation"
            }
        }


class ActivateDeactivateResponse(BaseModel):
    """Activate/deactivate response schema (Laravel compatible)"""
    success: bool = True
    message: str
    data: UserResponse
    errors: Optional[dict] = None


class ChangeRoleRequest(BaseModel):
    """Change user role request"""
    role: str = Field(..., description="New role")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for role change")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed_roles = ['super_admin', 'clinic_admin', 'doctor', 'nurse', 'staff', 'receptionist', 'patient']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "doctor",
                "reason": "Promoted from nurse to doctor"
            }
        }


class ChangeRoleResponse(BaseModel):
    """Change role response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Role changed successfully"
    data: UserResponse
    errors: Optional[dict] = None


class RoleInfo(BaseModel):
    """Role information"""
    name: str
    display_name: str
    description: str
    permissions: List[str]


class RolesListResponse(BaseModel):
    """Roles list response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Roles retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Roles retrieved successfully",
                "data": {
                    "roles": [
                        {
                            "name": "doctor",
                            "display_name": "Doctor",
                            "description": "Medical professional with full patient care access",
                            "permissions": ["view_patients", "create_prescriptions", "view_appointments"]
                        }
                    ]
                },
                "errors": None
            }
        }


class UserStatsResponse(BaseModel):
    """User statistics response schema (Laravel compatible)"""
    success: bool = True
    message: str = "Statistics retrieved successfully"
    data: dict
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Statistics retrieved successfully",
                "data": {
                    "total_users": 100,
                    "active_users": 95,
                    "inactive_users": 5,
                    "by_role": {
                        "doctor": 20,
                        "nurse": 30,
                        "patient": 45,
                        "receptionist": 5
                    }
                },
                "errors": None
            }
        }
