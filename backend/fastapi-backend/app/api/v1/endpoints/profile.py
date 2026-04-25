"""
User Profile API Endpoints
Laravel-compatible routes for profile management
"""

from fastapi import APIRouter, Depends, Request, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import date, datetime
import os
import json
from pathlib import Path

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin_user
from app.core.security import CurrentUser
from app.models.user import User
from app.models.audit import AuditLog
from app.services.audit_service import AuditService
from app.schemas.profile import (
    ProfileUpdate,
    ProfileCompletion,
    PatientPersonalInfoUpdate,
    PatientMedicalInfoUpdate,
    DoctorProfileUpdate,
    ContactDetailsUpdate,
    ProfileSingleResponse,
    ProfileUpdateResponse,
    PatientPersonalInfoSingleResponse,
    PatientMedicalInfoSingleResponse,
    DoctorProfileSingleResponse
)
from app.services.profile_service import get_profile_service, ProfileService
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from loguru import logger


router = APIRouter(tags=["Profile"])


def _parse_uuid_list(value, field_name="field"):
    """Parse UUIDs from string, list, or comma-separated string"""
    if not value:
        return None
    result = []
    try:
        # If it's already a list
        if isinstance(value, list):
            for item in value:
                if item:
                    item_str = str(item).strip().strip('[]"\'')
                    if item_str:
                        # Check if comma-separated
                        if ',' in item_str:
                            for part in item_str.split(','):
                                part_clean = part.strip().strip('[]"\'')
                                if part_clean:
                                    result.append(UUID(part_clean))
                        else:
                            result.append(UUID(item_str))
        # If it's a string
        elif isinstance(value, str):
            value_str = value.strip().strip('[]"\'')
            # Try JSON first
            try:
                parsed = json.loads(value_str)
                if isinstance(parsed, list):
                    for item in parsed:
                        if item:
                            item_str = str(item).strip().strip('[]"\'')
                            if item_str:
                                result.append(UUID(item_str))
                else:
                    raise ValidationException(
                        message=f"Invalid {field_name} format",
                        errors={field_name: [f"{field_name.title()} must be a JSON array"]}
                    )
            except json.JSONDecodeError:
                # Not JSON, try comma-separated
                if ',' in value_str:
                    for part in value_str.split(','):
                        part_clean = part.strip().strip('[]"\'')
                        if part_clean:
                            result.append(UUID(part_clean))
                else:
                    # Single value
                    result.append(UUID(value_str))
    except ValueError as e:
        raise ValidationException(
            message=f"Invalid {field_name} ID format",
            errors={field_name: [f"Invalid UUID format: {str(e)}"]}
        )
    return result if result else None


def _create_audit_log(
    db: Session,
    user: User,
    action: str,
    target_user_id: UUID,
    request: Request,
    metadata: dict = None
):
    """
    Create audit log entry for profile operations
    
    Args:
        db: Database session
        user: Current user
        action: Action type
        target_user_id: Target user ID
        request: HTTP request
        metadata: Additional metadata
    """
    try:
        audit_service = AuditService(db)
        audit_service.create_audit_log_from_request(
            request=request,
            actor_user_id=user.id,
            action=action,
            entity_type="user_profile",
            entity_id=target_user_id,
            audit_metadata=metadata or {}
        )
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        # Don't fail the operation if audit logging fails


# ============================================================================
# SELF PROFILE ENDPOINTS
# ============================================================================


@router.get(
    "/profile",
    response_model=ProfileSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user's profile",
    description="Retrieve the authenticated user's profile information"
)
async def get_current_user_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get current user's profile
    
    **Laravel compatible:**
    - Same endpoint path: GET /profile
    - Same response format
    
    Returns:
        Profile with contact details
    """
    try:
        # Get profile
        profile_data = profile_service.get_profile(current_user.id)
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="PROFILE_VIEWED",
            target_user_id=current_user.id,
            request=request,
            metadata={"self_view": True}
        )
        
        return ProfileSingleResponse(
            success=True,
            message="Profile retrieved successfully",
            data=profile_data,
            errors=None
        )
    
    except Exception as e:
        logger.error(f"Failed to retrieve profile: {str(e)}")
        raise


@router.get(
    "/patients/profile/personal",
    response_model=PatientPersonalInfoSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient personal information",
    description="Retrieve the authenticated patient's personal information (name, contact, demographics, address, avatar). Patient-only endpoint."
)
async def get_patient_personal_info(
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get patient personal information
    
    **Patient-only endpoint**
    
    Returns:
        Patient personal information including:
        - Name fields (title, first_name, middle_name, last_name)
        - Demographics (gender, date_of_birth, age)
        - Contact numbers (contact, emergency, family)
        - Additional info (blood_type, occupation, marital_status, preferred_language)
        - Address (country, state, city, street, zip)
        - Profile image (avatar URL)
    """
    try:
        # Check if user is patient
        if current_user.role != "patient":
            raise ForbiddenException(
                message="This endpoint is only for patients",
                errors={"role": ["Only patients can use this endpoint"]}
            )
        
        # Get patient personal info
        personal_info = profile_service.get_patient_personal_info(current_user.id)
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="PATIENT_PERSONAL_INFO_VIEWED",
            target_user_id=current_user.id,
            request=request,
            metadata={"self_view": True}
        )
        
        return PatientPersonalInfoSingleResponse(
            success=True,
            message="Personal information retrieved successfully",
            data=personal_info,
            errors=None
        )
    
    except Exception as e:
        logger.error(f"Failed to retrieve patient personal info: {str(e)}")
        raise


