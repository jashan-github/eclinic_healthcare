"""
Staff Dashboard API Endpoints
Routes for staff to view their assigned doctor's information and dashboard data
"""

from fastapi import APIRouter, Depends, status, Request, Query, Path
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy import or_, and_, func, distinct
from sqlalchemy.orm import joinedload
from datetime import datetime, date

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_feature
from app.core.security import CurrentUser
from app.models.user import User
from app.models.profile import ContactDetail, UserProfile
from app.models.appointment import Appointment
from app.models.appointment_request import AppointmentRequest
from app.models.appointment_payment import AppointmentPayment
from app.models.service import Service
from app.core.exceptions import laravel_response, NotFoundException, ForbiddenException
from app.schemas.profile import DoctorProfileResponse, DoctorProfileSingleResponse
from app.services.profile_service import ProfileService
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from loguru import logger


router = APIRouter(prefix="/staff", tags=["Staff - Dashboard"])


class StaffDashboardResponse(BaseModel):
    """Staff dashboard response with doctor profile and appointments"""
    success: bool = True
    message: str = "Assigned doctor information retrieved successfully"
    data: Dict[str, Any]
    errors: Optional[dict] = None


class PatientContactDetailsResponse(BaseModel):
    """Patient contact details response for staff"""
    success: bool = True
    message: str = "Patient contact details retrieved successfully"
    data: Dict[str, Any]
    errors: Optional[dict] = None


class StaffDashboardStatsResponse(BaseModel):
    """Staff dashboard statistics response"""
    success: bool = True
    message: str = "Dashboard statistics retrieved successfully"
    data: Dict[str, Any]
    errors: Optional[dict] = None


class PatientListResponse(BaseModel):
    """Patient list response for staff"""
    success: bool = True
    message: str = "Patients retrieved successfully"
    data: Dict[str, Any]
    errors: Optional[dict] = None


