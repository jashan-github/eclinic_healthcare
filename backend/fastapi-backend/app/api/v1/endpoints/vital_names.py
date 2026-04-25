"""
Vital Names API Endpoints
Admin-only routes for vital name management
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.services.vital_name_service import VitalNameService
from app.schemas.vital_name import (
    VitalNameCreate,
    VitalNameUpdate,
    VitalNameListResponse,
    VitalNameSingleResponse,
    VitalNameCreateResponse,
    VitalNameUpdateResponse,
    VitalNameDeleteResponse
)
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    ValidationException,
    laravel_response
)
from loguru import logger


router = APIRouter(prefix="/admin/vital-names", tags=["Admin - Vital Names"])


@router.post(
    "",
    response_model=VitalNameCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new vital name",
    description="""Create a new vital name (Admin only)

**Use Cases:**

1. **Add standard vital signs**:
   - Add common vitals like Weight, Blood Pressure, Temperature, etc.
   - Example: Create "Weight (lbs)" with unit "lbs" and data_type "number"
   - This vital will then appear in the form when recording patient vitals

2. **Add custom vital signs**:
   - Add clinic-specific or specialty vitals
   - Example: "Pain Scale (1-10)" with data_type "number"
   - Example: "Mood" with data_type "select" and options '["Happy", "Sad", "Anxious"]'

3. **Configure vital properties**:
   - Set `display_order` to control how vitals appear in forms
   - Set `is_active` to show/hide vitals without deleting them
   - `max_entries_per_day` is automatically set to "1" by the backend

**Important Notes:**
- Once created, doctors and patients can record this vital sign
- Each vital name must be unique
- Set `is_active: false` to hide a vital without deleting it
- `max_entries_per_day` defaults to "1" and is handled by the backend (can be overridden by frequency rules)

**Example Scenarios:**

Scenario 1: Standard Weight Vital
```json
{
  "name": "Weight (lbs)",
  "unit": "lbs",
  "data_type": "number"
}
```

