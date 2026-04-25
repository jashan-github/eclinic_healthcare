"""
Doctor Patient Service
Business logic for doctors to manage their patients
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, distinct, desc, exists
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.appointment import Appointment
from app.models.appointment_request import AppointmentRequest
from app.models.user import User
from app.models.patient_vital_signs import PatientVitalSigns
from app.models.profile import UserProfile
from loguru import logger


class DoctorPatientService:
    """Service for doctors to manage their patients"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_doctor_patients(
        self,
        doctor_id: UUID,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated list of patients who have appointments with the doctor
        
        Includes patients with:
        - Confirmed/completed appointments (Appointment table)
        - Accepted appointment requests (AppointmentRequest with status='ACCEPTED')
        
        Args:
            doctor_id: Doctor user ID
            page: Page number (1-indexed)
            per_page: Items per page
            search: Search by patient name or phone number
            
        Returns:
            Dictionary with patients list and pagination info
        """
        # Get all distinct patient IDs who have appointments OR accepted requests with this doctor
        # Use a simpler approach: Query users who have either appointments or accepted requests
        
        # Get patient IDs from appointments
        appointment_patient_ids_subq = self.db.query(
            Appointment.patient_id
        ).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.deleted_at.is_(None)
            )
        ).distinct().subquery()
        
        # Get patient IDs from accepted appointment requests
        accepted_request_patient_ids_subq = self.db.query(
            AppointmentRequest.patient_id
        ).filter(
            and_(
                AppointmentRequest.doctor_id == doctor_id,
                AppointmentRequest.status == 'ACCEPTED',
                AppointmentRequest.deleted_at.is_(None)
            )
        ).distinct().subquery()
        
        # Subqueries for aggregated stats per patient
        # Appointment stats: last date and count per patient
        appointment_stats = self.db.query(
            Appointment.patient_id.label('patient_id'),
            func.max(Appointment.appointment_date).label('last_appt_date'),
            func.count(distinct(Appointment.id)).label('appt_count')
        ).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.deleted_at.is_(None)
            )
        ).group_by(Appointment.patient_id).subquery()
        
        # Accepted request stats: last date and count per patient
        request_stats = self.db.query(
            AppointmentRequest.patient_id.label('patient_id'),
            func.max(AppointmentRequest.preferred_date).label('last_request_date'),
            func.count(distinct(AppointmentRequest.id)).label('request_count')
        ).filter(
            and_(
                AppointmentRequest.doctor_id == doctor_id,
                AppointmentRequest.status == 'ACCEPTED',
                AppointmentRequest.deleted_at.is_(None)
            )
        ).group_by(AppointmentRequest.patient_id).subquery()
        
        # Main query: Get patient details with aggregated stats from subqueries
        base_query = self.db.query(
            User.id,
            User.name,
            User.email,
            User.phone,
            User.clinic_id,
            User.created_at,
            User.is_active,
            # Get last visited date: max of appointment dates and accepted request preferred dates
            # Use CASE to handle NULL dates properly
            func.nullif(
                func.greatest(
                    func.coalesce(appointment_stats.c.last_appt_date, date(1900, 1, 1)),
                    func.coalesce(request_stats.c.last_request_date, date(1900, 1, 1))
                ),
                date(1900, 1, 1)
            ).label('last_visited_date'),
            # Count total: appointments + accepted requests
            (
                func.coalesce(appointment_stats.c.appt_count, 0) + 
                func.coalesce(request_stats.c.request_count, 0)
            ).label('total_appointments')
        ).filter(
            and_(
                User.role == 'patient',
                User.deleted_at.is_(None),
                # Patient must have either appointments OR accepted requests
                or_(
                    User.id.in_(self.db.query(appointment_patient_ids_subq.c.patient_id)),
                    User.id.in_(self.db.query(accepted_request_patient_ids_subq.c.patient_id))
                )
            )
        ).outerjoin(
            appointment_stats,
            appointment_stats.c.patient_id == User.id
        ).outerjoin(
            request_stats,
            request_stats.c.patient_id == User.id
        )
        
        # Apply search filter if provided
        if search:
            search_pattern = f"%{search}%"
            base_query = base_query.filter(
                or_(
                    User.name.ilike(search_pattern),
                    User.phone.ilike(search_pattern)
                )
            )
        
        # Group by patient to get distinct patients
        # Include subquery columns in GROUP BY since they're used in SELECT
        base_query = base_query.group_by(
            User.id,
            User.name,
            User.email,
            User.phone,
            User.clinic_id,
            User.created_at,
            User.is_active,
            appointment_stats.c.last_appt_date,
            appointment_stats.c.appt_count,
            request_stats.c.last_request_date,
            request_stats.c.request_count
        )
        
        # Get total count before pagination
        total = base_query.count()
        
        # Apply pagination and ordering
        offset = (page - 1) * per_page
        results = base_query.order_by(desc('last_visited_date')).offset(offset).limit(per_page).all()
        
        # Extract patient IDs from results
        patient_ids = [result.id for result in results]
        
        # Pre-fetch all profiles in one query to avoid N+1
        profiles_map = {}
        if patient_ids:
            profiles = self.db.query(UserProfile).filter(
                UserProfile.user_id.in_(patient_ids)
            ).all()
            profiles_map = {profile.user_id: profile for profile in profiles}
        
        # Pre-fetch all clinics in one query
        clinic_ids = [result.clinic_id for result in results if result.clinic_id]
        clinics_map = {}
        if clinic_ids:
            from app.models.user import Clinic
            clinics = self.db.query(Clinic).filter(Clinic.id.in_(clinic_ids)).all()
            clinics_map = {clinic.id: clinic.name for clinic in clinics}
        
        # Pre-fetch vital signs status for all patients
        vital_signs_patient_ids = set()
        if patient_ids:
            vitals = self.db.query(PatientVitalSigns.patient_id).filter(
                and_(
                    PatientVitalSigns.patient_id.in_(patient_ids),
                    PatientVitalSigns.deleted_at.is_(None),
                    PatientVitalSigns.share_with_doctor == True
                )
            ).distinct().all()
            vital_signs_patient_ids = {vital[0] for vital in vitals}
        
        # Pre-fetch today's appointments for all patients with this doctor
        # Include both confirmed appointments AND accepted appointment requests
        today = date.today()
        today_appointments_map = {}
        today_appointment_requests_map = {}  # Track appointment request IDs separately
        
        if patient_ids:
            # Get confirmed appointments for today
            today_appointments = self.db.query(
                Appointment.patient_id,
                Appointment.id
            ).filter(
                and_(
                    Appointment.doctor_id == doctor_id,
                    Appointment.patient_id.in_(patient_ids),
                    Appointment.appointment_date == today,
                    Appointment.status.in_(['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS']),
                    Appointment.deleted_at.is_(None)
                )
            ).all()
            
            # Map patient_id -> appointment_id (if multiple, take first one)
            for appt in today_appointments:
                if appt.patient_id not in today_appointments_map:
                    today_appointments_map[appt.patient_id] = appt.id
            
            # Also get ACCEPTED appointment requests for today (not yet paid/converted to appointment)
            today_accepted_requests = self.db.query(
                AppointmentRequest.patient_id,
                AppointmentRequest.id
            ).filter(
                and_(
                    AppointmentRequest.doctor_id == doctor_id,
                    AppointmentRequest.patient_id.in_(patient_ids),
                    AppointmentRequest.preferred_date == today,
                    AppointmentRequest.status == 'ACCEPTED',
                    AppointmentRequest.deleted_at.is_(None)
                )
            ).all()
            
            # Map patient_id -> appointment_request_id (only if no confirmed appointment exists)
            for req in today_accepted_requests:
                if req.patient_id not in today_appointments_map:
                    today_appointment_requests_map[req.patient_id] = req.id
        
        # Build patient list with additional info
        patients_data = []
        
        for result in results:
            patient_id = result.id
            profile = profiles_map.get(patient_id)
            
            # Extract profile information
            gender = None
            age = None
            if profile:
                gender = profile.gender
                # Calculate age from date_of_birth
                if profile.date_of_birth:
                    dob = profile.date_of_birth
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            # Check if patient has vital signs (medical history status)
            has_vital_signs = patient_id in vital_signs_patient_ids
            
            # Extract medical history text from medical_info JSONB
            medical_history_text = self._extract_medical_history_text(profile)
            
            # Get full medical info
            medical_info = self._safe_get_medical_info(profile)
            
            # Get patient's clinic name from pre-fetched map
            clinic_name = clinics_map.get(result.clinic_id) if result.clinic_id else None
            
            # Check if patient has appointment today with this doctor
            # First check confirmed appointments, then accepted requests
            today_appointment_id = today_appointments_map.get(patient_id)
            today_appointment_request_id = today_appointment_requests_map.get(patient_id)
            
            # Determine which ID to use and whether it's a request or appointment
            is_appointment_request = False
            if today_appointment_id:
                # Has a confirmed appointment
                pass
            elif today_appointment_request_id:
                # Has an accepted request (not yet paid)
                today_appointment_id = today_appointment_request_id
                is_appointment_request = True
            
            # Build patient data
            patient_data = {
                "id": str(patient_id),
                "name": result.name,
                "email": result.email,
                "phone": result.phone,
                "gender": gender,
                "age": age,
                "clinic_id": str(result.clinic_id) if result.clinic_id else None,
                "clinic_name": clinic_name,
                "is_active": result.is_active,
                "last_visited_date": result.last_visited_date.isoformat() if result.last_visited_date else None,
                "total_appointments": result.total_appointments,
                # `has_medical_history` indicates whether the profile contains medical info
                # `has_vital_signs_shared` indicates whether the patient has consented to share vitals
                "has_medical_history": bool(medical_history_text),
                "has_vital_signs_shared": has_vital_signs,
                "medical_history_text": medical_history_text,
                # Full medical info object with all conditions, allergies, medications
                "medical_info": medical_info,
                "available_actions": self._get_available_actions(patient_id, doctor_id),
                # Appointment ID if patient has a booking today with this doctor
                # Can be either an appointment ID or an appointment request ID
                "today_appointment_id": str(today_appointment_id) if today_appointment_id else None,
                # Flag to indicate if the ID is for an appointment request (needs payment)
                "is_appointment_request": is_appointment_request
            }
            
            patients_data.append(patient_data)
        
        return {
            "patients": patients_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 0
        }
    
    def _get_available_actions(
        self,
        patient_id: UUID,
        doctor_id: UUID
    ) -> List[str]:
        """
        Get available actions for a patient
        
        Args:
            patient_id: Patient user ID
            doctor_id: Doctor user ID
            
        Returns:
            List of available action names
        """
        actions = []
        
        # Check if patient has consented vital signs
        has_consented_vitals = self.db.query(PatientVitalSigns).filter(
            and_(
                PatientVitalSigns.patient_id == patient_id,
                PatientVitalSigns.deleted_at.is_(None),
                PatientVitalSigns.share_with_doctor == True
            )
        ).first() is not None
        
        # Check if there are upcoming appointments
        from datetime import date
        has_upcoming_appointments = self.db.query(Appointment).filter(
            and_(
                Appointment.patient_id == patient_id,
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date >= date.today(),
                Appointment.status.in_(['SCHEDULED', 'CONFIRMED']),
                Appointment.deleted_at.is_(None)
            )
        ).first() is not None
        
        # Available actions
        if has_consented_vitals:
            actions.append("view_vital_signs")
        
        actions.append("view_appointments")
        actions.append("create_appointment")
        
        if has_upcoming_appointments:
            actions.append("manage_appointments")
        
        actions.append("view_profile")
        
        return actions
    
    def _extract_medical_history_text(self, profile: Optional[UserProfile]) -> Optional[str]:
        """
        Extract medical history text from profile's medical_info JSONB field
        
        Args:
            profile: UserProfile object (may be None)
            
        Returns:
            Medical history text string (e.g., "Hypertension") or None
        """
        if not profile or not hasattr(profile, 'medical_info') or not profile.medical_info:
            return None
        
        medical_info = profile.medical_info
        
        # List to collect condition names
        conditions = []
        
        # Check pre-defined conditions (if years > 0, condition exists)
        condition_mapping = {
            'hypertension_years': 'Hypertension',
            'diabetes_mellitus_years': 'Diabetes Mellitus',
            'hypothyroidism_years': 'Hypothyroidism'
        }
        
        for key, condition_name in condition_mapping.items():
            if key in medical_info and medical_info[key] is not None:
                # Condition exists if years field is present (even if 0)
                conditions.append(condition_name)
        
        # Check existing_condition field
        if 'existing_condition' in medical_info and medical_info['existing_condition']:
            conditions.append(medical_info['existing_condition'])
        
        # Check custom_conditions
        if 'custom_conditions' in medical_info and medical_info['custom_conditions']:
            custom_conditions = medical_info['custom_conditions']
            if isinstance(custom_conditions, list):
                for custom_cond in custom_conditions:
                    if isinstance(custom_cond, dict) and 'name' in custom_cond:
                        conditions.append(custom_cond['name'])
            elif isinstance(custom_conditions, dict) and 'name' in custom_conditions:
                conditions.append(custom_conditions['name'])
        
        # Return all conditions as comma-separated string
        if conditions:
            # Return all conditions, comma-separated (limit to 5 to avoid too long)
            return ", ".join(conditions[:5])
        
        return None
    
    def _safe_get_medical_info(self, profile: Optional[UserProfile]) -> Optional[Dict[str, Any]]:
        """
        Safely extract medical info from profile
        
        Args:
            profile: UserProfile object or None
            
        Returns:
            Medical info dictionary or None
        """
        if not profile or not hasattr(profile, 'medical_info') or not profile.medical_info:
            return None
        
        # Return the full medical_info JSONB object
        medical_info = profile.medical_info
        
        # Ensure it's a dictionary
        if isinstance(medical_info, dict):
            return medical_info
        
        # If it's a string (JSON), try to parse it
        if isinstance(medical_info, str):
            import json
            try:
                return json.loads(medical_info)
            except (json.JSONDecodeError, ValueError):
                return None
        
        return None
    
    def get_patient_past_visits(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get paginated list of past visits (appointments) for a specific patient with the doctor
        
        IMPORTANT: Only returns appointments that have a SOAP note.
        Appointments without SOAP notes are excluded from the results.
        
        Args:
            doctor_id: Doctor user ID
            patient_id: Patient user ID
            page: Page number (1-indexed)
            per_page: Items per page
            
        Returns:
            Dictionary with visits records and pagination info
            Each visit includes the SOAP note data
        """
        from datetime import datetime
        from app.models.soap_note import SoapNote
        
        # Get past appointments for this doctor-patient pair
        # ONLY include appointments that have a SOAP note
        # Use EXISTS subquery to filter appointments with SOAP notes
        query = self.db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None),
                # Past appointments: either date is in the past or status is COMPLETED/NO_SHOW/CANCELLED
                or_(
                    Appointment.appointment_date < date.today(),
                    Appointment.status.in_(['COMPLETED', 'NO_SHOW', 'CANCELLED'])
                ),
                # Only include appointments that have a SOAP note (not deleted)
                exists().where(
                    and_(
                        SoapNote.appointment_id == Appointment.id,
                        SoapNote.deleted_at.is_(None)
                    )
                )
            )
        )
        
        # Get total count (only appointments with SOAP notes)
        total = query.count()
        
        # Apply pagination and sorting (most recent first)
        offset = (page - 1) * per_page
        appointments = query.order_by(desc(Appointment.appointment_date), desc(Appointment.start_time)).offset(offset).limit(per_page).all()
        
        # Get SOAP notes for these appointments (all should have SOAP notes)
        appointment_ids = [appt.id for appt in appointments]
        soap_notes = []
        if appointment_ids:
            soap_notes = self.db.query(SoapNote).filter(
                and_(
                    SoapNote.appointment_id.in_(appointment_ids),
                    SoapNote.deleted_at.is_(None)
                )
            ).all()
        
        # Create a map of appointment_id -> soap_note
        soap_notes_map = {soap.appointment_id: soap for soap in soap_notes}
        
        # Format visits
        visits = []
        for appt in appointments:
            # Determine check_status based on appointment status
            check_status = "Pending"
            if appt.status in ['COMPLETED', 'IN_PROGRESS']:
                check_status = "Checked"
            elif appt.status in ['CANCELLED', 'NO_SHOW']:
                check_status = "Cancelled"
            
            # Format appointment date
            appt_date = appt.appointment_date
            appointment_date_obj = {
                "date": appt_date.isoformat(),
                "day": f"{appt_date.day:02d}",
                "day_name": appt_date.strftime("%a"),  # Mon, Tue, etc.
                "month_name": appt_date.strftime("%b"),  # Jan, Feb, etc.
                "month": f"{appt_date.month:02d}",
                "year": str(appt_date.year)
            }
            
            # Format created_at as "11 Dec 2025 17:22:47"
            if appt.created_at:
                appointment_created_at = appt.created_at.strftime("%d %b %Y %H:%M:%S")
            else:
                appointment_created_at = ""
            
            # Get SOAP note for this appointment (should always exist due to query filter)
            soap_note = soap_notes_map.get(appt.id)
            if not soap_note:
                # Skip appointments without SOAP notes (shouldn't happen due to query filter, but defensive check)
                continue
            
            # Format SOAP note data
            soap_data = {
                "id": str(soap_note.id),
                "subjective": soap_note.subjective,
                "objective": soap_note.objective,
                "assessment": soap_note.assessment,
                "plan": soap_note.plan,
                "created_at": soap_note.created_at.isoformat() if soap_note.created_at else None,
                "updated_at": soap_note.updated_at.isoformat() if soap_note.updated_at else None
            }
            
            visit = {
                "id": str(appt.id),
                "title": f"Regular appointment on {appt_date.strftime('%b %Y')}",
                "appointment_created_at": appointment_created_at,
                "appointment_start_time": appt.start_time.isoformat() if appt.start_time else "00:00:00",
                "appointment_end_time": appt.end_time.isoformat() if appt.end_time else "00:00:00",
                "check_status": check_status,
                "bookingId": None,
                "device_type": None,
                "notes": "",
                "precription_pdf_url": None,
                "digital_precription_pdf_url": None,
                "video_call_recordings": [],
                "assessment_summary": None,
                "appointment_date": appointment_date_obj,
                "soap_note": soap_data  # Always present (query filtered for appointments with SOAP notes)
            }
            visits.append(visit)
        
        # Calculate skip value for response (offset in pagination terms)
        skip = (page - 1) * per_page
        
        return {
            "records": visits,
            "skip": skip,
            "limit": per_page,
            "total": total
        }
    
    def get_patient_detail(self, doctor_id: UUID, patient_id: UUID) -> Dict[str, Any]:
        """
        Get detailed information for a specific patient
        
        Args:
            doctor_id: Doctor user ID
            patient_id: Patient user ID
            
        Returns:
            Dictionary with patient details
        """
        from datetime import datetime, date
        
        # Get patient
        patient = self.db.query(User).filter(
            User.id == patient_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            return None
        
        # Get patient profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == patient_id
        ).first()
        
        # Get contact details (primary contact)
        from app.models.profile import ContactDetail
        contact = self.db.query(ContactDetail).filter(
            ContactDetail.user_id == patient_id,
            ContactDetail.is_primary == True
        ).first()
        
        # If no primary contact, get any contact
        if not contact:
            contact = self.db.query(ContactDetail).filter(
                ContactDetail.user_id == patient_id
            ).first()
        
        # Calculate age from date_of_birth
        age_years = None
        date_of_birth_str = None
        if profile and profile.date_of_birth:
            today = date.today()
            age_years = today.year - profile.date_of_birth.year
            if (today.month, today.day) < (profile.date_of_birth.month, profile.date_of_birth.day):
                age_years -= 1
            # Format date_of_birth as DD-MM-YYYY
            date_of_birth_str = profile.date_of_birth.strftime("%d-%m-%Y")
        
        # Extract health issues from medical_info
        health_issues = []
        if profile and profile.medical_info:
            medical_info = profile.medical_info
            
            # Collect health issues from medical_info JSONB field
            # Structure: {"hypertension": {"years": 5}, "diabetes": {"years": 10}, ...}
            condition_mapping = {
                "hypertension": "Hypertension",
                "diabetes": "Diabetes",
                "asthma": "Asthma",
                "heart_disease": "Heart Disease",
                "thyroid": "Thyroid Disorder",
                "arthritis": "Arthritis",
                "cancer": "Cancer",
                "depression": "Depression",
                "anxiety": "Anxiety"
            }
            
            for key, display_name in condition_mapping.items():
                if key in medical_info and medical_info[key]:
                    health_issues.append(display_name)
            
            # Check existing_condition field
            if 'existing_condition' in medical_info and medical_info['existing_condition']:
                health_issues.append(medical_info['existing_condition'])
            
            # Check custom_conditions
            if 'custom_conditions' in medical_info and medical_info['custom_conditions']:
                custom_conditions = medical_info['custom_conditions']
                if isinstance(custom_conditions, list):
                    for custom_cond in custom_conditions:
                        if isinstance(custom_cond, dict) and 'name' in custom_cond:
                            health_issues.append(custom_cond['name'])
                elif isinstance(custom_conditions, dict) and 'name' in custom_conditions:
                    health_issues.append(custom_conditions['name'])
        
        # Get preferred language name
        preferred_language = None
        if profile and profile.preferred_language:
            preferred_language = profile.preferred_language.language_name
        
        # Build address (from contact details)
        address = None
        if contact and contact.address_line_1:
            address_parts = [contact.address_line_1]
            if contact.address_line_2:
                address_parts.append(contact.address_line_2)
            if contact.city and hasattr(contact.city, 'name'):
                address_parts.append(contact.city.name)
            if contact.state and hasattr(contact.state, 'name'):
                address_parts.append(contact.state.name)
            if contact.postal_code:
                address_parts.append(contact.postal_code)
            address = ", ".join(address_parts)
        
        # Age object
        age_obj = None
        if age_years is not None:
            age_obj = {
                "age": age_years,
                "type": "years",
                "full_age": f"{age_years} years"
            }
        
        return {
            "id": str(patient.id),
            "name": patient.name,
            "age": age_obj,
            "phone_number": contact.phone if contact else None,
            "gender": profile.gender if profile else None,
            "address": address,
            "email": patient.email,
            "emergency_contact_number": contact.emergency_contact_phone if contact else None,
            "blood_type": profile.blood_type if profile else None,
            "occupation": profile.occupation if profile else None,
            "date_of_birth": date_of_birth_str,
            "family_contact_number": contact.family_contact_phone if contact else None,
            "marital_status": profile.marital_status if profile else None,
            "preferred_language": preferred_language,
            "health_issues": health_issues
        }
    
    def get_patient_medical_info(self, doctor_id: UUID, patient_id: UUID) -> Dict[str, Any]:
        """
        Get medical information for a specific patient (for doctor view)
        
        Args:
            doctor_id: Doctor user ID
            patient_id: Patient user ID
            
        Returns:
            Dictionary with patient medical info
        """
        # Get patient profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == patient_id
        ).first()
        
        if not profile:
            return None
        
        # Get medical info from JSONB field
        medical_info = profile.medical_info if profile.medical_info else {}
        
        return {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "medical_info": medical_info,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
        }
    
    def update_patient_medical_info(self, doctor_id: UUID, patient_id: UUID, medical_info: dict) -> Dict[str, Any]:
        """
        Update patient's medical information
        
        Args:
            doctor_id: Doctor user ID
            patient_id: Patient user ID
            medical_info: Medical information dict
            
        Returns:
            Updated profile data
        """
        # Get patient profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == patient_id
        ).first()
        
        if not profile:
            profile = UserProfile(user_id=patient_id)
            self.db.add(profile)
        
        # Update medical info
        try:
            if isinstance(medical_info, dict):
                profile.medical_info = medical_info
            elif hasattr(medical_info, 'model_dump'):
                profile.medical_info = medical_info.model_dump(exclude_unset=True, exclude_none=True)
        except Exception as e:
            logger.error(f"Error updating medical_info for patient {patient_id}: {e}", exc_info=True)
            raise
        
        # Commit changes
        self.db.commit()
        self.db.refresh(profile)
        
        return {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "medical_info": profile.medical_info if profile.medical_info else {},
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
        }

