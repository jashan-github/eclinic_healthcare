"""
Vital Frequency API Endpoints
Routes for managing vital frequency rules (Admin only)
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.core.security import CurrentUser
from app.services.vital_frequency_service import VitalFrequencyService
from app.schemas.vital_frequency import (
    VitalFrequencyCreate,
    VitalFrequencyUpdate,
    VitalFrequencyListResponse,
    VitalFrequencySingleResponse,
    VitalFrequencyCreateResponse,
    VitalFrequencyUpdateResponse,
    VitalFrequencyDeleteResponse
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    ConflictException,
    laravel_response
)
from loguru import logger


router = APIRouter(prefix="/admin/vital-frequency", tags=["Admin - Vital Frequency"])


def serialize_frequency_rule(rule, db: Session):
    """Serialize a frequency rule to dict"""
    from app.models.vital_name import VitalName
    from app.models.user import User
    from app.models.user import Clinic
    
    data = {
        "id": str(rule.id),
        "patient_id": str(rule.patient_id) if rule.patient_id else None,
        "vital_name_id": str(rule.vital_name_id) if rule.vital_name_id else None,
        "clinic_id": str(rule.clinic_id) if rule.clinic_id else None,
        "frequency_type": rule.frequency_type,
        "max_entries_per_day": rule.max_entries_per_day,
        "times_per_day": rule.times_per_day,
        "preferred_times": rule.preferred_times,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
        "patient_name": None,
        "vital_name": None,
        "clinic_name": None
    }
    
    # Load related entities
    if rule.patient_id:
        patient = db.query(User).filter(User.id == rule.patient_id).first()
        if patient:
            data["patient_name"] = patient.name
    
    if rule.vital_name_id:
        vital_name = db.query(VitalName).filter(VitalName.id == rule.vital_name_id).first()
        if vital_name:
            data["vital_name"] = vital_name.name
    
    if rule.clinic_id:
        clinic = db.query(Clinic).filter(Clinic.id == rule.clinic_id).first()
        if clinic:
            data["clinic_name"] = clinic.name
    
    return data


@router.post(
    "",
    response_model=VitalFrequencyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create vital frequency rule",
    description="""Create a new vital frequency rule (Admin only)

**Use Cases:**

1. **Clinic-wide default** (Most Common):
   - Set a default limit for all patients in a clinic
   - Example: "All patients in Main Clinic can record any vital 2 times per day"
   - Request: `{"clinic_id": "uuid", "max_entries_per_day": 2}`

2. **Specific vital limit**:
   - Limit how often a specific vital can be recorded
   - Example: "Weight should only be recorded once per day to avoid confusion"
   - Request: `{"clinic_id": "uuid", "vital_name_id": "weight-uuid", "max_entries_per_day": 1}`

3. **Patient exception** (Rare):
   - Allow a specific patient to record more frequently
   - Example: "Patient John needs to monitor BP 4 times daily per doctor's orders"
   - Request: `{"patient_id": "patient-uuid", "vital_name_id": "bp-uuid", "max_entries_per_day": 4}`

**Priority System:**
The system checks rules in this order (first match wins):
1. Patient-specific + Vital-specific (highest priority)
2. Patient-specific + All vitals
3. Clinic-specific + Vital-specific
4. Clinic-specific + All vitals
5. Global + Vital-specific
6. Global + All vitals (lowest priority)

