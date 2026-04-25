"""
Profile Service
Business logic for user profile management
"""

from typing import Optional, Dict, Any
from datetime import date
from fastapi import Depends
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from loguru import logger

from app.core.database import get_db

from app.models.user import User
from app.models.profile import UserProfile, ContactDetail, user_languages, user_medical_services
from app.models.location import Country, State, City
from app.models.language import Language
from app.models.medical_service import MedicalService
from app.utils.phone import format_phone_number, parse_phone_number
from app.core.config import settings
from app.schemas.profile import (
    ProfileUpdate,
    ProfileCompletion,
    PatientPersonalInfoUpdate,
    PatientMedicalInfoUpdate,
    PatientProfileUpdate,
    DoctorProfileUpdate,
    ContactDetailsUpdate,
    ProfileResponse,
    ContactDetailsResponse,
    ProfileWithContactsResponse,
    PatientPersonalInfoResponse,
    PatientMedicalInfoResponse,
    DoctorProfileResponse
)
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException


class ProfileService:
    """
    Service for managing user profiles
    
    Responsibilities:
    - Create/update user profiles
    - Manage contact details
    - Enforce access control
    - Calculate computed fields (age)
    """
    
    def __init__(self, db: Session):
        """
        Initialize profile service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _calculate_age(self, date_of_birth: Optional[date]) -> Optional[int]:
        """
        Calculate age from date of birth
        
        Args:
            date_of_birth: Date of birth
        
        Returns:
            Age in years or None
        """
        if not date_of_birth:
            return None
        
        today = date.today()
        age = today.year - date_of_birth.year
        
        # Adjust if birthday hasn't occurred yet this year
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1
        
        return age
    
    def _get_avatar_url(self, avatar_path: Optional[str]) -> Optional[str]:
        """
        Generate full URL for avatar image
        
        Args:
            avatar_path: Relative path to avatar (e.g., "uploads/avatars/user_id.jpg")
        
        Returns:
            Full URL (e.g., "http://localhost:8000/uploads/avatars/user_id.jpg") or None
        """
        if not avatar_path:
            return None
        
        # Remove leading slash if present
        avatar_path = avatar_path.lstrip('/')
        
        # Construct full URL
        base_url = settings.BASE_URL.rstrip('/')
        return f"{base_url}/{avatar_path}"
    
    def _safe_get_medical_info(self, profile: UserProfile) -> Optional[Dict[str, Any]]:
        """
        Safely get medical_info from profile (handles missing column if migration not run)
        
        Args:
            profile: UserProfile model
        
        Returns:
            Medical info dict or None
        """
        try:
            medical_info = getattr(profile, 'medical_info', None)
            if medical_info is None:
                return None
            # If it's already a dict, return it
            if isinstance(medical_info, dict):
                return medical_info
            # If it's a string (JSON), try to parse it
            if isinstance(medical_info, str):
                import json
                try:
                    return json.loads(medical_info)
                except (json.JSONDecodeError, ValueError):
                    return None
            # For other types, return None
            return None
        except (AttributeError, KeyError, ValueError):
            return None
    
    def _format_profile_response(self, profile: UserProfile, primary_contact: ContactDetail = None, user: User = None) -> ProfileResponse:
        """
        Format profile for response
        
        Args:
            profile: UserProfile model
            primary_contact: Primary ContactDetail (optional, for address fields)
            user: User model (optional, for avatar)
        
        Returns:
            ProfileResponse
        """
        # Calculate age from date_of_birth
        age = self._calculate_age(profile.date_of_birth)
        
        # Get address fields from primary contact if available
        # Address fields are stored in contact_details, not user_profiles
        address_line_1 = None
        postal_code = None
        country_id = None
        state_id = None
        city_id = None
        country_name = None
        state_name = None
        city_name = None
        
        if primary_contact:
            address_line_1 = primary_contact.address_line_1
            postal_code = primary_contact.postal_code
            country_id = primary_contact.country_id
            state_id = primary_contact.state_id
            city_id = primary_contact.city_id
            
            # Get location names from relationships
            if primary_contact.country:
                country_name = primary_contact.country.name
            if primary_contact.state:
                state_name = primary_contact.state.name
            if primary_contact.city:
                city_name = primary_contact.city.name
        
        # Get avatar from profile first, then fallback to user
        avatar = None
        avatar_url = None
        if hasattr(profile, 'avatar') and profile.avatar:
            avatar = profile.avatar
        elif user and user.avatar:
            avatar = user.avatar
        elif hasattr(profile, 'user') and profile.user and profile.user.avatar:
            avatar = profile.user.avatar
        
        # Generate full URL for avatar
        if avatar:
            avatar_url = self._get_avatar_url(avatar)
        
        return ProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            title=profile.title if hasattr(profile, 'title') else None,
            first_name=profile.first_name,
            last_name=profile.last_name,
            middle_name=profile.middle_name,
            date_of_birth=profile.date_of_birth,
            age=age,
            gender=profile.gender,
            blood_type=getattr(profile, 'blood_type', None),
            marital_status=getattr(profile, 'marital_status', None),
            preferred_language_id=getattr(profile, 'preferred_language_id', None),
            medical_info=self._safe_get_medical_info(profile),
            address_line_1=address_line_1,  # From contact_details
            postal_code=postal_code,  # From contact_details
            country_id=country_id,  # From contact_details
            state_id=state_id,  # From contact_details
            city_id=city_id,  # From contact_details
            country_name=country_name,  # From relationships
            state_name=state_name,  # From relationships
            city_name=city_name,  # From relationships
            avatar=avatar_url,  # Full URL for avatar
            is_profile_complete=False,  # Will be set by get_profile
            hipaa_form_filled=getattr(profile, 'hipaa_form_filled', False),  # HIPAA form status
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    
    def _format_contact_response(self, contact: ContactDetail) -> ContactDetailsResponse:
        """
        Format contact detail for response
        
        Args:
            contact: ContactDetail model
        
        Returns:
            ContactDetailsResponse
        """
        # Get location names from relationships
        country_name = None
        state_name = None
        city_name = None
        if contact.country:
            country_name = contact.country.name
        if contact.state:
            state_name = contact.state.name
        if contact.city:
            city_name = contact.city.name
        
        return ContactDetailsResponse(
            id=contact.id,
            user_id=contact.user_id,
            contact_type=contact.contact_type,
            phone=contact.phone,
            phone_secondary=contact.phone_secondary,
            fax=contact.fax,
            email=contact.email,
            address_line_1=contact.address_line_1,
            address_line_2=contact.address_line_2,
            postal_code=contact.postal_code,
            country_id=contact.country_id,
            state_id=contact.state_id,
            city_id=contact.city_id,
            country_name=country_name,
            state_name=state_name,
            city_name=city_name,
            emergency_contact_name=contact.emergency_contact_name,
            emergency_contact_phone=contact.emergency_contact_phone,
            emergency_contact_relationship=contact.emergency_contact_relationship,
            notes=contact.notes,
            is_primary=contact.is_primary,
            created_at=contact.created_at,
            updated_at=contact.updated_at
        )
    
    def get_profile(self, user_id: UUID) -> ProfileWithContactsResponse:
        """
        Get user profile with contact details
        
        Args:
            user_id: User ID
        
        Returns:
            ProfileWithContactsResponse
        
        Raises:
            NotFoundException: If user or profile not found
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Get or create profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.deleted_at.is_(None)
        ).first()
        
        if not profile:
            # Create empty profile if doesn't exist
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        
        # Get contact details with location relationships eagerly loaded
        contacts = self.db.query(ContactDetail).options(
            joinedload(ContactDetail.country),
            joinedload(ContactDetail.state),
            joinedload(ContactDetail.city)
        ).filter(
            ContactDetail.user_id == user_id,
            ContactDetail.deleted_at.is_(None)
        ).all()
        
        # Get primary contact for address fields
        primary_contact = next((c for c in contacts if c.is_primary or c.contact_type == "primary"), None)
        if not primary_contact and contacts:
            # If no primary marked, use first contact
            primary_contact = contacts[0]
        
        # Ensure primary contact exists and has email/phone synced from users table
        if not primary_contact:
            # Create primary contact if doesn't exist
            primary_contact = ContactDetail(
                user_id=user_id,
                contact_type="primary",
                is_primary=True,
                email=user.email,  # Sync email from users table
                phone=user.phone if user.phone else None  # Sync phone from users table
            )
            self.db.add(primary_contact)
            self.db.commit()
            self.db.refresh(primary_contact)
            contacts.append(primary_contact)
        else:
            # Sync email from users table if missing in contact_details
            email_synced = False
            if not primary_contact.email and user.email:
                primary_contact.email = user.email
                email_synced = True
            # Sync phone from users table if missing in contact_details
            phone_synced = False
            if not primary_contact.phone and user.phone:
                primary_contact.phone = user.phone
                phone_synced = True
            # Commit if any sync happened
            if email_synced or phone_synced:
                self.db.commit()
                self.db.refresh(primary_contact)
        
        # Check if profile is complete
        # Staff users always have complete profiles
        # For other roles: first_name, gender, date_of_birth are required
        if user.role == 'staff':
            is_profile_complete = True
        else:
            is_profile_complete = bool(
                profile.first_name and 
                profile.gender and 
                profile.date_of_birth
            )
        
        # Format response
        profile_response = self._format_profile_response(profile, primary_contact, user)
        profile_response.is_profile_complete = is_profile_complete
        contact_responses = [self._format_contact_response(c) for c in contacts]
        
        return ProfileWithContactsResponse(
            profile=profile_response,
            contacts=contact_responses,
            is_profile_complete=is_profile_complete
        )
    
    def _format_profile_with_contacts_response(
        self,
        profile: UserProfile,
        primary_contact: ContactDetail = None,
        contacts: list = None,
        user: User = None
    ) -> ProfileWithContactsResponse:
        """
        Format profile with contacts for response
        
        Args:
            profile: UserProfile model
            primary_contact: Primary ContactDetail
            contacts: List of ContactDetail models
            user: User model (for avatar)
        
        Returns:
            ProfileWithContactsResponse
        """
        # Check if profile is complete
        is_profile_complete = bool(
            profile.first_name and 
            profile.gender and 
            profile.date_of_birth
        )
        
        # Format profile response
        profile_response = self._format_profile_response(profile, primary_contact, user)
        profile_response.is_profile_complete = is_profile_complete
        
        # Format contact responses
        contact_responses = [self._format_contact_response(c) for c in (contacts or [])]
        
        return ProfileWithContactsResponse(
            profile=profile_response,
            contacts=contact_responses,
            is_profile_complete=is_profile_complete
        )
    
    def update_profile(
        self,
        user_id: UUID,
        profile_data: ProfileUpdate,
        current_user: User,
        skip_permission_check: bool = False
    ) -> ProfileWithContactsResponse:
        """
        Update user profile
        
        Args:
            user_id: User ID to update
            profile_data: Profile update data
            current_user: Current authenticated user
            skip_permission_check: Skip permission check (used internally for self-updates)
        
        Returns:
            ProfileWithContactsResponse
        
        Raises:
            NotFoundException: If user or profile not found
            ForbiddenException: If user doesn't have permission
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Check permissions (skip for internal self-update calls like complete_profile)
        if not skip_permission_check:
            # Patient/Doctor can only update their own profile
            # Admin can update any profile
            if current_user.role not in ['admin', 'clinic_admin', 'super_admin']:
                # Compare as strings to handle UUID vs string type mismatch
                if str(current_user.id) != str(user_id):
                    raise ForbiddenException(
                        message="You do not have permission to update this profile",
                        errors={"permission": ["Insufficient permissions"]}
                    )
        
        # Get or create profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.deleted_at.is_(None)
        ).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        # Update profile fields (only update provided fields)
        update_data = profile_data.model_dump(exclude_unset=True)
        
        # Separate fields: profile fields vs contact fields
        # Address fields and mobile_number go to contact_details
        # Email is NOT editable - it's synced from users.email automatically
        address_fields = ['address_line_1', 'postal_code']
        location_fields = ['country_id', 'state_id', 'city_id']
        mobile_number = update_data.pop('mobile_number', None)
        
        # Remove email if somehow provided (email is not editable via profile update)
        update_data.pop('email', None)
        
        # Extract address fields to save to contact_details
        address_data = {}
        for field in address_fields:
            if field in update_data:
                address_data[field] = update_data.pop(field)
        
        # Extract location UUID fields
        location_data = {}
        for field in location_fields:
            if field in update_data:
                location_data[field] = update_data.pop(field)
        
        # Get or create primary contact detail with location relationships eagerly loaded
        primary_contact = self.db.query(ContactDetail).options(
            joinedload(ContactDetail.country),
            joinedload(ContactDetail.state),
            joinedload(ContactDetail.city)
        ).filter(
            ContactDetail.user_id == user_id,
            ContactDetail.contact_type == "primary",
            ContactDetail.deleted_at.is_(None)
        ).first()
        
        if not primary_contact:
            # Create new primary contact
            primary_contact = ContactDetail(
                user_id=user_id,
                contact_type="primary",
                is_primary=True,
                email=user.email,  # Sync email from users table
                phone=user.phone if user.phone else None  # Sync phone from users table
            )
            self.db.add(primary_contact)
        else:
            # Always sync email from users table to contact_details (email is not editable)
            primary_contact.email = user.email
            # Sync phone from users table if contact_details.phone is missing
            if not primary_contact.phone and user.phone:
                primary_contact.phone = user.phone
        
        # Update mobile_number -> User.phone and ContactDetail.phone
        # Format phone number if provided (format: +1-721-555-6781)
        if mobile_number is not None:
            # If mobile_number already has country code (starts with +), parse and format it
            if mobile_number.strip().startswith('+'):
                try:
                    country_code, phone_num = parse_phone_number(mobile_number)
                    formatted_phone = format_phone_number(country_code, phone_num)
                except Exception as e:
                    logger.warning(f"Failed to parse/format phone number {mobile_number}: {e}, using as-is")
                    formatted_phone = mobile_number
            # If country_id is provided, use it to format the phone number
            elif location_data.get('country_id'):
                country = self.db.query(Country).filter(
                    Country.id == location_data['country_id'],
                    Country.deleted_at.is_(None)
                ).first()
                if country:
                    phone_clean = mobile_number.strip().lstrip('+')
                    formatted_phone = format_phone_number(str(country.phonecode), phone_clean)
                else:
                    formatted_phone = mobile_number
            else:
                # No country code available, use as-is
                formatted_phone = mobile_number
            
            user.phone = formatted_phone
            primary_contact.phone = formatted_phone
        
        # Update address fields in primary contact
        if address_data:
            for field, value in address_data.items():
                if hasattr(primary_contact, field):
                    setattr(primary_contact, field, value)
        
        # Update location UUID fields in primary contact
        if location_data:
            for field, value in location_data.items():
                if hasattr(primary_contact, field):
                    setattr(primary_contact, field, value)
        
        # Update profile fields (only fields that exist in UserProfile model)
        # These are: title, first_name, middle_name, last_name, gender, date_of_birth, bio, occupation, company, website
        # NOTE: Doctor-specific fields (education, years_of_experience) should NOT be updated here
        # They should only be updated via the doctor-specific endpoint (update_doctor_profile)
        doctor_specific_fields = ['education', 'years_of_experience']  # Exclude these from general profile update
        name_updated = False
        for field, value in update_data.items():
            # Skip doctor-specific fields - they should only be updated via doctor endpoint
            if field in doctor_specific_fields:
                logger.warning(f"Skipping doctor-specific field '{field}' in general profile update. Use doctor endpoint instead.")
                continue
            if hasattr(profile, field):
                setattr(profile, field, value)
                # Track if name fields are being updated
                if field in ['first_name', 'middle_name', 'last_name']:
                    name_updated = True
            else:
                # Log warning for fields not in model
                logger.warning(f"Field '{field}' not found in UserProfile model, skipping update")
        
        # Update users.name if any name field was updated
        if name_updated:
            # Construct full name from profile fields
            name_parts = []
            if profile.first_name:
                name_parts.append(profile.first_name)
            if profile.middle_name:
                name_parts.append(profile.middle_name)
            if profile.last_name:
                name_parts.append(profile.last_name)
            
            # Update users.name with constructed full name
            if name_parts:
                user.name = ' '.join(name_parts)
            else:
                # Fallback: use existing name if all name fields are empty
                logger.warning(f"All name fields are empty for user {user_id}, keeping existing name")
        
        # Commit changes
        self.db.commit()
        self.db.refresh(profile)
        
        logger.info(
            f"Profile updated for user {user_id} by {current_user.id}"
        )
        
        # Return updated profile with contacts
        return self.get_profile(user_id)
    
    def complete_profile(
        self,
        user_id: UUID,
        profile_data: ProfileCompletion,
        current_user: User
    ) -> ProfileWithContactsResponse:
        """
        Complete initial profile setup for admin-created users
        
        Required fields: first_name, date_of_birth, gender
        Optional fields: title, middle_name, last_name, country_id, mobile_number, address fields
        
        Args:
            user_id: User ID
            profile_data: Profile completion data
            current_user: Current user (must be the same as user_id)
        
        Returns:
            Completed profile with contact details
        """
        # Convert ProfileCompletion to ProfileUpdate for processing
        # Note: Permission check not needed here - endpoint already ensures user can only complete their own profile
        update_dict = profile_data.model_dump(exclude_unset=True)
        profile_update = ProfileUpdate(**update_dict)
        
        # Use update_profile logic with skip_permission_check=True (endpoint already validates self-update)
        return self.update_profile(user_id, profile_update, current_user, skip_permission_check=True)
    
    def update_patient_profile(
        self,
        user_id: UUID,
        profile_data: PatientProfileUpdate,
        current_user: User
    ) -> ProfileWithContactsResponse:
        """
        Update patient profile with medical information
        
        Args:
            user_id: User ID
            profile_data: Patient profile update data (includes medical info)
            current_user: Current user
        
        Returns:
            Updated profile with contact details
        """
        # Check permissions
        if current_user.role not in ['admin', 'clinic_admin']:
            if current_user.id != user_id:
                raise ForbiddenException(
                    message="You can only update your own profile",
                    errors={"permission": ["Insufficient permissions"]}
                )
        
        user = self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Get or create profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.deleted_at.is_(None)
        ).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        # Update profile fields
        update_data = profile_data.model_dump(exclude_unset=True)
        
        # Extract medical info
        medical_info = update_data.pop('medical_info', None)
        
        # Extract contact numbers
        contact_number = update_data.pop('contact_number', None)
        emergency_contact_number = update_data.pop('emergency_contact_number', None)
        family_contact_number = update_data.pop('family_contact_number', None)
        
        # Extract address and location fields
        address_fields = ['address_line_1', 'postal_code']
        location_fields = ['country_id', 'state_id', 'city_id']
        address_data = {}
        location_data = {}
        
        for field in address_fields:
            if field in update_data:
                address_data[field] = update_data.pop(field)
        
        for field in location_fields:
            if field in update_data:
                location_data[field] = update_data.pop(field)
        
        # Update medical/demographic fields
        if 'blood_type' in update_data:
            profile.blood_type = update_data.pop('blood_type')
        if 'marital_status' in update_data:
            profile.marital_status = update_data.pop('marital_status')
        if 'preferred_language_id' in update_data:
            profile.preferred_language_id = update_data.pop('preferred_language_id')
        if medical_info is not None:
            # Store medical info as JSONB
            profile.medical_info = medical_info.model_dump() if hasattr(medical_info, 'model_dump') else medical_info
        
        # Update other profile fields
        for field, value in update_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        # Update users.name from name fields
        name_parts = []
        if profile.first_name:
            name_parts.append(profile.first_name)
        if profile.middle_name:
            name_parts.append(profile.middle_name)
        if profile.last_name:
            name_parts.append(profile.last_name)
        if name_parts:
            user.name = ' '.join(name_parts)
        
        # Get or create primary contact
        primary_contact = self.db.query(ContactDetail).options(
            joinedload(ContactDetail.country),
            joinedload(ContactDetail.state),
            joinedload(ContactDetail.city)
        ).filter(
            ContactDetail.user_id == user_id,
            ContactDetail.contact_type == "primary",
            ContactDetail.deleted_at.is_(None)
        ).first()
        
        if not primary_contact:
            primary_contact = ContactDetail(
                user_id=user_id,
                contact_type="primary",
                is_primary=True,
                email=user.email,
                phone=user.phone if user.phone else None
            )
            self.db.add(primary_contact)
        else:
            primary_contact.email = user.email
        
        # Update contact numbers
        if contact_number is not None:
            user.phone = contact_number
            primary_contact.phone = contact_number
        if emergency_contact_number is not None:
            primary_contact.emergency_contact_phone = emergency_contact_number
        if family_contact_number is not None:
            primary_contact.family_contact_phone = family_contact_number
        
        # Update address and location
        if address_data:
            for field, value in address_data.items():
                if hasattr(primary_contact, field):
                    setattr(primary_contact, field, value)
        
        if location_data:
            for field, value in location_data.items():
                if hasattr(primary_contact, field):
                    setattr(primary_contact, field, value)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(profile)
        self.db.refresh(primary_contact)
        
        # Get all contacts
        contacts = self.db.query(ContactDetail).filter(
            ContactDetail.user_id == user_id,
            ContactDetail.deleted_at.is_(None)
        ).all()
        
        return self._format_profile_with_contacts_response(profile, primary_contact, contacts, user)
    
    def update_patient_personal_info(
        self,
        user_id: UUID,
        profile_data: PatientPersonalInfoUpdate,
        current_user: User
    ) -> ProfileWithContactsResponse:
        """
        Update patient personal information only
        
        Args:
            user_id: User ID
            profile_data: Patient personal information update data
            current_user: Current user
        
        Returns:
            Updated profile with contact details
        """
        # Check permissions
        if current_user.role not in ['admin', 'clinic_admin']:
            if current_user.id != user_id:
                raise ForbiddenException(
                    message="You can only update your own profile",
                    errors={"permission": ["Insufficient permissions"]}
                )
        
        user = self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Get or create profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.deleted_at.is_(None)
        ).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        # Update profile fields
        update_data = profile_data.model_dump(exclude_unset=True)
        
        # Extract contact numbers
        contact_number = update_data.pop('contact_number', None)
        emergency_contact_number = update_data.pop('emergency_contact_number', None)
        family_contact_number = update_data.pop('family_contact_number', None)
        
        # Extract avatar (stored in users table, not user_profiles)
        avatar = update_data.pop('avatar', None)
        
        # Extract address and location fields
        address_fields = ['address_line_1', 'postal_code']
        location_fields = ['country_id', 'state_id', 'city_id']
        address_data = {}
        location_data = {}
        
        for field in address_fields:
            if field in update_data:
                address_data[field] = update_data.pop(field)
        
        for field in location_fields:
            if field in update_data:
                location_data[field] = update_data.pop(field)
        
        # Update medical/demographic fields
        if 'blood_type' in update_data:
            profile.blood_type = update_data.pop('blood_type')
        if 'marital_status' in update_data:
            profile.marital_status = update_data.pop('marital_status')
        if 'preferred_language_id' in update_data:
            profile.preferred_language_id = update_data.pop('preferred_language_id')
        
        # Update other profile fields
        for field, value in update_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        # Update avatar in both users and user_profiles tables
        if avatar is not None:
            user.avatar = avatar
            profile.avatar = avatar
        
        # Update users.name from name fields
        name_parts = []
        if profile.first_name:
            name_parts.append(profile.first_name)
        if profile.middle_name:
            name_parts.append(profile.middle_name)
        if profile.last_name:
            name_parts.append(profile.last_name)
        if name_parts:
            user.name = ' '.join(name_parts)
        
        # Get or create primary contact
        primary_contact = self.db.query(ContactDetail).options(
            joinedload(ContactDetail.country),
            joinedload(ContactDetail.state),
            joinedload(ContactDetail.city)
        ).filter(
            ContactDetail.user_id == user_id,
            ContactDetail.contact_type == "primary",
            ContactDetail.deleted_at.is_(None)
        ).first()
        
        if not primary_contact:
            primary_contact = ContactDetail(
                user_id=user_id,
                contact_type="primary",
                is_primary=True,
                email=user.email,
                phone=user.phone if user.phone else None
            )
            self.db.add(primary_contact)
        else:
            primary_contact.email = user.email
        
        # Update contact numbers
        if contact_number is not None:
            user.phone = contact_number
            primary_contact.phone = contact_number
        if emergency_contact_number is not None:
            primary_contact.emergency_contact_phone = emergency_contact_number
        if family_contact_number is not None:
            primary_contact.family_contact_phone = family_contact_number
        
        # Update address and location
        if address_data:
            for field, value in address_data.items():
                if hasattr(primary_contact, field):
                    setattr(primary_contact, field, value)
        
        if location_data:
            for field, value in location_data.items():
                if hasattr(primary_contact, field):
                    setattr(primary_contact, field, value)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(profile)
        self.db.refresh(primary_contact)
        
        # Get all contacts
        contacts = self.db.query(ContactDetail).filter(
            ContactDetail.user_id == user_id,
            ContactDetail.deleted_at.is_(None)
        ).all()
        
        return self._format_profile_with_contacts_response(profile, primary_contact, contacts, user)
    
    def update_patient_medical_info(
        self,
        user_id: UUID,
        profile_data: PatientMedicalInfoUpdate,
        current_user: User
    ) -> ProfileWithContactsResponse:
        """
        Update patient medical information only
        
        Args:
            user_id: User ID
            profile_data: Patient medical information update data
            current_user: Current user
        
        Returns:
            Updated profile with contact details
        """
        # Check permissions
        if current_user.role not in ['admin', 'clinic_admin']:
            if current_user.id != user_id:
                raise ForbiddenException(
                    message="You can only update your own profile",
                    errors={"permission": ["Insufficient permissions"]}
                )
        
        user = self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Get or create profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.deleted_at.is_(None)
        ).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        # Update medical info
        try:
            medical_info = getattr(profile_data, 'medical_info', None)
            if medical_info is not None:
                # Store medical info as JSONB
                if hasattr(medical_info, 'model_dump'):
                    medical_info_dict = medical_info.model_dump(exclude_unset=True, exclude_none=True)
                    # Ensure medical_info column exists before setting
                    if hasattr(profile, 'medical_info'):
                        profile.medical_info = medical_info_dict
                    else:
                        logger.warning(f"UserProfile model does not have medical_info attribute for user {user_id}")
                elif isinstance(medical_info, dict):
                    if hasattr(profile, 'medical_info'):
                        profile.medical_info = medical_info
                    else:
                        logger.warning(f"UserProfile model does not have medical_info attribute for user {user_id}")
                else:
                    logger.warning(f"Unexpected medical_info type: {type(medical_info)} for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating medical_info for user {user_id}: {e}", exc_info=True)
            raise
        
        # Commit changes
        self.db.commit()
        self.db.refresh(profile)
        
        # Get primary contact and all contacts
        primary_contact = self.db.query(ContactDetail).options(
            joinedload(ContactDetail.country),
            joinedload(ContactDetail.state),
            joinedload(ContactDetail.city)
        ).filter(
            ContactDetail.user_id == user_id,
            ContactDetail.contact_type == "primary",
            ContactDetail.deleted_at.is_(None)
        ).first()
        
        # Create primary contact if it doesn't exist
        if not primary_contact:
            primary_contact = ContactDetail(
                user_id=user_id,
                contact_type="primary",
                is_primary=True,
                email=user.email,
                phone=user.phone if user.phone else None
            )
            self.db.add(primary_contact)
            self.db.commit()
            self.db.refresh(primary_contact)
        
        contacts = self.db.query(ContactDetail).filter(
            ContactDetail.user_id == user_id,
            ContactDetail.deleted_at.is_(None)
        ).all()
        
        return self._format_profile_with_contacts_response(profile, primary_contact, contacts, user)
    
    def get_patient_personal_info(self, user_id: UUID) -> PatientPersonalInfoResponse:
        """
        Get patient personal information only
        
        Args:
            user_id: User ID
        
        Returns:
            PatientPersonalInfoResponse
        
        Raises:
            NotFoundException: If user not found
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Get profile (or create empty one for admin-created users)
        profile = self.db.query(UserProfile).options(
            joinedload(UserProfile.preferred_language)
        ).filter(
            UserProfile.user_id == user_id,
            UserProfile.deleted_at.is_(None)
        ).first()
        
        if not profile:
            # Create empty profile for admin-created users
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            logger.info(f"Created empty profile for admin-created user: {user_id}")
        
        # Get primary contact with location relationships
        primary_contact = self.db.query(ContactDetail).options(
            joinedload(ContactDetail.country),
            joinedload(ContactDetail.state),
            joinedload(ContactDetail.city)
        ).filter(
            ContactDetail.user_id == user_id,
            ContactDetail.contact_type == "primary",
            ContactDetail.deleted_at.is_(None)
        ).first()
        
        # Get avatar URL
        avatar_url = None
        if hasattr(profile, 'avatar') and profile.avatar:
            avatar_url = self._get_avatar_url(profile.avatar)
        elif user.avatar:
            avatar_url = self._get_avatar_url(user.avatar)
        
        # Calculate age
        age = self._calculate_age(profile.date_of_birth)
        
        # Get preferred language name
        preferred_language_name = None
        if profile.preferred_language:
            preferred_language_name = profile.preferred_language.language_name
        
        return PatientPersonalInfoResponse(
            id=profile.id,
            user_id=profile.user_id,
            email=user.email,
            title=profile.title,
            first_name=profile.first_name,
            middle_name=profile.middle_name,
            last_name=profile.last_name,
            date_of_birth=profile.date_of_birth,
            age=age,
            gender=profile.gender,
            contact_number=primary_contact.phone if primary_contact else None,
            emergency_contact_number=primary_contact.emergency_contact_phone if primary_contact else None,
            family_contact_number=primary_contact.family_contact_phone if primary_contact else None,
            blood_type=getattr(profile, 'blood_type', None),
            occupation=getattr(profile, 'occupation', None),
            marital_status=getattr(profile, 'marital_status', None),
            preferred_language_id=getattr(profile, 'preferred_language_id', None),
            preferred_language_name=preferred_language_name,
            country_id=primary_contact.country_id if primary_contact else None,
            country_name=primary_contact.country.name if primary_contact and primary_contact.country else None,
            state_id=primary_contact.state_id if primary_contact else None,
            state_name=primary_contact.state.name if primary_contact and primary_contact.state else None,
            city_id=primary_contact.city_id if primary_contact else None,
            city_name=primary_contact.city.name if primary_contact and primary_contact.city else None,
            address_line_1=primary_contact.address_line_1 if primary_contact else None,
            postal_code=primary_contact.postal_code if primary_contact else None,
            avatar=avatar_url,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    
    def get_patient_medical_info(self, user_id: UUID) -> PatientMedicalInfoResponse:
        """
        Get patient medical information only
        
        Args:
            user_id: User ID
        
        Returns:
            PatientMedicalInfoResponse
        
        Raises:
            NotFoundException: If user not found
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Get profile (or create empty one for admin-created users)
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.deleted_at.is_(None)
        ).first()
        
        if not profile:
            # Create empty profile for admin-created users
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            logger.info(f"Created empty profile for admin-created user: {user_id}")
        
        # Get medical info
        medical_info = self._safe_get_medical_info(profile)
        
        return PatientMedicalInfoResponse(
            id=profile.id,
            user_id=profile.user_id,
            medical_info=medical_info,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    
    def update_contact_details(
        self,
        user_id: UUID,
        contact_data: ContactDetailsUpdate,
        current_user: User,
        contact_id: Optional[UUID] = None
    ) -> ContactDetailsResponse:
        """
        Update or create contact details
        
        Args:
            user_id: User ID
            contact_data: Contact update data
            current_user: Current authenticated user
            contact_id: Contact ID to update (if None, creates new)
        
        Returns:
            ContactDetailsResponse
        
        Raises:
            NotFoundException: If user or contact not found
            ForbiddenException: If user doesn't have permission
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        # Check permissions
        if current_user.role not in ['admin', 'clinic_admin']:
            if current_user.id != user_id:
                raise ForbiddenException(
                    message="You do not have permission to update contact details",
                    errors={"permission": ["Insufficient permissions"]}
                )
        
        # Get or create contact
        if contact_id:
            contact = self.db.query(ContactDetail).filter(
                ContactDetail.id == contact_id,
                ContactDetail.user_id == user_id,
                ContactDetail.deleted_at.is_(None)
            ).first()
            
            if not contact:
                raise NotFoundException(
                    message="Contact detail not found",
                    errors={"contact_id": ["Contact does not exist"]}
                )
        else:
            # Create new contact (default to primary)
            contact = ContactDetail(
                user_id=user_id,
                contact_type=contact_data.contact_type or 'primary'
            )
            self.db.add(contact)
        
        # Update contact fields
        update_data = contact_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(contact, field):
                setattr(contact, field, value)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(contact)
        
        logger.info(
            f"Contact details updated for user {user_id} by {current_user.id}"
        )
        
        return self._format_contact_response(contact)
    
    def can_update_profile(self, user_id: UUID, current_user: User) -> bool:
        """
        Check if current user can update profile
        
        Args:
            user_id: Target user ID
            current_user: Current authenticated user
        
        Returns:
            True if user can update profile
        """
        # Admin can update any profile
        if current_user.role in ['admin', 'clinic_admin']:
            return True
        
        # User can update their own profile
        if current_user.id == user_id:
            return True
        
        return False
    
    def can_view_profile(self, user_id: UUID, current_user: User) -> bool:
        """
        Check if current user can view profile
        
        Args:
            user_id: Target user ID
            current_user: Current authenticated user
        
        Returns:
            True if user can view profile
        """
        # Admin and doctors can view any profile
        if current_user.role in ['admin', 'clinic_admin', 'doctor']:
            return True
        
        # User can view their own profile
        if current_user.id == user_id:
            return True
        
        return False
    
    def update_doctor_profile(
        self,
        user_id: UUID,
        profile_data: DoctorProfileUpdate,
        current_user: User,
        avatar_path: Optional[str] = None
    ) -> DoctorProfileResponse:
        """
        Update doctor profile information
        
        Args:
            user_id: User ID
            profile_data: Doctor profile update data
            current_user: Current user
            avatar_path: Path to uploaded avatar file
        
        Returns:
            Updated doctor profile response
        
        Raises:
            NotFoundException: If user not found
            ForbiddenException: If user doesn't have permission
        """
        logger.debug(f"update_doctor_profile called with user_id={user_id}, avatar_path={avatar_path}")
        logger.debug(f"profile_data: {profile_data}")
        
        # Check permissions
        if current_user.role not in ['super_admin', 'clinic_admin']:
            if current_user.id != user_id:
                raise ForbiddenException(
                    message="You can only update your own profile",
                    errors={"permission": ["Insufficient permissions"]}
                )
        
        # Verify user is a doctor
        user = self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        if user.role != "doctor":
            raise ForbiddenException(
                message="This endpoint is only for doctors",
                errors={"role": ["User is not a doctor"]}
            )
        
        # Get or create profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.deleted_at.is_(None)
        ).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        # Update profile fields from profile_data
        update_data = profile_data.model_dump(exclude_unset=True, exclude={'languages', 'specializations', 'profile_img'})
        
        # Handle date_of_birth (from 'dob' alias)
        if 'date_of_birth' in update_data:
            profile.date_of_birth = update_data.pop('date_of_birth')
        
        # Update basic profile fields
        for field, value in update_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        # Update education and years_of_experience
        if hasattr(profile_data, 'education'):
            profile.education = profile_data.education
        if hasattr(profile_data, 'years_of_experience'):
            profile.years_of_experience = profile_data.years_of_experience
        
        # Update bio (about field)
        if hasattr(profile_data, 'about'):
            profile.bio = profile_data.about
        
        # Update avatar
        if avatar_path:
            user.avatar = avatar_path
            profile.avatar = avatar_path
        
        # Update users.name from name fields
        name_parts = []
        if profile.first_name:
            name_parts.append(profile.first_name)
        if profile.middle_name:
            name_parts.append(profile.middle_name)
        if profile.last_name:
            name_parts.append(profile.last_name)
        if name_parts:
            user.name = ' '.join(name_parts)
        
        # Update phone and email
        if hasattr(profile_data, 'phone_number') and profile_data.phone_number is not None:
            user.phone = profile_data.phone_number
        if hasattr(profile_data, 'email') and profile_data.email is not None:
            # Check if email is unique
            existing_user = self.db.query(User).filter(
                User.email == profile_data.email.lower(),
                User.id != user_id,
                User.deleted_at.is_(None)
            ).first()
            if existing_user:
                raise ConflictException(
                    message="Email already exists",
                    errors={"email": ["This email is already registered"]}
                )
            user.email = profile_data.email.lower()
        
        # Update languages (many-to-many)
        if hasattr(profile_data, 'languages') and profile_data.languages is not None:
            # Clear existing languages
            self.db.execute(
                user_languages.delete().where(user_languages.c.user_id == user_id)
            )
            # Add new languages
            for language_id in profile_data.languages:
                # Verify language exists (Language uses Base, not BaseModel, so no deleted_at)
                language = self.db.query(Language).filter(
                    Language.id == language_id
                ).first()
                if language:
                    self.db.execute(
                        user_languages.insert().values(
                            user_id=user_id,
                            language_id=language_id
                        )
                    )
        
        # Update specializations (many-to-many)
        if hasattr(profile_data, 'specializations') and profile_data.specializations is not None:
            # Clear existing specializations
            self.db.execute(
                user_medical_services.delete().where(user_medical_services.c.user_id == user_id)
            )
            # Add new specializations
            for service_id in profile_data.specializations:
                # Verify medical service exists
                service = self.db.query(MedicalService).filter(
                    MedicalService.id == service_id
                ).first()
                if service:
                    self.db.execute(
                        user_medical_services.insert().values(
                            user_id=user_id,
                            medical_service_id=service_id
                        )
                    )
        
        # Commit changes
        self.db.commit()
        self.db.refresh(profile)
        self.db.refresh(user)
        
        # Reload relationships
        self.db.refresh(user)
        
        # Get languages with details
        languages_list = []
        if user.languages:
            for lang in user.languages:
                languages_list.append({
                    "id": str(lang.id),
                    "language_name": lang.language_name,
                    "language_code": lang.language_code
                })
        
        # Get specializations with details
        specializations_list = []
        if user.medical_services:
            for service in user.medical_services:
                specializations_list.append({
                    "id": str(service.id),
                    "name": service.name,
                    "image": service.image
                })
        
        # Calculate age
        age = self._calculate_age(profile.date_of_birth)
        
        # Get avatar URL
        avatar_url = self._get_avatar_url(profile.avatar) if profile.avatar else self._get_avatar_url(user.avatar)
        
        return DoctorProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            first_name=profile.first_name,
            middle_name=profile.middle_name,
            last_name=profile.last_name,
            date_of_birth=profile.date_of_birth,
            age=age,
            phone_number=user.phone,
            email=user.email,
            education=profile.education,
            years_of_experience=profile.years_of_experience,
            languages=languages_list if languages_list else None,
            specializations=specializations_list if specializations_list else None,
            about=profile.bio,
            profile_img=avatar_url,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    
    def get_doctor_profile(self, user_id: UUID) -> DoctorProfileResponse:
        """
        Get doctor profile information
        
        Args:
            user_id: User ID
        
        Returns:
            DoctorProfileResponse
        
        Raises:
            NotFoundException: If user or profile not found
        """
        # Get user with relationships
        user = self.db.query(User).options(
            joinedload(User.languages),
            joinedload(User.medical_services)
        ).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user_id": ["User does not exist"]}
            )
        
        if user.role != "doctor":
            raise ForbiddenException(
                message="This endpoint is only for doctors",
                errors={"role": ["User is not a doctor"]}
            )
        
        # Get profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.deleted_at.is_(None)
        ).first()
        
        if not profile:
            raise NotFoundException(
                message="Profile not found",
                errors={"profile": ["User profile does not exist"]}
            )
        
        # Get languages with details
        languages_list = []
        if user.languages:
            for lang in user.languages:
                languages_list.append({
                    "id": str(lang.id),
                    "language_name": lang.language_name,
                    "language_code": lang.language_code
                })
        
        # Get specializations with details
        specializations_list = []
        if user.medical_services:
            for service in user.medical_services:
                specializations_list.append({
                    "id": str(service.id),
                    "name": service.name,
                    "image": service.image
                })
        
        # Calculate age
        age = self._calculate_age(profile.date_of_birth)
        
        # Get avatar URL
        avatar_url = self._get_avatar_url(profile.avatar) if profile.avatar else self._get_avatar_url(user.avatar)
        
        return DoctorProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            first_name=profile.first_name,
            middle_name=profile.middle_name,
            last_name=profile.last_name,
            date_of_birth=profile.date_of_birth,
            age=age,
            phone_number=user.phone,
            email=user.email,
            education=profile.education,
            years_of_experience=profile.years_of_experience,
            languages=languages_list if languages_list else None,
            specializations=specializations_list if specializations_list else None,
            about=profile.bio,
            profile_img=avatar_url,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )


def get_profile_service(db: Session = Depends(get_db)) -> ProfileService:
    """
    Get profile service instance (for dependency injection)
    
    Args:
        db: Database session
    
    Returns:
        ProfileService instance
    """
    return ProfileService(db)
