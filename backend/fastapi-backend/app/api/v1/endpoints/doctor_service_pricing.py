"""
Doctor Service Pricing API Endpoints
Routes for doctors to set their own prices for services
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import CurrentUser
from app.services.doctor_service_pricing_service import DoctorServicePricingService
from app.schemas.doctor_service_pricing import (
    DoctorServicePricingCreate,
    DoctorServicePricingUpdate,
    DoctorServicePricingResponse,
    DoctorServicePricingListResponse,
    DoctorServicePricingSingleResponse
)
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException
)
from loguru import logger


router = APIRouter(prefix="/doctor/service-pricing", tags=["Doctor - Service Pricing"])


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


def _build_response(pricing) -> DoctorServicePricingResponse:
    """
    Build response object with related details
    
    Args:
        pricing: DoctorServicePricing object
        
    Returns:
        DoctorServicePricingResponse
    """
    return DoctorServicePricingResponse(
        id=pricing.id,
        doctor_id=pricing.doctor_id,
        service_id=pricing.service_id,
        price_amount=float(pricing.price_amount) if pricing.price_amount else None,
        currency=pricing.currency,
        created_at=pricing.created_at,
        service_name=pricing.service.name if pricing.service else None,
        service_mode=pricing.service.service_mode if pricing.service else None,
        global_price=float(pricing.service.price) if pricing.service and pricing.service.price else None
    )


@router.get(
    "",
    response_model=DoctorServicePricingListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my service pricing",
    description="Get doctor's service pricing (overrides global prices)"
)
async def get_my_pricing(
    service_id: Optional[UUID] = Query(None, description="Filter by service ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get doctor's service pricing
    
    **Doctor only endpoint**
    
    Returns all pricing set by the doctor for services.
    These prices override the global service prices.
    
    Args:
        service_id: Optional filter by service ID
        
    Returns:
        List of service pricing
    """
    try:
        service = DoctorServicePricingService(db)
        pricing_list = service.get_doctor_pricing(current_user, service_id)
        
        data = [_build_response(p) for p in pricing_list]
        
        return DoctorServicePricingListResponse(
            success=True,
            message=f"Found {len(data)} pricing records",
            data=data,
            errors=None
        )
    
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Failed to get doctor pricing: {str(e)}")
        raise


@router.post(
    "",
    response_model=DoctorServicePricingSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set service price",
    description="Set or update price for a service (overrides global price)"
)
async def set_price(
    data: DoctorServicePricingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Set price for a service
    
    **Doctor only endpoint**
    
    Sets or updates the doctor's price for a service.
    This price overrides the global service price.
    
    Rules:
    - Overrides global service price
    - One price per doctor + service (upsert pattern)
    - Doctor cannot edit global price (only their own pricing)
    
    Args:
        data: Service pricing data
        
    Returns:
        Created or updated service pricing
    """
    try:
        service = DoctorServicePricingService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        pricing = service.set_price(
            current_user=current_user,
            service_id=data.service_id,
            price_amount=data.price_amount,
            currency=data.currency,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return DoctorServicePricingSingleResponse(
            success=True,
            message="Service price set successfully",
            data=_build_response(pricing),
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to set service price: {str(e)}")
        raise


@router.patch(
    "/{pricing_id}",
    response_model=DoctorServicePricingSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update service price",
    description="Update existing service price"
)
async def update_price(
    pricing_id: UUID,
    data: DoctorServicePricingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update service price
    
    **Doctor only endpoint**
    
    Updates an existing pricing record.
    
    Args:
        pricing_id: Pricing ID
        data: Update data
        
    Returns:
        Updated service pricing
    """
    try:
        service = DoctorServicePricingService(db)
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
        
        return DoctorServicePricingSingleResponse(
            success=True,
            message="Service price updated successfully",
            data=_build_response(pricing),
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Failed to update service price: {str(e)}")
        raise


@router.delete(
    "/{pricing_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove service price",
    description="Remove custom price (reverts to global service price)"
)
async def remove_price(
    pricing_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Remove service price
    
    **Doctor only endpoint**
    
    Removes the doctor's custom price for a service.
    After removal, the global service price will be used.
    
    Args:
        pricing_id: Pricing ID
        
    Returns:
        Success message
    """
    try:
        service = DoctorServicePricingService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        service.remove_price(
            current_user=current_user,
            pricing_id=pricing_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "message": "Service price removed successfully",
            "data": None,
            "errors": None
        }
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to remove service price: {str(e)}")
        raise
