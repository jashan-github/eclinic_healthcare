"""
Pydantic schemas for user profiles
Laravel-compatible request/response schemas
"""

from typing import Optional, Union, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, validator, field_validator, model_validator, EmailStr, ConfigDict
from uuid import UUID
from datetime import date as date_type


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class ProfileCompletion(BaseModel):
    """
    Schema for initial profile completion
    Used when admin-created users first login and need to complete their profile
    
    Required fields: first_name, date_of_birth, gender
    Optional fields: title, middle_name, last_name, country_id, mobile_number, address fields
    
    Matches the "Create Profile" screen (3rd screenshot) - common for patient and doctor
    """
    # Title (optional)
    title: Optional[str] = Field(None, max_length=10, description="Title (Dr, Mr, Mrs, Ms, etc.)", examples=["Dr"])
    
    # Name fields
    first_name: str = Field(..., min_length=1, max_length=255, description="First name (required)", examples=["John"])
    middle_name: Optional[str] = Field(None, max_length=255, description="Middle name (optional)", examples=["Michael"])
    last_name: Optional[str] = Field(None, max_length=255, description="Last name (optional)", examples=["Doe"])
    
    # Date of birth (required)
    date_of_birth: date = Field(..., description="Date of birth (required)", examples=["1990-01-15"])
    
    # Gender (required)
    gender: str = Field(..., max_length=20, description="Gender (required)", examples=["male"])
    
    # Location and contact (optional for completion)
    country_id: Optional[UUID] = Field(None, description="Country ID (UUID)", examples=["f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"])
    mobile_number: Optional[str] = Field(None, max_length=10, description="10-digit mobile number without country code", examples=["7215442275"])
    address_line_1: Optional[str] = Field(None, max_length=255, description="Street Address", examples=["123 Main Street"])
    city_id: Optional[UUID] = Field(None, description="City ID (UUID)", examples=["a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"])
    state_id: Optional[UUID] = Field(None, description="State ID (UUID)", examples=["b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7"])
    postal_code: Optional[str] = Field(None, max_length=20, description="Zip Code", examples=["10001"])
    
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
    
    @classmethod
    def model_json_schema(cls, **kwargs):
        """Override to ensure example is in correct order matching Figma design"""
        from collections import OrderedDict
        schema = super().model_json_schema(**kwargs)
        example = OrderedDict([
            ("title", "Dr"),
            ("first_name", "John"),
            ("middle_name", "Michael"),
            ("last_name", "Doe"),
            ("date_of_birth", "1990-01-15"),
            ("gender", "male"),
            ("country_id", "f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"),
            ("mobile_number", "7215442275"),
            ("address_line_1", "123 Main Street"),
            ("city_id", "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"),
            ("state_id", "b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7"),
            ("postal_code", "10001")
        ])
        schema['example'] = dict(example)
        return schema


