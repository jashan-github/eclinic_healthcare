"""
Patient Vital Signs API Endpoints
Routes for recording and managing patient vital signs
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin_user
from app.core.security import CurrentUser
from app.models.user import User
from app.models.vital_name import VitalName
from app.services.patient_vital_signs_service import PatientVitalSignsService
from app.services.vital_name_service import VitalNameService
from app.core.exceptions import BadRequestException
from app.schemas.patient_vital_signs import (
    PatientVitalSignsCreate,
    PatientVitalSignsUpdate,
    PatientVitalSignsListResponse,
    PatientVitalSignsSingleResponse,
    PatientVitalSignsCreateResponse,
    PatientVitalSignsUpdateResponse,
    PatientVitalSignsDeleteResponse,
    PatientVitalSignsResponse
)
from app.schemas.vital_signs_consent import (
    VitalSignsConsentUpdate,
    VitalSignsConsentUpdateResponse
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    ForbiddenException,
    laravel_response
)
from loguru import logger


router = APIRouter(prefix="/patient-vital-signs", tags=["Patient Vital Signs"])


@router.get(
    "/vital-names",
    status_code=status.HTTP_200_OK,
    summary="Get list of active vital names",
    description="Retrieve all active vital names that admin has added (accessible by patients and doctors)"
)
async def get_active_vital_names(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get list of active vital names
    
    **Patient and Doctor endpoint**
    
    Retrieves all active vital names that admin has added to the system.
    This endpoint is accessible by both patients and doctors to see which
    vital signs are available for recording.
    
    Returns only active vital names (is_active = true) that are not deleted.
    Results are ordered by display_order, then by name.
    
    Returns:
        List of active vital names
    """
    try:
        service = VitalNameService(db)
        
        # Get only active vital names
        vital_names = service.get_all_vital_names(is_active=True)
        
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
            message="Active vital names retrieved successfully",
            data={"vital_names": vital_names_data}
        )
    
    except Exception as e:
        logger.error(f"Failed to get active vital names: {str(e)}")
        raise


def serialize_vital_record(record, include_vital_name: bool = False):
    """Serialize a vital signs record to dict. Use actual stored values only (no defaults for filled fields)."""
    # Use actual values from DB; only use None when column is truly null (so frontend doesn't show wrong default)
    share_val = getattr(record, "share_with_doctor", None)
    if share_val is None:
        share_val = False
    data = {
        "id": str(record.id),
        "patient_id": str(record.patient_id),
        "vital_name_id": str(record.vital_name_id),
        "clinic_id": str(record.clinic_id),
        "doctor_id": str(record.doctor_id) if record.doctor_id else None,
        "appointment_id": str(record.appointment_id) if record.appointment_id else None,
        "record_date": record.record_date.isoformat() if record.record_date else None,
        "numeric_value": float(record.numeric_value) if record.numeric_value is not None else None,
        "text_value": record.text_value if record.text_value is not None else None,
        "unit": record.unit,
        "notes": record.notes,
        "share_with_doctor": bool(share_val),
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None
    }
    
    if include_vital_name:
        vital_name = record.vital_name if hasattr(record, 'vital_name') else None
        if vital_name:
            data["vital_name"] = {
                "id": str(vital_name.id),
                "name": vital_name.name,
                "unit": vital_name.unit,
                "data_type": vital_name.data_type,
                "display_order": vital_name.display_order,
            }
    
    return data


