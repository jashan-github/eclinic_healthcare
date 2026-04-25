"""
Patient Vital Signs schemas
Request/response models for patient vital signs endpoints
"""

from typing import Optional, List, Union, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class VitalReadingInput(BaseModel):
    """Single vital reading input"""
    vital_name_id: UUID = Field(..., description="Vital name ID (FK to vital_names table)")
    value: Union[float, int, str] = Field(..., description="Vital sign value (number, text, or select option)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "vital_name_id": "550e8400-e29b-41d4-a716-446655440000",
                "value": 185.5
            }
        }


class PatientVitalSignsCreate(BaseModel):
    """Patient Vital Signs creation schema
    
    Creates multiple vital sign records (one per vital in the vitals array).
    Each vital will be validated against vital_names and frequency rules.
    
    **Auto-handled Fields:**
    - `patient_id`: Automatically set from logged-in user for patients. Required in request body for doctors/admins.
    - `clinic_id`: Automatically fetched from patient's user record. Not required in request.
    
    **For Patients:**
    - Both `patient_id` and `clinic_id` are automatically determined from your account
    - You can only record vital signs for yourself
    - Simply provide the `vitals` array with your readings
    
    **For Doctors/Staff/Admins:**
    - `patient_id` must be provided in the request body (which patient you're recording for)
    - `clinic_id` is automatically fetched from the patient's user record
    - Clinic access is validated (you can only record for patients in your clinic)
    """
    patient_id: Optional[UUID] = Field(
        None,
        description="""Patient user ID (optional, auto-handled by backend)
        
        - **For Patients**: Automatically set from your logged-in account. Do not include this field.
        - **For Doctors/Staff/Admins**: Required. Specify which patient you're recording vital signs for.
        
        Example: "587ec4ec-e2ae-48fb-819c-5bb5d84f20ec"
        """
    )
    clinic_id: Optional[UUID] = Field(
        None,
        description="""Clinic ID (optional, auto-handled by backend)
        
        This field is automatically fetched from the patient's user record.
        Do not include this field in your request - it will be determined automatically.
        
        Example: "4a2c23c9-b31e-4ab5-9819-c4e69ac27879"
        """
    )
    vitals: List[VitalReadingInput] = Field(
        ...,
        min_length=1,
        description="""Array of vital sign readings (required)
        
        Each object in the array represents one vital sign reading.
        Must contain at least one vital reading.
        
        Example:
        [
          {
            "vital_name_id": "a744f208-09a7-4c8a-a266-fa261313dee8",
            "value": 185.5
          },
          {
            "vital_name_id": "b5b97a36-de08-4b4d-81e2-cb1270a21c74",
            "value": 37.0
          }
        ]
        """
    )
    doctor_id: Optional[UUID] = Field(
        None,
        description="""Doctor user ID who recorded the vital signs (optional)
        
        - **For Patients**: Leave as null (automatically set to null)
        - **For Doctors**: Leave as null (automatically set to your doctor ID)
        - **For Admins**: Optional. Specify a doctor ID if recording on behalf of a doctor.
        
        Example: "7cf36af4-23b5-4a50-aa71-f99e1dd1ed3d"
        """
    )
    appointment_id: Optional[UUID] = Field(
        None,
        description="""Associated appointment ID (optional)
        
        Include this if the vital signs are being recorded during an appointment.
        Leave as null if recording outside of an appointment.
        
        Example: "abc123-def456-ghi789"
        """
    )
    record_date: Optional[datetime] = Field(
        None,
        description="""Date and time when vital signs were recorded (optional)
        
        If not provided, defaults to the current date and time.
        Format: ISO 8601 datetime string (e.g., "2026-01-05T09:30:00Z")
        
        Example: "2026-01-05T09:30:00Z"
        """
    )
    notes: Optional[str] = Field(
        None,
        description="""Additional notes about the vital signs (optional)
        
        Any additional information or observations about the vital sign readings.
        
        Example: "Patient appears healthy, readings taken in morning"
        """
    )
    share_with_doctor: Optional[bool] = Field(
        None,
        description="""Patient consent to share vital signs with doctor (optional)
        
        - **For Patients**: Required. Set to `true` if you consent to share these vital signs with your doctor for medical evaluation and care. Set to `false` if you do not consent. If not provided, defaults to `false` (no consent).
        - **For Doctors**: Optional. Defaults to `true` when doctor records vitals. Can be set to `false` if needed.
        
        **Important**: If you do not consent (`false`), your doctor will NOT be able to see these vital signs.
        
        Example: true
        """
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "vitals": [
                    {
                        "vital_name_id": "a744f208-09a7-4c8a-a266-fa261313dee8",
                        "value": 185.5
                    },
                    {
                        "vital_name_id": "b5b97a36-de08-4b4d-81e2-cb1270a21c74",
                        "value": 37.0
                    },
                    {
                        "vital_name_id": "b0abc0bb-863b-45e7-bd22-55d93e98d465",
                        "value": 98
                    }
                ],
                "appointment_id": None,
                "record_date": "2026-01-05T09:30:00Z",
                "notes": "Patient appears healthy",
                "share_with_doctor": True
            }
        }


