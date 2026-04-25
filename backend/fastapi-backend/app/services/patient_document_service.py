"""
Patient Document Service
Business logic for patient document management
"""

import os
import shutil
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import UploadFile

from app.models.patient_document import PatientDocument
from app.models.user import User
from app.models.appointment import Appointment
from app.models.appointment_request import AppointmentRequest
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException
from loguru import logger


class PatientDocumentService:
    """Service for managing patient documents"""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'images': ['.jpg', '.jpeg', '.png'],
        'documents': ['.pdf', '.doc', '.docx']
    }
    
    # Maximum file size: 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    
    # Base upload directory
    BASE_UPLOAD_DIR = "uploads"
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        return Path(filename).suffix.lower()
    
    def _validate_file(self, file: UploadFile) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded file
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Get file extension
        ext = self._get_file_extension(file.filename)
        
        # Check if extension is allowed
        all_allowed = self.ALLOWED_EXTENSIONS['images'] + self.ALLOWED_EXTENSIONS['documents']
        if ext not in all_allowed:
            return False, f"File type not allowed. Allowed types: {', '.join(all_allowed)}"
        
        # Check file size (if available)
        if file.size and file.size > self.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed size of 50MB"
        
        return True, None
    
    def _generate_file_path(
        self,
        patient_id: UUID,
        document_type: str,
        file_extension: str
    ) -> tuple[str, str]:
        """
        Generate file path according to structure: uploads/patient_id/date/document_type.extension
        
        Returns:
            tuple: (relative_path, absolute_path)
        """
        # Get current date for folder structure
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Sanitize document type for filename
        safe_doc_type = document_type.replace(' ', '_').replace('/', '_')
        filename = f"{safe_doc_type}{file_extension}"
        
        # Create relative path
        relative_path = os.path.join(
            self.BASE_UPLOAD_DIR,
            str(patient_id),
            today,
            filename
        )
        
        # Create absolute path
        absolute_path = os.path.join(os.getcwd(), relative_path)
        
        return relative_path, absolute_path
    
    def _save_file(self, file: UploadFile, absolute_path: str) -> int:
        """
        Save uploaded file to disk
        
        Returns:
            int: File size in bytes
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
        
        # Save file
        with open(absolute_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(absolute_path)
        
        return file_size
    
    def upload_document(
        self,
        patient_id: UUID,
        file: UploadFile,
        document_type: str,
        uploaded_by: UUID,
        issued_by: Optional[str] = None,
        issued_by_id: Optional[UUID] = None,
        issued_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> PatientDocument:
        """
        Upload a patient document
        
        Args:
            patient_id: Patient user ID
            file: Uploaded file
            document_type: Type of document
            uploaded_by: User ID who is uploading
            issued_by: Doctor/issuer name
            issued_by_id: Doctor/issuer user ID (optional)
            issued_date: Date document was issued
            notes: Additional notes
            
        Returns:
            Created PatientDocument object
            
        Raises:
            NotFoundException: If patient not found
            ValidationException: If file validation fails
        """
        # Verify patient exists
        patient = self.db.query(User).filter(
            and_(
                User.id == patient_id,
                User.deleted_at.is_(None)
            )
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient with this ID does not exist"]}
            )
        
        # Validate file
        is_valid, error_msg = self._validate_file(file)
        if not is_valid:
            raise ValidationException(
                message="File validation failed",
                errors={"file": [error_msg]}
            )
        
        # Get file extension and MIME type
        file_extension = self._get_file_extension(file.filename)
        mime_type = file.content_type or "application/octet-stream"
        
        # Generate file path
        relative_path, absolute_path = self._generate_file_path(
            patient_id, document_type, file_extension
        )
        
        # If file already exists, add timestamp to avoid overwrite
        if os.path.exists(absolute_path):
            timestamp = datetime.now().strftime("%H%M%S")
            base_name = document_type.replace(' ', '_').replace('/', '_')
            filename = f"{base_name}_{timestamp}{file_extension}"
            relative_path = os.path.join(
                self.BASE_UPLOAD_DIR,
                str(patient_id),
                datetime.now().strftime("%Y-%m-%d"),
                filename
            )
            absolute_path = os.path.join(os.getcwd(), relative_path)
        
        # Save file to disk
        try:
            file_size = self._save_file(file, absolute_path)
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            raise ValidationException(
                message="Failed to save file",
                errors={"file": [f"Error saving file: {str(e)}"]}
            )
        
        # Create document record
        document = PatientDocument(
            patient_id=patient_id,
            document_type=document_type,
            file_name=file.filename,
            file_path=relative_path,
            file_size=file_size,
            file_extension=file_extension,
            mime_type=mime_type,
            issued_by=issued_by,
            issued_by_id=issued_by_id,
            issued_date=issued_date,
            uploaded_by=uploaded_by,
            notes=notes
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        logger.info(f"Uploaded document: {document_type} for patient {patient_id} (id: {document.id})")
        
        return document
    
    def get_patient_documents(
        self,
        patient_id: UUID,
        document_type: Optional[str] = None,
        file_extension: Optional[str] = None,
        issued_by: Optional[str] = None
    ) -> List[PatientDocument]:
        """
        Get patient documents with optional filters
        
        Args:
            patient_id: Patient user ID
            document_type: Filter by document type
            file_extension: Filter by file extension
            issued_by: Filter by issuer name
            
        Returns:
            List of PatientDocument objects
        """
        query = self.db.query(PatientDocument).filter(
            and_(
                PatientDocument.patient_id == patient_id,
                PatientDocument.deleted_at.is_(None)
            )
        )
        
        if document_type:
            query = query.filter(PatientDocument.document_type == document_type)
        
        if file_extension:
            query = query.filter(PatientDocument.file_extension == file_extension)
        
        if issued_by:
            query = query.filter(PatientDocument.issued_by.ilike(f"%{issued_by}%"))
        
        documents = query.order_by(
            PatientDocument.issued_date.desc().nullslast(),
            PatientDocument.created_at.desc()
        ).all()
        
        return documents
    
    def get_document_by_id(self, document_id: UUID, patient_id: UUID) -> PatientDocument:
        """
        Get a document by ID
        
        Args:
            document_id: Document ID
            patient_id: Patient ID (for authorization)
            
        Returns:
            PatientDocument object
            
        Raises:
            NotFoundException: If document not found
        """
        document = self.db.query(PatientDocument).filter(
            and_(
                PatientDocument.id == document_id,
                PatientDocument.patient_id == patient_id,
                PatientDocument.deleted_at.is_(None)
            )
        ).first()
        
        if not document:
            raise NotFoundException(
                message="Document not found",
                errors={"id": ["Document with this ID does not exist or you don't have access"]}
            )
        
        return document
    
    def delete_document(self, document_id: UUID, patient_id: UUID) -> bool:
        """
        Soft delete a document
        
        Args:
            document_id: Document ID
            patient_id: Patient ID (for authorization)
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If document not found
        """
        document = self.get_document_by_id(document_id, patient_id)
        
        # Soft delete
        from datetime import timezone
        document.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(f"Deleted document: {document.document_type} (id: {document_id})")
        
        return True
    
    def format_document_response(
        self,
        document: PatientDocument,
        include_url: bool = True,
        download_base: str = "/api/v1/patient/documents"
    ) -> dict:
        """
        Format a document for API response
        
        Args:
            document: PatientDocument object
            include_url: Whether to include download URL
            download_base: Base path for download URL (e.g. /api/v1/doctor/documents for doctor API)
            
        Returns:
            Formatted document dictionary
        """
        # Calculate file size in MB
        file_size_mb = f"{document.file_size / (1024 * 1024):.2f}"
        
        # Generate download URL if requested
        download_url = None
        if include_url:
            download_url = f"{download_base.rstrip('/')}/{document.id}/download"
        
        return {
            "id": str(document.id),
            "patient_id": str(document.patient_id),
            "document_type": document.document_type,
            "file_name": document.file_name,
            "file_path": document.file_path,
            "file_size": document.file_size,
            "file_size_mb": file_size_mb,
            "file_extension": document.file_extension,
            "mime_type": document.mime_type,
            "issued_by": document.issued_by,
            "issued_by_id": str(document.issued_by_id) if document.issued_by_id else None,
            "issued_date": document.issued_date.strftime("%Y-%m-%d") if document.issued_date else None,
            "uploaded_by": str(document.uploaded_by) if document.uploaded_by else None,
            "notes": document.notes,
            "download_url": download_url,
            "created_at": document.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": document.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "deleted_at": document.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if document.deleted_at else None
        }

    def _doctor_has_access_to_patient(self, doctor_id: UUID, patient_id: UUID) -> bool:
        """Check if doctor has at least one appointment or accepted request with the patient."""
        has_appointment = self.db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None)
            )
        ).first()
        if has_appointment:
            return True
        has_request = self.db.query(AppointmentRequest).filter(
            and_(
                AppointmentRequest.doctor_id == doctor_id,
                AppointmentRequest.patient_id == patient_id,
                AppointmentRequest.status == 'ACCEPTED',
                AppointmentRequest.deleted_at.is_(None)
            )
        ).first()
        return has_request is not None

    def get_document_by_id_for_doctor(self, document_id: UUID, doctor_id: UUID) -> PatientDocument:
        """Get a document by ID; doctor must have access to the document's patient."""
        document = self.db.query(PatientDocument).filter(
            and_(
                PatientDocument.id == document_id,
                PatientDocument.deleted_at.is_(None)
            )
        ).first()
        if not document:
            raise NotFoundException(
                message="Document not found",
                errors={"id": ["Document with this ID does not exist"]}
            )
        if not self._doctor_has_access_to_patient(doctor_id, document.patient_id):
            raise ForbiddenException(
                message="Access denied",
                errors={"id": ["You do not have access to this patient's documents"]}
            )
        return document

    def delete_document_for_doctor(self, document_id: UUID, doctor_id: UUID) -> bool:
        """Soft delete a document; doctor must have access to the document's patient."""
        document = self.get_document_by_id_for_doctor(document_id, doctor_id)
        from datetime import timezone
        document.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        logger.info(f"Doctor {doctor_id} deleted document {document_id}")
        return True