@router.get(
    "/patients/profile/medical",
    response_model=PatientMedicalInfoSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient medical information",
    description="Retrieve the authenticated patient's medical information (conditions, allergies, medications). Patient-only endpoint."
)
async def get_patient_medical_info(
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get patient medical information
    
    **Patient-only endpoint**
    
    Returns:
        Patient medical information including:
        - Pre-defined conditions (diabetes, hypertension, etc.) with years
        - Custom conditions
        - Existing conditions
        - Allergies
        - Current medications
    """
    try:
        # Check if user is patient
        if current_user.role != "patient":
            raise ForbiddenException(
                message="This endpoint is only for patients",
                errors={"role": ["Only patients can use this endpoint"]}
            )
        
        # Get patient medical info
        medical_info = profile_service.get_patient_medical_info(current_user.id)
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="PATIENT_MEDICAL_INFO_VIEWED",
            target_user_id=current_user.id,
            request=request,
            metadata={"self_view": True}
        )
        
        return PatientMedicalInfoSingleResponse(
            success=True,
            message="Medical information retrieved successfully",
            data=medical_info,
            errors=None
        )
    
    except Exception as e:
        logger.error(f"Failed to retrieve patient medical info: {str(e)}")
        raise


@router.post(
    "/profile/complete",
    response_model=ProfileUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete initial profile setup",
    description="Complete profile for admin-created users (first_name, dob, gender required). Common for patient and doctor."
)
async def complete_profile(
    profile_data: ProfileCompletion,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Complete initial profile setup
    
    Used when admin-created users first login and need to complete their profile.
    Required fields: first_name, date_of_birth, gender
    Optional fields: title, middle_name, last_name, country_id, mobile_number, address fields
    
    This endpoint is common for both patient and doctor roles.
    
    Args:
        profile_data: Profile completion data
    
    Returns:
        Completed profile with contact details
    """
    try:
        # Get User object from database (service methods expect User, not CurrentUser)
        user = db.query(User).filter(User.id == current_user.id, User.deleted_at.is_(None)).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Check if profile is already complete
        profile = profile_service.get_profile(current_user.id)
        if profile.is_profile_complete:
            raise ValidationException(
                message="Profile is already complete",
                errors={"profile": ["Profile has already been completed. Use PUT /profile to update."]}
            )
        
        # Complete profile (treats ProfileCompletion as ProfileUpdate)
        updated_profile = profile_service.complete_profile(
            user_id=current_user.id,
            profile_data=profile_data,
            current_user=user
        )
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=user,
            action="PROFILE_COMPLETED",
            target_user_id=current_user.id,
            request=request,
            metadata={
                "self_completion": True,
                "role": current_user.role
            }
        )
        
        logger.info(f"User {current_user.id} completed their profile")
        
        return ProfileUpdateResponse(
            success=True,
            message="Profile completed successfully",
            data=updated_profile,
            errors=None
        )
    
    except (ValidationException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Failed to complete profile: {str(e)}")
        raise


@router.put(
    "/profile",
    response_model=ProfileUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user's profile (Non-patient roles)",
    description="Update the authenticated user's profile information. For non-patient roles only. Patients should use /patients/profile endpoints."
)
async def update_current_user_profile(
    profile_data: ProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Update current user's profile (for non-patient roles)
    
    **Note:** Patients should use:
    - PUT /patients/profile/personal - for personal information
    - PUT /patients/profile/medical - for medical information
    
    **Laravel compatible:**
    - Same endpoint path: PUT /profile
    - Same request payload
    - Same response format
    
    Args:
        profile_data: Profile update data (ProfileUpdate)
    
    Returns:
        Updated profile with contact details
    """
    try:
        # Check if user is patient - redirect them to patient endpoints
        if current_user.role == "patient":
            raise ValidationException(
                message="Patients must use patient-specific endpoints",
                errors={"endpoint": ["Please use PUT /patients/profile/personal or PUT /patients/profile/medical"]}
            )
        
        # Check if user is doctor - redirect them to doctor endpoint
        if current_user.role == "doctor":
            raise ValidationException(
                message="Doctors must use doctor-specific endpoint",
                errors={"endpoint": ["Please use PUT /doctors/profile to update your profile"]}
            )
        
        # Check if profile is complete (required for updates)
        profile = profile_service.get_profile(current_user.id)
        if not profile.is_profile_complete:
            raise ValidationException(
                message="Profile must be completed first",
                errors={"profile": ["Please complete your profile first using POST /profile/complete"]}
            )
        
        # Get User object from database (service methods expect User, not CurrentUser)
        user = db.query(User).filter(User.id == current_user.id, User.deleted_at.is_(None)).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Update profile
        updated_profile = profile_service.update_profile(
            user_id=current_user.id,
            profile_data=profile_data,
            current_user=user
        )
        
        # Create audit log
        update_fields = profile_data.model_dump(exclude_unset=True)
        _create_audit_log(
            db=db,
            user=user,
            action="PROFILE_UPDATED",
            target_user_id=current_user.id,
            request=request,
            metadata={
                "self_update": True,
                "updated_fields": list(update_fields.keys()),
                "role": current_user.role
            }
        )
        
        logger.info(f"User {current_user.id} updated their profile")
        
        return ProfileUpdateResponse(
            success=True,
            message="Profile updated successfully",
            data=updated_profile,
            errors=None
        )
    
    except (ValidationException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Failed to update profile: {str(e)}")
        raise


# ============================================================================
# PATIENT-SPECIFIC PROFILE ENDPOINTS
# ============================================================================


@router.put(
    "/patients/profile/personal",
    response_model=ProfileUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update patient personal information",
    description="Update patient's personal information (name, contact, demographics, address, avatar). Uses multipart/form-data for file uploads. Matches Figma Personal Info tab.",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["first_name", "last_name", "gender", "date_of_birth"],
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title prefix (Dr, Mr, Mrs, Ms, etc.)",
                                "example": "Dr"
                            },
                            "first_name": {
                                "type": "string",
                                "description": "First name (required)",
                                "example": "John"
                            },
                            "middle_name": {
                                "type": "string",
                                "description": "Middle name (optional)",
                                "example": "Michael"
                            },
                            "last_name": {
                                "type": "string",
                                "description": "Last name (required)",
                                "example": "Doe"
                            },
                            "gender": {
                                "type": "string",
                                "enum": ["male", "female", "other"],
                                "description": "Gender (required). Options: male, female, other",
                                "example": "male"
                            },
                            "date_of_birth": {
                                "type": "string",
                                "format": "date",
                                "description": "Date of birth in YYYY-MM-DD format (required)",
                                "example": "1990-01-15"
                            },
                            "contact_number": {
                                "type": "string",
                                "description": "Contact number with country code (e.g., +1 (721) 544-2275)",
                                "example": "+1 (721) 544-2275"
                            },
                            "emergency_contact_number": {
                                "type": "string",
                                "description": "Emergency contact number",
                                "example": "+1 (721) 555-1234"
                            },
                            "family_contact_number": {
                                "type": "string",
                                "description": "Family contact number",
                                "example": "+1 (721) 555-5678"
                            },
                            "blood_type": {
                                "type": "string",
                                "enum": ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"],
                                "description": "Blood type group. Options: O+, O-, A+, A-, B+, B-, AB+, AB-",
                                "example": "O+"
                            },
                            "occupation": {
                                "type": "string",
                                "description": "Occupation or profession",
                                "example": "Software Engineer"
                            },
                            "marital_status": {
                                "type": "string",
                                "enum": ["Single", "Married", "Divorced", "Widowed", "Separated", "Domestic Partnership"],
                                "description": "Marital status. Options: Single, Married, Divorced, Widowed, Separated, Domestic Partnership",
                                "example": "Single"
                            },
                            "preferred_language_id": {
                                "type": "string",
                                "format": "uuid",
                                "description": "Preferred language UUID from languages table. Use GET /api/v1/languages to get available languages",
                                "example": "a734ef5c-5653-444c-825e-ac8629e7eaf0"
                            },
                            "country_id": {
                                "type": "string",
                                "format": "uuid",
                                "description": "Country UUID from countries table. Use GET /api/v1/locations/countries to get available countries",
                                "example": "f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"
                            },
                            "state_id": {
                                "type": "string",
                                "format": "uuid",
                                "description": "State UUID from states table. Use GET /api/v1/locations/countries/{country_id}/states to get states for a country",
                                "example": "b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7"
                            },
                            "city_id": {
                                "type": "string",
                                "format": "uuid",
                                "description": "City UUID from cities table. Use GET /api/v1/locations/states/{state_id}/cities to get cities for a state",
                                "example": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"
                            },
                            "address_line_1": {
                                "type": "string",
                                "description": "Street address line 1",
                                "example": "123 Main Street"
                            },
                            "postal_code": {
                                "type": "string",
                                "description": "Postal/ZIP code",
                                "example": "10001"
                            },
                            "avatar": {
                                "type": "string",
                                "format": "binary",
                                "description": "Profile image file (jpg, jpeg, png, gif, webp, max 5MB)"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def update_patient_personal_info(
    # Form fields with descriptions and examples
    title: Optional[str] = Form(None, description="Title prefix (Dr, Mr, Mrs, Ms, etc.)", example="Dr"),
    first_name: str = Form(..., description="First name (required)", example="John"),
    middle_name: Optional[str] = Form(None, description="Middle name (optional)", example="Michael"),
    last_name: str = Form(..., description="Last name (required)", example="Doe"),
    gender: str = Form(..., description="Gender (required). Options: male, female, other", example="male"),
    date_of_birth: str = Form(..., description="Date of birth in YYYY-MM-DD format (required)", example="1990-01-15"),
    contact_number: Optional[str] = Form(None, description="Contact number with country code (e.g., +1 (721) 544-2275)", example="+1 (721) 544-2275"),
    emergency_contact_number: Optional[str] = Form(None, description="Emergency contact number", example="+1 (721) 555-1234"),
    family_contact_number: Optional[str] = Form(None, description="Family contact number", example="+1 (721) 555-5678"),
    blood_type: Optional[str] = Form(None, description="Blood type group. Options: O+, O-, A+, A-, B+, B-, AB+, AB-", example="O+"),
    occupation: Optional[str] = Form(None, description="Occupation or profession", example="Software Engineer"),
    marital_status: Optional[str] = Form(None, description="Marital status. Options: Single, Married, Divorced, Widowed, Separated, Domestic Partnership", example="Single"),
    preferred_language_id: Optional[str] = Form(None, description="Preferred language UUID from languages table. Use GET /api/v1/languages to get available languages", example="a734ef5c-5653-444c-825e-ac8629e7eaf0"),
    country_id: Optional[str] = Form(None, description="Country UUID from countries table. Use GET /api/v1/locations/countries to get available countries", example="f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"),
    state_id: Optional[str] = Form(None, description="State UUID from states table. Use GET /api/v1/locations/countries/{country_id}/states to get states for a country", example="b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7"),
    city_id: Optional[str] = Form(None, description="City UUID from cities table. Use GET /api/v1/locations/states/{state_id}/cities to get cities for a state", example="a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"),
    address_line_1: Optional[str] = Form(None, description="Street address line 1", example="123 Main Street"),
    postal_code: Optional[str] = Form(None, description="Postal/ZIP code", example="10001"),
    # File upload - MUST be declared with File() for Swagger UI to show file picker
    avatar: Optional[UploadFile] = File(None, description="Profile image file (jpg, jpeg, png, gif, webp, max 5MB)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Update patient personal information
    
    **Patient-only endpoint**
    Uses multipart/form-data to support file uploads for avatar.
    
    Updates personal information including:
    - Name fields (title, first_name, middle_name, last_name)
    - Demographics (gender, date_of_birth)
    - Contact numbers (contact, emergency, family)
    - Additional info (blood_type, occupation, marital_status, preferred_language)
    - Profile image (avatar) - file upload
    - Address (country, state, city, street, zip)
    
    Args:
        Form fields: All personal information fields
        avatar: Profile image file (optional)
    
    Returns:
        Updated profile with contact details
    """
    try:
        # Check if user is patient
        if current_user.role != "patient":
            raise ForbiddenException(
                message="This endpoint is only for patients",
                errors={"role": ["Only patients can use this endpoint"]}
            )
        
        # Check if profile is complete (required for updates)
        profile_response = profile_service.get_profile(current_user.id)
        if not profile_response.is_profile_complete:
            raise ValidationException(
                message="Profile must be completed first",
                errors={"profile": ["Please complete your profile first using POST /profile/complete"]}
            )
        
        # Handle avatar file upload
        avatar_path = None
        if avatar and avatar.filename:
            avatar_path = await _save_avatar_file(avatar, current_user.id, db)
        
        # Validate gender enum
        valid_genders = ["male", "female", "other"]
        if gender.lower() not in valid_genders:
            raise ValidationException(
                message="Invalid gender value",
                errors={"gender": [f"Gender must be one of: {', '.join(valid_genders)}"]}
            )
        gender = gender.lower()
        
        # Validate marital_status enum if provided
        if marital_status:
            valid_marital_statuses = ["Single", "Married", "Divorced", "Widowed", "Separated", "Domestic Partnership"]
            if marital_status not in valid_marital_statuses:
                raise ValidationException(
                    message="Invalid marital status value",
                    errors={"marital_status": [f"Marital status must be one of: {', '.join(valid_marital_statuses)}"]}
                )
        
        # Validate blood_type enum if provided
        if blood_type:
            valid_blood_types = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
            if blood_type not in valid_blood_types:
                raise ValidationException(
                    message="Invalid blood type value",
                    errors={"blood_type": [f"Blood type must be one of: {', '.join(valid_blood_types)}"]}
                )
        
        # Parse date_of_birth from string (YYYY-MM-DD format)
        try:
            parsed_date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date() if date_of_birth else None
        except (ValueError, TypeError) as e:
            raise ValidationException(
                message="Invalid date format",
                errors={"date_of_birth": [f"Invalid date format: {date_of_birth}. Use YYYY-MM-DD format."]}
            )
        
        # Parse UUID fields from strings
        def parse_uuid(value: Optional[str]) -> Optional[UUID]:
            if value and value.strip():
                try:
                    return UUID(value)
                except ValueError:
                    raise ValidationException(
                        message="Invalid UUID format",
                        errors={"uuid": [f"Invalid UUID format: {value}"]}
                    )
            return None
        
        # Build profile data from form fields
        profile_data_dict = {
            "title": title,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "gender": gender,
            "date_of_birth": parsed_date_of_birth,
            "contact_number": contact_number,
            "emergency_contact_number": emergency_contact_number,
            "family_contact_number": family_contact_number,
            "blood_type": blood_type,
            "occupation": occupation,
            "marital_status": marital_status,
            "preferred_language_id": parse_uuid(preferred_language_id),
            "country_id": parse_uuid(country_id),
            "state_id": parse_uuid(state_id),
            "city_id": parse_uuid(city_id),
            "address_line_1": address_line_1,
            "postal_code": postal_code,
            "avatar": avatar_path  # Set avatar path if file was uploaded
        }
        
        # Remove None values to only update provided fields
        profile_data_dict = {k: v for k, v in profile_data_dict.items() if v is not None}
        
        # Create schema instance
        profile_data = PatientPersonalInfoUpdate(**profile_data_dict)
        
        # Update patient personal info
        updated_profile = profile_service.update_patient_personal_info(
            user_id=current_user.id,
            profile_data=profile_data,
            current_user=current_user
        )
        
        # Create audit log
        update_fields = list(profile_data_dict.keys())
        _create_audit_log(
            db=db,
            user=current_user,
            action="PATIENT_PERSONAL_INFO_UPDATED",
            target_user_id=current_user.id,
            request=request,
            metadata={
                "self_update": True,
                "updated_fields": update_fields
            }
        )
        
        logger.info(f"Patient {current_user.id} updated personal information")
        
        return ProfileUpdateResponse(
            success=True,
            message="Personal information updated successfully",
            data=updated_profile,
            errors=None
        )
    
    except (ValidationException, NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to update patient personal info: {str(e)}")
        raise


async def _save_avatar_file(avatar: UploadFile, user_id: UUID, db: Session) -> str:
    """
    Save uploaded avatar file and return the file path
    
    Args:
        avatar: Uploaded file
        user_id: User ID for unique filename
        db: Database session
    
    Returns:
        File path relative to uploads directory (e.g., "uploads/avatars/user_id.jpg")
    
    Raises:
        ValidationException: If file is invalid
    """
    from app.core.config import settings
    from app.core.exceptions import ValidationException
    
    # Validate file extension
    if avatar.filename:
        file_ext = avatar.filename.split('.')[-1].lower()
        if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationException(
                message="Invalid file type",
                errors={"avatar": [f"Allowed extensions: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"]}
            )
    
    # Validate file size
    contents = await avatar.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise ValidationException(
            message="File too large",
            errors={"avatar": [f"Maximum file size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"]}
        )
    
    # Create upload directory if it doesn't exist
    try:
        upload_dir = Path(settings.AVATAR_UPLOAD_DIR)
        # Resolve to absolute path
        upload_dir = upload_dir.resolve()
        
        # Create directory if it doesn't exist
        if not upload_dir.exists():
            upload_dir.mkdir(parents=True, mode=0o755)
        else:
            # Check if directory is writable
            if not os.access(upload_dir, os.W_OK):
                raise PermissionError(f"Upload directory is not writable: {upload_dir}")
    except PermissionError as e:
        logger.error(f"Permission denied creating/accessing upload directory: {upload_dir}. Error: {e}")
        raise ValidationException(
            message="Unable to save file",
            errors={"avatar": ["Permission denied: Cannot create or write to upload directory. Please contact administrator."]}
        )
    except OSError as e:
        logger.error(f"OS error creating upload directory: {upload_dir}. Error: {e}")
        raise ValidationException(
            message="Unable to save file",
            errors={"avatar": [f"Error creating upload directory: {str(e)}"]}
        )
    
    # Generate unique filename: user_id.extension
    file_ext = avatar.filename.split('.')[-1].lower() if avatar.filename else 'jpg'
    filename = f"{user_id}.{file_ext}"
    file_path = upload_dir / filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except PermissionError as e:
        logger.error(f"Permission denied writing file: {file_path}. Error: {e}")
        raise ValidationException(
            message="Unable to save file",
            errors={"avatar": ["Permission denied: Cannot write file. Please contact administrator."]}
        )
    except OSError as e:
        logger.error(f"OS error writing file: {file_path}. Error: {e}")
        raise ValidationException(
            message="Unable to save file",
            errors={"avatar": [f"Error saving file: {str(e)}"]}
        )
    
    # Return relative path for database storage
    return f"{settings.AVATAR_UPLOAD_DIR}/{filename}"


@router.put(
    "/patients/profile/medical",
    response_model=ProfileUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update patient medical information",
    description="Update patient's medical information (conditions, allergies, medications). Matches Figma Medical Info tab."
)
async def update_patient_medical_info(
    profile_data: PatientMedicalInfoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Update patient medical information
    
    **Patient-only endpoint**
    Updates medical information including:
    - Pre-defined conditions (diabetes, hypertension, etc.) with years
    - Custom conditions
    - Existing conditions
    - Allergies
    - Current medications
    
    Args:
        profile_data: Patient medical information update data
    
    Returns:
        Updated profile with contact details
    """
    try:
        # Check if user is patient
        if current_user.role != "patient":
            raise ForbiddenException(
                message="This endpoint is only for patients",
                errors={"role": ["Only patients can use this endpoint"]}
            )
        
        # Check if profile is complete (required for updates)
        profile_response = profile_service.get_profile(current_user.id)
        if not profile_response.is_profile_complete:
            raise ValidationException(
                message="Profile must be completed first",
                errors={"profile": ["Please complete your profile first using POST /profile/complete"]}
            )
        
        # Update patient medical info
        updated_profile = profile_service.update_patient_medical_info(
            user_id=current_user.id,
            profile_data=profile_data,
            current_user=current_user
        )
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="PATIENT_MEDICAL_INFO_UPDATED",
            target_user_id=current_user.id,
            request=request,
            metadata={
                "self_update": True
            }
        )
        
        logger.info(f"Patient {current_user.id} updated medical information")
        
        return ProfileUpdateResponse(
            success=True,
            message="Medical information updated successfully",
            data=updated_profile,
            errors=None
        )
    
    except (ValidationException, NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to update patient medical info: {str(e)}")
        raise


# ============================================================================
# ADMIN/DOCTOR PROFILE ENDPOINTS
# ============================================================================


@router.get(
    "/users/{user_id}/profile",
    response_model=ProfileSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile (Admin/Doctor)",
    description="Retrieve any user's profile information (Admin/Doctor only)"
)
async def get_user_profile(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get user profile by ID
    
    **Laravel compatible:**
    - Same endpoint path: GET /users/{id}/profile
    - Same response format
    
    **Permissions:**
    - Admin: Can view any profile
    - Doctor: Can view any profile (read-only)
    - Patient: Can only view own profile (use /profile instead)
    
    Args:
        user_id: User ID to retrieve
    
    Returns:
        Profile with contact details
    """
    try:
        # Check permissions
        if not profile_service.can_view_profile(user_id, current_user):
            raise ForbiddenException(
                message="You do not have permission to view this profile",
                errors={"permission": ["Insufficient permissions to view this profile"]}
            )
        
        # Get profile
        profile_data = profile_service.get_profile(user_id)
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="PROFILE_VIEWED",
            target_user_id=user_id,
            request=request,
            metadata={
                "viewer_role": current_user.role,
                "self_view": (current_user.id == user_id)
            }
        )
        
        return ProfileSingleResponse(
            success=True,
            message="Profile retrieved successfully",
            data=profile_data,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve user profile: {str(e)}")
        raise


@router.put(
    "/users/{user_id}/profile",
    response_model=ProfileUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile (Admin only)",
    description="Update any user's profile information (Admin only)"
)
async def update_user_profile(
    user_id: UUID,
    profile_data: ProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Update user profile by ID
    
    **Laravel compatible:**
    - Same endpoint path: PUT /users/{id}/profile
    - Same request payload
    - Same response format
    
    **Permissions:**
    - Admin only
    
    Args:
        user_id: User ID to update
        profile_data: Profile update data
    
    Returns:
        Updated profile with contact details
    """
    try:
        # Update profile (admin check already done by get_current_admin_user)
        updated_profile = profile_service.update_profile(
            user_id=user_id,
            profile_data=profile_data,
            current_user=current_user
        )
        
        # Create audit log
        update_fields = profile_data.model_dump(exclude_unset=True)
        _create_audit_log(
            db=db,
            user=current_user,
            action="PROFILE_UPDATED",
            target_user_id=user_id,
            request=request,
            metadata={
                "admin_update": True,
                "updated_fields": list(update_fields.keys())
            }
        )
        
        logger.info(
            f"Admin {current_user.id} updated profile for user {user_id}"
        )
        
        return ProfileUpdateResponse(
            success=True,
            message="Profile updated successfully",
            data=updated_profile,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        raise


# ============================================================================
# DOCTOR-SPECIFIC PROFILE ENDPOINTS
# ============================================================================


@router.put(
    "/doctors/profile",
    response_model=DoctorProfileSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update doctor profile",
    description="Update doctor's profile information (name, contact, education, experience, languages, specializations, about, avatar). Uses multipart/form-data for file uploads. Matches Figma doctor profile form.",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["first_name", "last_name", "dob"],
                        "properties": {
                            "first_name": {
                                "type": "string",
                                "description": "First name (required)",
                                "example": "John"
                            },
                            "middle_name": {
                                "type": "string",
                                "description": "Middle name (optional)",
                                "example": "Michael"
                            },
                            "last_name": {
                                "type": "string",
                                "description": "Last name (required)",
                                "example": "Doe"
                            },
                            "dob": {
                                "type": "string",
                                "format": "date",
                                "description": "Date of birth in YYYY-MM-DD format (required, must be at least 18 years old)",
                                "example": "1990-01-15"
                            },
                            "phone_number": {
                                "type": "string",
                                "description": "Phone number (10 digits, must be unique)",
                                "example": "9876543210"
                            },
                            "email": {
                                "type": "string",
                                "format": "email",
                                "description": "Email address (must be unique)",
                                "example": "dr.bajwa@gmail.com"
                            },
                            "education": {
                                "type": "string",
                                "description": "Education details (e.g., MBBS, MD in Cardiology)",
                                "example": "MBBS, MD in Cardiology"
                            },
                            "years_of_experience": {
                                "type": "integer",
                                "description": "Years of experience",
                                "example": 10
                            },
                            "languages": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "format": "uuid"
                                },
                                "description": "Array of language IDs from languages table. Use GET /api/v1/languages to get available languages. Enter each UUID in a separate field.",
                                "example": ["a734ef5c-5653-444c-825e-ac8629e7eaf0", "a9a02cce-1624-4162-8c1a-56580a0f1558", "5b7a93c0-3c0d-4c9c-a23f-5e2e04d5d5c1"]
                            },
                            "specializations": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "format": "uuid"
                                },
                                "description": "Array of medical service/specialization IDs from medical_services table. Use GET /api/v1/medical-services to get available services. Enter each UUID in a separate field.",
                                "example": ["9cdf3788-f630-47d5-8e11-a49d84409d21", "9cdf3789-00dd-40fd-9932-3ed703e12a44", "9cdf3789-019b-4366-a8ca-e42f879ba156"]
                            },
                            "about": {
                                "type": "string",
                                "description": "About the doctor",
                                "example": "Experienced cardiologist with 10+ years of practice"
                            },
                            "profile_img": {
                                "type": "string",
                                "format": "binary",
                                "description": "Profile image file (jpeg, png, jpg, gif, svg, max 2MB)"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def update_doctor_profile(
    request: Request,
    first_name: str = Form(..., description="First name (required)", example="John"),
    middle_name: Optional[str] = Form(None, description="Middle name (optional)", example="Michael"),
    last_name: str = Form(..., description="Last name (required)", example="Doe"),
    dob: str = Form(..., description="Date of birth in YYYY-MM-DD format (required, must be at least 18 years old)", example="1990-01-15"),
    phone_number: Optional[str] = Form(None, description="Phone number (10 digits, must be unique)", example="9876543210"),
    email: Optional[str] = Form(None, description="Email address (must be unique)", example="dr.bajwa@gmail.com"),
    education: Optional[str] = Form(None, description="Education details (e.g., MBBS, MD in Cardiology)", example="MBBS, MD in Cardiology"),
    years_of_experience: Optional[int] = Form(None, description="Years of experience", example=10),
    languages: Optional[str] = Form(None, description="Array of language IDs from languages table (JSON array string or comma-separated). Use GET /api/v1/languages to get available languages. Example: [\"a734ef5c-5653-444c-825e-ac8629e7eaf0\", \"a9a02cce-1624-4162-8c1a-56580a0f1558\"] or a734ef5c-5653-444c-825e-ac8629e7eaf0,a9a02cce-1624-4162-8c1a-56580a0f1558", example='["a734ef5c-5653-444c-825e-ac8629e7eaf0", "a9a02cce-1624-4162-8c1a-56580a0f1558"]'),
    specializations: Optional[str] = Form(None, description="Array of medical service/specialization IDs from medical_services table (JSON array string or comma-separated). Use GET /api/v1/medical-services to get available services. Example: [\"9cdf3788-f630-47d5-8e11-a49d84409d21\", \"9cdf3789-00dd-40fd-9932-3ed703e12a44\"] or 9cdf3788-f630-47d5-8e11-a49d84409d21,9cdf3789-00dd-40fd-9932-3ed703e12a44", example='["9cdf3788-f630-47d5-8e11-a49d84409d21", "9cdf3789-00dd-40fd-9932-3ed703e12a44"]'),
    about: Optional[str] = Form(None, description="About the doctor", example="Experienced cardiologist with 10+ years of practice"),
    profile_img: Optional[UploadFile] = File(None, description="Profile image file (jpeg, png, jpg, gif, svg, max 2MB)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Update doctor profile information
    
    **Doctor-only endpoint**
    Uses multipart/form-data to support file uploads for profile image.
    
    Updates doctor information including:
    - Name fields (first_name, middle_name, last_name)
    - Date of birth (dob)
    - Contact (phone_number, email)
    - Education and experience
    - Languages (array of language IDs)
    - Specializations (array of medical service IDs)
    - About (bio)
    - Profile image (profile_img) - file upload
    
    Args:
        Form fields: All doctor profile fields
        profile_img: Profile image file (optional)
    
    Returns:
        Updated doctor profile
    """
    from dateutil.parser import parse as date_parse
    
    # Check if user is doctor
    if current_user.role != "doctor":
        raise ForbiddenException(
            message="This endpoint is only for doctors",
            errors={"role": ["Only doctors can use this endpoint"]}
        )
    
    # Handle avatar file upload
    avatar_path = None
    if profile_img:
        avatar_path = await _save_avatar_file(profile_img, current_user.id, db)
    
    # Extract languages from form data - handle multiple formats
    languages_list = None
    specializations_list = None
    
    form_data = await request.form()
    languages_from_form = form_data.getlist("languages")
    specializations_from_form = form_data.getlist("specializations")
    
    logger.debug(f"Languages from form: {languages_from_form}")
    logger.debug(f"Languages param: {languages}")
    logger.debug(f"Specializations from form: {specializations_from_form}")
    logger.debug(f"Specializations param: {specializations}")
    
    # Parse languages
    if languages_from_form and len(languages_from_form) > 0:
        languages_list = _parse_uuid_list(languages_from_form, "languages")
    elif languages:
        languages_list = _parse_uuid_list(languages, "languages")
    
    # Parse specializations
    if specializations_from_form and len(specializations_from_form) > 0:
        specializations_list = _parse_uuid_list(specializations_from_form, "specializations")
    elif specializations:
        specializations_list = _parse_uuid_list(specializations, "specializations")
    
    logger.debug(f"Parsed languages_list: {languages_list}")
    logger.debug(f"Parsed specializations_list: {specializations_list}")
    
    # Parse date of birth
    try:
        date_of_birth = date_parse(dob).date()
    except (ValueError, TypeError) as e:
        logger.error(f"Date parse error: {e}")
        raise ValidationException(
            message="Invalid date format",
            errors={"dob": ["Date must be in YYYY-MM-DD format"]}
        )
    
    logger.debug(f"Parsed date_of_birth: {date_of_birth}")
    
    # Create DoctorProfileUpdate schema
    profile_data = DoctorProfileUpdate(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        dob=date_of_birth,
        phone_number=phone_number,
        email=email,
        education=education,
        years_of_experience=years_of_experience,
        languages=languages_list,
        specializations=specializations_list,
        about=about
    )
    
    logger.debug(f"Created profile_data: {profile_data}")
    
    # Update doctor profile
    updated_profile = profile_service.update_doctor_profile(
        user_id=current_user.id,
        profile_data=profile_data,
        current_user=current_user,
        avatar_path=avatar_path
    )
    
    # Create audit log
    _create_audit_log(
        db=db,
        user=current_user,
        action="DOCTOR_PROFILE_UPDATED",
        target_user_id=current_user.id,
        request=request,
        metadata={
            "self_update": True,
            "updated_fields": list(profile_data.model_dump(exclude_unset=True).keys())
        }
    )
    
    logger.info(f"Doctor {current_user.id} updated their profile")
    
    return DoctorProfileSingleResponse(
        success=True,
        message="Doctor profile updated successfully",
        data=updated_profile,
        errors=None
    )


@router.get(
    "/doctors/profile",
    response_model=DoctorProfileSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current doctor's profile",
    description="Retrieve the authenticated doctor's profile information."
)
async def get_current_doctor_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get current doctor's profile information
    
    **Doctor-only endpoint**
    
    Returns:
        Doctor profile information including:
        - Name fields
        - Date of birth and age
        - Contact (phone, email)
        - Education and experience
        - Languages (with details)
        - Specializations (with details)
        - About (bio)
        - Profile image URL
    """
    try:
        # Check if user is doctor
        if current_user.role != "doctor":
            raise ForbiddenException(
                message="This endpoint is only for doctors",
                errors={"role": ["Only doctors can use this endpoint"]}
            )
        
        # Get doctor profile
        doctor_profile = profile_service.get_doctor_profile(current_user.id)
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="DOCTOR_PROFILE_VIEWED",
            target_user_id=current_user.id,
            request=request,
            metadata={"self_view": True}
        )
        
        return DoctorProfileSingleResponse(
            success=True,
            message="Doctor profile retrieved successfully",
            data=doctor_profile,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve doctor profile: {str(e)}")
        raise


@router.get(
    "/doctors/{doctor_id}/profile",
    response_model=DoctorProfileSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get doctor profile by ID (Admin/Doctor)",
    description="Retrieve any doctor's profile information by doctor ID. Admin and doctors can view any doctor's profile."
)
async def get_doctor_profile_by_id(
    doctor_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get doctor profile by ID
    
    **Permissions:**
    - Admin: Can view any doctor's profile
    - Doctor: Can view any doctor's profile (read-only)
    - Other roles: Cannot access this endpoint
    
    Args:
        doctor_id: Doctor user ID to retrieve
    
    Returns:
        Doctor profile information including:
        - Name fields
        - Date of birth and age
        - Contact (phone, email)
        - Education and experience
        - Languages (with details)
        - Specializations (with details)
        - About (bio)
        - Profile image URL
    """
    try:
        # Check permissions - only admin and doctors can view doctor profiles
        if current_user.role not in ['super_admin', 'clinic_admin', 'doctor']:
            raise ForbiddenException(
                message="You do not have permission to view doctor profiles",
                errors={"permission": ["Only admins and doctors can view doctor profiles"]}
            )
        
        # Verify the user is actually a doctor
        user = db.query(User).filter(User.id == doctor_id, User.deleted_at.is_(None)).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"doctor_id": ["Doctor does not exist"]}
            )
        
        if user.role != "doctor":
            raise ValidationException(
                message="User is not a doctor",
                errors={"doctor_id": [f"User {doctor_id} is not a doctor (role: {user.role})"]}
            )
        
        # Get doctor profile
        doctor_profile = profile_service.get_doctor_profile(doctor_id)
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="DOCTOR_PROFILE_VIEWED",
            target_user_id=doctor_id,
            request=request,
            metadata={
                "viewer_role": current_user.role,
                "self_view": (current_user.id == doctor_id)
            }
        )
        
        return DoctorProfileSingleResponse(
            success=True,
            message="Doctor profile retrieved successfully",
            data=doctor_profile,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve doctor profile: {str(e)}")
        raise


# ============================================================================
# CONTACT DETAILS ENDPOINTS (Optional - for future expansion)
# ============================================================================


@router.post(
    "/profile/contacts",
    status_code=status.HTTP_201_CREATED,
    summary="Add contact details",
    description="Add new contact details to current user's profile",
    include_in_schema=False  # Hidden for now
)
async def add_contact_details(
    contact_data: ContactDetailsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Add contact details (for future expansion)
    Currently hidden from documentation
    """
    try:
        contact = profile_service.update_contact_details(
            user_id=current_user.id,
            contact_data=contact_data,
            current_user=current_user
        )
        
        return {
            "success": True,
            "message": "Contact details added successfully",
            "data": contact,
            "errors": None
        }
    
    except Exception as e:
        logger.error(f"Failed to add contact details: {str(e)}")
        raise
