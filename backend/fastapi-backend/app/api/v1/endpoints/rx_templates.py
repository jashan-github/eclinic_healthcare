"""
RX Template API Endpoints
Doctor-only routes for managing prescription templates
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, status, Path, Form, File, UploadFile, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_feature
from app.core.security import CurrentUser
from app.services.rx_template_service import RxTemplateService
from app.services.clinic_location_service import ClinicLocationService
from app.models.clinic_location import ClinicLocation
from app.schemas.rx_template import (
    RxTemplateListResponse,
    RxTemplateSingleResponse,
    RxTemplateDeleteResponse
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    ForbiddenException,
    laravel_response
)
from loguru import logger


router = APIRouter(
    prefix="/doctor/rx-templates",
    tags=["Doctor - RX Templates"],
    dependencies=[Depends(require_feature("rx_templates"))],
)


def get_rx_template_service(db: Session = Depends(get_db)) -> RxTemplateService:
    """Dependency to get RX template service"""
    return RxTemplateService(db)


def get_clinic_location_service(db: Session = Depends(get_db)) -> ClinicLocationService:
    """Dependency to get clinic location service"""
    return ClinicLocationService(db)


@router.get(
    "/locations",
    status_code=status.HTTP_200_OK,
    summary="Get clinic locations for RX templates",
    description="""Get all clinic locations available for creating RX templates
    
**Use Cases:**
- Get list of clinic locations that the doctor can use for RX templates
- Locations are filtered by the doctor's clinic
- Returns location information needed for template creation

**Response includes:**
- Location ID, name, branch type
- Address information
- Contact details (phone, email)
- Geographic information (country, state, city)

**Example Response:**
```json
{
  "status": true,
  "message": "Clinic locations retrieved successfully",
  "data": {
    "locations": [
      {
        "id": "93f951f4-3d45-4395-aa18-c2115656d633",
        "name": "Pure Health BV",
        "branch_type": "Main Branch",
        "address": "#139E Union Road, Cole Bay",
        "phone": "+1 (721) 544-2275",
        "email": "purehealthbv@gmail.com",
        "country": "Sint Maarten",
        "state": "Sint Maarten",
        "city": "Cole Bay",
        "is_primary": true
      }
    ]
  }
}
```"""
)
async def get_clinic_locations(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    location_service: ClinicLocationService = Depends(get_clinic_location_service)
):
    """
    Get clinic locations for RX templates
    
    **Doctor-only endpoint**
    Returns all clinic locations from the doctor's clinic
    """
    # Check if user is doctor
    if current_user.role != "doctor":
        raise ForbiddenException(
            message="This endpoint is only for doctors",
            errors={"role": ["Only doctors can use this endpoint"]}
        )
    
    try:
        # Get doctor's clinic ID
        from app.models.user import User
        doctor = db.query(User).filter(User.id == current_user.id).first()
        
        if not doctor or not doctor.clinic_id:
            raise NotFoundException(
                message="Doctor clinic not found",
                errors={"clinic": ["Doctor is not associated with a clinic"]}
            )
        
        # Get all locations for the doctor's clinic
        locations = location_service.get_all_locations(clinic_id=doctor.clinic_id)
        
        # Format locations for response
        locations_data = [
            {
                "id": str(location.id),
                "name": location.name,
                "branch_type": location.branch_type,
                "address": location.address,
                "phone": location.phone,
                "email": location.email,
                "country": location.country.name if location.country else None,
                "state": location.state.name if location.state else None,
                "city": location.city.name if location.city else None,
                "is_primary": location.is_primary
            }
            for location in locations
        ]
        
        return laravel_response(
            success=True,
            message="Clinic locations retrieved successfully",
            data={
                "locations": locations_data
            }
        )
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve clinic locations: {str(e)}")
        raise


@router.get(
    "",
    response_model=RxTemplateListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all RX templates",
    description="""Get all RX templates for the authenticated doctor
    
**Use Cases:**
- List all templates across all clinic locations
- Filter by clinic location (optional query parameter)
- Templates are ordered by default status and creation date

