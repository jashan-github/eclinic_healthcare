"""
Service Catalog Service
Business logic for admin-managed service catalog
"""

from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session
from loguru import logger

from app.models.service import Service
from app.models.user import User, Clinic
from app.services.audit_service import AuditService
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException
)
from app.core.security import UserRole


class ServiceCatalogService:
    """
    Service for managing service catalog
    Admin-only operations
    """
    
    def __init__(self, db: Session):
        """
        Initialize service catalog service
        
        Args:
            db: Database session
        """
        self.db = db
        self.audit_service = AuditService(db)
    
    def _check_clinic_access(self, user: User, clinic_id: UUID) -> None:
        """
        Check if user has access to the specified clinic
        
        Args:
            user: Current user
            clinic_id: Clinic ID to check
            
        Raises:
            ForbiddenException: If user doesn't have access
        """
        # Super admin can access all clinics
        if user.role == UserRole.SUPER_ADMIN.value:
            return
        
        # Clinic admin can only access their own clinic
        if user.clinic_id != clinic_id:
            raise ForbiddenException(
                message="Access denied to this clinic",
                errors={"clinic_id": ["You don't have permission to manage services in this clinic"]}
            )
    
    def _validate_clinic_exists(self, clinic_id: UUID) -> Clinic:
        """
        Validate that clinic exists
        
        Args:
            clinic_id: Clinic ID to validate
            
        Returns:
            Clinic object
            
        Raises:
            ValidationException: If clinic doesn't exist
        """
        clinic = self.db.query(Clinic).filter(
            Clinic.id == clinic_id,
            Clinic.deleted_at.is_(None)
        ).first()
        
        if not clinic:
            raise ValidationException(
                message="Clinic not found",
                errors={"clinic_id": ["The specified clinic does not exist"]}
            )
        
        return clinic
    
    def create_service(
        self,
        user: User,
        clinic_id: UUID,
        name: str,
        service_mode: str,
        appointment_type: str,
        payment_type: str,
        nickname: Optional[str] = None,
        is_bookable: bool = True,
        advance_booking_days: int = 30,
        minimum_notice_minutes: int = 60,
        price: Optional[Decimal] = None,
        currency: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Service:
        """
        Create a new service
        
        Args:
            user: Current admin user
            clinic_id: Clinic ID
            name: Service name
            service_mode: Service mode (IN_CLINIC, TELECONSULTATION)
            appointment_type: Appointment type (REGULAR, FOLLOW_UP)
            payment_type: Payment type (PREPAID, POSTPAID)
            nickname: Service nickname (optional)
            is_bookable: Whether service is bookable
            advance_booking_days: Days in advance for booking
            minimum_notice_minutes: Minimum notice in minutes
            price: Service price (optional)
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created Service object
            
        Raises:
            ForbiddenException: If user doesn't have access
            ValidationException: If clinic doesn't exist
        """
        # Validate clinic exists
        self._validate_clinic_exists(clinic_id)
        
        # Check clinic access
        self._check_clinic_access(user, clinic_id)
        
        # Validate currency is provided when price is set
        if price is not None and currency is None:
            raise ValidationException(
                message="Currency is required when price is provided",
                errors={"currency": ["Currency must be specified when setting a service price"]}
            )
        
        # Create service
        service = Service(
            clinic_id=clinic_id,
            name=name,
            nickname=nickname,
            service_mode=service_mode,
            appointment_type=appointment_type,
            is_bookable=is_bookable,
            advance_booking_days=advance_booking_days,
            minimum_notice_minutes=minimum_notice_minutes,
            payment_type=payment_type,
            price=price,
            currency=currency,
            created_by=user.id
        )
        
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        
        # Audit log (NO PHI - no service name)
        self.audit_service.create_audit_log(
            actor_user_id=user.id,
            action="SERVICE_CREATED",
            entity_type="service",
            entity_id=service.id,
            audit_metadata={
                "service_id": str(service.id),
                "clinic_id": str(clinic_id),
                "is_bookable": is_bookable
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Service created: {service.id} by admin: {user.id}")
        
        return service
    
    def get_services(
        self,
        user: User,
        clinic_id: Optional[UUID] = None,
        service_mode: Optional[str] = None,
        appointment_type: Optional[str] = None,
        is_bookable: Optional[bool] = None,
        payment_type: Optional[str] = None
    ) -> List[Service]:
        """
        Get list of services with filters
        
        Args:
            user: Current admin user
            clinic_id: Filter by clinic ID
            service_mode: Filter by service mode
            appointment_type: Filter by appointment type
            is_bookable: Filter by bookable status
            payment_type: Filter by payment type
            
        Returns:
            List of Service objects
        """
        query = self.db.query(Service).filter(Service.deleted_at.is_(None))
        
        # Clinic access control
        if user.role == UserRole.SUPER_ADMIN.value:
            # Super admin can see all clinics, optionally filter
            if clinic_id:
                query = query.filter(Service.clinic_id == clinic_id)
        else:
            # Clinic admin can only see their own clinic
            query = query.filter(Service.clinic_id == user.clinic_id)
        
        # Apply filters
        if service_mode:
            query = query.filter(Service.service_mode == service_mode)
        
        if appointment_type:
            query = query.filter(Service.appointment_type == appointment_type)
        
        if is_bookable is not None:
            query = query.filter(Service.is_bookable == is_bookable)
        
        if payment_type:
            query = query.filter(Service.payment_type == payment_type)
        
        # Order by created_at descending
        query = query.order_by(Service.created_at.desc())
        
        return query.all()
    
    def get_service_by_id(self, user: User, service_id: UUID) -> Service:
        """
        Get service by ID
        
        Args:
            user: Current admin user
            service_id: Service ID
            
        Returns:
            Service object
            
        Raises:
            NotFoundException: If service not found
            ForbiddenException: If user doesn't have access
        """
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()
        
        if not service:
            raise NotFoundException(
                message="Service not found",
                errors={"service_id": ["The specified service does not exist"]}
            )
        
        # Check clinic access
        self._check_clinic_access(user, service.clinic_id)
        
        return service
    
    def update_service(
        self,
        user: User,
        service_id: UUID,
        name: Optional[str] = None,
        nickname: Optional[str] = None,
        service_mode: Optional[str] = None,
        appointment_type: Optional[str] = None,
        is_bookable: Optional[bool] = None,
        advance_booking_days: Optional[int] = None,
        minimum_notice_minutes: Optional[int] = None,
        payment_type: Optional[str] = None,
        price: Optional[Decimal] = None,
        currency: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Service:
        """
        Update a service
        
        Args:
            user: Current admin user
            service_id: Service ID
            name: New service name
            nickname: New service nickname
            service_mode: New service mode
            appointment_type: New appointment type
            is_bookable: New bookable status
            advance_booking_days: New advance booking days
            minimum_notice_minutes: New minimum notice minutes
            payment_type: New payment type
            price: New price
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated Service object
            
        Raises:
            NotFoundException: If service not found
            ForbiddenException: If user doesn't have access
        """
        service = self.get_service_by_id(user, service_id)
        
        # Track if is_bookable changed for audit
        old_is_bookable = service.is_bookable
        is_bookable_changed = is_bookable is not None and is_bookable != old_is_bookable
        
        # Update fields
        if name is not None:
            service.name = name
        
        if nickname is not None:
            service.nickname = nickname if nickname else None
        
        if service_mode is not None:
            service.service_mode = service_mode
        
        if appointment_type is not None:
            service.appointment_type = appointment_type
        
        if is_bookable is not None:
            service.is_bookable = is_bookable
        
        if advance_booking_days is not None:
            service.advance_booking_days = advance_booking_days
        
        if minimum_notice_minutes is not None:
            service.minimum_notice_minutes = minimum_notice_minutes
        
        if payment_type is not None:
            service.payment_type = payment_type
        
        if price is not None:
            service.price = price
        
        if currency is not None:
            service.currency = currency
        
        # Validate: if service has price, it must have currency
        if service.price is not None and service.currency is None:
            raise ValidationException(
                message="Currency is required when price is set",
                errors={"currency": ["Currency must be specified when service has a price"]}
            )
        
        self.db.commit()
        self.db.refresh(service)
        
        # Determine audit action
        action = "SERVICE_UPDATED"
        if is_bookable_changed and not service.is_bookable:
            action = "SERVICE_DISABLED"
        
        # Audit log (NO PHI - no service name)
        self.audit_service.create_audit_log(
            actor_user_id=user.id,
            action=action,
            entity_type="service",
            entity_id=service.id,
            audit_metadata={
                "service_id": str(service.id),
                "clinic_id": str(service.clinic_id),
                "is_bookable": service.is_bookable
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Service updated: {service.id} by admin: {user.id}")
        
        return service
    
    def delete_service(
        self,
        user: User,
        service_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Delete a service (soft delete)
        
        Args:
            user: Current admin user
            service_id: Service ID
            ip_address: Request IP address
            user_agent: Request user agent
            
        Raises:
            NotFoundException: If service not found
            ForbiddenException: If user doesn't have access
        """
        service = self.get_service_by_id(user, service_id)
        
        # Soft delete
        service.soft_delete()
        
        self.db.commit()
        
        # Audit log
        self.audit_service.create_audit_log(
            actor_user_id=user.id,
            action="SERVICE_DELETED",
            entity_type="service",
            entity_id=service.id,
            audit_metadata={
                "service_id": str(service.id),
                "clinic_id": str(service.clinic_id),
                "name": service.name
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Service deleted: {service.id} by admin: {user.id}")