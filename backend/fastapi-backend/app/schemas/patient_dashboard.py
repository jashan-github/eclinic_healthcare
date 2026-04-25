"""
Patient Dashboard Schemas
Request/response models for patient dashboard
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class DashboardSummary(BaseModel):
    """Dashboard summary statistics"""
    upcoming_appointments: int = Field(..., description="Number of upcoming appointments")
    documents_uploaded: int = Field(..., description="Number of documents uploaded")
    pending_approvals: int = Field(..., description="Number of pending appointment approvals")


class DashboardDoctorInfo(BaseModel):
    """Doctor information in dashboard"""
    id: Optional[str] = Field(None, description="Doctor ID")
    name: str = Field(..., description="Doctor name")
    specialty: str = Field(..., description="Doctor specialty")
    profile_image: Optional[str] = Field(None, description="Doctor profile image URL")


class DashboardServiceInfo(BaseModel):
    """Service information in dashboard"""
    id: Optional[str] = Field(None, description="Service ID")
    name: Optional[str] = Field(None, description="Service name")


class DashboardAppointment(BaseModel):
    """Upcoming appointment in dashboard"""
    id: str = Field(..., description="Appointment ID")
    doctor: DashboardDoctorInfo = Field(..., description="Doctor information")
    service: DashboardServiceInfo = Field(..., description="Service information")
    appointment_date: str = Field(..., description="Appointment date (YYYY-MM-DD)")
    appointment_time: str = Field(..., description="Appointment time (HH:MM AM/PM)")
    appointment_datetime: str = Field(..., description="Appointment datetime (ISO format)")
    status: str = Field(..., description="Appointment status")
    consultation_mode: str = Field(..., description="Consultation mode")


class DashboardActivity(BaseModel):
    """Recent activity item"""
    id: str = Field(..., description="Activity ID")
    type: str = Field(..., description="Activity type (appointment_confirmed, document_uploaded)")
    icon: str = Field(..., description="Icon identifier for frontend")
    message: str = Field(..., description="Activity message")
    created_at: Optional[str] = Field(None, description="Activity timestamp (ISO format)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DashboardData(BaseModel):
    """Complete dashboard data"""
    summary: DashboardSummary = Field(..., description="Summary statistics")
    upcoming_appointments: List[DashboardAppointment] = Field(default_factory=list, description="Upcoming appointments")
    recent_activity: List[DashboardActivity] = Field(default_factory=list, description="Recent activities")


# ============================================================================
# LARAVEL-COMPATIBLE RESPONSE WRAPPERS
# ============================================================================


class PatientDashboardResponse(BaseModel):
    """Laravel-compatible patient dashboard response"""
    success: bool = True
    message: str = "Dashboard data retrieved successfully"
    data: DashboardData
    errors: Optional[dict] = None