class ProfileUpdate(BaseModel):
    """
    Schema for updating user profile
    
    Matches Figma design for profile completion form.
    
    Required fields: first_name, last_name, gender, date_of_birth
    Optional fields: title, middle_name, country_id, mobile_number, address_line_1, city_id, state_id, postal_code
    
    Field order matches Figma design exactly.
    """
    
    # Order matches Figma design exactly
    # 1. Title (optional)
    title: Optional[str] = Field(None, max_length=10, description="Title (Dr, Mr, Mrs, Ms, etc.)", examples=["Dr"])
    
    # 2. First Name (required)
    first_name: str = Field(..., min_length=1, max_length=255, description="First name (required)", examples=["John"])
    
    # 3. Middle Name (optional)
    middle_name: Optional[str] = Field(None, max_length=255, description="Middle name (optional)", examples=["Michael"])
    
    # 4. Last Name (required)
    last_name: str = Field(..., min_length=1, max_length=255, description="Last name (required)", examples=["Doe"])
    
    # 5. Gender (required)
    gender: str = Field(..., max_length=20, description="Gender (required)", examples=["male"])
    
    # 6. Date of Birth (required)
    date_of_birth: date = Field(..., description="Date of birth (required)", examples=["1990-01-15"])
    
    # 7. Current Country (optional) - UUID foreign key
    country_id: Optional[UUID] = Field(None, description="Country ID (UUID)", examples=["f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"])
    
    # 8. Mobile Number with country code (optional)
    mobile_number: Optional[str] = Field(None, max_length=20, description="Mobile number with country code (e.g., +1234567890)", examples=["+1234567890"])
    
    # 9. Street Address (optional)
    address_line_1: Optional[str] = Field(None, max_length=255, description="Street Address", examples=["123 Main Street"])
    
    # 10. City (optional) - UUID foreign key
    city_id: Optional[UUID] = Field(None, description="City ID (UUID)", examples=["a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"])
    
    # 11. State (optional) - UUID foreign key
    state_id: Optional[UUID] = Field(None, description="State ID (UUID)", examples=["b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7"])
    
    # 12. Zip Code (optional)
    postal_code: Optional[str] = Field(None, max_length=20, description="Zip Code", examples=["10001"])
    
    # Note: Email is NOT included in this schema - it's automatically synced from users.email to contact_details.email
    
    @validator('gender')
    def validate_gender(cls, v):
        """Validate gender value (required field) - matches Figma design"""
        if v is None:
            raise ValueError("Gender is required")
        v = v.lower()
        # Matches Figma design: Male, Female, Other
        valid_genders = ['male', 'female', 'other']
        if v not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
        return v
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title value"""
        if v is not None:
            v = v.strip()
            valid_titles = ['Dr', 'Mr', 'Mrs', 'Ms', 'Miss', 'Prof', 'Sir', 'Madam']
            if v not in valid_titles:
                # Allow any title but log warning
                pass
        return v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth is not in future (required field)"""
        if v is None:
            raise ValueError("Date of birth is required")
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v
    
    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        """Validate mobile number format (optional field)"""
        if v is not None:
            v = v.strip()
            # Basic validation: should start with + for country code
            if v and not v.startswith('+'):
                # Allow without + but warn
                pass
        return v
    
    @classmethod
    def model_json_schema(cls, **kwargs):
        """Override to ensure example is in correct order matching Figma design"""
        schema = super().model_json_schema(**kwargs)
        
        # Build example in EXACT field order (matching Figma design)
        # Order: title, first_name, middle_name, last_name, gender, date_of_birth, country_id, mobile_number, address_line_1, city_id, state_id, postal_code
        # Note: Email is NOT included - it's synced from users.email automatically
        # Using dict with explicit order (Python 3.7+ preserves insertion order)
        example = {
            "title": "Dr",
            "first_name": "John",
            "middle_name": "Michael",
            "last_name": "Doe",
            "gender": "male",
            "date_of_birth": "1990-01-15",
            "country_id": "f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c",
            "mobile_number": "+1234567890",
            "address_line_1": "123 Main Street",
            "city_id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
            "state_id": "b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7",
            "postal_code": "10001"
        }
        # Force the example into the schema
        schema['example'] = example
        return schema
    
    model_config = ConfigDict(
        json_encoders={},
        populate_by_name=True
    )


