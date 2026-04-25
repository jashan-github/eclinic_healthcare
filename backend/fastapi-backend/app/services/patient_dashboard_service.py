"""
Patient Dashboard Service
Business logic for patient dashboard data aggregation
"""

from typing import Dict, Any, List
from uuid import UUID
from datetime import date, datetime, time
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from loguru import logger

from app.models.appointment import Appointment
from app.models.appointment_request import AppointmentRequest
from app.models.patient_document import PatientDocument
from app.models.user import User
from app.models.profile import UserProfile
from app.models.service import Service
from app.core.security import CurrentUser
# Import EST timezone helpers from appointment_request_service
import pytz
EST = pytz.timezone('America/New_York')

def get_est_date() -> date:
    """Get current date in EST timezone"""
    return datetime.now(EST).date()

def get_est_datetime() -> datetime:
    """Get current datetime in EST timezone"""
    return datetime.now(EST)

def get_est_time() -> time:
    """Get current time in EST timezone"""
    return datetime.now(EST).time()


class PatientDashboardService:
    """Service for patient dashboard operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_data(self, current_user: CurrentUser) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for a patient
        
        Returns:
            Dictionary containing:
            - summary: Statistics (upcoming_appointments, documents_uploaded, pending_approvals)
            - upcoming_appointments: List of upcoming appointments with doctor details
            - recent_activity: List of recent activities (appointments, documents)
        """
        patient_id = current_user.id
        today = get_est_date()
        now_datetime = get_est_datetime()
        now_time = get_est_time()
        
        # Get summary statistics
        summary = self._get_summary_statistics(patient_id, today, now_time)
        
        # Get upcoming appointments
        upcoming_appointments = self._get_upcoming_appointments(patient_id, today, now_time)
        
        # Get recent activity
        recent_activity = self._get_recent_activity(patient_id)
        
        return {
            "summary": summary,
            "upcoming_appointments": upcoming_appointments,
            "recent_activity": recent_activity
        }
    
    def _get_summary_statistics(
        self,
        patient_id: UUID,
        today: date,
        now_time: time
    ) -> Dict[str, int]:
        """Get summary statistics for dashboard cards"""
        
        # Upcoming appointments count (appointments with date >= today and status not CANCELLED/NO_SHOW)
        upcoming_appointments_count = self.db.query(Appointment).filter(
            and_(
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None),
                Appointment.status.in_(['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS']),
                or_(
                    Appointment.appointment_date > today,
                    and_(
                        Appointment.appointment_date == today,
                        Appointment.start_time >= now_time
                    )
                )
            )
        ).count()
        
        # Documents uploaded count (all non-deleted documents)
        documents_count = self.db.query(PatientDocument).filter(
            and_(
                PatientDocument.patient_id == patient_id,
                PatientDocument.deleted_at.is_(None)
            )
        ).count()
        
        # Pending approvals count (appointment requests with PENDING status)
        pending_approvals_count = self.db.query(AppointmentRequest).filter(
            and_(
                AppointmentRequest.patient_id == patient_id,
                AppointmentRequest.deleted_at.is_(None),
                AppointmentRequest.status == 'PENDING'
            )
        ).count()
        
        return {
            "upcoming_appointments": upcoming_appointments_count,
            "documents_uploaded": documents_count,
            "pending_approvals": pending_approvals_count
        }
    
    def _get_upcoming_appointments(
        self,
        patient_id: UUID,
        today: date,
        now_time: time,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get upcoming appointments with doctor details"""
        
        appointments = self.db.query(Appointment).options(
            joinedload(Appointment.doctor).joinedload(User.profile),
            joinedload(Appointment.service)
        ).filter(
            and_(
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None),
                Appointment.status.in_(['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS']),
                or_(
                    Appointment.appointment_date > today,
                    and_(
                        Appointment.appointment_date == today,
                        Appointment.start_time >= now_time
                    )
                )
            )
        ).order_by(
            Appointment.appointment_date.asc(),
            Appointment.start_time.asc()
        ).limit(limit).all()
        
        appointments_data = []
        for appointment in appointments:
            doctor = appointment.doctor
            doctor_profile = doctor.profile if doctor and hasattr(doctor, 'profile') else None
            service = appointment.service
            
            # Get doctor specialty from profile or service
            specialty = None
            if doctor_profile:
                # Try to get specialty from profile (could be in bio or education)
                if doctor_profile.bio:
                    specialty = doctor_profile.bio
                elif doctor_profile.education:
                    specialty = doctor_profile.education
            if not specialty and service:
                specialty = service.name
            if not specialty:
                specialty = "General Physician"
            
            # Format doctor name
            doctor_name = doctor.name if doctor else "Unknown Doctor"
            if doctor_profile:
                if doctor_profile.first_name and doctor_profile.last_name:
                    full_name = f"{doctor_profile.first_name} {doctor_profile.last_name}"
                    if doctor_profile.title:
                        doctor_name = f"{doctor_profile.title} {full_name}"
                    else:
                        doctor_name = full_name
                elif doctor_profile.title:
                    doctor_name = f"{doctor_profile.title} {doctor_name}"
            
            # Format appointment date and time
            appointment_datetime = datetime.combine(appointment.appointment_date, appointment.start_time)
            formatted_date = appointment.appointment_date.strftime("%Y-%m-%d")
            formatted_time = appointment.start_time.strftime("%I:%M %p")
            
            appointments_data.append({
                "id": str(appointment.id),
                "doctor": {
                    "id": str(doctor.id) if doctor else None,
                    "name": doctor_name,
                    "specialty": specialty or "General Physician",
                    "profile_image": doctor_profile.avatar if doctor_profile else None
                },
                "service": {
                    "id": str(service.id) if service else None,
                    "name": service.name if service else None
                },
                "appointment_date": formatted_date,
                "appointment_time": formatted_time,
                "appointment_datetime": appointment_datetime.isoformat(),
                "status": appointment.status,
                "consultation_mode": appointment.consultation_mode
            })
        
        return appointments_data
    
    def _get_recent_activity(
        self,
        patient_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent activity from appointments and documents"""
        
        activities = []
        
        # Get recent appointment requests (ACCEPTED status for "confirmed" activities)
        appointment_requests = self.db.query(AppointmentRequest).options(
            joinedload(AppointmentRequest.doctor).joinedload(User.profile),
            joinedload(AppointmentRequest.service)
        ).filter(
            and_(
                AppointmentRequest.patient_id == patient_id,
                AppointmentRequest.deleted_at.is_(None),
                AppointmentRequest.status == 'ACCEPTED'
            )
        ).order_by(
            AppointmentRequest.updated_at.desc()
        ).limit(limit).all()
        
        for req in appointment_requests:
            doctor = req.doctor
            doctor_name = doctor.name if doctor else "Unknown Doctor"
            if doctor and hasattr(doctor, 'profile') and doctor.profile:
                if doctor.profile.first_name and doctor.profile.last_name:
                    doctor_name = f"{doctor.profile.first_name} {doctor.profile.last_name}"
            
            service_name = req.service.name if req.service else "Service"
            formatted_date = req.preferred_date.strftime("%b %d")
            
            activities.append({
                "id": str(req.id),
                "type": "appointment_confirmed",
                "icon": "checkmark",  # Frontend can map this to an icon
                "message": f"Your appointment with {doctor_name} has been confirmed for {formatted_date}.",
                "created_at": req.updated_at.isoformat() if req.updated_at else None,
                "metadata": {
                    "appointment_request_id": str(req.id),
                    "doctor_id": str(doctor.id) if doctor else None,
                    "doctor_name": doctor_name,
                    "service_name": service_name,
                    "appointment_date": req.preferred_date.isoformat()
                }
            })
        
        # Get recent document uploads
        documents = self.db.query(PatientDocument).filter(
            and_(
                PatientDocument.patient_id == patient_id,
                PatientDocument.deleted_at.is_(None)
            )
        ).order_by(
            PatientDocument.created_at.desc()
        ).limit(limit).all()
        
        for doc in documents:
            activities.append({
                "id": str(doc.id),
                "type": "document_uploaded",
                "icon": "upload",  # Frontend can map this to an icon
                "message": f"{doc.document_type} uploaded successfully.",
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "metadata": {
                    "document_id": str(doc.id),
                    "document_type": doc.document_type,
                    "file_name": doc.file_name
                }
            })
        
        # Sort all activities by created_at (most recent first)
        activities.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        
        # Return top N activities
        return activities[:limit]
