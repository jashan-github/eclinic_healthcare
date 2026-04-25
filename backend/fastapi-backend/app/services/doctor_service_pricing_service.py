"""
Doctor Service Pricing Service
Business logic for doctor service pricing
"""

from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session
from loguru import logger

from app.models.doctor_service_pricing import DoctorServicePricing
from app.models.service import Service
from app.models.user import User
from app.services.audit_service import AuditService
from app.core.security import CurrentUser, UserRole
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException
)


class DoctorServicePricingService:
    """
    Service for managing doctor service pricing
    Doctors can set their own prices for services (overrides global price)
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
                message="Only doctors can manage service pricing",
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
    
    def get_doctor_pricing(
        self,
        current_user: CurrentUser,
        service_id: Optional[UUID] = None
    ) -> List[DoctorServicePricing]:
        """
        Get doctor's service pricing
        
        Args:
            current_user: Current doctor user
            service_id: Optional filter by service ID
            
        Returns:
            List of DoctorServicePricing objects
        """
        doctor = self._get_doctor_user(current_user)
        
        query = self.db.query(DoctorServicePricing).filter(
            DoctorServicePricing.doctor_id == doctor.id
        )
        
        if service_id:
            query = query.filter(DoctorServicePricing.service_id == service_id)
        
        return query.order_by(DoctorServicePricing.created_at.desc()).all()
    
    def set_price(
        self,
        current_user: CurrentUser,
        service_id: UUID,
        price_amount: Decimal,
        currency: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DoctorServicePricing:
        """
        Set price for a service (creates or updates)
        
        Rules:
        - Overrides global service price
        - One price per doctor + service (enforced by UNIQUE constraint)
        - Doctor cannot edit global price (only their own pricing)
        
        Args:
            current_user: Current doctor user
            service_id: Service ID
            price_amount: Price amount
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created or updated DoctorServicePricing object
            
        Raises:
            NotFoundException: If service not found
            ForbiddenException: If service not in doctor's clinic
            BadRequestException: If validation fails
        """
        doctor = self._get_doctor_user(current_user)
        
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
        
        # Validate price amount
        if price_amount <= 0:
            raise BadRequestException(
                message="Invalid price amount",
                errors={"price_amount": ["Price amount must be greater than 0"]}
            )
        
        # Check if pricing already exists (upsert pattern)
        existing_pricing = self.db.query(DoctorServicePricing).filter(
            DoctorServicePricing.doctor_id == doctor.id,
            DoctorServicePricing.service_id == service_id
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
                action="DOCTOR_SERVICE_PRICE_SET",
                entity_type="doctor_service_pricing",
                entity_id=existing_pricing.id,
                audit_metadata={
                    "service_id": str(service_id),
                    "price_amount": float(price_amount)
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Doctor {doctor.id} updated price for service {service_id}")
            return existing_pricing
        else:
            # Create new pricing
            pricing = DoctorServicePricing(
                doctor_id=doctor.id,
                service_id=service_id,
                price_amount=price_amount,
                currency=currency  # Currency is required, passed from request
            )
            
            self.db.add(pricing)
            self.db.commit()
            self.db.refresh(pricing)
            
            # Audit log (NO PHI)
            self.audit_service.create_audit_log(
                actor_user_id=doctor.id,
                action="DOCTOR_SERVICE_PRICE_SET",
                entity_type="doctor_service_pricing",
                entity_id=pricing.id,
                audit_metadata={
                    "service_id": str(service_id),
                    "price_amount": float(price_amount)
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Doctor {doctor.id} set price for service {service_id}")
            return pricing
    
    def update_price(
        self,
        current_user: CurrentUser,
        pricing_id: UUID,
        price_amount: Optional[Decimal] = None,
        currency: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DoctorServicePricing:
        """
        Update existing pricing
        
        Args:
            current_user: Current doctor user
            pricing_id: Pricing ID
            price_amount: New price amount (optional)
            currency: New currency code (optional)
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated DoctorServicePricing object
            
        Raises:
            NotFoundException: If pricing not found
            ForbiddenException: If not owner
            BadRequestException: If validation fails
        """
        doctor = self._get_doctor_user(current_user)
        
        pricing = self.db.query(DoctorServicePricing).filter(
            DoctorServicePricing.id == pricing_id
        ).first()
        
        if not pricing:
            raise NotFoundException(
                message="Pricing not found",
                errors={"id": ["The specified pricing does not exist"]}
            )
        
        if pricing.doctor_id != doctor.id:
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
            action="DOCTOR_SERVICE_PRICE_SET",
            entity_type="doctor_service_pricing",
            entity_id=pricing.id,
            audit_metadata={
                "service_id": str(pricing.service_id),
                "price_amount": float(price_amount)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} updated pricing {pricing_id}")
        return pricing
    
    def remove_price(
        self,
        current_user: CurrentUser,
        pricing_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Remove pricing (reverts to global service price)
        
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
        
        pricing = self.db.query(DoctorServicePricing).filter(
            DoctorServicePricing.id == pricing_id
        ).first()
        
        if not pricing:
            raise NotFoundException(
                message="Pricing not found",
                errors={"id": ["The specified pricing does not exist"]}
            )
        
        if pricing.doctor_id != doctor.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"id": ["You can only remove your own pricing"]}
            )
        
        service_id = pricing.service_id
        price_amount = pricing.price_amount
        
        self.db.delete(pricing)
        self.db.commit()
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=doctor.id,
            action="DOCTOR_SERVICE_PRICE_REMOVED",
            entity_type="doctor_service_pricing",
            entity_id=pricing_id,
            audit_metadata={
                "service_id": str(service_id),
                "price_amount": float(price_amount)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Doctor {doctor.id} removed pricing {pricing_id}")
