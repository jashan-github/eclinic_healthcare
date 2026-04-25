"""
SOAP Notes API Endpoints
Routes for managing SOAP notes
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Path, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from loguru import logger
from io import BytesIO
import os
import tempfile

from app.core.database import get_db
from app.core.dependencies import DoctorUser, get_client_ip
from app.services.soap_note_service import SoapNoteService
from app.services.soap_pdf_service import SoapPdfService
from app.services.audit_service import AuditService
from app.schemas.soap_note import (
    SoapNoteCreate,
    SoapNoteUpdate,
    SoapNoteSingleResponse,
    SoapNoteListResponse,
    SoapNoteResponse
)
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    laravel_response
)


router = APIRouter(prefix="/doctor/patients", tags=["Doctor - SOAP Notes"])


def cleanup_temp_file(file_path: str):
    """Cleanup function to delete temporary file after response"""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Deleted temporary PDF file: {file_path}")
    except Exception as e:
        logger.error(f"Error deleting temporary PDF file {file_path}: {e}")


@router.post(
    "/{patient_id}/soap-notes",
    response_model=SoapNoteSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create SOAP note for appointment",
    description="""Create a new SOAP note for a patient's appointment

**Doctor only endpoint**

**SOAP Components:**
- **Subjective (S):** Patient's symptoms, feelings, concerns
- **Objective (O):** Observable findings, measurements, test results
- **Assessment (A):** Diagnosis, evaluation, clinical impression
- **Plan (P):** Treatment plan, medications, follow-up actions

**Validation:**
- Can only create SOAP notes for current or future appointments
- Cannot create SOAP note for past appointments
- One SOAP note per appointment (unique constraint)

**Example Request:**
```json
{
  "appointment_id": "a5894914-d964-440c-8cfb-4bec2e4792a4",
  "patient_id": "b5894914-d964-440c-8cfb-4bec2e4792a5",
  "subjective": "Feeling feverish, Symptom: Chest wall",
  "objective": "High temperature 90°, Color of face changes, High blood pressure",
  "assessment": "Infection by malaria, Mulberry molar",
  "plan": "Suggested: DOLO 650 for 10 days, Injection IV Glucose for regaining strength"
}
```"""
)
async def create_soap_note(
    patient_id: UUID = Path(..., description="Patient user ID"),
    soap_data: SoapNoteCreate = None,
    current_user: DoctorUser = None,
    db: Session = Depends(get_db)
):
    """
    Create a new SOAP note for an appointment
    
    **Doctor only endpoint**
    """
    if not soap_data:
        raise ValidationException(
            message="Request body is required",
            errors={"body": ["SOAP note data is required"]}
        )
    
    # Verify patient_id matches
    if str(soap_data.patient_id) != str(patient_id):
        raise ValidationException(
            message="Patient ID mismatch",
            errors={"patient_id": ["Patient ID in path does not match request body"]}
        )
    
    try:
        service = SoapNoteService(db)
        
        soap_note = service.create_soap_note(
            doctor_id=UUID(current_user.id),
            patient_id=soap_data.patient_id,
            appointment_id=soap_data.appointment_id,
            subjective=soap_data.subjective,
            objective=soap_data.objective,
            assessment=soap_data.assessment,
            plan=soap_data.plan
        )
        
        # Format response
        appointment = soap_note.appointment
        appt_date = appointment.appointment_date
        appt_time = appointment.start_time
        formatted_datetime = datetime.combine(appt_date, appt_time)
        
        response_data = SoapNoteResponse(
            id=str(soap_note.id),
            appointment_id=str(soap_note.appointment_id),
            subjective=soap_note.subjective,
            objective=soap_note.objective,
            assessment=soap_note.assessment,
            plan=soap_note.plan,
            appointment_date=appt_date.isoformat(),
            appointment_time=appt_time.strftime("%I:%M %p") if appt_time else None,
            appointment_datetime=formatted_datetime.isoformat(),
            created_at=soap_note.created_at.isoformat() if soap_note.created_at else None,
            updated_at=soap_note.updated_at.isoformat() if soap_note.updated_at else None,
            can_edit=service._can_edit_soap_note(appointment)
        )
        
        return laravel_response(
            success=True,
            message="SOAP note created successfully",
            data=response_data
        )
    
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Error creating SOAP note: {str(e)}", exc_info=True)
        raise ValidationException(
            message="Error creating SOAP note",
            errors={"general": [str(e)]}
        )


@router.put(
    "/{patient_id}/soap-notes/{soap_note_id}",
    response_model=SoapNoteSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update SOAP note",
    description="""Update an existing SOAP note

