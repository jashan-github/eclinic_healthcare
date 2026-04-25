"""
HIPAA Release Form API Endpoints
Routes for saving and retrieving HIPAA authorization form details
"""

from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.core.security import CurrentUser
from app.services.hipaa_release_form_service import HipaaReleaseFormService
from app.schemas.hipaa_release_form import (
    HipaaReleaseFormCreate,
    HipaaReleaseFormListResponse,
    HipaaReleaseFormSingleResponse,
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    laravel_response,
)
from loguru import logger


router = APIRouter(prefix="/patient/hipaa-release-forms", tags=["Patient - HIPAA Release Forms"])


@router.post(
    "",
    response_model=HipaaReleaseFormSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save HIPAA release form",
    description="""Save HIPAA authorization/release form details for the authenticated patient.

**Fields:** individual_name (required), date_of_birth, address, phone, email,
authorization_purpose, covered_entity, recipient_name, recipient_address,
include_medical, include_mental_health, include_substance_abuse,
expiration_date, right_to_revoke_noted, signature_name, signature_date,
relationship_to_patient, witnessed_by.
""",
)
async def create_hipaa_release_form(
    payload: HipaaReleaseFormCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Save a new HIPAA release form for the current patient."""
    try:
        service = HipaaReleaseFormService(db)
        form = service.create(patient_id=current_user.id, payload=payload)
        data = service.format_form_response(form)
        return laravel_response(
            success=True,
            message="HIPAA release form saved successfully",
            data=data,
        )
    except NotFoundException as e:
        logger.warning(f"Create HIPAA form failed: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error saving HIPAA form: {str(e)}")
        raise ValidationException(
            message="Failed to save HIPAA release form",
            errors={"error": [str(e)]},
        )


@router.get(
    "",
    response_model=HipaaReleaseFormListResponse,
    summary="List HIPAA release forms",
    description="Get all HIPAA release forms for the authenticated patient.",
)
async def list_hipaa_release_forms(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List HIPAA release forms for the current patient."""
    try:
        service = HipaaReleaseFormService(db)
        forms = service.get_by_patient_id(patient_id=current_user.id)
        data = {"forms": [service.format_form_response(f) for f in forms]}
        return laravel_response(
            success=True,
            message="HIPAA release forms retrieved successfully",
            data=data,
        )
    except Exception as e:
        logger.error(f"Unexpected error listing HIPAA forms: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve HIPAA release forms",
            errors={"error": [str(e)]},
        )


@router.get(
    "/{form_id}",
    response_model=HipaaReleaseFormSingleResponse,
    summary="Get HIPAA release form by ID",
    description="Get a single HIPAA release form by ID for the authenticated patient.",
)
async def get_hipaa_release_form(
    form_id: UUID = Path(..., description="HIPAA release form ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a HIPAA release form by ID (scoped to current patient)."""
    try:
        service = HipaaReleaseFormService(db)
        form = service.get_by_id(form_id=form_id, patient_id=current_user.id)
        data = service.format_form_response(form)
        return laravel_response(
            success=True,
            message="HIPAA release form retrieved successfully",
            data=data,
        )
    except NotFoundException as e:
        logger.warning(f"HIPAA form not found: {form_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving HIPAA form: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve HIPAA release form",
            errors={"error": [str(e)]},
        )
