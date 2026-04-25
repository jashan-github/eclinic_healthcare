"""
Clinic Location API Endpoints
Admin-only routes for managing clinic branch locations
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.services.clinic_location_service import ClinicLocationService
from app.schemas.clinic_location import (
    ClinicLocationCreate,
    ClinicLocationUpdate,
    ClinicLocationListResponse,
    ClinicLocationSingleResponse,
    ClinicLocationDeleteResponse
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    laravel_response
)
from loguru import logger


router = APIRouter(prefix="/admin/clinic-locations", tags=["Admin - Clinic Locations"])


@router.post(
    "",
    response_model=ClinicLocationSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new clinic location",
    description="""Create a new clinic branch/location (Admin only)

**Use Cases:**

1. **Add main clinic location**:
   - Create the primary location for a clinic
   - Set `is_primary: true` to mark as the main branch
   - Only one location per clinic can be primary

2. **Add branch locations**:
   - Create additional branches for multi-location clinics
   - Set different branch types (Main Branch, Sub Branch, etc.)
   - Each branch can have its own contact information

3. **Geographic information**:
   - Country, State, and City are required for each location
   - Address is parsed to extract building_name and street_name
   - Latitude/longitude can be added later for maps integration

**Important Notes:**
- If `is_primary` is set to true, any existing primary location for the clinic will be unmarked
- The address field is automatically parsed into building_name and street_name
- All locations are tied to a specific clinic via clinic_id from the authenticated user

**Example Request:**
```json
{
  "name": "Pure Health BV",
  "branch_type": "Main Branch",
  "address": "#139E Union Road, Cole Bay",
  "country_id": "653838a6-000b-4050-9df5-ed81f0737fa1",
  "state_id": "af949d3b-eacb-4c2a-970e-fc586d0920df",
  "city_id": "6be27348-382f-4f24-8f3e-c7d0965d0d55",
  "phone": "+1 (721) 544-2275",
  "email": "purehealthbv@gmail.com",
  "is_primary": true
}
```"""
)
async def create_location(
    request: ClinicLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new clinic location
    """
    try:
        # Use the clinic_id from the authenticated user
        clinic_id = current_user.clinic_id
        
        service = ClinicLocationService(db)
        location = service.create_location(
            clinic_id=clinic_id,
            name=request.name,
            branch_type=request.branch_type,
            address=request.address,
            country_id=request.country_id,
            state_id=request.state_id,
            city_id=request.city_id,
            phone=request.phone,
            email=request.email,
            is_primary=request.is_primary
        )
        
        formatted_location = service.format_location_response(location)
        
        return laravel_response(
            success=True,
            message="Location created successfully",
            data={"location": formatted_location}
        )
        
    except (NotFoundException, ValidationException) as e:
        logger.warning(f"Failed to create location: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating location: {str(e)}")
        raise ValidationException(
            message="Failed to create location",
            errors={"error": [str(e)]}
        )


