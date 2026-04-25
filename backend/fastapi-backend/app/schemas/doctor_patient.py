"""
Doctor Patient schemas
Request/response models for doctor patient management
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from pydantic import BaseModel, Field


class DoctorPatientResponse(BaseModel):
    """Single patient response for doctor"""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None  # male, female, other
    age: Optional[int] = None  # Calculated from date_of_birth
    clinic_id: Optional[str] = None
    clinic_name: Optional[str] = None
    is_active: bool
    last_visited_date: Optional[str] = None  # ISO date string
    total_appointments: int
    has_medical_history: bool
    has_vital_signs_shared: bool
    medical_history_text: Optional[str] = None  # Extracted condition name (e.g., "Hypertension")
    available_actions: List[str]
    today_appointment_id: Optional[str] = None  # Appointment ID if patient has booking today with this doctor
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "gender": "male",
                "age": 42,
                "clinic_id": "4a2c23c9-b31e-4ab5-9819-c4e69ac27879",
                "clinic_name": "Main Clinic",
                "is_active": True,
                "last_visited_date": "2026-01-05",
                "total_appointments": 5,
                "has_medical_history": True,
                "has_vital_signs_shared": True,
                "medical_history_text": "Hypertension",
                "available_actions": ["view_vital_signs", "view_appointments", "create_appointment", "view_profile"],
                "today_appointment_id": "a5894914-d964-440c-8cfb-4bec2e4792a4"
            }
        }


class DoctorPatientListResponse(BaseModel):
    """Paginated list of patients for doctor (Laravel compatible)"""
    success: bool = True
    message: str = "Patients retrieved successfully"
    data: dict
    errors: Optional[dict] = None


class VisitDateResponse(BaseModel):
    """Visit date breakdown for display"""
    date: str  # ISO format: YYYY-MM-DD
    day: str  # Day of month as string: "01", "11", etc.
    day_name: str  # Day name: "Mon", "Tue", etc.
    month_name: str  # Month name: "Jan", "Feb", etc.
    month: str  # Month as string: "01", "12", etc.
    year: str  # Year as string: "2025", "2026", etc.


class PastVisitResponse(BaseModel):
    """Single past visit/appointment for doctor"""
    id: str  # Appointment ID
    title: str  # e.g., "Regular appointment on Dec 2025"
    appointment_created_at: str  # e.g., "11 Dec 2025 17:22:47"
    appointment_start_time: str  # HH:MM:SS
    appointment_end_time: str  # HH:MM:SS
    check_status: str  # "Pending" or "Checked" (based on appointment status)
    bookingId: Optional[str] = None
    device_type: Optional[str] = None
    notes: str = ""
    precription_pdf_url: Optional[str] = None
    digital_precription_pdf_url: Optional[str] = None
    video_call_recordings: List[str] = []
    assessment_summary: Optional[str] = None
    appointment_date: VisitDateResponse


class PatientVisitsListResponse(BaseModel):
    """Paginated list of past visits for a specific patient (Laravel compatible)"""
    success: bool = True
    message: str = "Past visits fetched successfully"
    data: dict  # Contains records, skip, limit, total
    errors: Optional[dict] = None


class AgeResponse(BaseModel):
    """Age breakdown for display"""
    age: int
    type: str = "years"
    full_age: str  # e.g., "32 years"


class PatientDetailResponse(BaseModel):
    """Detailed patient information for doctor"""
    id: str
    name: str
    age: AgeResponse
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    blood_type: Optional[str] = None
    occupation: Optional[str] = None
    date_of_birth: Optional[str] = None  # DD-MM-YYYY format
    family_contact_number: Optional[str] = None
    marital_status: Optional[str] = None
    preferred_language: Optional[str] = None
    health_issues: List[str] = []


class PatientDetailSingleResponse(BaseModel):
    """Patient detail response (Laravel compatible)"""
    success: bool = True
    data: PatientDetailResponse
    errors: Optional[dict] = None


class DoctorPatientMedicalInfoResponse(BaseModel):
    """Patient medical information for doctor"""
    id: str
    user_id: str
    medical_info: dict
    created_at: str
    updated_at: str


class DoctorPatientMedicalInfoSingleResponse(BaseModel):
    """Doctor view of patient medical info (Laravel compatible)"""
    success: bool = True
    message: str = "Medical information retrieved successfully"
    data: DoctorPatientMedicalInfoResponse
    errors: Optional[dict] = None

