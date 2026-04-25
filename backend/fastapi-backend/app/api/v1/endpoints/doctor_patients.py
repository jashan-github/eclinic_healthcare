"""
Doctor Patients API Endpoints
Routes for doctors to manage their patients
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import DoctorUser, require_feature
from app.core.security import CurrentUser
from app.services.doctor_patient_service import DoctorPatientService
from app.schemas.doctor_patient import (
    DoctorPatientListResponse,
    PatientVisitsListResponse,
    PatientDetailSingleResponse,
    DoctorPatientMedicalInfoSingleResponse
)
from app.schemas.profile import PatientMedicalInfoUpdate
from app.core.exceptions import laravel_response, NotFoundException, ForbiddenException, ValidationException
from loguru import logger


router = APIRouter(
    prefix="/doctor/patients",
    tags=["Doctor - Patients"],
    dependencies=[Depends(require_feature("patients"))],
)


@router.get(
    "",
    response_model=DoctorPatientListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get doctor's patients list",
    description="Retrieves a paginated list of patients who have appointments with the authenticated doctor. Returns patient details including personal info, medical info, last visited and available actions. Supports search by patient name or phone number."
)
async def get_doctor_patients(
    current_user: DoctorUser,
    page: int = Query(1, ge=1, description="Page number (default: 1)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (default: 20, max: 100)"),
    search: Optional[str] = Query(None, description="Search by patient name or phone number"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of patients who have appointments with the authenticated doctor
    
    **Doctor only endpoint**
    
    Includes patients with:
    - Confirmed/completed appointments (Appointment table)
    - Accepted appointment requests (AppointmentRequest with status='ACCEPTED')
    
    Returns patient details including:
    - Personal information (name, email, phone, gender, age)
    - Last visited date (most recent appointment date or accepted request date)
    - Medical history (whether patient has consented vital signs and condition names)
    - Total appointment count (including both appointments and accepted requests)
    - Available actions (what the doctor can do with this patient)
    
    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **search**: Optional search term to filter by patient name or phone number
    
    **Response Fields:**
    - **id**: Patient user ID
    - **name**: Patient full name
    - **email**: Patient email address
    - **phone**: Patient phone number
    - **clinic_id**: Clinic ID where patient is registered
    - **clinic_name**: Clinic name
    - **is_active**: Whether patient account is active
    - **last_visited_date**: Date of most recent appointment or accepted request (ISO format: YYYY-MM-DD)
    - **total_appointments**: Total number of appointments and accepted requests with this doctor
    - **has_medical_history**: Whether patient has medical history recorded in profile (true/false)
    - **has_vital_signs_shared**: Whether patient has consented to share vital signs with the doctor (true/false)
    - **medical_history_text**: Medical condition name extracted from patient profile (e.g., "Hypertension") or None
    - **gender**: Patient gender (male, female, other) or None
    - **age**: Patient age calculated from date of birth or None
    - **available_actions**: List of available actions:
      - `view_vital_signs`: Patient has consented vital signs
      - `view_appointments`: Can view patient appointments
      - `create_appointment`: Can create new appointment
      - `manage_appointments`: Has upcoming appointments to manage
      - `view_profile`: Can view patient profile
    
    **Search:**
    The search parameter filters patients by:
    - Patient name (case-insensitive partial match)
    - Phone number (case-insensitive partial match)
    
    **Pagination:**
    Results are paginated and sorted by last visited date (most recent first).
    
    Args:
        page: Page number (1-indexed)
        per_page: Number of items per page
        search: Optional search term for name or phone
        
    Returns:
        Paginated list of patients with their details
    """
    service = DoctorPatientService(db)
    
    # Get patients list
    result = service.get_doctor_patients(
        doctor_id=UUID(current_user.id),
        page=page,
        per_page=per_page,
        search=search
    )
    
    return laravel_response(
        success=True,
        message=f"Retrieved {len(result['patients'])} patient(s)",
        data={
            "patients": result["patients"],
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "per_page": result["per_page"],
                "total_pages": result["total_pages"]
            }
        }
    )


