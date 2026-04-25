"""
Clinic endpoints
API endpoints for clinic management
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.dependencies import get_db, get_current_user_optional
from app.core.security import CurrentUser
from app.core.exceptions import laravel_response, NotFoundException
from app.models.user import Clinic
from app.models.location import Country
from app.schemas.clinic import (
    ClinicResponse,
    ClinicsListResponse,
    ClinicSingleResponse
)

router = APIRouter()


@router.get("", response_model=ClinicsListResponse, status_code=200, include_in_schema=False)
@router.get("/", response_model=ClinicsListResponse, status_code=200)
async def list_clinics(
    status: Optional[str] = Query(None, description="Filter by status (active, inactive)"),
    country_id: Optional[UUID] = Query(None, description="Filter by country ID"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Get list of all clinics
    
    **Laravel-compatible endpoint** - Public (no authentication required)
    
    Query parameters:
    - **status**: Filter by status (active, inactive)
    - **country_id**: Filter by country ID (UUID)
    - **search**: Search by clinic name or code
    
    Returns all clinics sorted by name.
    Public endpoint - if authenticated, clinic admins will only see their own clinic.
    """
    query = db.query(Clinic).options(
        joinedload(Clinic.country_rel)
    ).filter(
        Clinic.deleted_at.is_(None)
    )
    
    # If user is clinic_admin, only show their clinic
    if current_user and current_user.role == "clinic_admin" and current_user.clinic_id:
        query = query.filter(Clinic.id == current_user.clinic_id)
    
    # Apply filters
    if status:
        query = query.filter(Clinic.status == status)
    
    if country_id:
        query = query.filter(Clinic.country_id == country_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Clinic.name.ilike(search_term)) | (Clinic.code.ilike(search_term))
        )
    
    clinics = query.order_by(Clinic.name).all()
    
    clinics_data = [
        ClinicResponse(
            id=clinic.id,
            name=clinic.name,
            code=clinic.code,
            timezone=clinic.timezone,
            country_id=clinic.country_id,
            country_name=clinic.country_rel.name if clinic.country_rel else None,
            status=clinic.status,
            metadata=clinic.clinic_metadata,
            created_at=clinic.created_at,
            updated_at=clinic.updated_at
        )
        for clinic in clinics
    ]
    
    return laravel_response(
        success=True,
        message="Clinics retrieved successfully",
        data={"clinics": clinics_data}
    )


@router.get("/{clinic_id}", response_model=ClinicSingleResponse, status_code=200)
async def get_clinic(
    clinic_id: UUID = Path(..., description="Clinic ID (UUID)"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Get a single clinic by ID
    
    **Laravel-compatible endpoint** - Public (no authentication required)
    
    Path parameters:
    - **clinic_id**: Clinic ID (UUID)
    
    Returns clinic details.
    Public endpoint - if authenticated, clinic admins can only access their own clinic.
    """
    query = db.query(Clinic).options(
        joinedload(Clinic.country_rel)
    ).filter(
        Clinic.id == clinic_id,
        Clinic.deleted_at.is_(None)
    )
    
    # If user is clinic_admin, verify they can access this clinic
    if current_user and current_user.role == "clinic_admin":
        if current_user.clinic_id != clinic_id:
            raise NotFoundException(
                message="Clinic not found",
                errors={"clinic_id": ["Clinic does not exist or you don't have access"]}
            )
    
    clinic = query.first()
    
    if not clinic:
        raise NotFoundException(
            message="Clinic not found",
            errors={"clinic_id": ["Clinic does not exist"]}
        )
    
    clinic_data = ClinicResponse(
        id=clinic.id,
        name=clinic.name,
        code=clinic.code,
        timezone=clinic.timezone,
        country_id=clinic.country_id,
        country_name=clinic.country_rel.name if clinic.country_rel else None,
        status=clinic.status,
        metadata=clinic.clinic_metadata,
        created_at=clinic.created_at,
        updated_at=clinic.updated_at
    )
    
    return laravel_response(
        success=True,
        message="Clinic retrieved successfully",
        data={"clinic": clinic_data}
    )