class MedicalInfo(BaseModel):
    """
    Medical information schema
    Matches Figma design for Medical Information tab
    """
    # Pre-defined conditions with years
    diabetes_mellitus_years: Optional[int] = Field(None, description="Years with diabetes mellitus", examples=[5])
    hypertension_years: Optional[int] = Field(None, description="Years with hypertension", examples=[None])
    hypothyroidism_years: Optional[int] = Field(None, description="Years with hypothyroidism", examples=[None])
    alcohol_years: Optional[int] = Field(None, description="Years of alcohol use", examples=[None])
    tobacco_years: Optional[int] = Field(None, description="Years of tobacco use", examples=[None])
    smoke_years: Optional[int] = Field(None, description="Years of smoking", examples=[None])
    
    # Custom conditions - accept both single dict and list (validators will normalize to list)
    custom_conditions: Optional[List[Dict[str, Any]]] = Field(default=None, description="Custom medical conditions (can be a single object or list of objects with 'name' and 'years')", examples=[[{"name": "Custom Condition", "years": 3}]])
    
    # Existing condition
    existing_condition: Optional[str] = Field(None, max_length=500, description="Any existing medical condition", examples=["Asthma"])
    existing_condition_years: Optional[int] = Field(None, description="Number of years with existing condition", examples=[10])
    
    # Allergies
    allergies: Optional[str] = Field(None, max_length=500, description="Allergies (medications, food, others)", examples=["Penicillin, Peanuts"])
    allergies_years: Optional[int] = Field(None, description="Number of years with allergies", examples=[5])
    
    # Current medications - accept both single dict and list (validators will normalize to list)
    current_medications: Optional[List[Dict[str, Any]]] = Field(default=None, description="Current medications (can be a single object or list of objects with 'name', 'dosage', 'frequency')", examples=[[{"name": "Aspirin", "dosage": "100mg", "frequency": "Once daily"}]])
    
    @field_validator('custom_conditions', mode='before')
    @classmethod
    def validate_custom_conditions(cls, v):
        """Validate and normalize custom_conditions - convert single dict to list"""
        # Handle None, empty string, or empty list
        if v is None or v == "" or v == []:
            return None
        # Handle string that might be JSON
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed if parsed else None
                elif isinstance(parsed, dict):
                    # Convert single dict to list
                    return [parsed]
                return None
            except (json.JSONDecodeError, ValueError):
                return None
        # Handle dict - convert to list
        if isinstance(v, dict):
            return [v]
        # Handle list
        if isinstance(v, list):
            # Return empty list as None to be consistent
            return v if v else None
        # For any other type, return None
        return None
    
    @field_validator('current_medications', mode='before')
    @classmethod
    def validate_current_medications(cls, v):
        """Validate and normalize current_medications - convert single dict to list"""
        # Handle None, empty string, or empty list
        if v is None or v == "" or v == []:
            return None
        # Handle string that might be JSON
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed if parsed else None
                elif isinstance(parsed, dict):
                    # Convert single dict to list
                    return [parsed]
                return None
            except (json.JSONDecodeError, ValueError):
                return None
        # Handle dict - convert to list
        if isinstance(v, dict):
            return [v]
        # Handle list
        if isinstance(v, list):
            # Return empty list as None to be consistent
            return v if v else None
        # For any other type, return None
        return None
    
    @model_validator(mode='after')
    def normalize_list_fields(self):
        """Normalize list fields after validation"""
        # Convert single dicts to lists if needed
        if isinstance(self.custom_conditions, dict):
            self.custom_conditions = [self.custom_conditions]
        if isinstance(self.current_medications, dict):
            self.current_medications = [self.current_medications]
        return self


