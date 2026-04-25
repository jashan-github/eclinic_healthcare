"""
Admin Medical Service CRUD endpoints
Only admins can create, read, update, and delete medical services (specialties).
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Path, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.core.security import CurrentUser
from app.core.exceptions import laravel_response, NotFoundException, BadRequestException
from app.models.medical_service import MedicalService
from app.schemas.medical_service import MedicalServiceCreate, MedicalServiceUpdate
from loguru import logger


router = APIRouter(prefix="/admin/medical-services", tags=["Admin - Medical Services"])


def _service_to_dict(service: MedicalService) -> dict:
    """Format MedicalService model to response dict."""
    return {
        "id": str(service.id),
        "parent": service.parent,
        "name": service.name,
        "image": service.image,
        "status": service.status,
        "created_at": service.created_at.isoformat() if service.created_at else None,
        "updated_at": service.updated_at.isoformat() if service.updated_at else None,
    }


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List medical services (admin)",
    description="Get all medical services. Admin only. Optional filter by status.",
)
async def list_medical_services(
    status_filter: Optional[bool] = Query(None, alias="status", description="Filter by status (true=active, false=inactive)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """List all medical services. Admin only."""
    query = db.query(MedicalService)
    if status_filter is not None:
        query = query.filter(MedicalService.status == status_filter)
    services = query.order_by(MedicalService.name).all()
    data = [_service_to_dict(s) for s in services]
    return laravel_response(
        success=True,
        message="Medical services retrieved successfully",
        data={"medical_services": data},
    )


@router.get(
    "/{medical_service_id}",
    status_code=status.HTTP_200_OK,
    summary="Get one medical service (admin)",
    description="Get a medical service by ID. Admin only.",
)
async def get_medical_service(
    medical_service_id: UUID = Path(..., description="Medical service ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Get a single medical service by ID. Admin only."""
    service = db.query(MedicalService).filter(MedicalService.id == medical_service_id).first()
    if not service:
        raise NotFoundException(
            message="Medical service not found",
            errors={"medical_service_id": ["Medical service with this ID does not exist"]},
        )
    return laravel_response(
        success=True,
        message="Medical service retrieved successfully",
        data={"medical_service": _service_to_dict(service)},
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create medical service (admin)",
    description="Create a new medical service (specialty). Admin only.",
)
async def create_medical_service(
    payload: MedicalServiceCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Create a new medical service. Admin only."""
    try:
        service = MedicalService(
            name=payload.name,
            parent=payload.parent or "0",
            image=payload.image,
            status=payload.status,
        )
        db.add(service)
        db.commit()
        db.refresh(service)
        logger.info(f"Admin {current_user.id} created medical service: {service.name} ({service.id})")
        return laravel_response(
            success=True,
            message="Medical service created successfully",
            data={"medical_service": _service_to_dict(service)},
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create medical service: {e}")
        raise BadRequestException(
            message="Failed to create medical service",
            errors={"error": [str(e)]},
        )


@router.put(
    "/{medical_service_id}",
    status_code=status.HTTP_200_OK,
    summary="Update medical service (admin)",
    description="Update an existing medical service. Admin only.",
)
async def update_medical_service(
    medical_service_id: UUID = Path(..., description="Medical service ID"),
    payload: MedicalServiceUpdate = ...,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Update a medical service. Admin only."""
    service = db.query(MedicalService).filter(MedicalService.id == medical_service_id).first()
    if not service:
        raise NotFoundException(
            message="Medical service not found",
            errors={"medical_service_id": ["Medical service with this ID does not exist"]},
        )
    try:
        if payload.name is not None:
            service.name = payload.name
        if payload.parent is not None:
            service.parent = payload.parent
        if payload.image is not None:
            service.image = payload.image
        if payload.status is not None:
            service.status = payload.status
        db.add(service)
        db.commit()
        db.refresh(service)
        logger.info(f"Admin {current_user.id} updated medical service: {service.id}")
        return laravel_response(
            success=True,
            message="Medical service updated successfully",
            data={"medical_service": _service_to_dict(service)},
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update medical service: {e}")
        raise BadRequestException(
            message="Failed to update medical service",
            errors={"error": [str(e)]},
        )


@router.delete(
    "/{medical_service_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete medical service (admin)",
    description="Delete a medical service. Admin only. May fail if in use (e.g. linked to doctors).",
)
async def delete_medical_service(
    medical_service_id: UUID = Path(..., description="Medical service ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user),
):
    """Delete a medical service. Admin only."""
    service = db.query(MedicalService).filter(MedicalService.id == medical_service_id).first()
    if not service:
        raise NotFoundException(
            message="Medical service not found",
            errors={"medical_service_id": ["Medical service with this ID does not exist"]},
        )
    try:
        db.delete(service)
        db.commit()
        logger.info(f"Admin {current_user.id} deleted medical service: {medical_service_id}")
        return laravel_response(
            success=True,
            message="Medical service deleted successfully",
            data=None,
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete medical service: {e}")
        raise BadRequestException(
            message="Failed to delete medical service. It may be in use (e.g. linked to doctors).",
            errors={"error": [str(e)]},
        )