@router.post(
    "",
    response_model=PatientVitalSignsCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record patient vital signs",
    description="""Record vital signs for a patient (Doctor or Patient can record)

**Auto-handled Fields:**
- `patient_id`: Automatically set from logged-in user for patients. Required in request body for doctors/admins.
- `clinic_id`: Automatically fetched from patient's user record. Not required in request.

**For Patients:**
- Both `patient_id` and `clinic_id` are automatically determined from your account
- You can only record vital signs for yourself
- Simply provide the `vitals` array with your readings

**For Doctors/Staff/Admins:**
- `patient_id` must be provided in the request body (which patient you're recording for)
- `clinic_id` is automatically fetched from the patient's user record
- Clinic access is validated (you can only record for patients in your clinic)

**Request Body:**
- `vitals` (required): Array of vital sign readings
- `patient_id` (optional): Only required for doctors/admins, auto-filled for patients
- `clinic_id` (optional): Always auto-filled from patient's record
- `appointment_id` (optional): Associated appointment if recording during appointment
- `record_date` (optional): Date/time of recording (defaults to now)
- `notes` (optional): Additional notes about the vital signs

**Example Request (Patient):**
```json
{
  "vitals": [
    {
      "vital_name_id": "a744f208-09a7-4c8a-a266-fa261313dee8",
      "value": 185.5
    }
  ],
  "notes": "Morning reading"
}
```

**Example Request (Doctor):**
```json
{
  "patient_id": "587ec4ec-e2ae-48fb-819c-5bb5d84f20ec",
  "vitals": [
    {
      "vital_name_id": "a744f208-09a7-4c8a-a266-fa261313dee8",
      "value": 185.5
    }
  ],
  "appointment_id": "abc123...",
  "notes": "Recorded during consultation"
}
```"""
)
async def create_vital_signs(
    data: PatientVitalSignsCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Record patient vital signs
    
    **Doctor or Patient endpoint**
    
    Creates multiple vital signs records (one per vital in the vitals array).
    Each vital will be validated against vital_names and frequency rules.
    
    **Auto-handled Fields:**
    - `patient_id`: Automatically set from logged-in user for patients. Required in request body for doctors/admins.
    - `clinic_id`: Automatically fetched from patient's user record. Not required in request.
    
    **For Patients:**
    - Both `patient_id` and `clinic_id` are automatically determined from your account
    - You can only record vital signs for yourself
    - Simply provide the `vitals` array with your readings
    
    **For Doctors/Staff/Admins:**
    - `patient_id` must be provided in the request body (which patient you're recording for)
    - `clinic_id` is automatically fetched from the patient's user record
    - Clinic access is validated (you can only record for patients in your clinic)
    
    Args:
        data: Vital signs data with array of vitals
        
    Returns:
        Created vital signs records with success message
    """
    try:
        service = PatientVitalSignsService(db)
        
        # Auto-determine patient_id and clinic_id based on user role
        patient_id = None
        clinic_id = None
        
        if current_user.role == 'patient':
            # Patients can only record for themselves
            patient_id = UUID(current_user.id)
            
            # Fetch patient's clinic_id from User model
            patient_user = db.query(User).filter(User.id == patient_id).first()
            if not patient_user:
                raise NotFoundException("Patient user not found")
            
            if not patient_user.clinic_id:
                raise BadRequestException(
                    message="Patient clinic not assigned",
                    errors={"clinic_id": ["Patient must be assigned to a clinic"]}
                )
            
            clinic_id = patient_user.clinic_id
            doctor_id = None  # Patient recorded it
            
            # Determine consent: default to False if not provided (patient must explicitly consent)
            share_with_doctor = data.share_with_doctor if data.share_with_doctor is not None else False
            
        elif current_user.role in ['doctor', 'nurse', 'staff']:
            # Doctors/staff must provide patient_id
            if not data.patient_id:
                raise BadRequestException(
                    message="Patient ID required",
                    errors={"patient_id": ["patient_id is required when recording as a doctor/staff"]}
                )
            
            patient_id = data.patient_id
            
            # Fetch patient's clinic_id from User model
            patient_user = db.query(User).filter(User.id == patient_id).first()
            if not patient_user:
                raise NotFoundException("Patient user not found")
            
            if not patient_user.clinic_id:
                raise BadRequestException(
                    message="Patient clinic not assigned",
                    errors={"clinic_id": ["Patient must be assigned to a clinic"]}
                )
            
            clinic_id = patient_user.clinic_id
            
            # Check clinic access for doctors/nurses/staff (if they have a clinic_id)
            if current_user.clinic_id and str(current_user.clinic_id) != str(clinic_id):
                raise ForbiddenException("You can only record vital signs for patients in your clinic")
            
            doctor_id = current_user.id if current_user.role == 'doctor' else None
            
            # Default to True when doctor records (can be overridden)
            share_with_doctor = data.share_with_doctor if data.share_with_doctor is not None else True
            
        elif current_user.role in ['clinic_admin', 'super_admin']:
            # Admins must provide patient_id
            if not data.patient_id:
                raise BadRequestException(
                    message="Patient ID required",
                    errors={"patient_id": ["patient_id is required when recording as an admin"]}
                )
            
            patient_id = data.patient_id
            
            # Fetch patient's clinic_id from User model
            patient_user = db.query(User).filter(User.id == patient_id).first()
            if not patient_user:
                raise NotFoundException("Patient user not found")
            
            if not patient_user.clinic_id:
                raise BadRequestException(
                    message="Patient clinic not assigned",
                    errors={"clinic_id": ["Patient must be assigned to a clinic"]}
                )
            
            clinic_id = patient_user.clinic_id
            
            # Check clinic access for clinic admins
            if current_user.role == 'clinic_admin':
                if str(current_user.clinic_id) != str(clinic_id):
                    raise ForbiddenException("You can only record vital signs for patients in your clinic")
            
            doctor_id = data.doctor_id
            
            # Default to True when admin records (can be overridden)
            share_with_doctor = data.share_with_doctor if data.share_with_doctor is not None else True
        else:
            raise ForbiddenException("You do not have permission to record vital signs")
        
        # Convert vitals to list of dicts
        vitals_list = [{"vital_name_id": v.vital_name_id, "value": v.value} for v in data.vitals]
        
        # Create records (one per vital)
        created_records = service.create_vital_signs_records(
            patient_id=patient_id,
            clinic_id=clinic_id,
            vitals=vitals_list,
            doctor_id=doctor_id,
            appointment_id=data.appointment_id,
            record_date=data.record_date,
            notes=data.notes,
            check_max_entries=True,
            share_with_doctor=share_with_doctor
        )
        
        # Serialize records
        records_data = [serialize_vital_record(record, include_vital_name=True) for record in created_records]
        
        # For backward compatibility, return first record in data field
        # But also include all records in a 'records' field
        response_data = {
            "records": records_data,
            "count": len(records_data)
        }
        
        if records_data:
            response_data["record"] = records_data[0]  # First record for backward compatibility
        
        return laravel_response(
            success=True,
            message=f"Vital signs recorded successfully ({len(created_records)} records created)",
            data=response_data
        )
    
    except (ValidationException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to record vital signs: {str(e)}")
        raise


@router.get(
    "/patient/{patient_id}",
    response_model=PatientVitalSignsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current patient vital signs",
    description="""Retrieve current vital signs for a patient (latest record per vital type)
    
    **Current Vitals Endpoint**
    
    This endpoint returns the **most recent vital sign record for each active vital type**.
    It includes ALL active vitals configured by admin, even if the patient has never recorded
    a value for them. Vitals without recorded values will have null/empty fields.
    
    **Key Features:**
    - Returns all active vitals (configured by admin)
    - Shows latest recorded value for each vital (if available)
    - Vitals without recorded values appear with null/empty fields
    - Does NOT include historical/past records - only current/latest values
    
    **Use Cases:**
    - Display patient's current vital signs dashboard
    - Show latest readings for each vital type
    - Quick overview of patient's current health status
    - See which vitals are available but not yet recorded
    
    **For Historical Records:**
    Use the `/patient-vital-signs/patient/{patient_id}/history` endpoint to retrieve
    past vital signs grouped by date.
    
    **Permissions:**
    - Patients can only view their own vital signs
    - Doctors and staff can view records for patients in their clinic
    - Clinic admins can view records for patients in their clinic
    """
)
async def get_patient_vital_signs(
    patient_id: UUID = Path(..., description="Patient user ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current patient vital signs (latest per vital type)
    
    **Current Vitals Endpoint**
    
    Returns the most recent vital sign record for each vital type.
    This endpoint is designed for displaying the patient's current vital signs
    and does NOT include historical/past records.
    
    **Key Features:**
    - Returns ALL active vitals (configured by admin)
    - Shows latest recorded value for each vital (if available)
    - Vitals without recorded values appear with null/empty fields
    - No historical data included - only current/latest values
    - Optimized for current status display
    
    **For Historical Data:**
    Use `/patient-vital-signs/patient/{patient_id}/history` endpoint to get
    past vital signs grouped by date.
    
    Args:
        patient_id: Patient user ID
        
    Returns:
        List of current vital signs (latest record per vital type)
    """
    try:
        # Check permissions and determine if filtering by consent is needed
        for_doctor = False
        if current_user.role == 'patient':
            # Patients can only view their own records
            # Convert both to strings for proper comparison (current_user.id is string, patient_id is UUID)
            if str(current_user.id) != str(patient_id):
                raise ForbiddenException("You can only view your own vital signs")
            # Patients see all their vitals (no consent filtering)
            for_doctor = False
        elif current_user.role in ['doctor', 'nurse', 'staff']:
            # Doctors/nurses/staff can view vitals for patients in their clinic
            # But only see vitals where patient has consented
            for_doctor = True
        elif current_user.role == 'clinic_admin':
            # Clinic admins can only view records in their clinic
            # We'll check this after fetching records
            # Admins see all vitals (no consent filtering for now)
            for_doctor = False
        
        service = PatientVitalSignsService(db)
        
        # Get current vitals (includes all active vitals, even without records)
        # Filter by consent if querying for doctor
        vitals_data = service.get_current_vital_signs(patient_id=patient_id, for_doctor=for_doctor)
        
        # Check clinic access for clinic admins (only check if records exist)
        if current_user.role == 'clinic_admin':
            clinic_ids = set()
            for vital_data in vitals_data:
                if vital_data["record"]:
                    clinic_ids.add(str(vital_data["record"].clinic_id))
            if clinic_ids and (len(clinic_ids) > 1 or str(current_user.clinic_id) not in clinic_ids):
                raise ForbiddenException("You can only view vital signs for patients in your clinic")
        
        # Serialize records with vital name info
        records_data = []
        for vital_data in vitals_data:
            record = vital_data["record"]
            vital_name = vital_data["vital_name"]
            
            if record:
                # Patient has recorded this vital - serialize the record
                record_data = serialize_vital_record(record, include_vital_name=False)
                record_data["vital_name"] = {
                    "id": str(vital_name.id),
                    "name": vital_name.name,
                    "unit": vital_name.unit,
                    "data_type": vital_name.data_type,
                    "display_order": vital_name.display_order,
                }
            else:
                # Patient hasn't recorded this vital - return structure with null values (no default for filled)
                record_data = {
                    "id": None,
                    "patient_id": str(patient_id),
                    "vital_name_id": str(vital_name.id),
                    "clinic_id": None,
                    "doctor_id": None,
                    "appointment_id": None,
                    "record_date": None,
                    "numeric_value": None,
                    "text_value": None,
                    "unit": vital_name.unit,
                    "notes": None,
                    "share_with_doctor": False,
                    "created_at": None,
                    "updated_at": None,
                    "vital_name": {
                        "id": str(vital_name.id),
                        "name": vital_name.name,
                        "unit": vital_name.unit,
                        "data_type": vital_name.data_type,
                        "display_order": vital_name.display_order,
                    }
                }
            
            records_data.append(record_data)
        
        return laravel_response(
            success=True,
            message="Current vital signs retrieved successfully",
            data={
                "vital_signs": records_data,
                "total": len(records_data),
                "count": len(records_data)
            }
        )
    
    except (ForbiddenException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Failed to get current patient vital signs: {str(e)}")
        raise


@router.get(
    "/patient/{patient_id}/history",
    status_code=status.HTTP_200_OK,
    summary="Get patient historical vital signs by date",
    description="""Retrieve historical vital signs for a patient grouped by date
    
    **Historical Vitals Endpoint**
    
    This endpoint returns vital signs records grouped by date (YYYY-MM-DD format).
    Each date contains ALL active vitals configured by admin, with recorded values where available.
    Vitals without recorded values on a specific date will have null/empty fields.
    
    **Date Grouping:**
    - Records are grouped by the date they were recorded (YYYY-MM-DD format)
    - Dates are sorted in descending order (most recent first)
    - Each date contains an array of all active vitals
    - Vitals with recorded values on that date show the actual data
    - Vitals without recorded values on that date show null/empty fields
    
    **Key Features:**
    - Includes ALL active vitals for each date (even if not recorded)
    - Consistent structure across all dates (same vitals appear in each date)
    - Easy to display in table format with dates as columns
    - Shows which vitals were recorded vs. not recorded on each date
    - Array format is easier to iterate and more readable
    
    **Use Cases:**
    - View patient's vital signs history by specific dates
    - Track daily vital sign readings
    - Display historical data in a date-based table format
    - Analyze trends over specific dates
    - See which vitals are missing on specific dates
    
    **For Current Vitals:**
    Use the `/patient-vital-signs/patient/{patient_id}` endpoint to retrieve
    only the latest vital sign record for each vital type.
    
    **Query Parameters:**
    - **days_back**: (Optional) Number of days to go back from today. 
      If not provided, returns all historical records grouped by date.
    
    **Example Response:**
    ```json
    {
      "2025-01-07": [
        {"id": "...", "vital_name_id": "...", "vital_name": {...}, "numeric_value": 120, ...},
        {"id": null, "vital_name_id": "...", "vital_name": {...}, "numeric_value": null, ...},
        ...
      ],
      "2025-01-05": [
        {"id": "...", "vital_name_id": "...", "vital_name": {...}, "numeric_value": 118, ...},
        {"id": null, "vital_name_id": "...", "vital_name": {...}, "numeric_value": null, ...},
        ...
      ]
    }
    ```
    
    **Permissions:**
    - Patients can only view their own vital signs history
    - Doctors and staff can view history for patients in their clinic
    - Clinic admins can view history for patients in their clinic
    """
)
async def get_patient_vital_signs_history(
    patient_id: UUID = Path(..., description="Patient user ID"),
    days_back: Optional[int] = Query(None, ge=1, description="Number of days to go back (optional, returns all if not provided)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get patient historical vital signs grouped by date
    
    **Historical Vitals Endpoint**
    
    Returns vital signs records grouped by date (YYYY-MM-DD format).
    Each date contains all vital signs recorded on that specific date.
    
    **Date Format:**
    - Dates are in YYYY-MM-DD format (e.g., "2025-01-07")
    - Dates are sorted in descending order (most recent first)
    - Each date contains an array of ALL active vitals
    - Vitals with recorded values show actual data
    - Vitals without recorded values show null/empty fields
    
    **Example Response Structure:**
    ```json
    {
      "2025-01-07": [
        {"id": "...", "vital_name_id": "...", "vital_name": {...}, "numeric_value": 120, ...},
        {"id": null, "vital_name_id": "...", "vital_name": {...}, "numeric_value": null, ...},
        ...
      ],
      "2025-01-05": [
        {"id": "...", "vital_name_id": "...", "vital_name": {...}, "numeric_value": 118, ...},
        {"id": null, "vital_name_id": "...", "vital_name": {...}, "numeric_value": null, ...},
        ...
      ]
    }
    ```
    
    **Query Parameters:**
    - `days_back`: Optional. Limits results to last N days. 
      If omitted, returns all historical records grouped by date.
    
    Args:
        patient_id: Patient user ID
        days_back: Optional number of days to go back
        
    Returns:
        Dictionary with dates (YYYY-MM-DD) as keys and lists of vital signs as values
    """
    try:
        # Check permissions and determine if filtering by consent is needed
        for_doctor = False
        if current_user.role == 'patient':
            # Patients can only view their own records
            if str(current_user.id) != str(patient_id):
                raise ForbiddenException("You can only view your own vital signs history")
            # Patients see all their vitals (no consent filtering)
            for_doctor = False
        elif current_user.role in ['doctor', 'nurse', 'staff']:
            # Doctors/nurses/staff can view vitals for patients in their clinic
            # But only see vitals where patient has consented
            
            # Check clinic access - verify patient belongs to doctor's clinic
            patient_user = db.query(User).filter(User.id == patient_id).first()
            if not patient_user:
                raise NotFoundException("Patient not found")
            
            # Verify this is actually a patient
            if patient_user.role != 'patient':
                raise BadRequestException(
                    message="Invalid patient ID",
                    errors={"patient_id": [f"User with ID {patient_id} is not a patient (role: {patient_user.role})"]}
                )
            
            if not patient_user.clinic_id:
                raise BadRequestException(
                    message="Patient clinic not assigned",
                    errors={"clinic_id": ["Patient must be assigned to a clinic"]}
                )
            
            # Verify doctor has access to this patient's clinic
            if current_user.clinic_id and str(current_user.clinic_id) != str(patient_user.clinic_id):
                raise ForbiddenException("You can only view vital signs history for patients in your clinic")
            
            for_doctor = True
        elif current_user.role == 'clinic_admin':
            # Clinic admins can only view records in their clinic
            # We'll check this after fetching records
            # Admins see all vitals (no consent filtering for now)
            for_doctor = False
        
        service = PatientVitalSignsService(db)
        
        # Get historical vitals grouped by date (includes all active vitals for each date)
        # Filter by consent if querying for doctor
        dates_dict = service.get_historical_vital_signs_by_date(
            patient_id=patient_id,
            days_back=days_back,
            for_doctor=for_doctor
        )
        
        # Get all active vital names for reference
        from app.services.vital_name_service import VitalNameService
        vital_name_service = VitalNameService(db)
        all_active_vitals = vital_name_service.get_all_vital_names(is_active=True)
        vital_names_map = {str(vn.id): vn for vn in all_active_vitals}
        
        # Serialize records for each date (now returns array format)
        result = {}
        for date_key, date_vitals_list in dates_dict.items():
            date_vitals_data = []
            
            for vital_data in date_vitals_list:
                record = vital_data["record"]
                vital_name = vital_data["vital_name"]
                
                if record:
                    # Patient recorded this vital on this date - serialize the record
                    record_data = serialize_vital_record(record, include_vital_name=False)
                    record_data["vital_name"] = {
                        "id": str(vital_name.id),
                        "name": vital_name.name,
                        "unit": vital_name.unit,
                        "data_type": vital_name.data_type,
                        "display_order": vital_name.display_order,
                    }
                    date_vitals_data.append(record_data)
                else:
                    # Patient didn't record this vital on this date - return null structure
                    date_vitals_data.append({
                        "id": None,
                        "patient_id": str(patient_id),
                        "vital_name_id": str(vital_name.id),
                        "clinic_id": None,
                        "doctor_id": None,
                        "appointment_id": None,
                        "record_date": None,
                        "numeric_value": None,
                        "text_value": None,
                        "unit": vital_name.unit,
                        "notes": None,
                        "share_with_doctor": None,
                        "created_at": None,
                        "updated_at": None,
                        "vital_name": {
                            "id": str(vital_name.id),
                            "name": vital_name.name,
                            "unit": vital_name.unit,
                            "data_type": vital_name.data_type,
                            "display_order": vital_name.display_order,
                        }
                    })
            
            result[date_key] = date_vitals_data
        
        # Check clinic access for clinic admins
        if current_user.role == 'clinic_admin' and dates_dict:
            all_clinic_ids = set()
            for date_vitals_list in dates_dict.values():
                for vital_data in date_vitals_list:
                    record = vital_data.get("record")
                    if record:  # Only check if record exists
                        all_clinic_ids.add(str(record.clinic_id))
            if all_clinic_ids and (len(all_clinic_ids) > 1 or str(current_user.clinic_id) not in all_clinic_ids):
                raise ForbiddenException("You can only view vital signs history for patients in your clinic")
        
        return laravel_response(
            success=True,
            message=f"Historical vital signs retrieved successfully ({len(dates_dict)} date(s))",
            data={
                "vital_signs_by_date": result,
                "dates_count": len(dates_dict)
            }
        )
    
    except (ForbiddenException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Failed to get patient vital signs history: {str(e)}")
        raise


@router.patch(
    "/consent",
    response_model=VitalSignsConsentUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update consent for all vital signs",
    description="Update patient consent to share all vital signs with doctor (Patient only)"
)
async def update_vital_signs_consent(
    data: VitalSignsConsentUpdate = ...,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update consent for ALL vital signs
    
    **Patient only endpoint**
    
    Allows patients to update their consent to share ALL their vital signs with their doctor.
    This updates consent for all vital sign records recorded by the patient.
    
    **Consent Values:**
    - `true`: Patient consents to share all vital signs with doctor (doctor can see all vitals)
    - `false`: Patient does not consent (doctor cannot see any vitals)
    
    **Important**: This updates ALL vital signs at once. Setting this to `false` will immediately 
    hide all vital signs from doctor's view.
    
    Args:
        data: Consent update data with share_with_doctor boolean
        
    Returns:
        Success message with count of updated records
    """
    try:
        # Only patients can update consent
        if current_user.role != 'patient':
            raise ForbiddenException("Only patients can update consent for their vital signs")
        
        service = PatientVitalSignsService(db)
        
        # Update consent for all vitals
        updated_count = service.update_all_consent(
            patient_id=UUID(current_user.id),
            share_with_doctor=data.share_with_doctor
        )
        
        return VitalSignsConsentUpdateResponse(
            success=True,
            message=f"Consent updated successfully for {updated_count} vital sign record(s)",
            data={
                "updated_count": updated_count,
                "share_with_doctor": data.share_with_doctor
            },
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to update consent: {str(e)}")
        raise


@router.get(
    "/{vital_signs_id}",
    response_model=PatientVitalSignsSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vital signs by ID",
    description="Retrieve a specific vital signs record by ID"
)
async def get_vital_signs(
    vital_signs_id: UUID = Path(..., description="Vital signs record ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get vital signs by ID
    
    Retrieves a specific vital signs record by its ID.
    
    Args:
        vital_signs_id: UUID of the vital signs record
        
    Returns:
        Vital signs record details
    """
    try:
        service = PatientVitalSignsService(db)
        
        vital_record = service.get_vital_signs_by_id(vital_signs_id)
        
        # Check permissions
        if current_user.role == 'patient':
            # Convert both to strings for proper comparison (current_user.id is string, vital_record.patient_id is UUID)
            if str(current_user.id) != str(vital_record.patient_id):
                raise ForbiddenException("You can only view your own vital signs")
        elif current_user.role == 'clinic_admin':
            if current_user.clinic_id != vital_record.clinic_id:
                raise ForbiddenException("You can only view vital signs for patients in your clinic")
        
        # Load vital name
        vital_name = db.query(VitalName).filter(VitalName.id == vital_record.vital_name_id).first()
        record_data = serialize_vital_record(vital_record, include_vital_name=False)
        if vital_name:
            record_data["vital_name"] = {
                "id": str(vital_name.id),
                "name": vital_name.name,
                "unit": vital_name.unit,
                "data_type": vital_name.data_type,
                "display_order": vital_name.display_order,
            }
        
        return PatientVitalSignsSingleResponse(
            success=True,
            message="Vital signs retrieved successfully",
            data=record_data,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to get vital signs: {str(e)}")
        raise


@router.patch(
    "/{vital_signs_id}",
    response_model=PatientVitalSignsUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update vital signs",
    description="Update a vital signs record (Patient: own only; Doctor/Staff: patients in clinic)"
)
async def update_vital_signs(
    vital_signs_id: UUID = Path(..., description="Vital signs record ID"),
    data: PatientVitalSignsUpdate = ...,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update vital signs.
    Patient: can update their own records. Doctor/Staff/Admin: can update patients in their clinic.
    """
    try:
        service = PatientVitalSignsService(db)
        vital_record = service.get_vital_signs_by_id(vital_signs_id)
        
        if current_user.role == "patient":
            if str(current_user.id) != str(vital_record.patient_id):
                raise ForbiddenException("You can only update your own vital signs")
        elif current_user.role in ["doctor", "nurse", "staff"]:
            if current_user.clinic_id and str(current_user.clinic_id) != str(vital_record.clinic_id):
                raise ForbiddenException("You can only update vital signs for patients in your clinic")
        elif current_user.role == "clinic_admin":
            if str(current_user.clinic_id) != str(vital_record.clinic_id):
                raise ForbiddenException("You can only update vital signs for patients in your clinic")
        elif current_user.role != "super_admin":
            raise ForbiddenException("You do not have permission to update vital signs")
        
        updated_record = service.update_vital_signs_record(
            vital_signs_id=vital_signs_id,
            numeric_value=data.numeric_value,
            text_value=data.text_value,
            notes=data.notes,
            record_date=data.record_date,
            share_with_doctor=data.share_with_doctor
        )
        
        # Load vital name
        vital_name = db.query(VitalName).filter(VitalName.id == updated_record.vital_name_id).first()
        record_data = serialize_vital_record(updated_record, include_vital_name=False)
        if vital_name:
            record_data["vital_name"] = {
                "id": str(vital_name.id),
                "name": vital_name.name,
                "unit": vital_name.unit,
                "data_type": vital_name.data_type,
                "display_order": vital_name.display_order,
            }
        
        return PatientVitalSignsUpdateResponse(
            success=True,
            message="Vital signs updated successfully",
            data=record_data,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to update vital signs: {str(e)}")
        raise


@router.delete(
    "/{vital_signs_id}",
    response_model=PatientVitalSignsDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete vital signs",
    description="Delete a vital signs record (soft delete, Admin only)"
)
async def delete_vital_signs(
    vital_signs_id: UUID = Path(..., description="Vital signs record ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """
    Delete vital signs (soft delete)
    
    **Admin only endpoint**
    
    Soft deletes a vital signs record.
    
    Args:
        vital_signs_id: UUID of the vital signs record to delete
        
    Returns:
        Success message
    """
    try:
        service = PatientVitalSignsService(db)
        
        service.delete_vital_signs_record(vital_signs_id)
        
        return PatientVitalSignsDeleteResponse(
            success=True,
            message="Vital signs deleted successfully",
            data=None,
            errors=None
        )
    
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete vital signs: {str(e)}")
        raise


@router.patch(
    "/consent",
    response_model=VitalSignsConsentUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update consent for all vital signs",
    description="Update patient consent to share all vital signs with doctor (Patient only)"
)
async def update_vital_signs_consent(
    data: VitalSignsConsentUpdate = ...,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update consent for ALL vital signs
    
    **Patient only endpoint**
    
    Allows patients to update their consent to share ALL their vital signs with their doctor.
    This updates consent for all vital sign records recorded by the patient.
    
    **Consent Values:**
    - `true`: Patient consents to share all vital signs with doctor (doctor can see all vitals)
    - `false`: Patient does not consent (doctor cannot see any vitals)
    
    **Important**: This updates ALL vital signs at once. Setting this to `false` will immediately 
    hide all vital signs from doctor's view.
    
    Args:
        data: Consent update data with share_with_doctor boolean
        
    Returns:
        Success message with count of updated records
    """
    try:
        # Only patients can update consent
        if current_user.role != 'patient':
            raise ForbiddenException("Only patients can update consent for their vital signs")
        
        service = PatientVitalSignsService(db)
        
        # Update consent for all vitals
        updated_count = service.update_all_consent(
            patient_id=UUID(current_user.id),
            share_with_doctor=data.share_with_doctor
        )
        
        return VitalSignsConsentUpdateResponse(
            success=True,
            message=f"Consent updated successfully for {updated_count} vital sign record(s)",
            data={
                "updated_count": updated_count,
                "share_with_doctor": data.share_with_doctor
            },
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to update consent: {str(e)}")
        raise
