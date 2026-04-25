"""
Doctor Service Availability Service
Business logic for assigning services to availability blocks
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger

from app.models.doctor_service_availability import DoctorServiceAvailability
from app.models.availability import DoctorAvailability
from app.models.service import Service
from app.models.user import User
from app.services.audit_service import AuditService
from app.core.security import CurrentUser, UserRole, ConsultationMode
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException
)

# Validation constants
SLOT_DURATION_MIN = 5
SLOT_DURATION_MAX = 360


class DoctorServiceAvailabilityService:
    """
    Service for managing service assignments to availability blocks
    Doctors can assign services to their availability windows with custom durations
    """
    
    def __init__(self, db: Session):
        """
        Initialize service
        
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
        if not current_user.has_role(UserRole.DOCTOR):
            raise ForbiddenException(
                message="Only doctors can manage service availability assignments",
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
    
    def get_availability_services(
        self,
        current_user: CurrentUser,
        availability_id: Optional[UUID] = None
    ) -> List[DoctorServiceAvailability]:
        """
        Get doctor's service availability assignments
        
        Args:
            current_user: Current doctor user
            availability_id: Optional filter by availability ID
            
        Returns:
            List of DoctorServiceAvailability objects
        """
        doctor = self._get_doctor_user(current_user)
        
        # Build query - join with availability to filter by doctor
        query = self.db.query(DoctorServiceAvailability).join(
            DoctorAvailability,
            DoctorServiceAvailability.availability_id == DoctorAvailability.id
        ).filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.deleted_at.is_(None)
        )
        
        if availability_id:
            query = query.filter(DoctorServiceAvailability.availability_id == availability_id)
        
        return query.order_by(DoctorServiceAvailability.created_at.desc()).all()
    
    def assign_service(
        self,
        current_user: CurrentUser,
        availability_id: UUID,
        service_id: UUID,
        slot_duration_minutes: int,
        consultation_mode: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DoctorServiceAvailability:
        """
        Assign a service to an availability block. If consultation_mode is omitted,
        uses the admin-configured service_mode for this service (no static in-clinic default).
        
        Args:
            current_user: Current doctor user
            availability_id: Availability block ID
            service_id: Service ID to assign
            slot_duration_minutes: Slot duration in minutes
            consultation_mode: Consultation mode (IN_CLINIC or TELECONSULTATION). If None, uses admin service.service_mode.
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created DoctorServiceAvailability object
            
        Raises:
            NotFoundException: If availability or service not found
            ForbiddenException: If not owner of availability
            BadRequestException: If validation fails or duplicate assignment
        """
        doctor = self._get_doctor_user(current_user)
        
        # Validate availability exists and belongs to doctor
        availability = self.db.query(DoctorAvailability).filter(
            DoctorAvailability.id == availability_id,
            DoctorAvailability.deleted_at.is_(None)
        ).first()
        
        if not availability:
            raise NotFoundException(
                message="Availability not found",
                errors={"availability_id": ["The specified availability block does not exist"]}
            )
        
        if availability.doctor_id != doctor.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"availability_id": ["You can only assign services to your own availability blocks"]}
            )
        
        # Validate service exists and is in same clinic
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()
        
        if not service:
            raise NotFoundException(
                message="Service not found",
                errors={"service_id": ["The specified service does not exist"]}
            )
        
        if service.clinic_id != doctor.clinic_id:
            raise ForbiddenException(
                message="Service not available",
                errors={"service_id": ["This service is not available in your clinic"]}
            )
        
        if not service.is_bookable:
            raise BadRequestException(
                message="Service not bookable",
                errors={"service_id": ["This service is not available for booking"]}
            )
        
        # Use admin-configured service_mode when doctor does not specify consultation_mode
        if consultation_mode is None or consultation_mode == "":
            consultation_mode = service.service_mode
        
        # Validate slot duration
        if slot_duration_minutes < SLOT_DURATION_MIN or slot_duration_minutes > SLOT_DURATION_MAX:
            raise BadRequestException(
                message="Invalid slot duration",
                errors={"slot_duration_minutes": [f"Slot duration must be between {SLOT_DURATION_MIN} and {SLOT_DURATION_MAX} minutes"]}
            )
        
        # Validate consultation mode
        try:
            mode = ConsultationMode(consultation_mode)
            consultation_mode = mode.value
        except ValueError:
            valid_modes = [m.value for m in ConsultationMode]
            raise BadRequestException(
                message="Invalid consultation mode",
                errors={"consultation_mode": [f"consultation_mode must be one of {valid_modes}, got: {consultation_mode}"]}
            )
        
        # Check for duplicate assignment (same service + mode to same availability)
        existing = self.db.query(DoctorServiceAvailability).filter(
            DoctorServiceAvailability.availability_id == availability_id,
            DoctorServiceAvailability.service_id == service_id,
            DoctorServiceAvailability.consultation_mode == consultation_mode
        ).first()
        
        if existing:
            raise BadRequestException(
                message="Service already assigned to this availability with this consultation mode",
                errors={
                    "service_id": ["This service is already assigned to this availability block with this consultation mode"],
                    "consultation_mode": ["A duplicate assignment exists for this service and consultation mode"]
                }
            )
        
        # Create assignment
        assignment = DoctorServiceAvailability(
            availability_id=availability_id,
            service_id=service_id,
            slot_duration_minutes=slot_duration_minutes,
            consultation_mode=consultation_mode
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=doctor.id,
            action="SERVICE_ASSIGNED_WITH_MODE",
            entity_type="doctor_service_availability",
            entity_id=assignment.id,
            audit_metadata={
                "availability_id": str(availability_id),
                "service_id": str(service_id),
                "slot_duration_minutes": slot_duration_minutes,
                "consultation_mode": consultation_mode
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} assigned service {service_id} to availability {availability_id}")
        
        return assignment
    
    def update_assignment(
        self,
        current_user: CurrentUser,
        assignment_id: UUID,
        slot_duration_minutes: Optional[int] = None,
        consultation_mode: Optional[str] = None,
        payment_type: Optional[str] = None,
        advance_booking_days: Optional[int] = None,
        minimum_notice_minutes: Optional[int] = None,
        is_bookable: Optional[bool] = None,
        appointment_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DoctorServiceAvailability:
        """
        Update a service availability assignment and optionally update service properties
        
        Args:
            current_user: Current doctor user
            assignment_id: Assignment ID
            slot_duration_minutes: New slot duration (optional)
            consultation_mode: New consultation mode (optional)
            payment_type: Service payment type - PREPAID or POSTPAID (optional)
            advance_booking_days: Service advance booking days (optional)
            minimum_notice_minutes: Service minimum notice in minutes (optional)
            is_bookable: Whether service is bookable (optional)
            appointment_type: Service appointment type - REGULAR or FOLLOW_UP (optional)
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated DoctorServiceAvailability object
            
        Raises:
            NotFoundException: If assignment not found
            ForbiddenException: If not owner or service not in doctor's clinic
            BadRequestException: If validation fails
        """
        doctor = self._get_doctor_user(current_user)
        
        # Get assignment with availability join to verify ownership
        assignment = self.db.query(DoctorServiceAvailability).join(
            DoctorAvailability,
            DoctorServiceAvailability.availability_id == DoctorAvailability.id
        ).filter(
            DoctorServiceAvailability.id == assignment_id
        ).first()
        
        if not assignment:
            raise NotFoundException(
                message="Assignment not found",
                errors={"id": ["The specified assignment does not exist"]}
            )
        
        # Verify ownership through availability
        if assignment.availability.doctor_id != doctor.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"id": ["You can only modify your own service assignments"]}
            )
        
        # Check if at least one field is provided
        has_assignment_update = slot_duration_minutes is not None or consultation_mode is not None
        has_service_update = (
            payment_type is not None or
            advance_booking_days is not None or
            minimum_notice_minutes is not None or
            is_bookable is not None or
            appointment_type is not None
        )
        
        if not has_assignment_update and not has_service_update:
            raise BadRequestException(
                message="No update data provided",
                errors={"update": ["At least one field must be provided for update"]}
            )
        
        # Validate and update slot duration if provided
        if slot_duration_minutes is not None:
            if slot_duration_minutes < SLOT_DURATION_MIN or slot_duration_minutes > SLOT_DURATION_MAX:
                raise BadRequestException(
                    message="Invalid slot duration",
                    errors={"slot_duration_minutes": [f"Slot duration must be between {SLOT_DURATION_MIN} and {SLOT_DURATION_MAX} minutes"]}
                )
            assignment.slot_duration_minutes = slot_duration_minutes
        
        # Validate and update consultation_mode if provided
        if consultation_mode is not None:
            try:
                mode = ConsultationMode(consultation_mode)
                consultation_mode = mode.value
            except ValueError:
                valid_modes = [mode.value for mode in ConsultationMode]
                raise BadRequestException(
                    message="Invalid consultation mode",
                    errors={"consultation_mode": [f"consultation_mode must be one of {valid_modes}, got: {consultation_mode}"]}
                )
            assignment.consultation_mode = consultation_mode
        
        # Update service properties if provided
        if has_service_update:
            service = assignment.service
            if not service:
                raise NotFoundException(
                    message="Service not found",
                    errors={"service_id": ["Service associated with this assignment does not exist"]}
                )
            
            # Verify service belongs to doctor's clinic
            if doctor.clinic_id and service.clinic_id != doctor.clinic_id:
                raise ForbiddenException(
                    message="Access denied",
                    errors={"service_id": ["You can only update services in your clinic"]}
                )
            
            # Update service properties
            if payment_type is not None:
                if payment_type not in ['PREPAID', 'POSTPAID']:
                    raise BadRequestException(
                        message="Invalid payment type",
                        errors={"payment_type": ["payment_type must be PREPAID or POSTPAID"]}
                    )
                service.payment_type = payment_type
            
            if advance_booking_days is not None:
                if advance_booking_days < 0:
                    raise BadRequestException(
                        message="Invalid advance booking days",
                        errors={"advance_booking_days": ["advance_booking_days must be >= 0"]}
                    )
                service.advance_booking_days = advance_booking_days
            
            if minimum_notice_minutes is not None:
                if minimum_notice_minutes < 0:
                    raise BadRequestException(
                        message="Invalid minimum notice",
                        errors={"minimum_notice_minutes": ["minimum_notice_minutes must be >= 0"]}
                    )
                service.minimum_notice_minutes = minimum_notice_minutes
            
            if is_bookable is not None:
                service.is_bookable = is_bookable
            
            if appointment_type is not None:
                if appointment_type not in ['REGULAR', 'FOLLOW_UP']:
                    raise BadRequestException(
                        message="Invalid appointment type",
                        errors={"appointment_type": ["appointment_type must be REGULAR or FOLLOW_UP"]}
                    )
                service.appointment_type = appointment_type
        
        self.db.commit()
        self.db.refresh(assignment)
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=doctor.id,
            action="SERVICE_AVAILABILITY_UPDATED",
            entity_type="doctor_service_availability",
            entity_id=assignment.id,
            audit_metadata={
                "availability_id": str(assignment.availability_id),
                "service_id": str(assignment.service_id),
                "slot_duration_minutes": slot_duration_minutes
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} updated service availability assignment {assignment_id}")
        
        return assignment
    
    def remove_assignment(
        self,
        current_user: CurrentUser,
        assignment_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Remove a service availability assignment
        
        Args:
            current_user: Current doctor user
            assignment_id: Assignment ID
            ip_address: Request IP address
            user_agent: Request user agent
            
        Raises:
            NotFoundException: If assignment not found
            ForbiddenException: If not owner
        """
        doctor = self._get_doctor_user(current_user)
        
        # Get assignment with availability join to verify ownership
        assignment = self.db.query(DoctorServiceAvailability).join(
            DoctorAvailability,
            DoctorServiceAvailability.availability_id == DoctorAvailability.id
        ).filter(
            DoctorServiceAvailability.id == assignment_id
        ).first()
        
        if not assignment:
            raise NotFoundException(
                message="Assignment not found",
                errors={"id": ["The specified assignment does not exist"]}
            )
        
        # Verify ownership through availability
        if assignment.availability.doctor_id != doctor.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"id": ["You can only remove your own service assignments"]}
            )
        
        # Store for audit before deletion
        availability_id = assignment.availability_id
        service_id = assignment.service_id
        slot_duration = assignment.slot_duration_minutes
        
        # Delete assignment
        self.db.delete(assignment)
        self.db.commit()
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=doctor.id,
            action="SERVICE_REMOVED_FROM_AVAILABILITY",
            entity_type="doctor_service_availability",
            entity_id=assignment_id,
            audit_metadata={
                "availability_id": str(availability_id),
                "service_id": str(service_id),
                "slot_duration_minutes": slot_duration
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} removed service availability assignment {assignment_id}")