@router.get(
    "",
    response_model=ClinicLocationListResponse,
    summary="Get all clinic locations",
    description="""Get all clinic locations for the authenticated user's clinic (Admin only)

**Response Format:**
```json
{
  "status": true,
  "message": "Locations retrieved successfully",
  "data": {
    "locations": [
      {
        "id": "93f951f4-3d45-4395-aa18-c2115656d633",
        "name": "Pure Health BV",
        "branch_type": "Main Branch",
        "address": "#139E Union Road, Cole Bay",
        "building_name": "#139E",
        "street_name": "Union Road",
        "pincode": null,
        "phone": "+1 (721) 544-2275",
        "email": "purehealthbv@gmail.com",
        "country": "Sint Maarten",
        "state": "Sint Maarten",
        "city": "Cole Bay",
        "country_id": "653838a6-000b-4050-9df5-ed81f0737fa1",
        "state_id": "af949d3b-eacb-4c2a-970e-fc586d0920df",
        "city_id": "6be27348-382f-4f24-8f3e-c7d0965d0d55",
        "latitude": null,
        "longitude": null,
        "is_primary": true,
        "created_at": "2025-12-11 18:40:46",
        "updated_at": "2025-12-11 18:40:46"
      }
    ]
  }
}
```

**Notes:**
- Locations are ordered by: primary first, then by creation date
- Only returns locations for the authenticated user's clinic
- Returns empty array if no locations exist
"""
)
async def get_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all clinic locations for the authenticated user's clinic
    """
    try:
        clinic_id = current_user.clinic_id
        
        service = ClinicLocationService(db)
        locations = service.get_all_locations(clinic_id=clinic_id)
        
        formatted_locations = [
            service.format_location_response(location)
            for location in locations
        ]
        
        return laravel_response(
            success=True,
            message="Locations retrieved successfully",
            data={"locations": formatted_locations}
        )
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving locations: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve locations",
            errors={"error": [str(e)]}
        )


@router.get(
    "/{location_id}",
    response_model=ClinicLocationSingleResponse,
    summary="Get a specific clinic location",
    description="Get details of a specific clinic location by ID (Admin only)"
)
async def get_location(
    location_id: UUID = Path(..., description="Location ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get a specific clinic location
    """
    try:
        service = ClinicLocationService(db)
        location = service.get_location_by_id(location_id)
        
        # Verify the location belongs to the user's clinic
        if location.clinic_id != current_user.clinic_id:
            raise NotFoundException(
                message="Location not found",
                errors={"id": ["Location does not belong to your clinic"]}
            )
        
        formatted_location = service.format_location_response(location)
        
        return laravel_response(
            success=True,
            message="Location retrieved successfully",
            data={"location": formatted_location}
        )
        
    except NotFoundException as e:
        logger.warning(f"Location not found: {location_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving location: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve location",
            errors={"error": [str(e)]}
        )


@router.put(
    "/{location_id}",
    response_model=ClinicLocationSingleResponse,
    summary="Update a clinic location",
    description="""Update an existing clinic location (Admin only)

**Notes:**
- Only fields provided in the request will be updated
- If `is_primary` is set to true, other primary locations will be unmarked
- Cannot update locations that don't belong to your clinic
"""
)
async def update_location(
    location_id: UUID = Path(..., description="Location ID"),
    request: ClinicLocationUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update a clinic location
    """
    try:
        service = ClinicLocationService(db)
        location = service.get_location_by_id(location_id)
        
        # Verify the location belongs to the user's clinic
        if location.clinic_id != current_user.clinic_id:
            raise NotFoundException(
                message="Location not found",
                errors={"id": ["Location does not belong to your clinic"]}
            )
        
        # Update location
        update_data = request.model_dump(exclude_unset=True)
        updated_location = service.update_location(location_id, **update_data)
        
        formatted_location = service.format_location_response(updated_location)
        
        return laravel_response(
            success=True,
            message="Location updated successfully",
            data={"location": formatted_location}
        )
        
    except NotFoundException as e:
        logger.warning(f"Location not found: {location_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating location: {str(e)}")
        raise ValidationException(
            message="Failed to update location",
            errors={"error": [str(e)]}
        )


@router.delete(
    "/{location_id}",
    response_model=ClinicLocationDeleteResponse,
    summary="Delete a clinic location",
    description="""Delete a clinic location (Admin only)

**Notes:**
- This is a soft delete (location is marked as deleted but not removed from database)
- Cannot delete locations that don't belong to your clinic
- Deleted locations will not appear in list results
"""
)
async def delete_location(
    location_id: UUID = Path(..., description="Location ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a clinic location
    """
    try:
        service = ClinicLocationService(db)
        location = service.get_location_by_id(location_id)
        
        # Verify the location belongs to the user's clinic
        if location.clinic_id != current_user.clinic_id:
            raise NotFoundException(
                message="Location not found",
                errors={"id": ["Location does not belong to your clinic"]}
            )
        
        # Delete location
        service.delete_location(location_id)
        
        return laravel_response(
            success=True,
            message="Location deleted successfully",
            data={}
        )
        
    except NotFoundException as e:
        logger.warning(f"Location not found: {location_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting location: {str(e)}")
        raise ValidationException(
            message="Failed to delete location",
            errors={"error": [str(e)]}
        )