Scenario 2: Select-type Vital (Temperature Location)
```json
{
  "name": "Temperature Location",
  "data_type": "select",
  "options": "[\"Oral\", \"Axillary\", \"Rectal\", \"Tympanic\"]"
}
```"""
)
async def create_vital_name(
    data: VitalNameCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new vital name
    
    **Admin only endpoint**
    
    Creates a new vital sign name that will be available for doctors and patients to record.
    Vital names define which vital signs are available in the system.
    
    **Use Cases:**
    
    1. **Add standard vital signs**:
       - Add common vitals like Weight, Blood Pressure, Temperature, etc.
       - Example: Create "Weight (lbs)" with unit "lbs" and data_type "number"
       - This vital will then appear in the form when recording patient vitals
    
    2. **Add custom vital signs**:
       - Add clinic-specific or specialty vitals
       - Example: "Pain Scale (1-10)" with data_type "number"
       - Example: "Mood" with data_type "select" and options '["Happy", "Sad", "Anxious"]'
    
    3. **Configure vital properties**:
       - Set `display_order` to control how vitals appear in forms
       - Set `is_active` to show/hide vitals without deleting them
       - `max_entries_per_day` is automatically set to "1" by the backend
    
    **Important Notes:**
    - Once created, doctors and patients can record this vital sign
    - Each vital name must be unique
    - Set `is_active: false` to hide a vital without deleting it
    - `max_entries_per_day` defaults to "1" and is handled by the backend (can be overridden by frequency rules)
    
    **Example Scenarios:**
    
    Scenario 1: Standard Weight Vital
    ```json
    {
      "name": "Weight (lbs)",
      "unit": "lbs",
      "data_type": "number"
    }
    ```
    
    Scenario 2: Select-type Vital (Temperature Location)
    ```json
    {
      "name": "Temperature Location",
      "data_type": "select",
      "options": "[\"Oral\", \"Axillary\", \"Rectal\", \"Tympanic\"]"
    }
    ```
    
    Args:
        data: Vital name creation data
        
    Returns:
        Created vital name with success message
    """
    try:
        service = VitalNameService(db)
        
        vital_name = service.create_vital_name(
            name=data.name,
            unit=data.unit,
            display_order=data.display_order,
            is_active=data.is_active,
            data_type=data.data_type,
            options=data.options,
            max_entries_per_day="1"  # Always set to "1" by default in backend
        )
        
        return VitalNameCreateResponse(
            success=True,
            message="Vital name created successfully",
            data=vital_name,
            errors=None
        )
    
    except (ConflictException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to create vital name: {str(e)}")
        raise


@router.get(
    "",
    response_model=VitalNameListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all vital names",
    description="Retrieve all vital names with optional filters (Admin only)"
)
async def get_vital_names(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all vital names
    
    **Admin only endpoint**
    
    Retrieves all vital names with optional filtering by active status.
    Results are ordered by display_order, then by name.
    
    Returns:
        List of vital names matching the filters
    """
    try:
        service = VitalNameService(db)
        
        vital_names = service.get_all_vital_names(is_active=is_active)
        
        vital_names_data = [
            {
                "id": str(vn.id),
                "name": vn.name,
                "unit": vn.unit,
                "display_order": vn.display_order,
                "is_active": vn.is_active,
                "data_type": vn.data_type,
                "options": vn.options,
                "max_entries_per_day": vn.max_entries_per_day,
                "created_at": vn.created_at.isoformat() if vn.created_at else None,
                "updated_at": vn.updated_at.isoformat() if vn.updated_at else None
            }
            for vn in vital_names
        ]
        
        return laravel_response(
            success=True,
            message="Vital names retrieved successfully",
            data={"vital_names": vital_names_data}
        )
    
    except Exception as e:
        logger.error(f"Failed to get vital names: {str(e)}")
        raise


@router.get(
    "/{vital_name_id}",
    response_model=VitalNameSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vital name by ID",
    description="Retrieve a specific vital name by ID (Admin only)"
)
async def get_vital_name(
    vital_name_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get vital name by ID
    
    **Admin only endpoint**
    
    Retrieves a specific vital name by its ID.
    
    Args:
        vital_name_id: UUID of the vital name
        
    Returns:
        Vital name details
    """
    try:
        service = VitalNameService(db)
        
        vital_name = service.get_vital_name_by_id(vital_name_id)
        
        return VitalNameSingleResponse(
            success=True,
            message="Vital name retrieved successfully",
            data=vital_name,
            errors=None
        )
    
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vital name: {str(e)}")
        raise


@router.patch(
    "/{vital_name_id}",
    response_model=VitalNameUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update vital name",
    description="Update a vital name (Admin only)"
)
async def update_vital_name(
    vital_name_id: UUID,
    data: VitalNameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update a vital name
    
    **Admin only endpoint**
    
    Updates an existing vital name.
    
    **Note:** `max_entries_per_day` is automatically set to "1" by the backend and cannot be changed via this endpoint.
    
    Args:
        vital_name_id: UUID of the vital name
        data: Vital name update data (max_entries_per_day is handled by backend)
        
    Returns:
        Updated vital name with success message
    """
    try:
        service = VitalNameService(db)
        
        vital_name = service.update_vital_name(
            vital_name_id=vital_name_id,
            name=data.name,
            unit=data.unit,
            display_order=data.display_order,
            is_active=data.is_active,
            data_type=data.data_type,
            options=data.options,
            max_entries_per_day="1"  # Always set to "1" by backend
        )
        
        return VitalNameUpdateResponse(
            success=True,
            message="Vital name updated successfully",
            data=vital_name,
            errors=None
        )
    
    except (NotFoundException, ConflictException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to update vital name: {str(e)}")
        raise


@router.delete(
    "/{vital_name_id}",
    response_model=VitalNameDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete vital name",
    description="Delete a vital name (soft delete, Admin only)"
)
async def delete_vital_name(
    vital_name_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a vital name (soft delete)
    
    **Admin only endpoint**
    
    Soft deletes a vital name. The vital name will be marked as deleted
    but not removed from the database.
    
    Args:
        vital_name_id: UUID of the vital name to delete
        
    Returns:
        Success message
    """
    try:
        service = VitalNameService(db)
        
        service.delete_vital_name(vital_name_id)
        
        return VitalNameDeleteResponse(
            success=True,
            message="Vital name deleted successfully",
            data=None,
            errors=None
        )
    
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete vital name: {str(e)}")
        raise