**What happens:**
- If no rule exists: Uses default from `vital_names.max_entries_per_day` (usually 1)
- If rule exists: Patient can record up to `max_entries_per_day` times per day
- After limit reached: System blocks new recordings with error message"""
)
async def create_frequency_rule(
    data: VitalFrequencyCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """
    Create vital frequency rule
    
    **Admin only endpoint**
    
    Creates a new frequency rule that defines how many times per day a patient can record vital signs.
    This prevents patients from recording vitals too frequently and helps maintain data quality.
    
    **Use Cases:**
    
    1. **Clinic-wide default** (Most Common):
       - Set a default limit for all patients in a clinic
       - Example: "All patients in Main Clinic can record any vital 2 times per day"
       - Request: `{"clinic_id": "uuid", "max_entries_per_day": 2}`
    
    2. **Specific vital limit**:
       - Limit how often a specific vital can be recorded
       - Example: "Weight should only be recorded once per day to avoid confusion"
       - Request: `{"clinic_id": "uuid", "vital_name_id": "weight-uuid", "max_entries_per_day": 1}`
    
    3. **Patient exception** (Rare):
       - Allow a specific patient to record more frequently
       - Example: "Patient John needs to monitor BP 4 times daily per doctor's orders"
       - Request: `{"patient_id": "patient-uuid", "vital_name_id": "bp-uuid", "max_entries_per_day": 4}`
    
    **Priority System:**
    The system checks rules in this order (first match wins):
    1. Patient-specific + Vital-specific (highest priority)
    2. Patient-specific + All vitals
    3. Clinic-specific + Vital-specific
    4. Clinic-specific + All vitals
    5. Global + Vital-specific
    6. Global + All vitals (lowest priority)
    
    **What happens:**
    - If no rule exists: Uses default from `vital_names.max_entries_per_day` (usually 1)
    - If rule exists: Patient can record up to `max_entries_per_day` times per day
    - After limit reached: System blocks new recordings with error message
    
    Args:
        data: Frequency rule data
        
    Returns:
        Created frequency rule with success message
    """
    try:
        service = VitalFrequencyService(db)
        
        rule = service.create_frequency_rule(
            max_entries_per_day=data.max_entries_per_day,
            patient_id=data.patient_id,
            vital_name_id=data.vital_name_id,
            clinic_id=data.clinic_id,
            frequency_type=data.frequency_type,
            times_per_day=data.times_per_day,
            preferred_times=data.preferred_times,
            is_active=data.is_active
        )
        
        rule_data = serialize_frequency_rule(rule, db)
        
        return VitalFrequencyCreateResponse(
            success=True,
            message="Vital frequency rule created successfully",
            data=rule_data,
            errors=None
        )
    
    except (ValidationException, ConflictException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Failed to create frequency rule: {str(e)}")
        raise


@router.get(
    "",
    response_model=VitalFrequencyListResponse,
    status_code=status.HTTP_200_OK,
    summary="List vital frequency rules",
    description="Get all vital frequency rules with optional filters (Admin only)"
)
async def list_frequency_rules(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient ID"),
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID"),
    vital_name_id: Optional[UUID] = Query(None, description="Filter by vital name ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """
    List vital frequency rules
    
    **Admin only endpoint**
    
    Retrieves all frequency rules with optional filters.
    
    Args:
        patient_id: Filter by patient ID
        clinic_id: Filter by clinic ID
        vital_name_id: Filter by vital name ID
        is_active: Filter by active status
        
    Returns:
        List of frequency rules
    """
    try:
        service = VitalFrequencyService(db)
        
        rules = service.get_all_frequency_rules(
            patient_id=patient_id,
            clinic_id=clinic_id,
            vital_name_id=vital_name_id,
            is_active=is_active
        )
        
        rules_data = [serialize_frequency_rule(rule, db) for rule in rules]
        
        return laravel_response(
            success=True,
            message="Vital frequency rules retrieved successfully",
            data={
                "frequency_rules": rules_data,
                "count": len(rules_data)
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to list frequency rules: {str(e)}")
        raise


@router.get(
    "/{frequency_id}",
    response_model=VitalFrequencySingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vital frequency rule by ID",
    description="Retrieve a specific vital frequency rule by ID (Admin only)"
)
async def get_frequency_rule(
    frequency_id: UUID = Path(..., description="Frequency rule ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """
    Get vital frequency rule by ID
    
    **Admin only endpoint**
    
    Retrieves a specific frequency rule by its ID.
    
    Args:
        frequency_id: UUID of the frequency rule
        
    Returns:
        Frequency rule details
    """
    try:
        service = VitalFrequencyService(db)
        
        rule = service.get_frequency_rule_by_id(frequency_id)
        
        rule_data = serialize_frequency_rule(rule, db)
        
        return VitalFrequencySingleResponse(
            success=True,
            message="Vital frequency rule retrieved successfully",
            data=rule_data,
            errors=None
        )
    
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to get frequency rule: {str(e)}")
        raise


@router.patch(
    "/{frequency_id}",
    response_model=VitalFrequencyUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update vital frequency rule",
    description="Update a vital frequency rule (Admin only)"
)
async def update_frequency_rule(
    frequency_id: UUID = Path(..., description="Frequency rule ID"),
    data: VitalFrequencyUpdate = ...,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """
    Update vital frequency rule
    
    **Admin only endpoint**
    
    Updates an existing frequency rule.
    
    Args:
        frequency_id: UUID of the frequency rule
        data: Updated frequency rule data
        
    Returns:
        Updated frequency rule with success message
    """
    try:
        service = VitalFrequencyService(db)
        
        rule = service.update_frequency_rule(
            frequency_id=frequency_id,
            frequency_type=data.frequency_type,
            max_entries_per_day=data.max_entries_per_day,
            times_per_day=data.times_per_day,
            preferred_times=data.preferred_times,
            is_active=data.is_active
        )
        
        rule_data = serialize_frequency_rule(rule, db)
        
        return VitalFrequencyUpdateResponse(
            success=True,
            message="Vital frequency rule updated successfully",
            data=rule_data,
            errors=None
        )
    
    except (NotFoundException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to update frequency rule: {str(e)}")
        raise


@router.delete(
    "/{frequency_id}",
    response_model=VitalFrequencyDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete vital frequency rule",
    description="Delete a vital frequency rule (soft delete, Admin only)"
)
async def delete_frequency_rule(
    frequency_id: UUID = Path(..., description="Frequency rule ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """
    Delete vital frequency rule (soft delete)
    
    **Admin only endpoint**
    
    Soft deletes a frequency rule.
    
    Args:
        frequency_id: UUID of the frequency rule to delete
        
    Returns:
        Success message
    """
    try:
        service = VitalFrequencyService(db)
        
        service.delete_frequency_rule(frequency_id)
        
        return VitalFrequencyDeleteResponse(
            success=True,
            message="Vital frequency rule deleted successfully",
            data=None,
            errors=None
        )
    
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete frequency rule: {str(e)}")
        raise

