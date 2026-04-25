"""
Doctor Management API Endpoints
Admin-only routes for managing doctors
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.core.exceptions import laravel_response
from loguru import logger


router = APIRouter(prefix="/admin/doctors", tags=["Admin - Doctors"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get all doctors",
    description="""Get a list of all doctors (Admin only)
    
**Returns:**
- Only doctor name, email, and UUID
- No pagination - returns all doctors
- Can be filtered by clinic_id, is_active, or search

**Query Parameters:**
- **clinic_id**: Filter by clinic ID (optional)
- **is_active**: Filter by active status (optional)
- **search**: Search by name or email (optional)

**Example Response:**
```json
{
  "status": true,
  "message": "Doctors retrieved successfully",
  "data": {
    "doctors": [
      {
        "id": "7cf36af4-23b5-4a50-aa71-f99e1dd1ed3d",
        "name": "NS Bajwa",
        "email": "dr.bajwa@gmail.com"
      }
    ]
  }
}
```"""
)
async def get_all_doctors(
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all doctors (name, email, UUID only)
    
    **Admin-only endpoint**
    Returns all doctors without pagination
    """
    try:
        # Build query - only doctors
        query = db.query(User).filter(
            and_(
                User.role == "doctor",
                User.deleted_at.is_(None)
            )
        )
        
        # Filter by clinic (if clinic_admin, only show their clinic)
        if current_user.role == "clinic_admin" and current_user.clinic_id:
            query = query.filter(User.clinic_id == current_user.clinic_id)
        elif clinic_id:
            query = query.filter(User.clinic_id == clinic_id)
        
        # Filter by active status
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Search by name or email
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )
        
        # Get all doctors (no pagination)
        doctors = query.order_by(User.name.asc()).all()
        
        # Format doctors for response - only name, email, and UUID
        doctors_data = [
            {
                "id": str(doctor.id),
                "name": doctor.name,
                "email": doctor.email
            }
            for doctor in doctors
        ]
        
        return laravel_response(
            success=True,
            message="Doctors retrieved successfully",
            data={
                "doctors": doctors_data
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve doctors: {str(e)}")
        raise
