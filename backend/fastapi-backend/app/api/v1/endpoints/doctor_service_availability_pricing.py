"""
Doctor Service Availability Pricing API Endpoints
Routes for doctors to set availability-specific prices (highest priority)
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import CurrentUser
from app.services.doctor_service_availability_pricing_service import DoctorServiceAvailabilityPricingService
from app.schemas.doctor_service_availability_pricing import (
    DoctorServiceAvailabilityPricingCreate,
    DoctorServiceAvailabilityPricingUpdate,
    DoctorServiceAvailabilityPricingResponse,
    DoctorServiceAvailabilityPricingListResponse,
    DoctorServiceAvailabilityPricingSingleResponse
)
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException
)
from loguru import logger


router = APIRouter(prefix="/doctor/availability-service-pricing", tags=["Doctor - Availability Pricing"])


def _extract_request_info(request: Request) -> tuple:
    """
    Extract IP address and user agent from request
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Tuple of (ip_address, user_agent)
    """
    ip_address = None
    if request.client:
        ip_address = request.client.host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    
    user_agent = request.headers.get("user-agent")
    
    return ip_address, user_agent


def _build_response(pricing, db: Session) -> DoctorServiceAvailabilityPricingResponse:
    """
    Build response object with related details
    
    Args:
        pricing: DoctorServiceAvailabilityPricing object
        db: Database session
        
    Returns:
        DoctorServiceAvailabilityPricingResponse
    """
    # Get lower priority prices for comparison
    service_price = None
    global_price = None
    
    if pricing.doctor_service_availability and pricing.doctor_service_availability.service:
        service = pricing.doctor_service_availability.service
        global_price = float(service.price) if service.price else None
        
        # Get doctor service pricing if exists
        from app.models.doctor_service_pricing import DoctorServicePricing
        if pricing.doctor_service_availability.availability:
            doctor_id = pricing.doctor_service_availability.availability.doctor_id
            doctor_service_pricing = db.query(DoctorServicePricing).filter(
                DoctorServicePricing.doctor_id == doctor_id,
                DoctorServicePricing.service_id == service.id
            ).first()
            if doctor_service_pricing:
                service_price = float(doctor_service_pricing.price_amount) if doctor_service_pricing.price_amount else None
    
    return DoctorServiceAvailabilityPricingResponse(
        id=pricing.id,
        doctor_service_availability_id=pricing.doctor_service_availability_id,
        price_amount=float(pricing.price_amount) if pricing.price_amount else None,
        currency=pricing.currency,
        created_at=pricing.created_at,
        service_id=pricing.doctor_service_availability.service_id if pricing.doctor_service_availability else None,
        service_name=pricing.doctor_service_availability.service.name if pricing.doctor_service_availability and pricing.doctor_service_availability.service else None,
        availability_day=pricing.doctor_service_availability.availability.day_of_week if pricing.doctor_service_availability and pricing.doctor_service_availability.availability else None,
        availability_start_time=str(pricing.doctor_service_availability.availability.start_time) if pricing.doctor_service_availability and pricing.doctor_service_availability.availability else None,
        availability_end_time=str(pricing.doctor_service_availability.availability.end_time) if pricing.doctor_service_availability and pricing.doctor_service_availability.availability else None,
        service_price=service_price,
        global_price=global_price
    )


def _build_placeholder_response(assignment, db: Session) -> DoctorServiceAvailabilityPricingResponse:
    """
    Build a placeholder response when the assignment exists but no price has been set yet.
    Allows the UI to show the slot and prompt the doctor to set a price.
    """
    service_price = None
    global_price = None
    if assignment.service:
        global_price = float(assignment.service.price) if assignment.service.price else None
        from app.models.doctor_service_pricing import DoctorServicePricing
        if assignment.availability:
            doctor_id = assignment.availability.doctor_id
            doctor_service_pricing = db.query(DoctorServicePricing).filter(
                DoctorServicePricing.doctor_id == doctor_id,
                DoctorServicePricing.service_id == assignment.service_id
            ).first()
            if doctor_service_pricing:
                service_price = float(doctor_service_pricing.price_amount) if doctor_service_pricing.price_amount else None
    return DoctorServiceAvailabilityPricingResponse(
        id=assignment.id,
        doctor_service_availability_id=assignment.id,
        price_amount=None,
        currency=None,
        created_at=None,
        service_id=assignment.service_id,
        service_name=assignment.service.name if assignment.service else None,
        availability_day=assignment.availability.day_of_week if assignment.availability else None,
        availability_start_time=str(assignment.availability.start_time) if assignment.availability else None,
        availability_end_time=str(assignment.availability.end_time) if assignment.availability else None,
        service_price=service_price,
        global_price=global_price
    )


@router.get(
    "",
    response_model=DoctorServiceAvailabilityPricingListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get availability pricing",
    description="Get doctor's availability-specific pricing (highest priority)"
)
async def get_availability_pricing(
    doctor_service_availability_id: Optional[UUID] = Query(None, description="Filter by availability assignment ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get doctor's availability-specific pricing
    
    **Doctor only endpoint**
    
    Returns all availability-specific pricing set by the doctor.
    These prices have the highest priority (override service-level and global prices).
    
    Args:
        doctor_service_availability_id: Optional filter by availability assignment ID
        
    Returns:
        List of availability pricing
    """
    try:
        service = DoctorServiceAvailabilityPricingService(db)
        pricing_list = service.get_availability_pricing(current_user, doctor_service_availability_id)
        
        data = [_build_response(p, db) for p in pricing_list]
        
        # When filtering by ID and no pricing exists, return a placeholder if the assignment belongs to this doctor
        if not data and doctor_service_availability_id:
            assignment = service.get_assignment_if_owned(current_user, doctor_service_availability_id)
            if assignment:
                data = [_build_placeholder_response(assignment, db)]
        
        return DoctorServiceAvailabilityPricingListResponse(
            success=True,
            message=f"Found {len(data)} availability pricing records",
            data=data,
            errors=None
        )
    
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Failed to get availability pricing: {str(e)}")
        raise