class PatientPersonalInfoUpdate(BaseModel):
    """
    Schema for patient personal information update
    Matches Figma design for "Edit My Profile" - Personal Info tab
    
    Includes: name, contact numbers, demographics, address, avatar
    """
    # Personal Information - Name fields
    title: Optional[str] = Field(None, max_length=10, description="Title (Dr, Mr, Mrs, Ms, etc.)", examples=["Dr"])
    first_name: str = Field(..., min_length=1, max_length=255, description="First name (required)", examples=["John"])
    middle_name: Optional[str] = Field(None, max_length=255, description="Middle name (optional)", examples=["Michael"])
    last_name: str = Field(..., min_length=1, max_length=255, description="Last name (required)", examples=["Doe"])
    
    # Personal Information - Demographics
    gender: str = Field(..., max_length=20, description="Gender (required)", examples=["male"])
    date_of_birth: date = Field(..., description="Date of birth (required)", examples=["1990-01-15"])
    
    # Personal Information - Contact
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact number with country code", examples=["+1 (721) 544-2275"])
    emergency_contact_number: Optional[str] = Field(None, max_length=20, description="Emergency contact number", examples=["+1 (721) 555-1234"])
    family_contact_number: Optional[str] = Field(None, max_length=20, description="Family contact number", examples=["+1 (721) 555-5678"])
    
    # Personal Information - Additional
    blood_type: Optional[str] = Field(None, max_length=10, description="Blood type", examples=["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"])
    occupation: Optional[str] = Field(None, max_length=255, description="Occupation", examples=["Software Engineer"])
    marital_status: Optional[str] = Field(None, max_length=50, description="Marital status", examples=["Single", "Married", "Divorced", "Widowed"])
    preferred_language_id: Optional[UUID] = Field(None, description="Preferred language ID (UUID)", examples=["a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"])
    
    # Profile Image
    avatar: Optional[str] = Field(None, max_length=255, description="Profile image/avatar URL or path", examples=["/uploads/avatars/user123.jpg"])
    
    # Address
    country_id: Optional[UUID] = Field(None, description="Country ID (UUID)", examples=["f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"])
    state_id: Optional[UUID] = Field(None, description="State ID (UUID)", examples=["b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7"])
    city_id: Optional[UUID] = Field(None, description="City ID (UUID)", examples=["a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"])
    address_line_1: Optional[str] = Field(None, max_length=255, description="Street Address", examples=["123 Main Street"])
    postal_code: Optional[str] = Field(None, max_length=20, description="Zip Code", examples=["10001"])
    
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
    
    @validator('blood_type')
    def validate_blood_type(cls, v):
        """Validate blood type"""
        if v is not None:
            valid_blood_types = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
            if v.upper() not in valid_blood_types:
                raise ValueError(f"Blood type must be one of: {', '.join(valid_blood_types)}")
            return v.upper()
        return v
    
    @classmethod
    def model_json_schema(cls, **kwargs):
        """Override to ensure example is in correct order matching Figma design"""
        from collections import OrderedDict
        schema = super().model_json_schema(**kwargs)
        example = OrderedDict([
            ("title", "Dr"),
            ("first_name", "John"),
            ("middle_name", "Michael"),
            ("last_name", "Doe"),
            ("gender", "male"),
            ("date_of_birth", "1990-01-15"),
            ("contact_number", "+1 (721) 544-2275"),
            ("emergency_contact_number", "+1 (721) 555-1234"),
            ("family_contact_number", "+1 (721) 555-5678"),
            ("blood_type", "O+"),
            ("occupation", "Software Engineer"),
            ("marital_status", "Married"),
            ("preferred_language_id", "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"),
            ("avatar", "/uploads/avatars/user123.jpg"),
            ("country_id", "f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"),
            ("state_id", "b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7"),
            ("city_id", "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"),
            ("address_line_1", "123 Main Street"),
            ("postal_code", "10001")
        ])
        schema['example'] = dict(example)
        return schema
    
    model_config = ConfigDict(
        json_encoders={},
        populate_by_name=True
    )


class PatientMedicalInfoUpdate(BaseModel):
    """
    Schema for patient medical information update
    Matches Figma design for "Edit My Profile" - Medical Info tab
    """
    medical_info: MedicalInfo = Field(..., description="Medical information")
    
    @classmethod
    def model_json_schema(cls, **kwargs):
        """Override to ensure example is in correct order matching Figma design"""
        from collections import OrderedDict
        schema = super().model_json_schema(**kwargs)
        example = OrderedDict([
            ("medical_info", {
                "diabetes_mellitus_years": 5,
                "hypertension_years": None,
                "hypothyroidism_years": None,
                "alcohol_years": None,
                "tobacco_years": None,
                "smoke_years": None,
                "existing_condition": "Asthma",
                "existing_condition_years": 10,
                "allergies": "Penicillin, Peanuts",
                "allergies_years": 5,
                "current_medications": [
                    {"name": "Aspirin", "dosage": "100mg", "frequency": "Once daily"}
                ]
            })
        ])
        schema['example'] = dict(example)
        return schema
    
    model_config = ConfigDict(
        json_encoders={},
        populate_by_name=True
    )


