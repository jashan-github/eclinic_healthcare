"""
Doctor Document API Endpoints
Doctors can upload and manage documents for their patients.
Same as patient/documents but: issued_by is always the doctor's name (not in request).
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Path, Form, File, UploadFile, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
import os

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.security import CurrentUser, UserRole
from app.models.user import User
from app.services.patient_document_service import PatientDocumentService
from app.schemas.patient_document import (
    PatientDocumentListResponse,
    PatientDocumentSingleResponse,
    PatientDocumentDeleteResponse
)
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    laravel_response
)
from loguru import logger


router = APIRouter(prefix="/doctor/documents", tags=["Doctor - Documents"])


@router.post(
    "",
    response_model=PatientDocumentSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document for a patient",
    description="""Upload a document for a patient. **issued_by** is set automatically to the doctor's name (not required in request).

**Payload (same as patient/documents except no issued_by):**
- `patient_id` (required): Patient user ID
- `file` (required): Document file
- `document_type` (required): Type of document
- `issued_date` (optional): Date document was issued (YYYY-MM-DD)
- `notes` (optional): Additional notes

**File types:** JPG, JPEG, PNG, PDF, DOC, DOCX. Max 50MB.
"""
)
async def upload_document(
    patient_id: UUID = Form(..., description="Patient user ID"),
    file: UploadFile = File(..., description="Document file"),
    document_type: str = Form(..., description="Type of document"),
    issued_date: Optional[date] = Form(None, description="Date document was issued"),
    notes: Optional[str] = Form(None, description="Additional notes"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.DOCTOR)),
):
    """Upload a document for a patient. issued_by is set to the doctor's name."""
    try:
        service = PatientDocumentService(db)
        # Verify doctor has access to this patient
        if not service._doctor_has_access_to_patient(UUID(current_user.id), patient_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["You do not have any appointments with this patient"]}
            )
        # Get doctor's name for issued_by (always doctor, not in API)
        doctor = db.query(User).filter(
            User.id == current_user.id,
            User.deleted_at.is_(None)
        ).first()
        issued_by = doctor.name if doctor and doctor.name else None
        if not issued_by:
            issued_by = doctor.email if doctor else "Doctor"

        document = service.upload_document(
            patient_id=patient_id,
            file=file,
            document_type=document_type,
            uploaded_by=UUID(current_user.id),
            issued_by=issued_by,
            issued_by_id=UUID(current_user.id),
            issued_date=issued_date,
            notes=notes
        )

        formatted = service.format_document_response(
            document, download_base="/api/v1/doctor/documents"
        )
        return laravel_response(
            success=True,
            message="Document uploaded successfully",
            data=formatted
        )
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading document: {str(e)}")
        raise ValidationException(
            message="Failed to upload document",
            errors={"error": [str(e)]}
        )


@router.get(
    "",
    response_model=PatientDocumentListResponse,
    summary="Get documents for a patient",
    description="""Get all documents for a patient. Doctor must have at least one appointment with the patient.

**Query Parameters:**
- `patient_id` (required): Patient user ID
- `document_type`: Filter by document type
- `file_extension`: Filter by file extension
- `issued_by`: Filter by issuer name (partial match)
"""
)
async def get_documents(
    patient_id: UUID = Query(..., description="Patient user ID"),
    document_type: Optional[str] = Query(None),
    file_extension: Optional[str] = Query(None),
    issued_by: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.DOCTOR)),
):
    """Get all documents for a patient (doctor must have access)."""
    try:
        service = PatientDocumentService(db)
        if not service._doctor_has_access_to_patient(UUID(current_user.id), patient_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["You do not have any appointments with this patient"]}
            )
        documents = service.get_patient_documents(
            patient_id=patient_id,
            document_type=document_type,
            file_extension=file_extension,
            issued_by=issued_by
        )
        formatted = [
            service.format_document_response(doc, download_base="/api/v1/doctor/documents")
            for doc in documents
        ]
        return laravel_response(
            success=True,
            message="Documents retrieved successfully",
            data={"documents": formatted}
        )
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving documents: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve documents",
            errors={"error": [str(e)]}
        )


@router.get(
    "/{document_id}",
    response_model=PatientDocumentSingleResponse,
    summary="Get a specific document",
    description="Get details of a specific document by ID. Doctor must have access to the patient."
)
async def get_document(
    document_id: UUID = Path(..., description="Document ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.DOCTOR)),
):
    """Get a specific document."""
    try:
        service = PatientDocumentService(db)
        document = service.get_document_by_id_for_doctor(document_id, UUID(current_user.id))
        formatted = service.format_document_response(
            document, download_base="/api/v1/doctor/documents"
        )
        return laravel_response(
            success=True,
            message="Document retrieved successfully",
            data=formatted
        )
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving document: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve document",
            errors={"error": [str(e)]}
        )


@router.get(
    "/{document_id}/download",
    summary="Download a document",
    description="Download a document file. Doctor must have access to the patient."
)
async def download_document(
    document_id: UUID = Path(..., description="Document ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.DOCTOR)),
):
    """Download a document file."""
    try:
        service = PatientDocumentService(db)
        document = service.get_document_by_id_for_doctor(document_id, UUID(current_user.id))
        file_path = os.path.join(os.getcwd(), document.file_path)
        if not os.path.exists(file_path):
            raise NotFoundException(
                message="File not found",
                errors={"file": ["Document file does not exist on server"]}
            )
        return FileResponse(
            path=file_path,
            media_type=document.mime_type,
            filename=document.file_name
        )
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading document: {str(e)}")
        raise ValidationException(
            message="Failed to download document",
            errors={"error": [str(e)]}
        )


@router.delete(
    "/{document_id}",
    response_model=PatientDocumentDeleteResponse,
    summary="Delete a document",
    description="Soft delete a patient document. Doctor must have access to the patient."
)
async def delete_document(
    document_id: UUID = Path(..., description="Document ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.DOCTOR)),
):
    """Delete a document."""
    try:
        service = PatientDocumentService(db)
        service.delete_document_for_doctor(document_id, UUID(current_user.id))
        return laravel_response(
            success=True,
            message="Document deleted successfully",
            data={}
        )
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting document: {str(e)}")
        raise ValidationException(
            message="Failed to delete document",
            errors={"error": [str(e)]}
        )
