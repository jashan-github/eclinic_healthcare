"""
Doctor Service Availability Pricing Service
Business logic for availability-specific pricing (highest priority)
"""

from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session
from loguru import logger

from app.models.doctor_service_availability_pricing import DoctorServiceAvailabilityPricing
from app.models.doctor_service_availability import DoctorServiceAvailability
from app.models.doctor_service_pricing import DoctorServicePricing
from app.models.service import Service
from app.models.user import User
from app.services.audit_service import AuditService
from app.core.security import CurrentUser, UserRole, ConsultationMode
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException
)


class DoctorServiceAvailabilityPricingService:
    """
    Service for managing availability-specific pricing
    This has the highest pricing priority (overrides service-level and global prices)
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
                message="Only doctors can manage availability pricing",
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
    
    def get_availability_pricing(
        self,
        current_user: CurrentUser,
        doctor_service_availability_id: Optional[UUID] = None
    ) -> List[DoctorServiceAvailabilityPricing]:
        """
        Get doctor's availability-specific pricing
        
        Args:
            current_user: Current doctor user
            doctor_service_availability_id: Optional filter by availability assignment ID
            
        Returns:
            List of DoctorServiceAvailabilityPricing objects
        """
        doctor = self._get_doctor_user(current_user)
        
        # Get all availability assignments for this doctor
        from app.models.availability import DoctorAvailability
        
        avail_assignments = self.db.query(DoctorServiceAvailability).join(
            DoctorAvailability,
            DoctorServiceAvailability.availability_id == DoctorAvailability.id
        ).filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.deleted_at.is_(None)
        )
        
        if doctor_service_availability_id:
            avail_assignments = avail_assignments.filter(
                DoctorServiceAvailability.id == doctor_service_availability_id
            )
        
        avail_assignment_ids = [a.id for a in avail_assignments.all()]
        
        if not avail_assignment_ids:
            return []
        
        # Get pricing for these assignments
        query = self.db.query(DoctorServiceAvailabilityPricing).filter(
            DoctorServiceAvailabilityPricing.doctor_service_availability_id.in_(avail_assignment_ids)
        )
        pricing_list = query.order_by(DoctorServiceAvailabilityPricing.created_at.desc()).all()
        
        return pricing_list
    
    def get_assignment_if_owned(
        self,
        current_user: CurrentUser,
        doctor_service_availability_id: UUID
    ) -> Optional[DoctorServiceAvailability]:
        """
        Get a doctor service availability assignment if it exists and belongs to the current doctor.
        Used to return a placeholder when the assignment has no pricing set yet.
        """
        doctor = self._get_doctor_user(current_user)
        from app.models.availability import DoctorAvailability
        
        assignment = self.db.query(DoctorServiceAvailability).join(
            DoctorAvailability,
            DoctorServiceAvailability.availability_id == DoctorAvailability.id
        ).filter(
            DoctorServiceAvailability.id == doctor_service_availability_id,
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.deleted_at.is_(None)
        ).first()
        return assignment
    
    def set_price(
        self,
        current_user: CurrentUser,
        doctor_service_availability_id: UUID,
        price_amount: Decimal,
        currency: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DoctorServiceAvailabilityPricing:
        """
        Set price for an availability-service combination (creates or updates)
        
        Rules:
        - Highest pricing priority (overrides service-level and global prices)
        - Only one override per availability-service (enforced by UNIQUE constraint)
        - Duration logic unchanged
        
        Args:
            current_user: Current doctor user
            doctor_service_availability_id: Availability assignment ID
            price_amount: Price amount
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created or updated DoctorServiceAvailabilityPricing object
            
        Raises:
            NotFoundException: If availability assignment not found
            ForbiddenException: If not owner
            BadRequestException: If validation fails
        """
        doctor = self._get_doctor_user(current_user)
        
        # Validate availability assignment exists and belongs to doctor
        from app.models.availability import DoctorAvailability
        
        availability_assignment = self.db.query(DoctorServiceAvailability).join(
            DoctorAvailability,
            DoctorServiceAvailability.availability_id == DoctorAvailability.id
        ).filter(
            DoctorServiceAvailability.id == doctor_service_availability_id
        ).first()
        
        if not availability_assignment:
            raise NotFoundException(
                message="Availability assignment not found",
                errors={"doctor_service_availability_id": ["The specified availability assignment does not exist"]}
            )
        
        if availability_assignment.availability.doctor_id != doctor.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"doctor_service_availability_id": ["You can only set prices for your own availability assignments"]}
            )
        
        # Validate price amount
        if price_amount <= 0:
            raise BadRequestException(
                message="Invalid price amount",
                errors={"price_amount": ["Price amount must be greater than 0"]}
            )
        
        # Get consultation_mode from availability assignment
        consultation_mode = availability_assignment.consultation_mode
        
        # Check if pricing already exists for this availability + mode (upsert pattern)
        existing_pricing = self.db.query(DoctorServiceAvailabilityPricing).filter(
            DoctorServiceAvailabilityPricing.doctor_service_availability_id == doctor_service_availability_id,
            DoctorServiceAvailabilityPricing.consultation_mode == consultation_mode
        ).first()
        
        if existing_pricing:
            # Update existing pricing
            existing_pricing.price_amount = price_amount
            existing_pricing.currency = currency
            self.db.commit()
            self.db.refresh(existing_pricing)
            
            # Audit log (NO PHI)
            self.audit_service.create_audit_log(
                actor_user_id=doctor.id,
                action="SERVICE_MODE_PRICE_SET",
                entity_type="doctor_service_availability_pricing",
                entity_id=existing_pricing.id,
                audit_metadata={
                    "doctor_service_availability_id": str(doctor_service_availability_id),
                    "service_id": str(availability_assignment.service_id),
                    "consultation_mode": consultation_mode,
                    "price_amount": float(price_amount)
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Doctor {doctor.id} updated availability pricing for assignment {doctor_service_availability_id} (mode: {consultation_mode})")
            return existing_pricing
        else:
            # Create new pricing
            pricing = DoctorServiceAvailabilityPricing(
                doctor_service_availability_id=doctor_service_availability_id,
                price_amount=price_amount,
                currency=currency,  # Currency is required, passed from request
                consultation_mode=consultation_mode
            )
            
            self.db.add(pricing)
            self.db.commit()
            self.db.refresh(pricing)
            
            # Audit log (NO PHI)
            self.audit_service.create_audit_log(
                actor_user_id=doctor.id,
                action="SERVICE_MODE_PRICE_SET",
                entity_type="doctor_service_availability_pricing",
                entity_id=pricing.id,
                audit_metadata={
                    "doctor_service_availability_id": str(doctor_service_availability_id),
                    "service_id": str(availability_assignment.service_id),
                    "consultation_mode": consultation_mode,
                    "price_amount": float(price_amount)
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Doctor {doctor.id} set availability pricing for assignment {doctor_service_availability_id} (mode: {consultation_mode})")
            return pricing
    
    def update_price(
        self,
        current_user: CurrentUser,
        pricing_id: UUID,
        price_amount: Optional[Decimal] = None,
        currency: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DoctorServiceAvailabilityPricing:
        """
        Update existing availability pricing
        
        Args:
            current_user: Current doctor user
            pricing_id: Pricing ID
            price_amount: New price amount (optional)
            currency: New currency code (optional)
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated DoctorServiceAvailabilityPricing object
            
        Raises:
            NotFoundException: If pricing not found
            ForbiddenException: If not owner
            BadRequestException: If validation fails
        """
        doctor = self._get_doctor_user(current_user)
        
        # Get pricing with availability assignment to verify ownership
        from app.models.availability import DoctorAvailability
        
        pricing = self.db.query(DoctorServiceAvailabilityPricing).join(
            DoctorServiceAvailability,
            DoctorServiceAvailabilityPricing.doctor_service_availability_id == DoctorServiceAvailability.id
        ).join(
            DoctorAvailability,
            DoctorServiceAvailability.availability_id == DoctorAvailability.id
        ).filter(
            DoctorServiceAvailabilityPricing.id == pricing_id
        ).first()
        
        if not pricing:
            raise NotFoundException(
                message="Pricing not found",
                errors={"id": ["The specified pricing does not exist"]}
            )
        
        # Verify ownership through availability
        if pricing.doctor_service_availability.availability.doctor_id != doctor.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"id": ["You can only modify your own pricing"]}
            )
        
        # Validate and update price amount
        if price_amount is not None:
            if price_amount <= 0:
                raise BadRequestException(
                    message="Invalid price amount",
                    errors={"price_amount": ["Price amount must be greater than 0"]}
                )
            pricing.price_amount = price_amount
        
        # Update currency if provided
        if currency is not None:
            pricing.currency = currency
        
        self.db.commit()
        self.db.refresh(pricing)
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=doctor.id,
            action="SERVICE_MODE_PRICE_SET",
            entity_type="doctor_service_availability_pricing",
            entity_id=pricing.id,
            audit_metadata={
                "doctor_service_availability_id": str(pricing.doctor_service_availability_id),
                "service_id": str(pricing.doctor_service_availability.service_id),
                "consultation_mode": pricing.consultation_mode,
                "price_amount": float(price_amount)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} updated availability pricing {pricing_id}")
        return pricing
    
    def remove_price(
        self,
        current_user: CurrentUser,
        pricing_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Remove availability pricing (reverts to lower priority pricing)
        
        Args:
            current_user: Current doctor user
            pricing_id: Pricing ID
            ip_address: Request IP address
            user_agent: Request user agent
            
        Raises:
            NotFoundException: If pricing not found
            ForbiddenException: If not owner
        """
        doctor = self._get_doctor_user(current_user)
        
        # Get pricing with availability assignment to verify ownership
        from app.models.availability import DoctorAvailability
        
        pricing = self.db.query(DoctorServiceAvailabilityPricing).join(
            DoctorServiceAvailability,
            DoctorServiceAvailabilityPricing.doctor_service_availability_id == DoctorServiceAvailability.id
        ).join(
            DoctorAvailability,
            DoctorServiceAvailability.availability_id == DoctorAvailability.id
        ).filter(
            DoctorServiceAvailabilityPricing.id == pricing_id
        ).first()
        
        if not pricing:
            raise NotFoundException(
                message="Pricing not found",
                errors={"id": ["The specified pricing does not exist"]}
            )
        
        # Verify ownership through availability
        if pricing.doctor_service_availability.availability.doctor_id != doctor.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"id": ["You can only remove your own pricing"]}
            )
        
        doctor_service_availability_id = pricing.doctor_service_availability_id
        price_amount = pricing.price_amount
        
        self.db.delete(pricing)
        self.db.commit()
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=doctor.id,
            action="SERVICE_AVAILABILITY_PRICE_REMOVED",
            entity_type="doctor_service_availability_pricing",
            entity_id=pricing_id,
            audit_metadata={
                "doctor_service_availability_id": str(doctor_service_availability_id),
                "price_amount": float(price_amount)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} removed availability pricing {pricing_id}")