class DoctorProfileUpdate(BaseModel):
    """
    Schema for doctor profile update
    Matches Figma design for doctor profile form
    
    Required fields: first_name, last_name, date_of_birth
    Optional fields: middle_name, phone_number, email, education, years_of_experience, 
                     languages (array), specializations (array), about, profile_img
    """
    # Name fields
    first_name: str = Field(..., min_length=1, max_length=255, description="First name (required)", examples=["John"])
    middle_name: Optional[str] = Field(None, max_length=255, description="Middle name (optional)", examples=["Michael"])
    last_name: str = Field(..., min_length=1, max_length=255, description="Last name (required)", examples=["Doe"])
    
    # Date of birth (required)
    dob: date = Field(..., description="Date of birth (required, must be at least 18 years old)", examples=["1990-01-15"], alias="date_of_birth")
    
    # Contact (optional)
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number (10 digits, must be unique)", examples=["9876543210"])
    email: Optional[EmailStr] = Field(None, description="Email address (must be unique)", examples=["dr.bajwa@gmail.com"])
    
    # Doctor-specific fields
    education: Optional[str] = Field(None, max_length=255, description="Education details (e.g., MBBS, MD in Cardiology)", examples=["MBBS, MD in Cardiology"])
    years_of_experience: Optional[int] = Field(None, ge=0, description="Years of experience", examples=[10])
    
    # Languages (array of language IDs)
    languages: Optional[List[UUID]] = Field(None, description="Array of language IDs from languages table", examples=[["a734ef5c-5653-444c-825e-ac8629e7eaf0", "a9a02cce-1624-4162-8c1a-56580a0f1558"]])
    
    # Specializations (array of medical service IDs)
    specializations: Optional[List[UUID]] = Field(None, description="Array of medical service/specialization IDs from medical_services table", examples=[["9cdf3788-f630-47d5-8e11-a49d84409d21", "9cdf3789-00dd-40fd-9932-3ed703e12a44"]])
    
    # About
    about: Optional[str] = Field(None, description="About the doctor", examples=["Experienced cardiologist with 10+ years of practice"])
    
    # Profile image (handled separately in multipart/form-data)
    profile_img: Optional[str] = Field(None, description="Profile image URL or path (for reference only, use multipart/form-data for upload)", examples=["/uploads/avatars/doctor123.jpg"])
    
    @field_validator('dob', mode='before')
    @classmethod
    def validate_dob(cls, v):
        """Validate date of birth is not in future and user is at least 18 years old"""
        if v is None:
            raise ValueError("Date of birth is required")
        if isinstance(v, str):
            from dateutil.parser import parse
            v = parse(v).date()
        today = date.today()
        if v > today:
            raise ValueError("Date of birth cannot be in the future")
        # Check if at least 18 years old
        age = (today - v).days // 365
        if age < 18:
            raise ValueError("Doctor must be at least 18 years old")
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        """Validate phone number format (10 digits)"""
        if v is not None:
            # Remove all non-digit characters
            digits_only = ''.join(filter(str.isdigit, v))
            if len(digits_only) != 10:
                raise ValueError("Phone number must be exactly 10 digits")
        return v
    
    @field_validator('years_of_experience')
    @classmethod
    def validate_years_of_experience(cls, v):
        """Validate years of experience is non-negative"""
        if v is not None and v < 0:
            raise ValueError("Years of experience cannot be negative")
        return v
    
    @classmethod
    def model_json_schema(cls, **kwargs):
        """Override to ensure example is in correct order matching Figma design"""
        from collections import OrderedDict
        schema = super().model_json_schema(**kwargs)
        example = OrderedDict([
            ("first_name", "John"),
            ("middle_name", "Michael"),
            ("last_name", "Doe"),
            ("dob", "1990-01-15"),
            ("phone_number", "9876543210"),
            ("email", "dr.bajwa@gmail.com"),
            ("education", "MBBS, MD in Cardiology"),
            ("years_of_experience", 10),
            ("languages", ["a734ef5c-5653-444c-825e-ac8629e7eaf0", "a9a02cce-1624-4162-8c1a-56580a0f1558", "5b7a93c0-3c0d-4c9c-a23f-5e2e04d5d5c1"]),
            ("specializations", ["9cdf3788-f630-47d5-8e11-a49d84409d21", "9cdf3789-00dd-40fd-9932-3ed703e12a44", "9cdf3789-019b-4366-a8ca-e42f879ba156"]),
            ("about", "Experienced cardiologist with 10+ years of practice")
        ])
        schema['example'] = dict(example)
        return schema
    
    model_config = ConfigDict(
        json_encoders={},
        populate_by_name=True,
        allow_population_by_field_name=True
    )


