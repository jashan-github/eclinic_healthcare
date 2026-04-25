"""
Doctor Service Selection Service
Business logic for doctor service assignments
"""

from typing import Optional, List, Union
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger

from app.models.doctor_service import DoctorService
from app.models.service import Service
from app.models.user import User
from app.services.audit_service import AuditService
from app.core.security import CurrentUser, UserRole
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    ConflictException,
    BadRequestException
)

# Validation constants
SLOT_DURATION_MIN = 5
SLOT_DURATION_MAX = 360  # 6 hours
DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


class DoctorServiceSelectionService:
    """
    Service for managing doctor service selections
    Doctors can only select from admin-created services
    """
    
    def __init__(self, db: Session):
        """
        Initialize doctor service selection service
        
        Args:
            db: Database session
        """
        self.db = db
        self.audit_service = AuditService(db)
    
    def _get_doctor_user(self, current_user: CurrentUser) -> User:
        """
        Get doctor user from database and validate role
        
        Args:
            current_user: Current user from token
            
        Returns:
            User object
            
        Raises:
            ForbiddenException: If user is not a doctor
        """
        # Check if user is a doctor
        if not current_user.has_role(UserRole.DOCTOR):
            raise ForbiddenException(
                message="Only doctors can manage service assignments",
                errors={"role": ["You must be a doctor to perform this action"]}
            )
        
        user = self.db.query(User).filter(
            User.id == current_user.id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise ForbiddenException(
                message="User not found",
                errors={"user": ["User account not found"]}
            )
        
        if not user.is_active:
            raise ForbiddenException(
                message="Account is inactive",
                errors={"user": ["Your account is inactive"]}
            )
        
        return user
    
    def get_available_services(self, current_user: CurrentUser) -> List[Service]:
        """
        Get available services for doctor to select from
        
        Args:
            current_user: Current doctor user
            
        Returns:
            List of available Service objects
        """
        doctor = self._get_doctor_user(current_user)
        
        # Get services in doctor's clinic that are active and bookable
        services = self.db.query(Service).filter(
            Service.clinic_id == doctor.clinic_id,
            Service.is_bookable == True,
            Service.deleted_at.is_(None)
        ).order_by(Service.name).all()
        
        return services
    
    def get_doctor_services(self, current_user: CurrentUser) -> List[DoctorService]:
        """
        Get doctor's current service assignments
        
        Args:
            current_user: Current doctor user
            
        Returns:
            List of DoctorService objects
        """
        doctor = self._get_doctor_user(current_user)
        
        # Get doctor's service assignments
        assignments = self.db.query(DoctorService).filter(
            DoctorService.doctor_id == doctor.id,
            DoctorService.clinic_id == doctor.clinic_id
        ).order_by(DoctorService.created_at.desc()).all()
        
        return assignments
    
    def add_service(
        self,
        current_user: CurrentUser,
        service_id: UUID,
        day_of_week: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DoctorService:
        """
        Add a service to doctor's offerings. Fetches the admin-configured service and
        creates the assignment from it (service mode, appointment type, etc. from the
        linked service; slot duration default 30 when not on the service).
        
        Args:
            current_user: Current doctor user
            service_id: Service ID to add (admin-created service)
            day_of_week: Day of week (0=Sunday, 6=Saturday), None for default
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created DoctorService object
            
        Raises:
            ValidationException: If service is invalid
            ConflictException: If already assigned
            
        Rules:
        - Multiple records allowed for same service if day_of_week differs
        - Only ONE record allowed where day_of_week IS NULL per service
        """
        doctor = self._get_doctor_user(current_user)
        
        # Validate service exists and is in same clinic
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()
        
        if not service:
            raise ValidationException(
                message="Service not found",
                errors={"service_id": ["The specified service does not exist"]}
            )
        
        # Validate clinic match
        if service.clinic_id != doctor.clinic_id:
            raise ForbiddenException(
                message="Service not available",
                errors={"service_id": ["This service is not available in your clinic"]}
            )
        
        # Validate service is bookable
        if not service.is_bookable:
            raise ValidationException(
                message="Service not bookable",
                errors={"service_id": ["This service is not available for booking"]}
            )
        
        # Validate day_of_week (0=Sunday to 6=Saturday)
        if day_of_week is not None and (day_of_week < 0 or day_of_week > 6):
            raise BadRequestException(
                message="Invalid day of week",
                errors={"day_of_week": ["Day of week must be between 0 (Sunday) and 6 (Saturday)"]}
            )
        
        # Slot duration: default (admin service has no duration column; no new migration)
        slot_duration_minutes = 30
        
        # Check for duplicate assignment based on (doctor_id, service_id, day_of_week)
        # Rule: If already exists, return existing record instead of creating duplicate
        if day_of_week is None:
            # Check if default (NULL) already exists for this service
            existing = self.db.query(DoctorService).filter(
                DoctorService.doctor_id == doctor.id,
                DoctorService.service_id == service_id,
                DoctorService.day_of_week.is_(None)
            ).first()
            
            if existing:
                # Return existing record instead of raising error
                logger.info(f"Doctor {doctor.id} attempted to add service {service_id} (default), but it already exists. Returning existing assignment.")
                return existing
        else:
            # Check if specific day already exists
            existing = self.db.query(DoctorService).filter(
                DoctorService.doctor_id == doctor.id,
                DoctorService.service_id == service_id,
                DoctorService.day_of_week == day_of_week
            ).first()
            
            if existing:
                # Return existing record instead of raising error
                day_name = DAY_NAMES[day_of_week]
                logger.info(f"Doctor {doctor.id} attempted to add service {service_id} for {day_name}, but it already exists. Returning existing assignment.")
                return existing
        
        # Create assignment only if it doesn't exist
        doctor_service = DoctorService(
            doctor_id=doctor.id,
            service_id=service_id,
            clinic_id=doctor.clinic_id,
            day_of_week=day_of_week,
            slot_duration_minutes=slot_duration_minutes,
            is_active=True
        )
        
        self.db.add(doctor_service)
        self.db.commit()
        self.db.refresh(doctor_service)
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=doctor.id,
            action="DOCTOR_SERVICE_ASSIGNED",
            entity_type="doctor_service",
            entity_id=doctor_service.id,
            audit_metadata={
                "service_id": str(service_id),
                "slot_duration_minutes": slot_duration_minutes,
                "day_of_week": day_of_week
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} assigned service {service_id} (day={day_of_week})")
        
        return doctor_service
    
    def update_service(
        self,
        current_user: CurrentUser,
        assignment_id: UUID,
        slot_duration_minutes: Optional[int] = None,
        is_active: Optional[bool] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DoctorService:
        """
        Update a doctor's service assignment
        
        Args:
            current_user: Current doctor user
            assignment_id: DoctorService ID
            slot_duration_minutes: New slot duration
            is_active: New active status
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated DoctorService object
            
        Raises:
            NotFoundException: If assignment not found
            ForbiddenException: If not owner
        """
        doctor = self._get_doctor_user(current_user)
        
        # Get assignment
        assignment = self.db.query(DoctorService).filter(
            DoctorService.id == assignment_id
        ).first()
        
        if not assignment:
            raise NotFoundException(
                message="Service assignment not found",
                errors={"id": ["The specified assignment does not exist"]}
            )
        
        # Validate ownership
        if assignment.doctor_id != doctor.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"id": ["You can only modify your own service assignments"]}
            )
        
        # Track changes for audit
        old_duration = assignment.slot_duration_minutes
        
        # Update fields
        if slot_duration_minutes is not None:
            if slot_duration_minutes < SLOT_DURATION_MIN or slot_duration_minutes > SLOT_DURATION_MAX:
                raise BadRequestException(
                    message="Invalid slot duration",
                    errors={"slot_duration_minutes": [f"Slot duration must be between {SLOT_DURATION_MIN} and {SLOT_DURATION_MAX} minutes"]}
                )
            assignment.slot_duration_minutes = slot_duration_minutes
        
        if is_active is not None:
            assignment.is_active = is_active
        
        self.db.commit()
        self.db.refresh(assignment)
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=doctor.id,
            action="DOCTOR_SERVICE_UPDATED",
            entity_type="doctor_service",
            entity_id=assignment.id,
            audit_metadata={
                "service_id": str(assignment.service_id),
                "slot_duration_minutes": assignment.slot_duration_minutes,
                "day_of_week": assignment.day_of_week
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} updated service assignment {assignment_id} (day={assignment.day_of_week})")
        
        return assignment
    
    def remove_service(
        self,
        current_user: CurrentUser,
        assignment_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Remove a service from doctor's offerings
        
        Args:
            current_user: Current doctor user
            assignment_id: DoctorService ID
            ip_address: Request IP address
            user_agent: Request user agent
            
        Raises:
            NotFoundException: If assignment not found
            ForbiddenException: If not owner
        """
        doctor = self._get_doctor_user(current_user)
        
        # Get assignment
        assignment = self.db.query(DoctorService).filter(
            DoctorService.id == assignment_id
        ).first()
        
        if not assignment:
            raise NotFoundException(
                message="Service assignment not found",
                errors={"id": ["The specified assignment does not exist"]}
            )
        
        # Validate ownership
        if assignment.doctor_id != doctor.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"id": ["You can only remove your own service assignments"]}
            )
        
        # Store for audit before deletion
        service_id = assignment.service_id
        slot_duration = assignment.slot_duration_minutes
        day_of_week = assignment.day_of_week
        
        # Delete assignment
        self.db.delete(assignment)
        self.db.commit()
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=doctor.id,
            action="DOCTOR_SERVICE_REMOVED",
            entity_type="doctor_service",
            entity_id=assignment_id,
            audit_metadata={
                "service_id": str(service_id),
                "slot_duration_minutes": slot_duration,
                "day_of_week": day_of_week
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} removed service assignment {assignment_id} (day={day_of_week})")