class PatientVitalSignsUpdate(BaseModel):
    """Patient Vital Signs update schema"""
    numeric_value: Optional[Union[float, int, Decimal]] = Field(None, description="Updated numeric value (for number data_type)")
    text_value: Optional[str] = Field(None, description="Updated text value (for text/select data_type)")
    notes: Optional[str] = Field(None, description="Updated notes")
    record_date: Optional[datetime] = Field(None, description="Updated record date")
    share_with_doctor: Optional[bool] = Field(None, description="Update patient consent to share with doctor")
    
    @field_validator('numeric_value', 'text_value')
    @classmethod
    def validate_at_least_one_value(cls, v, info):
        """Ensure at least one value is provided"""
        values = info.data
        if not values.get('numeric_value') and not values.get('text_value'):
            raise ValueError("Either numeric_value or text_value must be provided")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "numeric_value": 186.0,
                "text_value": None,
                "notes": "Updated after patient consultation",
                "record_date": "2026-01-05T10:00:00Z"
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class PatientVitalSignsResponse(BaseModel):
    """Patient Vital Signs response schema"""
    id: UUID
    patient_id: UUID
    vital_name_id: UUID
    clinic_id: UUID
    doctor_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    record_date: datetime
    numeric_value: Optional[Decimal] = None
    text_value: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    share_with_doctor: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Include vital name details for convenience
    vital_name: Optional[dict] = None  # Will be populated by service
    
    class Config:
        from_attributes = True


# ============================================================================
# LIST RESPONSE SCHEMAS (Laravel compatible)
# ============================================================================


class PatientVitalSignsListResponse(BaseModel):
    """Patient Vital Signs list response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital signs retrieved successfully"
    data: dict
    errors: Optional[dict] = None


class PatientVitalSignsSingleResponse(BaseModel):
    """Single Patient Vital Signs response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital signs retrieved successfully"
    data: PatientVitalSignsResponse
    errors: Optional[dict] = None


class PatientVitalSignsCreateResponse(BaseModel):
    """Patient Vital Signs creation response (Laravel compatible)
    
    Returns multiple vital sign records (one per vital in the request).
    The data field contains:
    - records: Array of all created vital sign records
    - count: Number of records created
    - record: First record (for backward compatibility)
    """
    success: bool = True
    message: str = "Vital signs recorded successfully"
    data: Dict[str, Any]  # Contains records array, count, and optionally record (first record)
    errors: Optional[Dict[str, Any]] = None
    
    class Config:
        # Allow any extra fields and be lenient with validation
        extra = "allow"


class PatientVitalSignsUpdateResponse(BaseModel):
    """Patient Vital Signs update response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital signs updated successfully"
    data: PatientVitalSignsResponse
    errors: Optional[dict] = None


class PatientVitalSignsDeleteResponse(BaseModel):
    """Patient Vital Signs deletion response (Laravel compatible)"""
    success: bool = True
    message: str = "Vital signs deleted successfully"
    data: Optional[dict] = None
    errors: Optional[dict] = None