class PatientProfileUpdate(BaseModel):
    """
    Schema for patient profile update
    Matches Figma design for "Edit My Profile" - Personal Info and Medical Info tabs
    
    Personal Info fields (from 1st screenshot):
    - Full Name (title, first_name, middle_name, last_name)
    - Contact Number, Emergency Contact Number, Family Contact Number
    - Date of birth
    - Blood Type, Occupation, Marital Status, Preferred Language
    - Address (Country, State, City, Zip code)
    
    Medical Info fields (from 2nd screenshot):
    - Pre-defined conditions (Diabetes, Hypertension, etc.)
    - Existing Condition
    - Allergies
    - Current Medications
    """
    # Personal Information - Name fields
    title: Optional[str] = Field(None, max_length=10, description="Title (Dr, Mr, Mrs, Ms, etc.)", examples=["Dr"])
    first_name: str = Field(..., min_length=1, max_length=255, description="First name (required)", examples=["John"])
    middle_name: Optional[str] = Field(None, max_length=255, description="Middle name (optional)", examples=["Michael"])
    last_name: str = Field(..., min_length=1, max_length=255, description="Last name (required)", examples=["Doe"])
    
    # Personal Information - Demographics
    gender: str = Field(..., max_length=20, description="Gender (required)", examples=["male"])
    date_of_birth: date = Field(..., description="Date of birth (required)", examples=["1990-01-15"])
    
    # Personal Information - Contact
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact number with country code", examples=["+1 (721) 544-2275"])
    emergency_contact_number: Optional[str] = Field(None, max_length=20, description="Emergency contact number", examples=["+1 (721) 555-1234"])
    family_contact_number: Optional[str] = Field(None, max_length=20, description="Family contact number", examples=["+1 (721) 555-5678"])
    
    # Personal Information - Additional
    blood_type: Optional[str] = Field(None, max_length=10, description="Blood type", examples=["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"])
    occupation: Optional[str] = Field(None, max_length=255, description="Occupation", examples=["Software Engineer"])
    marital_status: Optional[str] = Field(None, max_length=50, description="Marital status", examples=["Single", "Married", "Divorced", "Widowed"])
    preferred_language_id: Optional[UUID] = Field(None, description="Preferred language ID (UUID)", examples=["a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"])
    
    # Address
    country_id: Optional[UUID] = Field(None, description="Country ID (UUID)", examples=["f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"])
    state_id: Optional[UUID] = Field(None, description="State ID (UUID)", examples=["b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7"])
    city_id: Optional[UUID] = Field(None, description="City ID (UUID)", examples=["a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"])
    address_line_1: Optional[str] = Field(None, max_length=255, description="Street Address", examples=["123 Main Street"])
    postal_code: Optional[str] = Field(None, max_length=20, description="Zip Code", examples=["10001"])
    
    # Medical Information
    medical_info: Optional[MedicalInfo] = Field(None, description="Medical information")
    
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
    
    @validator('blood_type')
    def validate_blood_type(cls, v):
        """Validate blood type"""
        if v is not None:
            valid_blood_types = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
            if v.upper() not in valid_blood_types:
                raise ValueError(f"Blood type must be one of: {', '.join(valid_blood_types)}")
            return v.upper()
        return v
    
    @classmethod
    def model_json_schema(cls, **kwargs):
        """Override to ensure example is in correct order matching Figma design"""
        from collections import OrderedDict
        schema = super().model_json_schema(**kwargs)
        example = OrderedDict([
            ("title", "Dr"),
            ("first_name", "John"),
            ("middle_name", "Michael"),
            ("last_name", "Doe"),
            ("gender", "male"),
            ("date_of_birth", "1990-01-15"),
            ("contact_number", "+1 (721) 544-2275"),
            ("emergency_contact_number", "+1 (721) 555-1234"),
            ("family_contact_number", "+1 (721) 555-5678"),
            ("blood_type", "O+"),
            ("occupation", "Software Engineer"),
            ("marital_status", "Married"),
            ("preferred_language_id", "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"),
            ("country_id", "f3a8b2c1-4d5e-4f6a-9b8c-1e2d3f4a5b6c"),
            ("state_id", "b2c3d4e5-6f7g-8h9i-0j1k-l2m3n4o5p6q7"),
            ("city_id", "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"),
            ("address_line_1", "123 Main Street"),
            ("postal_code", "10001"),
            ("medical_info", {
                "diabetes_mellitus_years": 5,
                "existing_condition": "Asthma",
                "existing_condition_years": 10,
                "allergies": "Penicillin, Peanuts",
                "allergies_years": 5,
                "current_medications": [
                    {"name": "Aspirin", "dosage": "100mg", "frequency": "Once daily"}
                ]
            })
        ])
        schema['example'] = dict(example)
        return schema
    
    model_config = ConfigDict(
        json_encoders={},
        populate_by_name=True
    )