**Doctor only endpoint**

**Validation:**
- Can only update SOAP notes for current or future appointments
- Cannot update SOAP notes for past appointments (read-only)
- Only the doctor who created the SOAP note can update it

**Example Request:**
```json
{
  "subjective": "Updated subjective notes",
  "objective": "Updated objective notes",
  "assessment": "Updated assessment",
  "plan": "Updated plan"
}
```"""
)
async def update_soap_note(
    patient_id: UUID = Path(..., description="Patient user ID"),
    soap_note_id: UUID = Path(..., description="SOAP note ID"),
    soap_data: SoapNoteUpdate = None,
    current_user: DoctorUser = None,
    db: Session = Depends(get_db)
):
    """
    Update an existing SOAP note
    
    **Doctor only endpoint**
    """
    if not soap_data:
        raise ValidationException(
            message="Request body is required",
            errors={"body": ["SOAP note update data is required"]}
        )
    
    try:
        service = SoapNoteService(db)
        
        soap_note = service.update_soap_note(
            soap_note_id=soap_note_id,
            doctor_id=UUID(current_user.id),
            subjective=soap_data.subjective,
            objective=soap_data.objective,
            assessment=soap_data.assessment,
            plan=soap_data.plan
        )
        
        # Verify patient_id matches
        if str(soap_note.patient_id) != str(patient_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["Patient ID does not match"]}
            )
        
        # Format response
        appointment = soap_note.appointment
        appt_date = appointment.appointment_date
        appt_time = appointment.start_time
        formatted_datetime = datetime.combine(appt_date, appt_time)
        
        response_data = SoapNoteResponse(
            id=str(soap_note.id),
            appointment_id=str(soap_note.appointment_id),
            subjective=soap_note.subjective,
            objective=soap_note.objective,
            assessment=soap_note.assessment,
            plan=soap_note.plan,
            appointment_date=appt_date.isoformat(),
            appointment_time=appt_time.strftime("%I:%M %p") if appt_time else None,
            appointment_datetime=formatted_datetime.isoformat(),
            created_at=soap_note.created_at.isoformat() if soap_note.created_at else None,
            updated_at=soap_note.updated_at.isoformat() if soap_note.updated_at else None,
            can_edit=service._can_edit_soap_note(appointment)
        )
        
        return laravel_response(
            success=True,
            message="SOAP note updated successfully",
            data=response_data
        )
    
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Error updating SOAP note: {str(e)}", exc_info=True)
        raise ValidationException(
            message="Error updating SOAP note",
            errors={"general": [str(e)]}
        )


@router.get(
    "/{patient_id}/soap-notes",
    response_model=SoapNoteListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient's SOAP notes",
    description="""Get paginated list of SOAP notes for a patient

**Doctor only endpoint**

**Query Parameters:**
- **page**: Page number (default: 1)
- **per_page**: Items per page (default: 20, max: 100)

**Response includes:**
- List of SOAP notes with all SOAP components
- Appointment date and time
- Can edit flag (indicates if SOAP note can be edited)
- Pagination metadata"""
)
async def get_patient_soap_notes(
    patient_id: UUID = Path(..., description="Patient user ID"),
    current_user: DoctorUser = None,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of SOAP notes for a patient
    
    **Doctor only endpoint**
    """
    try:
        service = SoapNoteService(db)
        
        result = service.get_patient_soap_notes(
            doctor_id=UUID(current_user.id),
            patient_id=patient_id,
            page=page,
            per_page=per_page
        )
        
        return laravel_response(
            success=True,
            message="SOAP notes retrieved successfully",
            data=result
        )
    
    except Exception as e:
        logger.error(f"Error retrieving SOAP notes: {str(e)}", exc_info=True)
        raise ValidationException(
            message="Error retrieving SOAP notes",
            errors={"general": [str(e)]}
        )