**Response includes:**
- Template ID, name, and default status
- Clinic location information
- Letterhead image URL (if uploaded)
- Creation and update timestamps"""
)
async def get_all_templates(
    clinic_location_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    service: RxTemplateService = Depends(get_rx_template_service)
):
    """
    Get all RX templates for the authenticated doctor
    
    **Doctor-only endpoint**
    """
    # Check if user is doctor
    if current_user.role != "doctor":
        raise ForbiddenException(
            message="This endpoint is only for doctors",
            errors={"role": ["Only doctors can use this endpoint"]}
        )
    
    try:
        templates = service.get_all_templates(
            doctor_id=current_user.id,
            clinic_location_id=clinic_location_id
        )
        
        # Format templates for response
        formatted_templates = [
            service.format_template_response(template, base_url="https://portal.salutogenahealthcareltd.com/backend/api-fast")
            for template in templates
        ]
        
        return laravel_response(
            success=True,
            message="RX templates retrieved successfully",
            data={"templates": formatted_templates}
        )
    except Exception as e:
        logger.error(f"Failed to retrieve RX templates: {str(e)}")
        raise


@router.get(
    "/{template_id}",
    response_model=RxTemplateSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific RX template",
    description="Get details of a specific RX template by ID"
)
async def get_template(
    template_id: UUID = Path(..., description="RX template ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    service: RxTemplateService = Depends(get_rx_template_service)
):
    """
    Get a specific RX template by ID
    
    **Doctor-only endpoint**
    """
    # Check if user is doctor
    if current_user.role != "doctor":
        raise ForbiddenException(
            message="This endpoint is only for doctors",
            errors={"role": ["Only doctors can use this endpoint"]}
        )
    
    try:
        template = service.get_template_by_id(template_id, current_user.id)
        
        formatted_template = service.format_template_response(
            template,
            base_url="https://portal.salutogenahealthcareltd.com/backend/api-fast"
        )
        
        return laravel_response(
            success=True,
            message="RX template retrieved successfully",
            data=formatted_template
        )
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve RX template: {str(e)}")
        raise


@router.post(
    "",
    response_model=RxTemplateSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new RX template",
    description="""Create a new RX template for a clinic location
    
**Use Cases:**
1. **Upload custom letterhead**:
   - Upload an image file for the letterhead
   - Set `use_default_letterhead: false` (or omit it)
   - Provide `letterhead` file in multipart/form-data

2. **Use default letterhead**:
   - Set `use_default_letterhead: true`
   - Do not provide `letterhead` file

**File Requirements:**
- Allowed formats: JPG, JPEG, PNG, GIF, WEBP
- Maximum size: 5MB
- File will be stored at: `uploads/rx-templates/{doctor_id}/{clinic_location_id}/letterhead.{ext}`

**Important Notes:**
- Clinic location must exist and belong to the doctor's clinic
- Only one template can be set as default per doctor per location
- New templates are not set as default by default"""
)
async def create_template(
    clinic_location_id: UUID = Form(..., description="Clinic location ID"),
    template_name: Optional[str] = Form(None, description="Optional template name"),
    use_default_letterhead: bool = Form(False, description="Use default letterhead instead of uploading"),
    letterhead: Optional[UploadFile] = File(None, description="Letterhead image file (JPG, JPEG, PNG, GIF, WEBP, max 5MB)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    service: RxTemplateService = Depends(get_rx_template_service)
):
    """
    Create a new RX template
    
    **Doctor-only endpoint**
    Uses multipart/form-data to support file uploads for letterhead images.
    """
    # Check if user is doctor
    if current_user.role != "doctor":
        raise ForbiddenException(
            message="This endpoint is only for doctors",
            errors={"role": ["Only doctors can use this endpoint"]}
        )
    
    try:
        # Validate: if use_default_letterhead is False, letterhead file must be provided
        if not use_default_letterhead and not letterhead:
            raise ValidationException(
                message="Letterhead file is required when not using default letterhead",
                errors={"letterhead": ["Please upload a letterhead image or set use_default_letterhead to true"]}
            )
        
        # Validate: if use_default_letterhead is True, letterhead file should not be provided
        if use_default_letterhead and letterhead:
            raise ValidationException(
                message="Cannot provide letterhead file when using default letterhead",
                errors={"letterhead": ["Do not upload a file when use_default_letterhead is true"]}
            )
        
        template = await service.create_template_with_file(
            doctor_id=current_user.id,
            clinic_location_id=clinic_location_id,
            template_name=template_name,
            letterhead_file=letterhead,
            use_default_letterhead=use_default_letterhead
        )
        
        formatted_template = service.format_template_response(
            template,
            base_url="https://portal.salutogenahealthcareltd.com/backend/api-fast"
        )
        
        return laravel_response(
            success=True,
            message="RX template created successfully",
            data=formatted_template
        )
    except (NotFoundException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to create RX template: {str(e)}")
        raise


@router.put(
    "/{template_id}",
    response_model=RxTemplateSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an RX template",
    description="""Update an existing RX template
    
**Use Cases:**
1. **Update template name only**:
   - Provide only `template_name`
   - Do not change letterhead