class ContactDetailsUpdate(BaseModel):
    """
    Schema for updating contact details
    """
    
    # Contact type
    contact_type: Optional[str] = Field(None, max_length=50)
    
    # Phone numbers
    phone: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    
    # Email
    email: Optional[EmailStr] = None
    
    # Address
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Location foreign keys (UUIDs)
    country_id: Optional[UUID] = Field(None, description="Country ID (UUID)")
    state_id: Optional[UUID] = Field(None, description="State ID (UUID)")
    city_id: Optional[UUID] = Field(None, description="City ID (UUID)")
    
    # Emergency contact
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=100)
    
    # Additional
    notes: Optional[str] = None
    is_primary: Optional[bool] = None
    
    @validator('contact_type')
    def validate_contact_type(cls, v):
        """Validate contact type"""
        if v is not None:
            v = v.lower()
            valid_types = ['primary', 'secondary', 'emergency', 'work', 'home']
            if v not in valid_types:
                raise ValueError(f"Contact type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "contact_type": "primary",
                "phone": "+1234567890",
                "email": "user@example.com",
                "emergency_contact_name": "Jane Doe",
                "emergency_contact_phone": "+1987654321",
                "emergency_contact_relationship": "Spouse"
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class ContactDetailsResponse(BaseModel):
    """Response schema for contact details"""
    
    id: UUID
    user_id: UUID
    contact_type: str
    
    # Phone numbers
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    fax: Optional[str] = None
    
    # Email
    email: Optional[str] = None
    
    # Address
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Location foreign keys (UUIDs)
    country_id: Optional[UUID] = None
    state_id: Optional[UUID] = None
    city_id: Optional[UUID] = None
    
    # Location names (from relationships, for response)
    country_name: Optional[str] = None
    state_name: Optional[str] = None
    city_name: Optional[str] = None
    
    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    
    # Additional
    notes: Optional[str] = None
    is_primary: bool
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    """
    Response schema for user profile
    
    Matches Figma design fields
    """
    
    id: UUID
    user_id: UUID
    
    # Title (as per Figma design)
    title: Optional[str] = None
    
    # Personal information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None  # Computed from date_of_birth
    gender: Optional[str] = None
    
    # Medical/Demographic fields (for patient profile)
    blood_type: Optional[str] = None
    marital_status: Optional[str] = None
    preferred_language_id: Optional[UUID] = None
    medical_info: Optional[Dict[str, Any]] = None
    
    # Profile image
    avatar: Optional[str] = None
    
    # Profile completion status
    is_profile_complete: Optional[bool] = False
    
    # HIPAA form status (for patients)
    hipaa_form_filled: Optional[bool] = False
    
    # Address (as per Figma design)
    address_line_1: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Location foreign keys (UUIDs)
    country_id: Optional[UUID] = None
    state_id: Optional[UUID] = None
    city_id: Optional[UUID] = None
    
    # Location names (from relationships, for response)
    country_name: Optional[str] = None
    state_name: Optional[str] = None
    city_name: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProfileWithContactsResponse(BaseModel):
    """
    Complete profile with contact details
    
    Laravel compatible response
    """
    
    profile: ProfileResponse
    contacts: list[ContactDetailsResponse] = []
    is_profile_complete: Optional[bool] = False


class PatientPersonalInfoResponse(BaseModel):
    """
    Patient personal information response
    Includes all personal/demographic information
    """
    id: UUID
    user_id: UUID
    email: Optional[str] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    contact_number: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    family_contact_number: Optional[str] = None
    blood_type: Optional[str] = None
    occupation: Optional[str] = None
    marital_status: Optional[str] = None
    preferred_language_id: Optional[UUID] = None
    preferred_language_name: Optional[str] = None
    country_id: Optional[UUID] = None
    country_name: Optional[str] = None
    state_id: Optional[UUID] = None
    state_name: Optional[str] = None
    city_id: Optional[UUID] = None
    city_name: Optional[str] = None
    address_line_1: Optional[str] = None
    postal_code: Optional[str] = None
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PatientMedicalInfoResponse(BaseModel):
    """
    Patient medical information response
    Includes all medical conditions, allergies, and medications
    """
    id: UUID
    user_id: UUID
    medical_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class PatientPersonalInfoSingleResponse(BaseModel):
    """Laravel-compatible response for patient personal info"""
    success: bool = True
    message: str = "Personal information retrieved successfully"
    data: PatientPersonalInfoResponse
    errors: Optional[Dict[str, List[str]]] = None


class PatientMedicalInfoSingleResponse(BaseModel):
    """Laravel-compatible response for patient medical info"""
    success: bool = True
    message: str = "Medical information retrieved successfully"
    data: PatientMedicalInfoResponse
    errors: Optional[Dict[str, List[str]]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "660e8400-e29b-41d4-a716-446655440000",
                    "first_name": "John",
                    "last_name": "Doe",
                    "date_of_birth": "1990-01-15",
                    "age": 35,
                    "gender": "male",
                    "profile_image": "/uploads/avatars/user123.jpg"
                },
                "contacts": [
                    {
                        "id": "770e8400-e29b-41d4-a716-446655440000",
                        "contact_type": "primary",
                        "phone": "+1234567890",
                        "email": "user@example.com"
                    }
                ]
            }
        }


