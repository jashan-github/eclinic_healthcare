"""
Patient Document API Endpoints
Routes for managing patient medical documents
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Path, Form, File, UploadFile, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
import os

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import CurrentUser
from app.services.patient_document_service import PatientDocumentService
from app.schemas.patient_document import (
    PatientDocumentListResponse,
    PatientDocumentSingleResponse,
    PatientDocumentDeleteResponse
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    laravel_response
)
from loguru import logger


router = APIRouter(prefix="/patient/documents", tags=["Patient - Documents"])


@router.post(
    "",
    response_model=PatientDocumentSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a patient document",
    description="""Upload a new medical document for a patient

**Supported File Types:**
- Images: JPG, JPEG, PNG
- Documents: PDF, DOC, DOCX

**Maximum File Size:** 50MB per file

**File Storage Structure:**
- Path: `uploads/patient_id/YYYY-MM-DD/document_type.extension`
- Example: `uploads/abc-123/2026-01-08/Blood_Test_Report.pdf`

**Fields:**
- `file` (required): The document file to upload
- `document_type` (required): Type of document (e.g., "Blood Test Report", "X-Ray", "Prescription")
- `issued_by` (optional): Name of the doctor/issuer
- `issued_date` (optional): Date the document was issued (YYYY-MM-DD)
- `notes` (optional): Additional notes about the document

**Example:**
```bash
curl -X POST "http://example.com/api/v1/patient/documents" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -F "file=@/path/to/document.pdf" \\
  -F "document_type=Blood Test Report" \\
  -F "issued_by=Dr. Sara Johnson" \\
  -F "issued_date=2026-01-08" \\
  -F "notes=Annual checkup results"
```"""
)
async def upload_document(
    file: UploadFile = File(..., description="Document file"),
    document_type: str = Form(..., description="Type of document"),
    issued_by: Optional[str] = Form(None, description="Doctor/issuer name"),
    issued_date: Optional[date] = Form(None, description="Date document was issued"),
    notes: Optional[str] = Form(None, description="Additional notes"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Upload a patient document
    """
    try:
        service = PatientDocumentService(db)
        
        # Upload document (patient uploads their own documents)
        document = service.upload_document(
            patient_id=current_user.id,
            file=file,
            document_type=document_type,
            uploaded_by=current_user.id,
            issued_by=issued_by,
            issued_date=issued_date,
            notes=notes
        )
        
        formatted_document = service.format_document_response(document)
        
        return laravel_response(
            success=True,
            message="Document uploaded successfully",
            data=formatted_document
        )
        
    except (NotFoundException, ValidationException) as e:
        logger.warning(f"Failed to upload document: {e.message}")
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
    summary="Get patient documents",
    description="""Get all documents for the authenticated patient

**Query Parameters:**
- `document_type`: Filter by document type
- `file_extension`: Filter by file extension (.pdf, .jpg, etc.)
- `issued_by`: Filter by issuer name (partial match)

**Response includes:**
- Document metadata
- File information (name, size, type)
- Issued by and date information
- Download URL

**Documents are ordered by:**
1. Issued date (most recent first)
2. Upload date (most recent first)

**Example Response:**
```json
{
  "status": true,
  "message": "Documents retrieved successfully",
  "data": {
    "documents": [
      {
        "id": "...",
        "document_type": "Blood Test Report",
        "file_name": "lab_results.pdf",
        "file_size_mb": "1.25",
        "issued_by": "Dr. Sara Johnson",
        "issued_date": "2025-07-20",
        "download_url": "/api/v1/patient/documents/{id}/download"
      }
    ]
  }
}
```"""
)
async def get_documents(
    document_type: Optional[str] = None,
    file_extension: Optional[str] = None,
    issued_by: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get all documents for the authenticated patient
    """
    try:
        service = PatientDocumentService(db)
        
        documents = service.get_patient_documents(
            patient_id=current_user.id,
            document_type=document_type,
            file_extension=file_extension,
            issued_by=issued_by
        )
        
        formatted_documents = [
            service.format_document_response(doc)
            for doc in documents
        ]
        
        return laravel_response(
            success=True,
            message="Documents retrieved successfully",
            data={"documents": formatted_documents}
        )
        
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
    description="Get details of a specific document by ID"
)
async def get_document(
    document_id: UUID = Path(..., description="Document ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get a specific document
    """
    try:
        service = PatientDocumentService(db)
        document = service.get_document_by_id(document_id, current_user.id)
        
        formatted_document = service.format_document_response(document)
        
        return laravel_response(
            success=True,
            message="Document retrieved successfully",
            data=formatted_document
        )
        
    except NotFoundException as e:
        logger.warning(f"Document not found: {document_id}")
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
    description="""Download a document file

**Returns:**
- The actual file with appropriate content type
- Content-Disposition header for file download
- Original filename preserved

**Example:**
```bash
curl -X GET "http://example.com/api/v1/patient/documents/{id}/download" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -O -J
```"""
)
async def download_document(
    document_id: UUID = Path(..., description="Document ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Download a document file
    """
    try:
        service = PatientDocumentService(db)
        document = service.get_document_by_id(document_id, current_user.id)
        
        # Get absolute file path
        file_path = os.path.join(os.getcwd(), document.file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise NotFoundException(
                message="File not found",
                errors={"file": ["Document file does not exist on server"]}
            )
        
        # Return file response
        return FileResponse(
            path=file_path,
            media_type=document.mime_type,
            filename=document.file_name
        )
        
    except NotFoundException as e:
        logger.warning(f"Document or file not found: {document_id}")
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
    description="""Delete a patient document

**Notes:**
- This is a soft delete (document is marked as deleted but not removed)
- The physical file remains on disk
- Deleted documents will not appear in list results
- Cannot be undone via API
"""
)
async def delete_document(
    document_id: UUID = Path(..., description="Document ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete a patient document
    """
    try:
        service = PatientDocumentService(db)
        service.delete_document(document_id, current_user.id)
        
        return laravel_response(
            success=True,
            message="Document deleted successfully",
            data={}
        )
        
    except NotFoundException as e:
        logger.warning(f"Document not found: {document_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting document: {str(e)}")
        raise ValidationException(
            message="Failed to delete document",
            errors={"error": [str(e)]}
        )