@router.post(
    "",
    response_model=DoctorServiceAvailabilityPricingSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set availability price",
    description="Set or update price for an availability-service combination (highest priority)"
)
async def set_price(
    data: DoctorServiceAvailabilityPricingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Set price for an availability-service combination
    
    **Doctor only endpoint**
    
    Sets or updates the doctor's price for a specific availability block and service.
    This price has the highest priority (overrides service-level and global prices).
    
    Rules:
    - Highest pricing priority
    - Only one override per availability-service (upsert pattern)
    - Duration logic unchanged
    
    Args:
        data: Availability pricing data
        
    Returns:
        Created or updated availability pricing
    """
    try:
        service = DoctorServiceAvailabilityPricingService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        pricing = service.set_price(
            current_user=current_user,
            doctor_service_availability_id=data.doctor_service_availability_id,
            price_amount=data.price_amount,
            currency=data.currency,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return DoctorServiceAvailabilityPricingSingleResponse(
            success=True,
            message="Availability price set successfully",
            data=_build_response(pricing, db),
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to set availability price: {str(e)}")
        raise


@router.patch(
    "/{pricing_id}",
    response_model=DoctorServiceAvailabilityPricingSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update availability price",
    description="Update existing availability-specific price"
)
async def update_price(
    pricing_id: UUID,
    data: DoctorServiceAvailabilityPricingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update availability price
    
    **Doctor only endpoint**
    
    Updates an existing availability-specific pricing record.
    
    Args:
        pricing_id: Pricing ID
        data: Update data
        
    Returns:
        Updated availability pricing
    """
    try:
        service = DoctorServiceAvailabilityPricingService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        if data.price_amount is None and data.currency is None:
            raise BadRequestException(
                message="No update data provided",
                errors={"price_amount": ["At least price_amount or currency is required"]}
            )
        
        pricing = service.update_price(
            current_user=current_user,
            pricing_id=pricing_id,
            price_amount=data.price_amount,
            currency=data.currency,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return DoctorServiceAvailabilityPricingSingleResponse(
            success=True,
            message="Availability price updated successfully",
            data=_build_response(pricing, db),
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to update availability price: {str(e)}")
        raise


@router.delete(
    "/{pricing_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove availability price",
    description="Remove availability-specific price (reverts to lower priority pricing)"
)
async def remove_price(
    pricing_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Remove availability price
    
    **Doctor only endpoint**
    
    Removes the doctor's availability-specific price.
    After removal, pricing will fall back to service-level or global price.
    
    Args:
        pricing_id: Pricing ID
        
    Returns:
        Success message
    """
    try:
        service = DoctorServiceAvailabilityPricingService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        service.remove_price(
            current_user=current_user,
            pricing_id=pricing_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "message": "Availability price removed successfully",
            "data": None,
            "errors": None
        }
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to remove availability price: {str(e)}")
        raise