@router.get(
    "/assigned-doctor",
    response_model=StaffDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get assigned doctor information with appointments",
    description="""
    Get the assigned doctor's profile information and appointments for the authenticated staff user.
    
    **Staff Only Endpoint**
    - Only authenticated staff users can access this endpoint
    - Returns the profile of the doctor assigned to the staff member
    - Includes doctor's name, contact, education, experience, languages, specializations, and bio
    - Includes paginated appointments (today or upcoming) with search by patient name
    
    **Query Parameters:**
    - **type**: Filter by appointment type - 'today' or 'upcoming' (optional, default: both)
    - **search**: Search by patient name (optional)
    - **page**: Page number (default: 1, minimum: 1)
    - **per_page**: Items per page (default: 20, minimum: 1, maximum: 100)
    
    **Returns:**
    - Doctor profile information
    - Paginated appointments list with pagination metadata
    - 404 error if no doctor is assigned
    """
)
async def get_assigned_doctor(
    request: Request,
    type: Optional[str] = Query(None, description="Filter by appointment type: 'today' or 'upcoming'"),
    search: Optional[str] = Query(None, description="Search by patient name"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get assigned doctor information for staff user
    
    **Authentication Required**: Yes (Staff role)
    
    Returns:
        Doctor profile information including:
        - Name fields (first_name, middle_name, last_name)
        - Date of birth and age
        - Contact information (phone, email)
        - Education and years of experience
        - Languages spoken (with details)
        - Specializations (with details)
        - About/bio
        - Profile image URL
    """
    try:
        # Check if user is staff
        if current_user.role != "staff":
            raise ForbiddenException(
                message="This endpoint is only for staff users",
                errors={"role": ["Only staff users can access this endpoint"]}
            )
        
        # Get the current user from database to access assigned_doctor_id
        user = db.query(User).filter(
            User.id == current_user.id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user": ["User account not found"]}
            )
        
        # Check if staff has an assigned doctor
        if not user.assigned_doctor_id:
            raise NotFoundException(
                message="No assigned doctor",
                errors={"assigned_doctor": ["No doctor has been assigned to this staff member"]}
            )
        
        # Get the assigned doctor's profile using ProfileService
        # Handle case where doctor profile might not exist yet
        profile_service = ProfileService(db)
        try:
            doctor_profile = profile_service.get_doctor_profile(user.assigned_doctor_id)
        except NotFoundException as e:
            # If doctor profile doesn't exist, create a minimal profile response
            from app.models.user_profile import UserProfile
            from app.models.user import User as UserModel
            
            doctor_user = db.query(UserModel).filter(
                UserModel.id == user.assigned_doctor_id,
                UserModel.deleted_at.is_(None)
            ).first()
            
            if not doctor_user:
                raise NotFoundException(
                    message="Assigned doctor not found",
                    errors={"doctor": ["Assigned doctor does not exist"]}
                )
            
            # Create a minimal doctor profile response with basic info
            from app.schemas.profile import DoctorProfileResponse
            doctor_profile = DoctorProfileResponse(
                id=doctor_user.id,
                user_id=doctor_user.id,
                first_name=None,
                middle_name=None,
                last_name=None,
                date_of_birth=None,
                age=None,
                phone_number=doctor_user.phone,
                email=doctor_user.email,
                education=None,
                years_of_experience=None,
                languages=None,
                specializations=None,
                about=None,
                profile_img=None,
                created_at=doctor_user.created_at if doctor_user.created_at else datetime.now(),
                updated_at=doctor_user.updated_at if doctor_user.updated_at else datetime.now()
            )
        
        # Validate appointment type parameter
        if type and type not in ['today', 'upcoming']:
            raise ForbiddenException(
                message="Invalid appointment type",
                errors={"type": ["Appointment type must be 'today' or 'upcoming'"]}
            )
        
        # Get the assigned doctor's appointments using AppointmentService
        appointment_service = AppointmentService(db)
        appointments_data = appointment_service.get_doctor_appointments_grouped_by_id(
            doctor_id=user.assigned_doctor_id,
            appointment_type=type,
            search=search,
            page=page,
            per_page=per_page
        )
        
        # Create audit log
        audit_service = AuditService(db)
        audit_service.create_audit_log_from_request(
            request=request,
            actor_user_id=current_user.id,
            action="VIEW_ASSIGNED_DOCTOR",
            entity_type="doctor_profile",
            entity_id=user.assigned_doctor_id,
            audit_metadata={
                "staff_id": str(current_user.id),
                "doctor_id": str(user.assigned_doctor_id),
                "access_type": "staff_dashboard",
                "appointment_type": type,
                "search": search,
                "page": page
            }
        )
        
        logger.info(f"Staff user {current_user.id} viewed assigned doctor {user.assigned_doctor_id} with appointments (type: {type}, search: {search}, page: {page})")
        
        # Convert doctor_profile to dict (it's a DoctorProfileResponse Pydantic model)
        doctor_profile_dict = doctor_profile.model_dump() if hasattr(doctor_profile, 'model_dump') else doctor_profile.dict() if hasattr(doctor_profile, 'dict') else doctor_profile
        
        # Combine doctor profile and appointments in response
        response_data = {
            "doctor_profile": doctor_profile_dict,
            "appointments": appointments_data.get("appointments", []),
            "pagination": appointments_data.get("pagination", {})
        }
        
        return StaffDashboardResponse(
            success=True,
            message="Assigned doctor information retrieved successfully",
            data=response_data,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve assigned doctor information: {str(e)}", exc_info=True)
        raise


@router.get(
    "/patients/{patient_id}/contact-details",
    response_model=PatientContactDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient contact details",
    description="""
    Get patient contact details for the authenticated staff user.
    
    **Staff Only Endpoint**
    - Only authenticated staff users can access this endpoint
    - Staff can only view contact details of patients who have appointments with their assigned doctor
    - Returns patient's full name, email, contact phone, emergency contact, and family contact
    
    **Path Parameters:**
    - **patient_id**: Patient user ID (UUID)
    
    **Returns:**
    - Full Name: Patient's full name
    - Email: Patient's email address
    - Contact: Patient's primary phone number
    - Emergency Contact: Emergency contact phone number
    - Family Contact: Family contact phone number
    - 404 error if patient not found or no appointment with assigned doctor
    - 403 error if staff doesn't have an assigned doctor
    """,
    dependencies=[Depends(require_feature("patients"))],
)
async def get_patient_contact_details(
    request: Request,
    patient_id: UUID = Path(..., description="Patient user ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get patient contact details for staff user
    
    **Authentication Required**: Yes (Staff role)
    
    **Access Control:**
    - Staff can only view contact details of patients who have appointments with their assigned doctor
    - Verifies that at least one appointment exists between the patient and assigned doctor
    
    Returns:
        Patient contact details including:
        - Full Name: Patient's full name from users table
        - Email: Patient's email (from users.email or contact_details.email)
        - Contact: Primary phone number (from contact_details.phone or users.phone)
        - Emergency Contact: Emergency contact phone number
        - Family Contact: Family contact phone number
    """
    try:
        # Check if user is staff
        if current_user.role != "staff":
            raise ForbiddenException(
                message="This endpoint is only for staff users",
                errors={"role": ["Only staff users can access this endpoint"]}
            )
        
        # Get the current user from database to access assigned_doctor_id
        user = db.query(User).filter(
            User.id == current_user.id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user": ["User account not found"]}
            )
        
        # Check if staff has an assigned doctor
        if not user.assigned_doctor_id:
            raise ForbiddenException(
                message="No assigned doctor",
                errors={"assigned_doctor": ["No doctor has been assigned to this staff member. Cannot view patient contact details."]}
            )
        
        # Get patient user
        patient = db.query(User).filter(
            User.id == patient_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient does not exist"]}
            )
        
        # Verify that patient has at least one appointment with the assigned doctor
        appointment_exists = db.query(Appointment).filter(
            Appointment.doctor_id == user.assigned_doctor_id,
            Appointment.patient_id == patient_id,
            Appointment.deleted_at.is_(None)
        ).first()
        
        if not appointment_exists:
            raise ForbiddenException(
                message="Access denied",
                errors={"patient_id": ["You can only view contact details of patients who have appointments with your assigned doctor"]}
            )
        
        # Get primary contact details
        primary_contact = db.query(ContactDetail).filter(
            ContactDetail.user_id == patient_id,
            or_(
                ContactDetail.is_primary == True,
                ContactDetail.contact_type == "primary"
            ),
            ContactDetail.deleted_at.is_(None)
        ).first()
        
        # If no primary contact exists, create one with basic info from user table
        if not primary_contact:
            primary_contact = ContactDetail(
                user_id=patient_id,
                contact_type="primary",
                is_primary=True,
                email=patient.email,
                phone=patient.phone if patient.phone else None
            )
            db.add(primary_contact)
            db.commit()
            db.refresh(primary_contact)
        else:
            # Sync email and phone from users table if missing
            if not primary_contact.email and patient.email:
                primary_contact.email = patient.email
            if not primary_contact.phone and patient.phone:
                primary_contact.phone = patient.phone
            if primary_contact.email != patient.email or primary_contact.phone != patient.phone:
                db.commit()
                db.refresh(primary_contact)
        
        # Build contact details response
        contact_details = {
            "full_name": patient.name,
            "email": primary_contact.email or patient.email,
            "contact": primary_contact.phone or patient.phone,
            "emergency_contact": primary_contact.emergency_contact_phone,
            "family_contact": primary_contact.family_contact_phone
        }
        
        # Create audit log
        audit_service = AuditService(db)
        audit_service.create_audit_log_from_request(
            request=request,
            actor_user_id=current_user.id,
            action="VIEW_PATIENT_CONTACT_DETAILS",
            entity_type="patient_contact",
            entity_id=patient_id,
            audit_metadata={
                "staff_id": str(current_user.id),
                "doctor_id": str(user.assigned_doctor_id),
                "patient_id": str(patient_id),
                "access_type": "staff_dashboard"
            }
        )
        
        logger.info(f"Staff user {current_user.id} viewed contact details for patient {patient_id} (assigned doctor: {user.assigned_doctor_id})")
        
        return PatientContactDetailsResponse(
            success=True,
            message="Patient contact details retrieved successfully",
            data=contact_details,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve patient contact details: {str(e)}", exc_info=True)
        raise


@router.get(
    "/stats",
    response_model=StaffDashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get staff dashboard statistics",
    description="Get statistics for the assigned doctor: today's appointment count, active patient count, and pending appointment request count",
    dependencies=[Depends(require_feature("patients"))],
)
async def get_staff_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get dashboard statistics for staff user's assigned doctor
    
    Returns:
    - today_appointments_count: Number of appointments scheduled for today
    - active_patients_count: Number of unique active patients (patients with appointments that are not COMPLETED or CANCELLED)
    - pending_appointment_requests_count: Number of pending appointment requests
    
    **Staff only endpoint**
    """
    # Validate current user is staff
    if current_user.role != 'staff':
        raise ForbiddenException(
            message="Access denied",
            errors={"role": ["Only staff users can access dashboard statistics"]}
        )
    
    # Get the staff user with assigned doctor
    user = db.query(User).filter(
        User.id == current_user.id,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        raise NotFoundException(
            message="User not found",
            errors={"user": ["User does not exist"]}
        )
    
    # Check if staff has assigned doctor
    if not user.assigned_doctor_id:
        raise NotFoundException(
            message="No assigned doctor",
            errors={"doctor": ["Staff user does not have an assigned doctor"]}
        )
    
    doctor_id = user.assigned_doctor_id
    today = date.today()
    
    try:
        # 1. Today's appointment count
        today_appointments_count = db.query(func.count(Appointment.id)).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == today,
            Appointment.deleted_at.is_(None)
        ).scalar() or 0
        
        # 2. Active patient count (unique patients with appointments that are not COMPLETED or CANCELLED)
        active_patients_count = db.query(
            func.count(distinct(Appointment.patient_id))
        ).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status.notin_(['COMPLETED', 'CANCELLED', 'NO_SHOW']),
            Appointment.deleted_at.is_(None)
        ).scalar() or 0
        
        # 3. Pending appointment request count
        pending_appointment_requests_count = db.query(
            func.count(AppointmentRequest.id)
        ).filter(
            AppointmentRequest.doctor_id == doctor_id,
            AppointmentRequest.status == 'PENDING',
            AppointmentRequest.deleted_at.is_(None)
        ).scalar() or 0
        
        # Prepare response data
        stats_data = {
            "today_appointments_count": today_appointments_count,
            "active_patients_count": active_patients_count,
            "pending_appointment_requests_count": pending_appointment_requests_count
        }
        
        # Log access
        audit_service = AuditService(db)
        audit_service.create_audit_log(
            actor_user_id=current_user.id,
            action="VIEW_STAFF_DASHBOARD_STATS",
            entity_type="staff_dashboard",
            entity_id=str(user.id),
            audit_metadata={
                "assigned_doctor_id": str(doctor_id),
                "stats": stats_data
            }
        )
        
        return laravel_response(
            success=True,
            message="Dashboard statistics retrieved successfully",
            data=stats_data
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Error retrieving staff dashboard statistics: {str(e)}", exc_info=True)
        raise NotFoundException(
            message="Error retrieving dashboard statistics",
            errors={"general": [str(e)]}
        )


@router.get(
    "/patients",
    response_model=PatientListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all patients list",
    description="Get list of all patients who have appointments with the assigned doctor, with pagination and search by name, phone, or email",
    dependencies=[Depends(require_feature("patients"))],
)
async def list_patients(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by patient name, phone number, or email"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get list of all patients for staff user's assigned doctor
    
    **Staff Only Endpoint**
    - Only authenticated staff users can access this endpoint
    - Returns only patients who have appointments with the assigned doctor
    - Supports pagination and search functionality
    
    **Query Parameters:**
    - **page**: Page number (default: 1, minimum: 1)
    - **per_page**: Items per page (default: 20, minimum: 1, maximum: 100)
    - **search**: Optional search term to filter by name, phone number, or email
    
    **Returns:**
    - List of patients with contact details
    - Pagination metadata (total, page, per_page, total_pages)
    - Each patient includes: id, name, email, contact, emergency_contact, family_contact, age, gender, profile_image
    """
    try:
        # Check if user is staff
        if current_user.role != "staff":
            raise ForbiddenException(
                message="This endpoint is only for staff users",
                errors={"role": ["Only staff users can access this endpoint"]}
            )
        
        # Get the current user from database to access assigned_doctor_id
        user = db.query(User).filter(
            User.id == current_user.id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise NotFoundException(
                message="User not found",
                errors={"user": ["User account not found"]}
            )
        
        # Check if staff has an assigned doctor
        if not user.assigned_doctor_id:
            raise NotFoundException(
                message="No assigned doctor",
                errors={"assigned_doctor": ["No doctor has been assigned to this staff member"]}
            )
        
        doctor_id = user.assigned_doctor_id
        
        # Get distinct patient IDs who have appointments with the assigned doctor
        patient_ids = db.query(distinct(Appointment.patient_id)).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.deleted_at.is_(None)
        ).all()
        patient_id_list = [pid[0] for pid in patient_ids]
        
        if not patient_id_list:
            # No patients found, return empty result
            return laravel_response(
                success=True,
                message="Patients retrieved successfully",
                data={
                    "patients": [],
                    "pagination": {
                        "total": 0,
                        "page": page,
                        "per_page": per_page,
                        "total_pages": 0
                    }
                }
            )
        
        # Build base query for patients
        query = db.query(User).filter(
            User.id.in_(patient_id_list),
            User.deleted_at.is_(None),
            User.role == 'patient'
        )
        
        # Apply search filter if provided
        if search:
            search_pattern = f"%{search}%"
            
            # Search in users table (name, email, phone)
            # Also search in contact_details table (phone, email)
            contact_detail_user_ids = db.query(ContactDetail.user_id).filter(
                or_(
                    ContactDetail.phone.ilike(search_pattern),
                    ContactDetail.email.ilike(search_pattern)
                ),
                ContactDetail.deleted_at.is_(None)
            ).all()
            contact_detail_id_list = [uid[0] for uid in contact_detail_user_ids]
            
            # Combine search conditions
            search_conditions = [
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.phone.ilike(search_pattern)
            ]
            
            if contact_detail_id_list:
                search_conditions.append(User.id.in_(contact_detail_id_list))
            
            query = query.filter(or_(*search_conditions))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination with eager loading to avoid N+1 queries
        offset = (page - 1) * per_page
        patients = query.options(
            joinedload(User.profile),
            joinedload(User.contact_details)
        ).order_by(User.name.asc()).offset(offset).limit(per_page).all()
        
        # Pre-fetch all contact details for these patients to avoid N+1 queries
        patient_id_list_for_contacts = [p.id for p in patients]
        all_contacts = {}
        if patient_id_list_for_contacts:
            contacts = db.query(ContactDetail).filter(
                ContactDetail.user_id.in_(patient_id_list_for_contacts),
                or_(
                    ContactDetail.is_primary == True,
                    ContactDetail.contact_type == "primary"
                ),
                ContactDetail.deleted_at.is_(None)
            ).all()
            for contact in contacts:
                if contact.user_id not in all_contacts:
                    all_contacts[contact.user_id] = contact
        
        # Build patient data list
        patients_data = []
        today = date.today()
        
        for patient in patients:
            # Get primary contact details from pre-fetched data
            primary_contact = all_contacts.get(patient.id)
            
            # Get patient profile (already loaded via joinedload)
            profile = patient.profile if hasattr(patient, 'profile') else None
            
            # Calculate age if date_of_birth exists
            age = None
            if profile and profile.date_of_birth:
                dob = profile.date_of_birth
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            # Get profile image
            profile_image = None
            if patient.avatar:
                from app.core.config import settings
                profile_image = f"{settings.BASE_URL}uploads/{patient.avatar}"
            elif profile and profile.avatar:
                from app.core.config import settings
                profile_image = f"{settings.BASE_URL}uploads/{profile.avatar}"
            
            # Build patient data
            patient_data = {
                "id": str(patient.id),
                "name": patient.name,
                "email": primary_contact.email if primary_contact and primary_contact.email else patient.email,
                "contact": primary_contact.phone if primary_contact and primary_contact.phone else patient.phone,
                "emergency_contact": primary_contact.emergency_contact_phone if primary_contact else None,
                "family_contact": primary_contact.family_contact_phone if primary_contact else None,
                "age": age,
                "gender": profile.gender if profile else None,
                "profile_image": profile_image
            }
            
            patients_data.append(patient_data)
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        # Prepare response data
        response_data = {
            "patients": patients_data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }
        }
        
        # Create audit log
        audit_service = AuditService(db)
        audit_service.create_audit_log_from_request(
            request=request,
            actor_user_id=current_user.id,
            action="VIEW_PATIENT_LIST",
            entity_type="patient_list",
            entity_id=None,
            audit_metadata={
                "staff_id": str(current_user.id),
                "doctor_id": str(doctor_id),
                "page": page,
                "per_page": per_page,
                "search": search,
                "total_results": total
            }
        )
        
        logger.info(f"Staff user {current_user.id} viewed patient list (assigned doctor: {doctor_id}, page: {page}, search: {search})")
        
        return laravel_response(
            success=True,
            message="Patients retrieved successfully",
            data=response_data
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve patient list: {str(e)}", exc_info=True)
        raise NotFoundException(
            message="Error retrieving patient list",
            errors={"general": [str(e)]}
        )


class InvoiceListResponse(BaseModel):
    """Invoice list response for staff"""
    success: bool = True
    message: str = "Invoices retrieved successfully"
    data: Dict[str, Any]
    errors: Optional[dict] = None


@router.get(
    "/invoices",
    status_code=status.HTTP_200_OK,
    summary="Get all invoices (staff: assigned doctor; doctor: own)",
    description="""
    Get list of all invoices (payments) for the doctor, ordered by latest (created_at desc).
    
    **Staff and Doctor**
    - **Staff**: Returns invoices for the staff member's assigned doctor
    - **Doctor**: Returns invoices for the authenticated doctor (own)
    - Supports pagination and search by patient name
    - Only shows COMPLETED payments (invoices)
    
    **Query Parameters:**
    - **page**: Page number (default: 1, minimum: 1)
    - **per_page**: Items per page (default: 20, minimum: 1, maximum: 100)
    - **search**: Optional search term to filter by patient name
    
    **Returns:**
    - List of invoices with payment details, patient information, and appointment details
    - Pagination metadata (total, page, per_page, total_pages)
    """,
    dependencies=[Depends(require_feature("payments"))],
)
async def list_invoices(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by patient name"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get list of all invoices for the doctor (staff: assigned doctor; doctor: own).
    """
    try:
        # Staff or doctor only (role is UserRole enum; compare with .value)
        role_value = getattr(current_user.role, "value", current_user.role)
        if role_value not in ("staff", "doctor"):
            raise ForbiddenException(
                message="This endpoint is for staff and doctor users only",
                errors={"role": ["Only staff or doctor users can access this endpoint"]}
            )
        
        # Resolve doctor_id: staff uses assigned doctor, doctor uses self
        if role_value == "doctor":
            doctor_id = current_user.id
        else:
            user = db.query(User).filter(
                User.id == current_user.id,
                User.deleted_at.is_(None)
            ).first()
            if not user:
                raise NotFoundException(
                    message="User not found",
                    errors={"user": ["User account not found"]}
                )
            if not user.assigned_doctor_id:
                raise NotFoundException(
                    message="No assigned doctor",
                    errors={"assigned_doctor": ["No doctor has been assigned to this staff member"]}
                )
            doctor_id = user.assigned_doctor_id
        
        # Base query - get payments for appointments/requests with this doctor
        # Join with appointment_request to get patient_id and filter by doctor_id
        query = db.query(AppointmentPayment).join(
            AppointmentRequest,
            AppointmentPayment.appointment_request_id == AppointmentRequest.id
        ).filter(
            AppointmentRequest.doctor_id == doctor_id,
            AppointmentPayment.status == 'COMPLETED',  # Only completed payments (invoices)
            AppointmentRequest.deleted_at.is_(None)
        )
        
        # Apply search filter if provided
        if search:
            search_pattern = f"%{search}%"
            # Join with User to search by patient name (if not already joined)
            # Check if User is already in the query
            query = query.join(
                User,
                AppointmentRequest.patient_id == User.id
            ).filter(
                func.lower(User.name).ilike(search_pattern),
                User.deleted_at.is_(None)
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination with eager loading
        offset = (page - 1) * per_page
        payments = query.options(
            joinedload(AppointmentPayment.appointment_request).joinedload(AppointmentRequest.patient),
            joinedload(AppointmentPayment.appointment_request).joinedload(AppointmentRequest.service),
            joinedload(AppointmentPayment.appointment_request).joinedload(AppointmentRequest.doctor)
        ).order_by(
            AppointmentPayment.created_at.desc()  # Latest first
        ).offset(offset).limit(per_page).all()
        
        # Build invoice data list
        invoices_data = []
        for payment in payments:
            req = payment.appointment_request
            patient = req.patient if req else None
            service = req.service if req else None
            doctor = req.doctor if req else None
            
            # Get appointment if it exists (created after payment)
            appointment = db.query(Appointment).filter(
                Appointment.doctor_id == doctor_id,
                Appointment.patient_id == req.patient_id if req else None,
                Appointment.appointment_date == req.preferred_date if req else None,
                Appointment.start_time == req.preferred_time if req else None,
                Appointment.deleted_at.is_(None)
            ).first()
            
            invoice_data = {
                "id": str(payment.id),
                "payment_id": str(payment.id),
                "invoice_number": f"INV-{str(payment.id)[:8].upper()}",
                "patient": {
                    "id": str(patient.id) if patient else None,
                    "name": patient.name if patient else None,
                    "email": patient.email if patient else None,
                    "phone": patient.phone if patient else None,
                } if patient else None,
                "doctor": {
                    "id": str(doctor.id) if doctor else None,
                    "name": doctor.name if doctor else None,
                } if doctor else None,
                "service": {
                    "id": str(service.id) if service else None,
                    "name": service.name if service else None,
                } if service else None,
                "appointment": {
                    "id": str(appointment.id) if appointment else None,
                    "appointment_date": appointment.appointment_date.isoformat() if appointment and appointment.appointment_date else None,
                    "start_time": str(appointment.start_time) if appointment and appointment.start_time else None,
                    "consultation_mode": appointment.consultation_mode if appointment else None,
                } if appointment else None,
                "appointment_request": {
                    "id": str(req.id) if req else None,
                    "preferred_date": req.preferred_date.isoformat() if req and req.preferred_date else None,
                    "preferred_time": str(req.preferred_time) if req and req.preferred_time else None,
                    "consultation_mode": req.consultation_mode if req else None,
                } if req else None,
                "amount": float(payment.amount) if payment.amount else None,
                "amount_before_waiver": float(payment.amount_before_waiver) if payment.amount_before_waiver is not None else None,
                "waiver_percent": payment.waiver_percent,
                "currency": payment.currency,
                "status": payment.status,
                "payment_mode": "Online",  # Sentoo payments are online
                "payment_date": payment.created_at.isoformat() if payment.created_at else None,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "updated_at": payment.updated_at.isoformat() if payment.updated_at else None,
            }
            
            invoices_data.append(invoice_data)
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        # Prepare response data
        response_data = {
            "invoices": invoices_data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
        # Create audit log
        audit_service = AuditService(db)
        audit_service.create_audit_log_from_request(
            request=request,
            actor_user_id=current_user.id,
            action="VIEW_INVOICES",
            entity_type="invoice_list",
            entity_id=None,
            audit_metadata={
                "actor_role": role_value,
                "actor_id": str(current_user.id),
                "doctor_id": str(doctor_id),
                "page": page,
                "per_page": per_page,
                "search": search,
                "total_results": total
            }
        )
        
        logger.info(f"User {current_user.id} ({role_value}) viewed invoices (doctor_id: {doctor_id}, page: {page}, search: {search})")
        
        return laravel_response(
            success=True,
            message="Invoices retrieved successfully",
            data=response_data
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve invoices: {str(e)}", exc_info=True)
        raise NotFoundException(
            message="Error retrieving invoices",
            errors={"general": [str(e)]}
        )


@router.get(
    "/invoices/{invoice_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download invoice receipt",
    description="""
    Download invoice receipt as PDF for the specified invoice.
    
    **Admin, Staff and Doctor**
    - **Admin** (super_admin, clinic_admin): Can download any invoice
    - **Staff**: Can only download invoices for the assigned doctor
    - **Doctor**: Can only download own invoices
    - Returns PDF file with invoice details
    """,
    dependencies=[Depends(require_feature("payments"))],
)
async def download_invoice_receipt(
    request: Request,
    invoice_id: UUID = Path(..., description="Invoice (Payment) ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Download invoice receipt as PDF (admin: any invoice; staff: assigned doctor's; doctor: own).
    """
    try:
        role_value = getattr(current_user.role, "value", current_user.role)
        if role_value not in ("super_admin", "clinic_admin", "staff", "doctor"):
            raise ForbiddenException(
                message="This endpoint is for admin, staff and doctor users only",
                errors={"role": ["Only admin, staff or doctor users can access this endpoint"]}
            )
        
        # Resolve doctor_id for access check: admin can access any; staff = assigned doctor; doctor = self
        doctor_id = None
        if role_value == "doctor":
            doctor_id = current_user.id
        elif role_value == "staff":
            user = db.query(User).filter(
                User.id == current_user.id,
                User.deleted_at.is_(None)
            ).first()
            if not user:
                raise NotFoundException(
                    message="User not found",
                    errors={"user": ["User account not found"]}
                )
            if not user.assigned_doctor_id:
                raise NotFoundException(
                    message="No assigned doctor",
                    errors={"assigned_doctor": ["No doctor has been assigned to this staff member"]}
                )
            doctor_id = user.assigned_doctor_id
        # else: super_admin or clinic_admin - doctor_id stays None (can access any invoice)
        
        # Get payment/invoice
        payment = db.query(AppointmentPayment).options(
            joinedload(AppointmentPayment.appointment_request).joinedload(AppointmentRequest.patient),
            joinedload(AppointmentPayment.appointment_request).joinedload(AppointmentRequest.service),
            joinedload(AppointmentPayment.appointment_request).joinedload(AppointmentRequest.doctor)
        ).filter(
            AppointmentPayment.id == invoice_id
        ).first()
        
        if not payment:
            raise NotFoundException(
                message="Invoice not found",
                errors={"invoice_id": ["Invoice with this ID does not exist"]}
            )
        
        req = payment.appointment_request
        # For staff/doctor: verify invoice belongs to their doctor
        if doctor_id is not None and (not req or str(req.doctor_id) != str(doctor_id)):
            raise ForbiddenException(
                message="Access denied",
                errors={"invoice_id": ["You can only download invoices for this doctor"]}
            )
        
        # Generate PDF receipt
        from app.utils.invoice_generator import generate_invoice_pdf
        
        pdf_content = generate_invoice_pdf(
            db=db,
            payment=payment,
            appointment_request=req
        )
        
        # Create audit log (invoice_doctor_id = doctor on the invoice, for context)
        invoice_doctor_id = str(req.doctor_id) if req else None
        audit_service = AuditService(db)
        audit_service.create_audit_log_from_request(
            request=request,
            actor_user_id=current_user.id,
            action="DOWNLOAD_INVOICE",
            entity_type="invoice",
            entity_id=invoice_id,
            audit_metadata={
                "actor_role": role_value,
                "actor_id": str(current_user.id),
                "invoice_doctor_id": invoice_doctor_id,
                "invoice_id": str(invoice_id),
                "payment_id": str(payment.id)
            }
        )
        
        logger.info(f"User {current_user.id} ({role_value}) downloaded invoice {invoice_id} (invoice_doctor_id: {invoice_doctor_id})")
        
        # Return PDF file
        from fastapi.responses import Response
        
        invoice_number = f"INV-{str(payment.id)[:8].upper()}"
        filename = f"invoice_{invoice_number}.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to download invoice: {str(e)}", exc_info=True)
        raise NotFoundException(
            message="Error downloading invoice",
            errors={"general": [str(e)]}
        )