@router.get(
    "/{patient_id}/visits",
    response_model=PatientVisitsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient's past visits",
    description="Retrieves the complete history of past visits (appointments) for a specific patient with the authenticated doctor. Includes visit dates, consultation details, and other visit-related information."
)
async def get_patient_past_visits(
    current_user: DoctorUser,
    patient_id: UUID = Path(..., description="Patient user ID"),
    page: int = Query(1, ge=1, description="Page number (default: 1)"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page (default: 10, max: 50)"),
    db: Session = Depends(get_db)
):
    """
    Get past visits for a specific patient
    
    **Doctor only endpoint**
    
    Retrieves all past appointments (visits) for a specific patient with the authenticated doctor.
    Includes completed, cancelled, and past appointments.
    
    **Path Parameters:**
    - **patient_id**: Patient user ID
    
    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 10, max: 50)
    
    **Response Fields per visit:**
    - **id**: Appointment ID
    - **title**: Visit title (e.g., "Regular appointment on Dec 2025")
    - **appointment_created_at**: Date/time when appointment was created (e.g., "11 Dec 2025 17:22:47")
    - **appointment_start_time**: Appointment start time (HH:MM:SS)
    - **appointment_end_time**: Appointment end time (HH:MM:SS)
    - **check_status**: "Pending", "Checked", or "Cancelled"
    - **bookingId**: Booking ID (null for now)
    - **device_type**: Device type (null for now)
    - **notes**: Visit notes (empty string for now)
    - **precription_pdf_url**: Prescription PDF URL (null)
    - **digital_precription_pdf_url**: Digital prescription PDF URL (null)
    - **video_call_recordings**: List of video recordings (empty array)
    - **assessment_summary**: Assessment summary (null)
    - **appointment_date**: Date breakdown with date, day, day_name, month_name, month, year
    
    Args:
        patient_id: Patient user ID
        page: Page number
        per_page: Items per page
        
    Returns:
        Paginated list of past visits with pagination metadata
    """
    service = DoctorPatientService(db)
    
    try:
        # Get patient to verify they have appointments with this doctor
        from app.models.user import User
        from app.models.appointment import Appointment
        from sqlalchemy import and_
        
        patient = db.query(User).filter(
            User.id == patient_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient does not exist"]}
            )
        
        # Verify the patient has at least one appointment OR accepted request with this doctor
        from app.models.appointment_request import AppointmentRequest
        
        has_appointment = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == UUID(current_user.id),
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None)
            )
        ).first()
        
        # Also check for accepted appointment requests
        has_accepted_request = db.query(AppointmentRequest).filter(
            and_(
                AppointmentRequest.doctor_id == UUID(current_user.id),
                AppointmentRequest.patient_id == patient_id,
                AppointmentRequest.status == 'ACCEPTED',
                AppointmentRequest.deleted_at.is_(None)
            )
        ).first()
        
        if not has_appointment and not has_accepted_request:
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["You do not have any appointments with this patient"]}
            )
        
        # Get past visits
        visits_data = service.get_patient_past_visits(
            doctor_id=UUID(current_user.id),
            patient_id=patient_id,
            page=page,
            per_page=per_page
        )
        
        return laravel_response(
            success=True,
            message="Past visits fetched successfully",
            data=visits_data
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving patient visits: {str(e)}", exc_info=True)
        raise NotFoundException(
            message="Error retrieving patient visits",
            errors={"general": [str(e)]}
        )


@router.get(
    "/{patient_id}",
    response_model=PatientDetailSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient's detailed information",
    description="Retrieves detailed information for a specific patient including personal details, contact information, medical history, and health issues."
)
async def get_patient_detail(
    current_user: DoctorUser,
    patient_id: UUID = Path(..., description="Patient user ID"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific patient
    
    **Doctor only endpoint**
    
    Retrieves comprehensive patient details including personal info, contact information,
    medical history, and health issues. Doctor must have at least one appointment with the patient.
    
    **Path Parameters:**
    - **patient_id**: Patient user ID
    
    **Response Fields:**
    - **id**: Patient user ID
    - **name**: Patient full name
    - **age**: Object with age in years and full_age string
    - **phone_number**: Patient phone number
    - **gender**: Patient gender
    - **address**: Full formatted address
    - **email**: Patient email
    - **emergency_contact_number**: Emergency contact phone
    - **blood_type**: Patient blood type
    - **occupation**: Patient occupation
    - **date_of_birth**: Date of birth in DD-MM-YYYY format
    - **family_contact_number**: Family contact phone
    - **marital_status**: Marital status
    - **preferred_language**: Preferred language name
    - **health_issues**: List of health conditions/issues
    
    Args:
        patient_id: Patient user ID
        
    Returns:
        Detailed patient information
    """
    service = DoctorPatientService(db)
    
    try:
        # Get patient to verify they exist
        from app.models.user import User
        from app.models.appointment import Appointment
        from sqlalchemy import and_
        
        patient = db.query(User).filter(
            User.id == patient_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient does not exist"]}
            )
        
        # Verify the patient has at least one appointment OR accepted request with this doctor
        from app.models.appointment_request import AppointmentRequest
        
        has_appointment = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == UUID(current_user.id),
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None)
            )
        ).first()
        
        # Also check for accepted appointment requests
        has_accepted_request = db.query(AppointmentRequest).filter(
            and_(
                AppointmentRequest.doctor_id == UUID(current_user.id),
                AppointmentRequest.patient_id == patient_id,
                AppointmentRequest.status == 'ACCEPTED',
                AppointmentRequest.deleted_at.is_(None)
            )
        ).first()
        
        if not has_appointment and not has_accepted_request:
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["You do not have any appointments with this patient"]}
            )
        
        # Get patient detail
        patient_detail = service.get_patient_detail(
            doctor_id=UUID(current_user.id),
            patient_id=patient_id
        )
        
        if not patient_detail:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient details not found"]}
            )
        
        return laravel_response(
            success=True,
            data=patient_detail
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving patient detail: {str(e)}", exc_info=True)
        raise NotFoundException(
            message="Error retrieving patient detail",
            errors={"general": [str(e)]}
        )


@router.get(
    "/{patient_id}/medical",
    response_model=DoctorPatientMedicalInfoSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient's medical information",
    description="Retrieve the patient's medical information (conditions, allergies, medications). Authenticated Doctor-only endpoint."
)
async def get_doctor_patient_medical_info(
    current_user: DoctorUser,
    patient_id: UUID = Path(..., description="Patient user ID"),
    db: Session = Depends(get_db)
):
    """
    Get patient medical information for doctor
    
    **Doctor only endpoint**
    
    Retrieves patient's medical information including conditions, allergies, and medications.
    Doctor must have at least one appointment with the patient.
    
    **Path Parameters:**
    - **patient_id**: Patient user ID
    
    **Response Fields:**
    - **id**: Profile ID
    - **user_id**: Patient user ID
    - **medical_info**: Medical information object containing:
      - existing_condition: Custom existing condition text
      - hypertension_years: Years with hypertension
      - diabetes_mellitus_years: Years with diabetes
      - asthma_years: Years with asthma
      - arthritis_years: Years with arthritis
      - heart_disease_years: Years with heart disease
      - thyroid_years: Years with thyroid issues
      - depression_years: Years with depression
      - anxiety_years: Years with anxiety
      - cancer_years: Years with cancer
      - allergies: List of allergies
      - medications: Current medications
      - and other medical fields
    - **created_at**: Profile creation timestamp
    - **updated_at**: Profile last update timestamp
    
    Args:
        patient_id: Patient user ID
        
    Returns:
        Patient medical information
    """
    service = DoctorPatientService(db)
    
    try:
        # Get patient to verify they exist
        from app.models.user import User
        from app.models.appointment import Appointment
        from sqlalchemy import and_
        
        patient = db.query(User).filter(
            User.id == patient_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient does not exist"]}
            )
        
        # Verify the patient has at least one appointment OR accepted request with this doctor
        from app.models.appointment_request import AppointmentRequest
        
        has_appointment = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == UUID(current_user.id),
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None)
            )
        ).first()
        
        # Also check for accepted appointment requests
        has_accepted_request = db.query(AppointmentRequest).filter(
            and_(
                AppointmentRequest.doctor_id == UUID(current_user.id),
                AppointmentRequest.patient_id == patient_id,
                AppointmentRequest.status == 'ACCEPTED',
                AppointmentRequest.deleted_at.is_(None)
            )
        ).first()
        
        if not has_appointment and not has_accepted_request:
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["You do not have any appointments with this patient"]}
            )
        
        # Get patient medical info
        medical_info = service.get_patient_medical_info(
            doctor_id=UUID(current_user.id),
            patient_id=patient_id
        )
        
        if not medical_info:
            raise NotFoundException(
                message="Medical information not found",
                errors={"patient_id": ["Patient medical information not found"]}
            )
        
        return laravel_response(
            success=True,
            message="Medical information retrieved successfully",
            data=medical_info
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving patient medical info: {str(e)}", exc_info=True)
        raise NotFoundException(
            message="Error retrieving patient medical info",
            errors={"general": [str(e)]}
        )


@router.put(
    "/{patient_id}/medical",
    response_model=DoctorPatientMedicalInfoSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update patient's medical information",
    description="Update a patient's medical information (conditions, allergies, medications). Authenticated Doctor-only endpoint."
)
async def update_doctor_patient_medical_info(
    current_user: DoctorUser,
    patient_id: UUID = Path(..., description="Patient user ID"),
    profile_data: PatientMedicalInfoUpdate = None,
    db: Session = Depends(get_db)
):
    """
    Update patient medical information for doctor
    
    **Doctor only endpoint**
    
    Updates patient's medical information including:
    - Pre-defined conditions (diabetes, hypertension, etc.) with years
    - Custom conditions
    - Existing conditions
    - Allergies
    - Current medications
    
    Doctor must have at least one appointment with the patient.
    
    **Path Parameters:**
    - **patient_id**: Patient user ID
    
    **Request Body:**
    - **medical_info**: Medical information object containing conditions, allergies, medications
    
    **Response Fields:**
    - **id**: Profile ID
    - **user_id**: Patient user ID
    - **medical_info**: Updated medical information object
    - **created_at**: Profile creation timestamp
    - **updated_at**: Profile last update timestamp
    
    Args:
        patient_id: Patient user ID
        profile_data: Patient medical information update data
        
    Returns:
        Updated patient medical information
    """
    service = DoctorPatientService(db)
    
    try:
        # Get patient to verify they exist
        from app.models.user import User
        from app.models.appointment import Appointment
        from sqlalchemy import and_
        
        patient = db.query(User).filter(
            User.id == patient_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient does not exist"]}
            )
        
        # Verify the patient has at least one appointment OR accepted request with this doctor
        from app.models.appointment_request import AppointmentRequest
        
        has_appointment = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == UUID(current_user.id),
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None)
            )
        ).first()
        
        # Also check for accepted appointment requests
        has_accepted_request = db.query(AppointmentRequest).filter(
            and_(
                AppointmentRequest.doctor_id == UUID(current_user.id),
                AppointmentRequest.patient_id == patient_id,
                AppointmentRequest.status == 'ACCEPTED',
                AppointmentRequest.deleted_at.is_(None)
            )
        ).first()
        
        if not has_appointment and not has_accepted_request:
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["You do not have any appointments with this patient"]}
            )
        
        # Get medical info from request
        if not profile_data:
            raise ValidationException(
                message="Request body is required",
                errors={"medical_info": ["Medical information is required"]}
            )
        
        medical_info = getattr(profile_data, 'medical_info', None)
        if medical_info is None:
            raise ValidationException(
                message="Medical information is required",
                errors={"medical_info": ["Medical information field is required"]}
            )
        
        # Convert medical_info to dict if it's a Pydantic model
        if hasattr(medical_info, 'model_dump'):
            medical_info_dict = medical_info.model_dump(exclude_unset=True, exclude_none=True)
        else:
            medical_info_dict = medical_info
        
        # Update patient medical info
        updated_info = service.update_patient_medical_info(
            doctor_id=UUID(current_user.id),
            patient_id=patient_id,
            medical_info=medical_info_dict
        )
        
        if not updated_info:
            raise NotFoundException(
                message="Medical information not found",
                errors={"patient_id": ["Patient medical information not found"]}
            )
        
        return laravel_response(
            success=True,
            message="Medical information updated successfully",
            data=updated_info
        )
    
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Error updating patient medical info: {str(e)}", exc_info=True)
        raise NotFoundException(
            message="Error updating patient medical info",
            errors={"general": [str(e)]}
        )


@router.get(
    "/{patient_id}/documents",
    status_code=status.HTTP_200_OK,
    summary="Get patient's documents",
    description="Retrieves a paginated list of documents uploaded by a patient. Doctor must have at least one appointment with the patient."
)
async def get_patient_documents(
    patient_id: UUID = Path(..., description="Patient user ID"),
    current_user: DoctorUser = None,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    page: int = Query(1, ge=1, description="Page number (default: 1)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (default: 20, max: 100)"),
    db: Session = Depends(get_db)
):
    """
    Get patient documents for doctor
    
    **Doctor only endpoint**
    
    Retrieves paginated list of documents uploaded by the patient.
    Doctor must have at least one appointment or accepted request with the patient.
    
    **Path Parameters:**
    - **patient_id**: Patient user ID
    
    **Query Parameters:**
    - **document_type**: Optional filter by document type (e.g., "Blood Test Report", "X-Ray")
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    
    **Response Fields per document:**
    - **id**: Document ID
    - **document_type**: Type of document (Blood Test Report, X-Ray, etc.)
    - **file_name**: Original file name
    - **file_url**: URL to access the document
    - **file_size**: File size in bytes
    - **file_extension**: File extension (pdf, jpg, png, etc.)
    - **mime_type**: MIME type of the file
    - **issued_by**: Doctor/issuer name
    - **issued_date**: Date document was issued (YYYY-MM-DD)
    - **notes**: Additional notes about the document
    - **created_at**: Upload timestamp
    
    Args:
        patient_id: Patient user ID
        document_type: Optional filter by document type
        page: Page number
        per_page: Items per page
        
    Returns:
        Paginated list of patient documents
    """
    try:
        from app.models.user import User
        from app.models.appointment import Appointment
        from app.models.appointment_request import AppointmentRequest
        from app.models.patient_document import PatientDocument
        from sqlalchemy import and_, desc
        from app.core.config import settings
        
        # Verify patient exists
        patient = db.query(User).filter(
            User.id == patient_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient does not exist"]}
            )
        
        # Verify the doctor has at least one appointment OR accepted request with this patient
        has_appointment = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == UUID(current_user.id),
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None)
            )
        ).first()
        
        has_accepted_request = db.query(AppointmentRequest).filter(
            and_(
                AppointmentRequest.doctor_id == UUID(current_user.id),
                AppointmentRequest.patient_id == patient_id,
                AppointmentRequest.status == 'ACCEPTED',
                AppointmentRequest.deleted_at.is_(None)
            )
        ).first()
        
        if not has_appointment and not has_accepted_request:
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["You do not have any appointments with this patient"]}
            )
        
        # Build query for patient documents
        query = db.query(PatientDocument).filter(
            and_(
                PatientDocument.patient_id == patient_id,
                PatientDocument.deleted_at.is_(None)
            )
        )
        
        # Apply document type filter if provided
        if document_type:
            query = query.filter(PatientDocument.document_type.ilike(f"%{document_type}%"))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and sorting (most recent first)
        offset = (page - 1) * per_page
        documents = query.order_by(desc(PatientDocument.created_at)).offset(offset).limit(per_page).all()
        
        # Format documents response
        documents_data = []
        base_url = (getattr(settings, 'BASE_URL', '') or '').rstrip('/')
        
        for doc in documents:
            # Build file URL
            # file_path already includes 'uploads/' prefix (e.g., uploads/patient_id/date/file.pdf)
            if doc.file_path:
                # Remove 'uploads/' prefix if present since we add it in the URL
                path = doc.file_path
                if path.startswith('uploads/'):
                    path = path[8:]  # Remove 'uploads/' prefix
                file_url = f"{base_url}/uploads/{path}"
            else:
                file_url = None
            
            doc_data = {
                "id": str(doc.id),
                "document_type": doc.document_type,
                "file_name": doc.file_name,
                "file_url": file_url,
                "file_size": doc.file_size,
                "file_extension": doc.file_extension,
                "mime_type": doc.mime_type,
                "issued_by": doc.issued_by,
                "issued_date": doc.issued_date.isoformat() if doc.issued_date else None,
                "notes": doc.notes,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            }
            documents_data.append(doc_data)
        
        return laravel_response(
            success=True,
            message=f"Retrieved {len(documents_data)} document(s)",
            data={
                "documents": documents_data,
                "pagination": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page if total > 0 else 0
                }
            }
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving patient documents: {str(e)}", exc_info=True)
        raise NotFoundException(
            message="Error retrieving patient documents",
            errors={"general": [str(e)]}
        )
