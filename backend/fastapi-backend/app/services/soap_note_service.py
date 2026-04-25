"""
SOAP Notes Service
Business logic for managing SOAP notes
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import date, datetime, time
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from loguru import logger

from app.models.soap_note import SoapNote
from app.models.appointment import Appointment
from app.models.user import User
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.services.appointment_request_service import get_est_date, get_est_datetime, get_est_time


class SoapNoteService:
    """Service for managing SOAP notes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_soap_note(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        appointment_id: UUID,
        subjective: Optional[str] = None,
        objective: Optional[str] = None,
        assessment: Optional[str] = None,
        plan: Optional[str] = None
    ) -> SoapNote:
        """
        Create a new SOAP note for an appointment
        
        Args:
            doctor_id: Doctor user ID
            patient_id: Patient user ID
            appointment_id: Appointment ID
            subjective: Subjective notes
            objective: Objective notes
            assessment: Assessment notes
            plan: Plan notes
            
        Returns:
            Created SOAP note
            
        Raises:
            NotFoundException: If appointment not found
            ValidationException: If appointment is in the past or SOAP note already exists
            ForbiddenException: If doctor doesn't have access to this appointment
        """
        # Get appointment
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.deleted_at.is_(None)
        ).first()
        
        if not appointment:
            raise NotFoundException(
                message="Appointment not found",
                errors={"appointment_id": ["Appointment does not exist"]}
            )
        
        # Verify doctor has access to this appointment
        if appointment.doctor_id != doctor_id:
            raise ForbiddenException(
                message="Access denied",
                errors={"appointment_id": ["You do not have access to this appointment"]}
            )
        
        # Verify patient matches
        if appointment.patient_id != patient_id:
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["Patient ID does not match appointment"]}
            )
        
        # Check if SOAP note already exists
        existing_soap = self.db.query(SoapNote).filter(
            SoapNote.appointment_id == appointment_id,
            SoapNote.deleted_at.is_(None)
        ).first()
        
        if existing_soap:
            raise ValidationException(
                message="SOAP note already exists for this appointment",
                errors={"appointment_id": ["SOAP note already exists. Use update endpoint to modify it."]}
            )
        
        # Validate that appointment is current or future (can only create for current/future appointments)
        today = get_est_date()
        now_time = get_est_time()
        
        is_past = (
            appointment.appointment_date < today or
            (appointment.appointment_date == today and appointment.start_time < now_time)
        )
        
        if is_past:
            raise ValidationException(
                message="Cannot create SOAP note for past appointments",
                errors={"appointment_id": ["SOAP notes can only be created for current or future appointments"]}
            )
        
        # Create SOAP note
        soap_note = SoapNote(
            appointment_id=appointment_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            subjective=subjective,
            objective=objective,
            assessment=assessment,
            plan=plan
        )
        
        self.db.add(soap_note)
        self.db.commit()
        self.db.refresh(soap_note)
        
        # Eagerly load appointment relationship to avoid lazy loading issues
        soap_note = self.db.query(SoapNote).options(
            joinedload(SoapNote.appointment)
        ).filter(SoapNote.id == soap_note.id).first()
        
        logger.info(f"Created SOAP note {soap_note.id} for appointment {appointment_id}")
        
        return soap_note
    
    def update_soap_note(
        self,
        soap_note_id: UUID,
        doctor_id: UUID,
        subjective: Optional[str] = None,
        objective: Optional[str] = None,
        assessment: Optional[str] = None,
        plan: Optional[str] = None
    ) -> SoapNote:
        """
        Update an existing SOAP note
        
        Args:
            soap_note_id: SOAP note ID
            doctor_id: Doctor user ID (must be the creator)
            subjective: Subjective notes
            objective: Objective notes
            assessment: Assessment notes
            plan: Plan notes
            
        Returns:
            Updated SOAP note
            
        Raises:
            NotFoundException: If SOAP note not found
            ForbiddenException: If doctor doesn't have access
            ValidationException: If appointment is in the past
        """
        # Get SOAP note with appointment
        soap_note = self.db.query(SoapNote).options(
            joinedload(SoapNote.appointment)
        ).filter(
            SoapNote.id == soap_note_id,
            SoapNote.deleted_at.is_(None)
        ).first()
        
        if not soap_note:
            raise NotFoundException(
                message="SOAP note not found",
                errors={"soap_note_id": ["SOAP note does not exist"]}
            )
        
        # Verify doctor has access
        if soap_note.doctor_id != doctor_id:
            raise ForbiddenException(
                message="Access denied",
                errors={"soap_note_id": ["You do not have access to this SOAP note"]}
            )
        
        # Validate that appointment is current or future (can only update for current/future appointments)
        appointment = soap_note.appointment
        today = get_est_date()
        now_time = get_est_time()
        
        is_past = (
            appointment.appointment_date < today or
            (appointment.appointment_date == today and appointment.start_time < now_time)
        )
        
        if is_past:
            raise ValidationException(
                message="Cannot update SOAP note for past appointments",
                errors={"soap_note_id": ["SOAP notes for past appointments cannot be edited"]}
            )
        
        # Update fields (only update provided fields)
        if subjective is not None:
            soap_note.subjective = subjective
        if objective is not None:
            soap_note.objective = objective
        if assessment is not None:
            soap_note.assessment = assessment
        if plan is not None:
            soap_note.plan = plan
        
        self.db.commit()
        self.db.refresh(soap_note)
        
        logger.info(f"Updated SOAP note {soap_note.id}")
        
        return soap_note
    
    def get_soap_note_by_id(
        self,
        soap_note_id: UUID,
        doctor_id: UUID
    ) -> SoapNote:
        """
        Get a SOAP note by ID
        
        Args:
            soap_note_id: SOAP note ID
            doctor_id: Doctor user ID
            
        Returns:
            SOAP note
            
        Raises:
            NotFoundException: If SOAP note not found
            ForbiddenException: If doctor doesn't have access
        """
        soap_note = self.db.query(SoapNote).options(
            joinedload(SoapNote.appointment)
        ).filter(
            SoapNote.id == soap_note_id,
            SoapNote.deleted_at.is_(None)
        ).first()
        
        if not soap_note:
            raise NotFoundException(
                message="SOAP note not found",
                errors={"soap_note_id": ["SOAP note does not exist"]}
            )
        
        # Verify doctor has access
        if soap_note.doctor_id != doctor_id:
            raise ForbiddenException(
                message="Access denied",
                errors={"soap_note_id": ["You do not have access to this SOAP note"]}
            )
        
        return soap_note
    
    def get_soap_note_by_appointment(
        self,
        appointment_id: UUID,
        doctor_id: UUID
    ) -> Optional[SoapNote]:
        """
        Get SOAP note by appointment ID
        
        Args:
            appointment_id: Appointment ID
            doctor_id: Doctor user ID
            
        Returns:
            SOAP note or None if not found
            
        Raises:
            ForbiddenException: If doctor doesn't have access to appointment
        """
        # Verify doctor has access to appointment
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.deleted_at.is_(None)
        ).first()
        
        if not appointment:
            return None
        
        if appointment.doctor_id != doctor_id:
            raise ForbiddenException(
                message="Access denied",
                errors={"appointment_id": ["You do not have access to this appointment"]}
            )
        
        # Get SOAP note
        soap_note = self.db.query(SoapNote).options(
            joinedload(SoapNote.appointment)
        ).filter(
            SoapNote.appointment_id == appointment_id,
            SoapNote.deleted_at.is_(None)
        ).first()
        
        return soap_note
    
    def get_patient_soap_notes(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated list of SOAP notes for a patient
        
        Args:
            doctor_id: Doctor user ID
            patient_id: Patient user ID
            page: Page number (1-indexed)
            per_page: Items per page
            
        Returns:
            Dictionary with SOAP notes list and pagination info
        """
        # Get today's date for filtering - only return today's SOAP notes
        today = get_est_date()
        
        # Base query - filter to only today's SOAP notes based on appointment date
        query = self.db.query(SoapNote).options(
            joinedload(SoapNote.appointment)
        ).join(
            Appointment,
            SoapNote.appointment_id == Appointment.id
        ).filter(
            and_(
                SoapNote.doctor_id == doctor_id,
                SoapNote.patient_id == patient_id,
                SoapNote.deleted_at.is_(None),
                Appointment.appointment_date == today  # Only today's appointments
            )
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and sorting (most recent first)
        offset = (page - 1) * per_page
        soap_notes = query.order_by(
            desc(SoapNote.created_at)
        ).offset(offset).limit(per_page).all()
        
        # Format SOAP notes
        soap_notes_data = []
        for soap_note in soap_notes:
            # Access appointment (already eagerly loaded)
            appointment = soap_note.appointment
            if not appointment:
                # Skip if appointment is missing (shouldn't happen, but safety check)
                continue
            
            appt_date = appointment.appointment_date
            appt_time = appointment.start_time
            
            # Format date and time
            formatted_datetime = datetime.combine(appt_date, appt_time)
            
            soap_note_data = {
                "id": str(soap_note.id),
                "appointment_id": str(soap_note.appointment_id),
                "subjective": soap_note.subjective,
                "objective": soap_note.objective,
                "assessment": soap_note.assessment,
                "plan": soap_note.plan,
                "appointment_date": appt_date.isoformat(),
                "appointment_time": appt_time.strftime("%I:%M %p") if appt_time else None,
                "appointment_datetime": formatted_datetime.isoformat(),
                "created_at": soap_note.created_at.isoformat() if soap_note.created_at else None,
                "updated_at": soap_note.updated_at.isoformat() if soap_note.updated_at else None,
                "can_edit": self._can_edit_soap_note(appointment)
            }
            soap_notes_data.append(soap_note_data)
        
        return {
            "soap_notes": soap_notes_data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page if total > 0 else 0
            }
        }
    
    def _can_edit_soap_note(self, appointment: Appointment) -> bool:
        """
        Check if SOAP note can be edited (only current/future appointments)
        
        Args:
            appointment: Appointment object
            
        Returns:
            True if can be edited, False otherwise
        """
        today = get_est_date()
        now_time = get_est_time()
        
        is_past = (
            appointment.appointment_date < today or
            (appointment.appointment_date == today and appointment.start_time < now_time)
        )
        
        return not is_past
