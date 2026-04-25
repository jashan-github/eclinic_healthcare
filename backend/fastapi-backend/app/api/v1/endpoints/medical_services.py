"""
Medical Service endpoints
API endpoints for medical services
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db
from app.core.exceptions import laravel_response
from app.models.medical_service import MedicalService
from app.schemas.medical_service import MedicalServicesListResponse

router = APIRouter()


@router.get("/", response_model=MedicalServicesListResponse, status_code=200)
async def list_medical_services(
    status: Optional[bool] = Query(None, description="Filter by status (true=active, false=inactive)"),
    db: Session = Depends(get_db)
):
    """
    Get list of all medical services
    
    **Laravel-compatible endpoint**
    
    Returns all medical services sorted by name.
    Optionally filter by status (active/inactive).
    No authentication required (public endpoint).
    
    Query Parameters:
    - **status**: Optional. Filter by status (true=active, false=inactive)
    """
    query = db.query(MedicalService)
    
    # Filter by status if provided
    if status is not None:
        query = query.filter(MedicalService.status == status)
    
    # Order by name
    medical_services = query.order_by(MedicalService.name).all()
    
    medical_services_data = [
        {
            "id": str(service.id),
            "parent": service.parent,
            "name": service.name,
            "image": service.image,
            "status": service.status,
            "created_at": service.created_at.isoformat() if service.created_at else None,
            "updated_at": service.updated_at.isoformat() if service.updated_at else None
        }
        for service in medical_services
    ]
    
    return laravel_response(
        success=True,
        message="Medical services retrieved successfully",
        data={"medical_services": medical_services_data}
    )

