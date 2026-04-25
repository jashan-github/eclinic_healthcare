"""
Pricing Resolution Utility
Determines the correct price for appointment booking based on priority hierarchy
"""

from typing import Optional, Tuple
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from loguru import logger

from app.models.doctor_service_availability_pricing import DoctorServiceAvailabilityPricing
from app.models.doctor_service_availability import DoctorServiceAvailability
from app.models.doctor_service_pricing import DoctorServicePricing
from app.models.service import Service
from app.core.exceptions import BadRequestException
from app.core.security import ConsultationMode


class PricingResolver:
    """
    Resolves pricing for appointment booking
    
    Price priority hierarchy:
    1. doctor_service_availability_pricing (availability-specific)
    2. doctor_service_pricing (doctor-service level)
    3. services.price (global default)
    4. Reject if none exists
    
    Currency resolution (always from priority source):
    1. From availability pricing (if available)
    2. From doctor pricing (if available)
    3. From service.currency (fallback)
    """
    
    def __init__(self, db: Session):
        """
        Initialize pricing resolver
        
        Args:
            db: Database session
        """
        self.db = db
    
    def resolve_price(
        self,
        doctor_id: UUID,
        service_id: UUID,
        doctor_service_availability_id: Optional[UUID] = None,
        consultation_mode: Optional[str] = None,
        currency: Optional[str] = None
    ) -> Tuple[Decimal, str, str]:
        """
        Resolve price for appointment booking (mode-aware)
        
        Priority hierarchy:
        1. availability + service + mode (highest priority)
        2. doctor + service + mode (future-safe, currently mode-agnostic)
        3. service base price (fallback)
        
        Currency resolution:
        - Currency always comes from the pricing source (never defaulted)
        - If currency parameter is provided, it's used for validation only
        - If requested currency doesn't match resolved currency, raises error
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            doctor_service_availability_id: Optional availability assignment ID (for highest priority)
            consultation_mode: Consultation mode (IN_CLINIC or TELECONSULTATION)
            currency: Optional expected currency (for validation only, no default)
            
        Returns:
            Tuple of (price_amount, resolved_currency, source)
            - price_amount: Resolved price
            - resolved_currency: Currency from pricing source
            - source: Source of price ('availability', 'service', 'global', or None)
            
        Raises:
            BadRequestException: If no price found or currency mismatch
        """
        # Normalize consultation_mode
        if consultation_mode:
            try:
                mode = ConsultationMode(consultation_mode)
                consultation_mode = mode.value
            except ValueError:
                # Invalid mode, but don't fail - use default
                consultation_mode = ConsultationMode.default()
        else:
            consultation_mode = ConsultationMode.default()
        
        # PRIORITY 1: Check availability + service + mode pricing
        if doctor_service_availability_id:
            # Get availability assignment to verify mode match
            availability_assignment = self.db.query(DoctorServiceAvailability).filter(
                DoctorServiceAvailability.id == doctor_service_availability_id
            ).first()
            
            if availability_assignment:
                # Query pricing with explicit mode match
                availability_pricing = self.db.query(DoctorServiceAvailabilityPricing).filter(
                    DoctorServiceAvailabilityPricing.doctor_service_availability_id == doctor_service_availability_id,
                    DoctorServiceAvailabilityPricing.consultation_mode == consultation_mode
                ).first()
                
                if availability_pricing:
                    resolved_currency = availability_pricing.currency
                    
                    # Validate currency match only if explicitly requested
                    if currency is not None and resolved_currency != currency:
                        raise BadRequestException(
                            message="Currency mismatch",
                            errors={
                                "currency": [
                                    f"Availability pricing uses {resolved_currency}, but {currency} was requested. "
                                    f"Please use {resolved_currency} or contact support."
                                ]
                            }
                        )
                    
                    logger.debug(
                        f"Resolved price from availability+service+mode pricing: {availability_pricing.price_amount} {resolved_currency} "
                        f"for doctor={doctor_id}, service={service_id}, availability={doctor_service_availability_id}, mode={consultation_mode}"
                    )
                    
                    return (
                        availability_pricing.price_amount,
                        resolved_currency,
                        'availability'
                    )
        
        # PRIORITY 2: Check doctor + service + mode pricing (future-safe)
        # Note: Currently doctor_service_pricing is mode-agnostic, but this structure
        # allows future extension to mode-aware doctor-service pricing
        doctor_service_pricing = self.db.query(DoctorServicePricing).filter(
            DoctorServicePricing.doctor_id == doctor_id,
            DoctorServicePricing.service_id == service_id
            # Future: Add consultation_mode filter here when doctor_service_pricing supports mode
        ).first()
        
        if doctor_service_pricing:
            resolved_currency = doctor_service_pricing.currency
            
            # Validate currency match only if explicitly requested
            if currency is not None and resolved_currency != currency:
                raise BadRequestException(
                    message="Currency mismatch",
                    errors={
                        "currency": [
                            f"Doctor service pricing uses {resolved_currency}, but {currency} was requested. "
                            f"Please use {resolved_currency} or contact support."
                        ]
                    }
                )
            
            logger.debug(
                f"Resolved price from doctor+service pricing: {doctor_service_pricing.price_amount} {resolved_currency} "
                f"for doctor={doctor_id}, service={service_id}, mode={consultation_mode} (mode-agnostic for now)"
            )
            
            return (
                doctor_service_pricing.price_amount,
                resolved_currency,
                'service'
            )
        
        # PRIORITY 3: Check global service price
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()
        
        if service and service.price is not None:
            # Use service.currency from database
            resolved_currency = service.currency
            
            # Service must have currency if price is set (enforced by DB constraint)
            if resolved_currency is None:
                raise BadRequestException(
                    message="Currency not configured",
                    errors={
                        "currency": [
                            "Service has a price but no currency configured. Please contact the clinic administrator."
                        ]
                    }
                )
            
            # Validate currency match if currency was explicitly requested
            if currency is not None and resolved_currency != currency:
                raise BadRequestException(
                    message="Currency mismatch",
                    errors={
                        "currency": [
                            f"Service uses {resolved_currency}, but {currency} was requested. "
                            f"Please use {resolved_currency} or contact support."
                        ]
                    }
                )
            
            logger.debug(
                f"Resolved price from global service price: {service.price} {resolved_currency} "
                f"for doctor={doctor_id}, service={service_id}"
            )
            
            return (
                service.price,
                resolved_currency,
                'global'
            )
        
        # PRIORITY 4: No price found - reject booking
        logger.warning(
            f"No price found for doctor={doctor_id}, service={service_id}, availability={doctor_service_availability_id}"
        )
        
        raise BadRequestException(
            message="No pricing available",
            errors={
                "price": [
                    "No pricing found for this service. Please contact the clinic administrator."
                ]
            }
        )
    
    def get_price_info(
        self,
        doctor_id: UUID,
        service_id: UUID,
        doctor_service_availability_id: Optional[UUID] = None
    ) -> dict:
        """
        Get pricing information for all priority levels (for display/comparison)
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            doctor_service_availability_id: Optional availability assignment ID
            
        Returns:
            Dictionary with pricing information from all sources
        """
        info = {
            "availability_price": None,
            "service_price": None,
            "global_price": None,
            "resolved_price": None,
            "resolved_currency": None,
            "resolved_source": None
        }
        
        # Check availability-specific pricing
        if doctor_service_availability_id:
            availability_pricing = self.db.query(DoctorServiceAvailabilityPricing).filter(
                DoctorServiceAvailabilityPricing.doctor_service_availability_id == doctor_service_availability_id
            ).first()
            
            if availability_pricing:
                info["availability_price"] = {
                    "amount": float(availability_pricing.price_amount),
                    "currency": availability_pricing.currency
                }
        
        # Check doctor-service pricing
        doctor_service_pricing = self.db.query(DoctorServicePricing).filter(
            DoctorServicePricing.doctor_id == doctor_id,
            DoctorServicePricing.service_id == service_id
        ).first()
        
        if doctor_service_pricing:
            info["service_price"] = {
                "amount": float(doctor_service_pricing.price_amount),
                "currency": doctor_service_pricing.currency
            }
        
        # Check global service price
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()
        
        if service and service.price is not None:
            info["global_price"] = {
                "amount": float(service.price),
                "currency": service.currency  # Use service.currency from database
            }
        
        # Try to resolve price (without currency validation for info)
        try:
            price, resolved_currency, source = self.resolve_price(
                doctor_id=doctor_id,
                service_id=service_id,
                doctor_service_availability_id=doctor_service_availability_id,
                currency=None  # No currency validation for info lookup
            )
            info["resolved_price"] = float(price)
            info["resolved_currency"] = resolved_currency
            info["resolved_source"] = source
        except BadRequestException:
            # No price found - that's okay for info
            pass
        
        return info


def get_pricing_resolver(db: Session) -> PricingResolver:
    """
    Get pricing resolver instance (for dependency injection)
    
    Args:
        db: Database session
        
    Returns:
        PricingResolver instance
    """
    return PricingResolver(db)