2. **Update letterhead**:
   - Upload new `letterhead` file
   - Set `use_default_letterhead: false` (or omit it)
   - Old letterhead will be deleted

3. **Switch to default letterhead**:
   - Set `use_default_letterhead: true`
   - Do not provide `letterhead` file
   - Existing letterhead file will be deleted

**File Requirements:**
- Same as create endpoint
- Old file is automatically deleted when updating"""
)
async def update_template(
    template_id: UUID = Path(..., description="RX template ID"),
    template_name: Optional[str] = Form(None, description="Optional template name"),
    use_default_letterhead: Optional[bool] = Form(None, description="Use default letterhead instead of uploaded image"),
    letterhead: Optional[UploadFile] = File(None, description="New letterhead image file (JPG, JPEG, PNG, GIF, WEBP, max 5MB)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    service: RxTemplateService = Depends(get_rx_template_service)
):
    """
    Update an existing RX template
    
    **Doctor-only endpoint**
    Uses multipart/form-data to support file uploads for letterhead images.
    """
    # Check if user is doctor
    if current_user.role != "doctor":
        raise ForbiddenException(
            message="This endpoint is only for doctors",
            errors={"role": ["Only doctors can use this endpoint"]}
        )
    
    try:
        # Validate: if use_default_letterhead is False and provided, letterhead file must be provided
        if use_default_letterhead is False and not letterhead:
            raise ValidationException(
                message="Letterhead file is required when not using default letterhead",
                errors={"letterhead": ["Please upload a letterhead image or set use_default_letterhead to true"]}
            )
        
        # Validate: if use_default_letterhead is True, letterhead file should not be provided
        if use_default_letterhead is True and letterhead:
            raise ValidationException(
                message="Cannot provide letterhead file when using default letterhead",
                errors={"letterhead": ["Do not upload a file when use_default_letterhead is true"]}
            )
        
        template = await service.update_template(
            template_id=template_id,
            doctor_id=current_user.id,
            template_name=template_name,
            letterhead_file=letterhead,
            use_default_letterhead=use_default_letterhead
        )
        
        formatted_template = service.format_template_response(
            template,
            base_url="https://portal.salutogenahealthcareltd.com/backend/api-fast"
        )
        
        return laravel_response(
            success=True,
            message="RX template updated successfully",
            data=formatted_template
        )
    except (NotFoundException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to update RX template: {str(e)}")
        raise


@router.post(
    "/{template_id}/set-default",
    response_model=RxTemplateSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Set template as default",
    description="""Set an RX template as the default template for its clinic location
    
**Use Cases:**
- Mark a template as the default for a specific clinic location
- Only one template can be default per doctor per location
- Setting a new default will unset the previous default

**Important Notes:**
- The template must belong to the authenticated doctor
- Only one default template per doctor per clinic location"""
)
async def set_default_template(
    template_id: UUID = Path(..., description="RX template ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    service: RxTemplateService = Depends(get_rx_template_service)
):
    """
    Set an RX template as default for its clinic location
    
    **Doctor-only endpoint**
    """
    # Check if user is doctor
    if current_user.role != "doctor":
        raise ForbiddenException(
            message="This endpoint is only for doctors",
            errors={"role": ["Only doctors can use this endpoint"]}
        )
    
    try:
        template = service.set_default_template(template_id, current_user.id)
        
        formatted_template = service.format_template_response(
            template,
            base_url="https://portal.salutogenahealthcareltd.com/backend/api-fast"
        )
        
        return laravel_response(
            success=True,
            message="RX template set as default successfully",
            data=formatted_template
        )
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default RX template: {str(e)}")
        raise


@router.delete(
    "/{template_id}",
    response_model=RxTemplateDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an RX template",
    description="""Delete (soft delete) an RX template
    
**Use Cases:**
- Remove a template that is no longer needed
- Letterhead file is automatically deleted from disk
- Template is soft deleted (can be restored if needed)

**Important Notes:**
- The template must belong to the authenticated doctor
- Letterhead file will be permanently deleted"""
)
async def delete_template(
    template_id: UUID = Path(..., description="RX template ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    service: RxTemplateService = Depends(get_rx_template_service)
):
    """
    Delete an RX template
    
    **Doctor-only endpoint**
    """
    # Check if user is doctor
    if current_user.role != "doctor":
        raise ForbiddenException(
            message="This endpoint is only for doctors",
            errors={"role": ["Only doctors can use this endpoint"]}
        )
    
    try:
        service.delete_template(template_id, current_user.id)
        
        return laravel_response(
            success=True,
            message="RX template deleted successfully",
            data=None
        )
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete RX template: {str(e)}")
        raise
