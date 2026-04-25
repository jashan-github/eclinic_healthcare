"""
Appointment Booking schemas
Request/response models for patient appointment booking flow
"""

from typing import Optional, List
from uuid import UUID
from datetime import date, time
from pydantic import BaseModel, Field


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class AppointmentBookingRequest(BaseModel):
    """Request to create an appointment booking"""
    doctor_id: UUID = Field(..., description="Doctor user ID")
    service_id: UUID = Field(..., description="Service ID")
    consultation_mode: str = Field(..., description="Consultation mode: IN_CLINIC or TELECONSULTATION")
    preferred_date: date = Field(..., description="Preferred appointment date")
    preferred_time: time = Field(..., description="Preferred appointment time (HH:MM)")
    reason: Optional[str] = Field(None, max_length=1000, description="Reason/symptoms for appointment (optional)")
    doctor_service_availability_id: Optional[UUID] = Field(None, description="Doctor service availability assignment ID (if applicable)")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class DoctorSummaryResponse(BaseModel):
    """Doctor summary for appointment booking"""
    id: UUID
    name: str
    profile_image: Optional[str] = None
    specialty: Optional[str] = None
    years_of_experience: Optional[int] = None
    rating: Optional[float] = None
    consultation_fee: Optional[float] = None
    intake_fee: Optional[float] = None
    total_fee: Optional[float] = None
    currency: Optional[str] = None
    
    class Config:
        from_attributes = True


class ConsultationTypeResponse(BaseModel):
    """Available consultation type"""
    mode: str = Field(..., description="Consultation mode: IN_CLINIC or TELECONSULTATION")
    label: str = Field(..., description="Human-readable label")
    consultation_fee: Optional[float] = None
    intake_fee: Optional[float] = None
    total_fee: Optional[float] = None
    currency: Optional[str] = None
    is_available: bool = Field(..., description="Whether this mode is available for the doctor")


class AvailableTimeSlotResponse(BaseModel):
    """Available time slot for booking"""
    date: date
    time: time
    duration_minutes: int
    consultation_mode: str


class AppointmentBookingResponse(BaseModel):
    """Response after creating appointment booking"""
    id: UUID
    doctor_id: UUID
    service_id: UUID
    consultation_mode: str
    appointment_date: date
    start_time: time
    end_time: time
    status: str
    total_price: float
    currency: str
    duration_minutes: int


class PatientAppointmentItem(BaseModel):
    """Appointment item for patient listing"""
    id: UUID
    doctor_id: UUID
    doctor_name: str
    doctor_profile_image: Optional[str] = None
    specialty: Optional[str] = None
    service_id: UUID
    service_name: Optional[str]
    consultation_mode: str
    appointment_date: date
    start_time: time
    end_time: time
    status: str
    price_amount: float
    currency: str
    duration_minutes: int
    payment_status: Optional[str] = None
    chat_room_id: Optional[str] = Field(None, description="Chat room ID if doctor has started a chat with the patient")


class PatientAppointmentRequestItem(BaseModel):
    """Appointment request item for patient pending list"""
    id: UUID
    doctor_id: UUID
    doctor_name: str
    doctor_profile_image: Optional[str] = None
    doctor_specialty: Optional[str] = None
    service_id: UUID
    consultation_mode: str
    preferred_date: date
    preferred_time: time
    status: str
    duration_minutes: int
    price_amount: Optional[float] = None
    currency: Optional[str] = None
    reason: Optional[str] = None
    payment_status: Optional[str] = None
    chat_room_id: Optional[str] = Field(None, description="Chat room ID if doctor has started a chat with the patient")


class PatientAppointmentsGroupedResponse(BaseModel):
    """Laravel-compatible grouped appointments response"""
    success: bool = True
    message: str = "Patient appointments retrieved successfully"
    data: dict
    errors: Optional[dict] = None


class DoctorAppointmentItem(BaseModel):
    """Appointment item for doctor listing"""
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    patient_profile_image: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_age: Optional[int] = None
    service_id: str
    service_name: Optional[str] = None
    consultation_mode: str
    appointment_date: str  # ISO date string
    start_time: str  # Time string
    end_time: str  # Time string
    status: str
    price_amount: Optional[float] = None
    currency: Optional[str] = None
    duration_minutes: int


class DoctorAppointmentsGroupedResponse(BaseModel):
    """Laravel-compatible grouped appointments response for doctors"""
    success: bool = True
    message: str = "Doctor appointments retrieved successfully"
    data: dict
    errors: Optional[dict] = None


class PaymentConfirmationResponse(BaseModel):
    """Response after payment confirmation"""
    payment_id: UUID
    appointment_id: UUID
    appointment_request_id: UUID
    amount: float
    currency: str
    status: str
    appointment_date: date
    start_time: time
    end_time: time
    consultation_mode: str


# ============================================================================
# LARAVEL-COMPATIBLE RESPONSE WRAPPERS
# ============================================================================


class DoctorSummarySingleResponse(BaseModel):
    """Laravel-compatible doctor summary response"""
    success: bool = True
    message: str = "Doctor summary retrieved successfully"
    data: DoctorSummaryResponse
    errors: Optional[dict] = None


class ConsultationTypesListResponse(BaseModel):
    """Laravel-compatible consultation types response"""
    success: bool = True
    message: str = "Consultation types retrieved successfully"
    data: dict
    errors: Optional[dict] = None


class AvailableTimeSlotsListResponse(BaseModel):
    """Laravel-compatible available time slots response"""
    success: bool = True
    message: str = "Available time slots retrieved successfully"
    data: dict
    errors: Optional[dict] = None


class AppointmentBookingSingleResponse(BaseModel):
    """Laravel-compatible appointment booking response"""
    success: bool = True
    message: str = "Appointment request created successfully"
    data: AppointmentBookingResponse
    errors: Optional[dict] = None


class PaymentConfirmationSingleResponse(BaseModel):
    """Laravel-compatible payment confirmation response"""
    success: bool = True
    message: str = "Payment processed successfully"
    data: PaymentConfirmationResponse
    errors: Optional[dict] = None