class ProfileSingleResponse(BaseModel):
    """
    Single profile response (Laravel format)
    """
    
    success: bool = True
    message: str = "Profile retrieved successfully"
    data: ProfileWithContactsResponse
    errors: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Profile retrieved successfully",
                "data": {
                    "profile": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "660e8400-e29b-41d4-a716-446655440000",
                        "first_name": "John",
                        "last_name": "Doe"
                    },
                    "contacts": []
                },
                "errors": None
            }
        }


class ProfileUpdateResponse(BaseModel):
    """
    Profile update response (Laravel format)
    """
    
    success: bool = True
    message: str = "Profile updated successfully"
    data: ProfileWithContactsResponse
    errors: Optional[dict] = None


class DoctorProfileResponse(BaseModel):
    """
    Doctor profile response
    Includes all doctor-specific information
    """
    id: UUID
    user_id: UUID
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    education: Optional[str] = None
    years_of_experience: Optional[int] = None
    languages: Optional[List[Dict[str, Any]]] = None  # List of {id, language_name, language_code}
    specializations: Optional[List[Dict[str, Any]]] = None  # List of {id, name, image}
    about: Optional[str] = None
    profile_img: Optional[str] = None  # Full URL
    created_at: datetime
    updated_at: datetime


class DoctorProfileSingleResponse(BaseModel):
    """Laravel-compatible response for doctor profile"""
    success: bool = True
    message: str = "Doctor profile retrieved successfully"
    data: DoctorProfileResponse
    errors: Optional[Dict[str, List[str]]] = None