@router.get(
    "/{patient_id}/soap-notes/{soap_note_id}",
    response_model=SoapNoteSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get SOAP note by ID",
    description="""Get a specific SOAP note by ID

**Doctor only endpoint**

**Response includes:**
- All SOAP components (Subjective, Objective, Assessment, Plan)
- Appointment details
- Can edit flag"""
)
async def get_soap_note(
    patient_id: UUID = Path(..., description="Patient user ID"),
    soap_note_id: UUID = Path(..., description="SOAP note ID"),
    current_user: DoctorUser = None,
    db: Session = Depends(get_db)
):
    """
    Get a specific SOAP note by ID
    
    **Doctor only endpoint**
    """
    try:
        service = SoapNoteService(db)
        
        soap_note = service.get_soap_note_by_id(
            soap_note_id=soap_note_id,
            doctor_id=UUID(current_user.id)
        )
        
        # Verify patient_id matches
        if str(soap_note.patient_id) != str(patient_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["Patient ID does not match"]}
            )
        
        # Format response
        appointment = soap_note.appointment
        appt_date = appointment.appointment_date
        appt_time = appointment.start_time
        formatted_datetime = datetime.combine(appt_date, appt_time)
        
        response_data = SoapNoteResponse(
            id=str(soap_note.id),
            appointment_id=str(soap_note.appointment_id),
            subjective=soap_note.subjective,
            objective=soap_note.objective,
            assessment=soap_note.assessment,
            plan=soap_note.plan,
            appointment_date=appt_date.isoformat(),
            appointment_time=appt_time.strftime("%I:%M %p") if appt_time else None,
            appointment_datetime=formatted_datetime.isoformat(),
            created_at=soap_note.created_at.isoformat() if soap_note.created_at else None,
            updated_at=soap_note.updated_at.isoformat() if soap_note.updated_at else None,
            can_edit=service._can_edit_soap_note(appointment)
        )
        
        return laravel_response(
            success=True,
            message="SOAP note retrieved successfully",
            data=response_data
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving SOAP note: {str(e)}", exc_info=True)
        raise ValidationException(
            message="Error retrieving SOAP note",
            errors={"general": [str(e)]}
        )


@router.get(
    "/{patient_id}/soap-notes/appointment/{appointment_id}",
    response_model=SoapNoteSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get SOAP note by appointment ID",
    description="""Get SOAP note for a specific appointment

**Doctor only endpoint**

Returns the SOAP note associated with the appointment, or 404 if not found."""
)
async def get_soap_note_by_appointment(
    patient_id: UUID = Path(..., description="Patient user ID"),
    appointment_id: UUID = Path(..., description="Appointment ID"),
    current_user: DoctorUser = None,
    db: Session = Depends(get_db)
):
    """
    Get SOAP note by appointment ID
    
    **Doctor only endpoint**
    """
    try:
        service = SoapNoteService(db)
        
        soap_note = service.get_soap_note_by_appointment(
            appointment_id=appointment_id,
            doctor_id=UUID(current_user.id)
        )
        
        if not soap_note:
            raise NotFoundException(
                message="SOAP note not found",
                errors={"appointment_id": ["No SOAP note found for this appointment"]}
            )
        
        # Verify patient_id matches
        if str(soap_note.patient_id) != str(patient_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["Patient ID does not match"]}
            )
        
        # Format response
        appointment = soap_note.appointment
        appt_date = appointment.appointment_date
        appt_time = appointment.start_time
        formatted_datetime = datetime.combine(appt_date, appt_time)
        
        response_data = SoapNoteResponse(
            id=str(soap_note.id),
            appointment_id=str(soap_note.appointment_id),
            subjective=soap_note.subjective,
            objective=soap_note.objective,
            assessment=soap_note.assessment,
            plan=soap_note.plan,
            appointment_date=appt_date.isoformat(),
            appointment_time=appt_time.strftime("%I:%M %p") if appt_time else None,
            appointment_datetime=formatted_datetime.isoformat(),
            created_at=soap_note.created_at.isoformat() if soap_note.created_at else None,
            updated_at=soap_note.updated_at.isoformat() if soap_note.updated_at else None,
            can_edit=service._can_edit_soap_note(appointment)
        )
        
        return laravel_response(
            success=True,
            message="SOAP note retrieved successfully",
            data=response_data
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving SOAP note: {str(e)}", exc_info=True)
        raise ValidationException(
            message="Error retrieving SOAP note",
            errors={"general": [str(e)]}
        )


@router.get(
    "/{patient_id}/soap-notes/{soap_note_id}/pdf",
    status_code=status.HTTP_200_OK,
    summary="Generate SOAP note PDF",
    description="""Generate a medical prescription/SOAP note PDF based on RX template

**Doctor, Clinic Admin, and Staff endpoint**

**Features:**
- Generates professional PDF with SOAP format (Subjective, Objective, Assessment, Plan)
- Uses RX template header (image or text) if available
- Includes patient information and metadata
- Multi-page support with repeating headers
- Page numbers in footer
- Printable A4 format
- PDF is automatically deleted from server after download

**Query Parameters:**
- **appointment_id** (required): Appointment ID associated with the SOAP note
- **rx_template_id** (required): RX template ID to use for header

**Response:**
- PDF file download (application/pdf)
- Filename: `soap-note-{soap_note_id}.pdf`

**Security:**
- Only authorized users (doctor, clinic admin, staff) can generate PDFs
- Audit log entry created (SOAP_PDF_GENERATED) without PHI
- SOAP content is not logged
- PDF files are automatically deleted after streaming"""
)
async def generate_soap_pdf(
    patient_id: UUID = Path(..., description="Patient user ID"),
    soap_note_id: UUID = Path(..., description="SOAP note ID"),
    appointment_id: UUID = Query(..., description="Appointment ID associated with SOAP note"),
    rx_template_id: UUID = Query(..., description="RX template ID for header"),
    request: Request = None,
    current_user: DoctorUser = None,
    db: Session = Depends(get_db),
    ip_address: str = Depends(get_client_ip)
):
    """
    Generate SOAP note PDF
    
    **Doctor, Clinic Admin, and Staff endpoint**
    
    Generates a professional PDF document with:
    - Header (clinic image or text information)
    - Patient information and metadata
    - SOAP sections (Subjective, Objective, Assessment, Plan)
    - Footer with page numbers
    
    The PDF is saved temporarily, streamed to the client, and then deleted from the server.
    """
    temp_file_path = None
    try:
        # Verify SOAP note exists and belongs to patient
        soap_note_service = SoapNoteService(db)
        soap_note = soap_note_service.get_soap_note_by_id(
            soap_note_id=soap_note_id,
            doctor_id=UUID(current_user.id)
        )
        
        # Verify patient_id matches
        if str(soap_note.patient_id) != str(patient_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["Patient ID does not match"]}
            )
        
        # Verify appointment_id matches
        if str(soap_note.appointment_id) != str(appointment_id):
            raise ValidationException(
                message="Appointment ID mismatch",
                errors={"appointment_id": ["Appointment ID does not match the SOAP note's appointment"]}
            )
        
        # Generate PDF
        pdf_service = SoapPdfService(db)
        pdf_buffer = pdf_service.generate_pdf(
            soap_note_id=soap_note_id,
            rx_template_id=rx_template_id,
            current_user_id=UUID(current_user.id)
        )
        
        # Create audit log (without PHI)
        audit_service = AuditService(db)
        user_agent = request.headers.get("user-agent") if request else None
        
        audit_service.create_audit_log(
            actor_user_id=current_user.id,
            action="SOAP_PDF_GENERATED",
            entity_type="soap_note",
            entity_id=soap_note_id,
            audit_metadata={
                "soap_note_id": str(soap_note_id),
                "appointment_id": str(appointment_id),
                "rx_template_id": str(rx_template_id)
                # Note: No PHI (patient name, SOAP content) in audit metadata
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Save PDF to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.pdf',
            prefix=f'soap-note-{soap_note_id}-',
            delete=False
        )
        temp_file_path = temp_file.name
        
        # Write PDF buffer to temporary file
        pdf_buffer.seek(0)
        temp_file.write(pdf_buffer.read())
        temp_file.close()
        
        # Return PDF as streaming response with cleanup
        filename = f"soap-note-{soap_note_id}.pdf"
        
        def generate_file_stream():
            """Generator function to stream file and cleanup after"""
            try:
                with open(temp_file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)  # Read in 8KB chunks
                        if not chunk:
                            break
                        yield chunk
            finally:
                # Cleanup: delete file after streaming is complete
                cleanup_temp_file(temp_file_path)
        
        return StreamingResponse(
            generate_file_stream(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf"
            }
        )
    
    except (NotFoundException, ForbiddenException, ValidationException):
        # Cleanup on error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        raise
    except Exception as e:
        # Cleanup on error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        logger.error(f"Error generating SOAP PDF: {str(e)}", exc_info=True)
        raise ValidationException(
            message="Error generating SOAP PDF",
            errors={"general": [str(e)]}
        )
