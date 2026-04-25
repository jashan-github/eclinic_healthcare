"""
RX Template Service
Business logic for RX template management
"""

import os
from typing import Optional, List
from uuid import UUID
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import UploadFile

from app.models.rx_template import RxTemplate
from app.models.clinic_location import ClinicLocation
from app.models.user import User
from app.core.exceptions import NotFoundException, ValidationException
from app.core.config import settings
from loguru import logger


class RxTemplateService:
    """Service for managing RX templates"""
    
    # Allowed file extensions for letterhead images
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Maximum file size: 5MB
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
    
    # Base upload directory
    BASE_UPLOAD_DIR = "uploads/rx-templates"
    
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
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        # Check file size (if available)
        if file.size and file.size > self.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed size of 5MB"
        
        return True, None
    
    def _generate_file_path(
        self,
        doctor_id: UUID,
        clinic_location_id: UUID
    ) -> tuple[str, str]:
        """
        Generate file path according to structure: uploads/rx-templates/doctor_id/clinic_location_id/letterhead.extension
        
        Returns:
            tuple: (relative_path, absolute_path)
        """
        # Create relative path
        relative_path = os.path.join(
            self.BASE_UPLOAD_DIR,
            str(doctor_id),
            str(clinic_location_id),
            "letterhead.jpg"  # Always use .jpg extension
        )
        
        # Create absolute path
        absolute_path = os.path.join(os.getcwd(), relative_path)
        
        return relative_path, absolute_path
    
    async def _save_letterhead_file(
        self,
        file: UploadFile,
        doctor_id: UUID,
        clinic_location_id: UUID
    ) -> str:
        """
        Save uploaded letterhead file and return the file path
        
        Args:
            file: Uploaded file
            doctor_id: Doctor ID
            clinic_location_id: Clinic location ID
        
        Returns:
            File path relative to uploads directory
        
        Raises:
            ValidationException: If file is invalid
        """
        # Validate file
        is_valid, error_msg = self._validate_file(file)
        if not is_valid:
            raise ValidationException(
                message="Invalid file",
                errors={"letterhead": [error_msg]}
            )
        
        # Get file extension
        ext = self._get_file_extension(file.filename)
        
        # Generate file path
        relative_path, absolute_path = self._generate_file_path(doctor_id, clinic_location_id)
        
        # Update extension in path
        relative_path = relative_path.replace('.jpg', ext)
        absolute_path = absolute_path.replace('.jpg', ext)
        
        # Create directory if it doesn't exist
        upload_dir = Path(absolute_path).parent
        try:
            upload_dir.mkdir(parents=True, mode=0o755, exist_ok=True)
        except PermissionError as e:
            logger.error(f"Permission denied creating upload directory: {upload_dir}. Error: {e}")
            raise ValidationException(
                message="Unable to save file",
                errors={"letterhead": ["Permission denied: Cannot create upload directory. Please contact administrator."]}
            )
        except OSError as e:
            logger.error(f"OS error creating upload directory: {upload_dir}. Error: {e}")
            raise ValidationException(
                message="Unable to save file",
                errors={"letterhead": [f"Error creating upload directory: {str(e)}"]}
            )
        
        # Read file contents
        try:
            contents = await file.read()
            
            # Validate file size after reading
            if len(contents) > self.MAX_FILE_SIZE:
                raise ValidationException(
                    message="File too large",
                    errors={"letterhead": [f"Maximum file size: {self.MAX_FILE_SIZE / (1024*1024)}MB"]}
                )
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise ValidationException(
                message="Unable to read file",
                errors={"letterhead": ["Error reading uploaded file"]}
            )
        
        # Save file
        try:
            with open(absolute_path, "wb") as f:
                f.write(contents)
        except PermissionError as e:
            logger.error(f"Permission denied writing file: {absolute_path}. Error: {e}")
            raise ValidationException(
                message="Unable to save file",
                errors={"letterhead": ["Permission denied: Cannot write file. Please contact administrator."]}
            )
        except OSError as e:
            logger.error(f"OS error writing file: {absolute_path}. Error: {e}")
            raise ValidationException(
                message="Unable to save file",
                errors={"letterhead": [f"Error saving file: {str(e)}"]}
            )
        
        logger.info(f"Saved letterhead file: {relative_path}")
        
        # Return relative path for database storage
        return relative_path
    
    def _delete_letterhead_file(self, file_path: str) -> bool:
        """
        Delete letterhead file from disk
        
        Args:
            file_path: Relative file path
        
        Returns:
            True if deleted successfully
        """
        if not file_path:
            return True
        
        absolute_path = os.path.join(os.getcwd(), file_path)
        
        try:
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
                logger.info(f"Deleted letterhead file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting letterhead file {file_path}: {e}")
            # Don't raise exception, just log the error
        
        return True
    
    def create_template(
        self,
        doctor_id: UUID,
        clinic_location_id: UUID,
        template_name: Optional[str] = None,
        letterhead_file: Optional[UploadFile] = None,
        use_default_letterhead: bool = False
    ) -> RxTemplate:
        """
        Create a new RX template
        
        Args:
            doctor_id: Doctor ID
            clinic_location_id: Clinic location ID
            template_name: Optional template name
            letterhead_file: Optional uploaded letterhead image
            use_default_letterhead: Use default letterhead instead of uploading
        
        Returns:
            Created RxTemplate object
        
        Raises:
            NotFoundException: If clinic location not found
            ValidationException: If validation fails
        """
        # Verify clinic location exists
        clinic_location = self.db.query(ClinicLocation).filter(
            and_(
                ClinicLocation.id == clinic_location_id,
                ClinicLocation.deleted_at.is_(None)
            )
        ).first()
        
        if not clinic_location:
            raise NotFoundException(
                message="Clinic location not found",
                errors={"clinic_location_id": ["Clinic location with this ID does not exist"]}
            )
        
        # Check if template already exists for this doctor and location
        existing_template = self.db.query(RxTemplate).filter(
            and_(
                RxTemplate.doctor_id == doctor_id,
                RxTemplate.clinic_location_id == clinic_location_id,
                RxTemplate.deleted_at.is_(None)
            )
        ).first()
        
        if existing_template:
            logger.warning(f"Attempted to create template for doctor {doctor_id} at location {clinic_location_id}, but template {existing_template.id} already exists. User should use PUT /doctor/rx-templates/{existing_template.id} to update instead.")
            raise ValidationException(
                message="Template already exists",
                errors={
                    "clinic_location_id": [
                        f"A template already exists for this doctor at this clinic location. "
                        f"Use PUT /doctor/rx-templates/{existing_template.id} to update the existing template instead."
                    ]
                }
            )
        
        # Determine letterhead path
        letterhead_path = None
        if not use_default_letterhead and letterhead_file:
            # File will be saved in the endpoint, not here
            # This is just for validation
            pass
        
        # Create template
        template = RxTemplate(
            doctor_id=doctor_id,
            clinic_location_id=clinic_location_id,
            template_name=template_name,
            letterhead_image_path=letterhead_path,  # Will be set after file upload
            is_default=False  # New templates are not default by default
        )
        
        self.db.add(template)
        self.db.flush()  # Flush to get the ID
        
        # If letterhead file is provided, save it
        if not use_default_letterhead and letterhead_file:
            # This will be handled in the endpoint
            pass
        
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Created RX template: {template.id} for doctor {doctor_id} at location {clinic_location_id}")
        
        return template
    
    async def create_template_with_file(
        self,
        doctor_id: UUID,
        clinic_location_id: UUID,
        template_name: Optional[str] = None,
        letterhead_file: Optional[UploadFile] = None,
        use_default_letterhead: bool = False
    ) -> RxTemplate:
        """
        Create a new RX template with file upload handling
        
        Args:
            doctor_id: Doctor ID
            clinic_location_id: Clinic location ID
            template_name: Optional template name
            letterhead_file: Optional uploaded letterhead image
            use_default_letterhead: Use default letterhead instead of uploading
        
        Returns:
            Created RxTemplate object
        """
        # Verify clinic location exists
        clinic_location = self.db.query(ClinicLocation).filter(
            and_(
                ClinicLocation.id == clinic_location_id,
                ClinicLocation.deleted_at.is_(None)
            )
        ).first()
        
        if not clinic_location:
            raise NotFoundException(
                message="Clinic location not found",
                errors={"clinic_location_id": ["Clinic location with this ID does not exist"]}
            )
        
        # Check if template already exists for this doctor and location
        existing_template = self.db.query(RxTemplate).filter(
            and_(
                RxTemplate.doctor_id == doctor_id,
                RxTemplate.clinic_location_id == clinic_location_id,
                RxTemplate.deleted_at.is_(None)
            )
        ).first()
        
        if existing_template:
            logger.warning(f"Attempted to create template for doctor {doctor_id} at location {clinic_location_id}, but template {existing_template.id} already exists. User should use PUT /doctor/rx-templates/{existing_template.id} to update instead.")
            raise ValidationException(
                message="Template already exists",
                errors={
                    "clinic_location_id": [
                        f"A template already exists for this doctor at this clinic location. "
                        f"Use PUT /doctor/rx-templates/{existing_template.id} to update the existing template instead."
                    ]
                }
            )
        
        # Save letterhead file if provided
        letterhead_path = None
        if not use_default_letterhead and letterhead_file:
            letterhead_path = await self._save_letterhead_file(letterhead_file, doctor_id, clinic_location_id)
        
        # Create template
        template = RxTemplate(
            doctor_id=doctor_id,
            clinic_location_id=clinic_location_id,
            template_name=template_name,
            letterhead_image_path=letterhead_path,
            is_default=False
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Created RX template: {template.id} for doctor {doctor_id} at location {clinic_location_id}")
        
        return template
    
    def get_all_templates(
        self,
        doctor_id: UUID,
        clinic_location_id: Optional[UUID] = None
    ) -> List[RxTemplate]:
        """
        Get all RX templates for a doctor
        
        Args:
            doctor_id: Doctor ID
            clinic_location_id: Optional filter by clinic location ID
        
        Returns:
            List of RxTemplate objects
        """
        query = self.db.query(RxTemplate).filter(
            and_(
                RxTemplate.doctor_id == doctor_id,
                RxTemplate.deleted_at.is_(None)
            )
        )
        
        if clinic_location_id:
            query = query.filter(RxTemplate.clinic_location_id == clinic_location_id)
        
        templates = query.order_by(
            RxTemplate.is_default.desc(),
            RxTemplate.created_at.desc()
        ).all()
        
        return templates
    
    def get_template_by_id(self, template_id: UUID, doctor_id: UUID) -> RxTemplate:
        """
        Get an RX template by ID
        
        Args:
            template_id: Template ID
            doctor_id: Doctor ID (for authorization)
        
        Returns:
            RxTemplate object
        
        Raises:
            NotFoundException: If template not found
        """
        template = self.db.query(RxTemplate).filter(
            and_(
                RxTemplate.id == template_id,
                RxTemplate.doctor_id == doctor_id,
                RxTemplate.deleted_at.is_(None)
            )
        ).first()
        
        if not template:
            raise NotFoundException(
                message="RX template not found",
                errors={"id": ["RX template with this ID does not exist"]}
            )
        
        return template
    
    async def update_template(
        self,
        template_id: UUID,
        doctor_id: UUID,
        template_name: Optional[str] = None,
        letterhead_file: Optional[UploadFile] = None,
        use_default_letterhead: Optional[bool] = None
    ) -> RxTemplate:
        """
        Update an RX template
        
        Args:
            template_id: Template ID
            doctor_id: Doctor ID (for authorization)
            template_name: Optional template name
            letterhead_file: Optional new letterhead image
            use_default_letterhead: Use default letterhead instead of uploaded image
        
        Returns:
            Updated RxTemplate object
        
        Raises:
            NotFoundException: If template not found
        """
        # Get the existing template (this also verifies ownership)
        template = self.get_template_by_id(template_id, doctor_id)
        
        # Log the update attempt for debugging
        logger.info(f"Updating RX template {template_id} for doctor {doctor_id} at location {template.clinic_location_id}")
        
        # Update template name
        if template_name is not None:
            template.template_name = template_name
        
        # Handle letterhead update
        if use_default_letterhead is not None:
            if use_default_letterhead:
                # Delete existing file if any
                if template.letterhead_image_path:
                    self._delete_letterhead_file(template.letterhead_image_path)
                template.letterhead_image_path = None
            elif letterhead_file:
                # Delete old file if exists
                if template.letterhead_image_path:
                    self._delete_letterhead_file(template.letterhead_image_path)
                # Save new file
                template.letterhead_image_path = await self._save_letterhead_file(
                    letterhead_file,
                    doctor_id,
                    template.clinic_location_id
                )
        
        # Commit changes
        try:
            self.db.commit()
            self.db.refresh(template)
            logger.info(f"Successfully updated RX template: {template_id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating RX template {template_id}: {str(e)}", exc_info=True)
            # Check if it's a unique constraint violation
            error_str = str(e).lower()
            if 'unique' in error_str or 'duplicate' in error_str:
                raise ValidationException(
                    message="Template update failed",
                    errors={"clinic_location_id": ["A template already exists for this doctor at this clinic location. This should not happen during update - please contact support."]}
                )
            raise
        
        return template
    
    def set_default_template(
        self,
        template_id: UUID,
        doctor_id: UUID
    ) -> RxTemplate:
        """
        Set a template as default for its clinic location
        
        Args:
            template_id: Template ID
            doctor_id: Doctor ID (for authorization)
        
        Returns:
            Updated RxTemplate object
        
        Raises:
            NotFoundException: If template not found
        """
        template = self.get_template_by_id(template_id, doctor_id)
        
        # Unset other default templates for this doctor at this location
        self.db.query(RxTemplate).filter(
            and_(
                RxTemplate.doctor_id == doctor_id,
                RxTemplate.clinic_location_id == template.clinic_location_id,
                RxTemplate.is_default == True,
                RxTemplate.deleted_at.is_(None),
                RxTemplate.id != template_id
            )
        ).update({"is_default": False})
        self.db.flush()
        
        # Set this template as default
        template.is_default = True
        
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Set RX template {template_id} as default for doctor {doctor_id} at location {template.clinic_location_id}")
        
        return template
    
    def delete_template(self, template_id: UUID, doctor_id: UUID) -> bool:
        """
        Soft delete an RX template
        
        Args:
            template_id: Template ID
            doctor_id: Doctor ID (for authorization)
        
        Returns:
            True if deleted successfully
        
        Raises:
            NotFoundException: If template not found
        """
        template = self.get_template_by_id(template_id, doctor_id)
        
        # Delete letterhead file if exists
        if template.letterhead_image_path:
            self._delete_letterhead_file(template.letterhead_image_path)
        
        # Soft delete
        from datetime import datetime, timezone
        template.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(f"Deleted RX template: {template_id}")
        
        return True
    
    def format_template_response(
        self,
        template: RxTemplate,
        base_url: str = None
    ) -> dict:
        """
        Format an RX template for API response
        
        Args:
            template: RxTemplate object
            base_url: Base URL for generating image URLs
        
        Returns:
            Formatted template dictionary
        """
        # Generate image URL if letterhead exists
        letterhead_url = None
        if template.letterhead_image_path:
            if base_url:
                # Remove 'uploads/' prefix if present in path
                path = template.letterhead_image_path
                if path.startswith('uploads/'):
                    path = path[8:]  # Remove 'uploads/' prefix
                letterhead_url = f"{base_url}/uploads/{path}"
            else:
                # Default base URL
                letterhead_url = f"https://portal.salutogenahealthcareltd.com/backend/api-fast/{template.letterhead_image_path}"
        
        return {
            "id": str(template.id),
            "doctor_id": str(template.doctor_id),
            "clinic_location_id": str(template.clinic_location_id),
            "clinic_location_name": template.clinic_location.name if template.clinic_location else None,
            "letterhead_image_path": template.letterhead_image_path,
            "letterhead_image_url": letterhead_url,
            "template_name": template.template_name,
            "is_default": template.is_default,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }
