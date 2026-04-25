"""
Admin Service Catalog API Endpoints
Admin-only routes for service management
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.core.security import ConsultationMode
from app.models.user import User
from app.services.service_catalog_service import ServiceCatalogService
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
    ServiceSingleResponse,
    ServiceDeleteResponse
)
from app.schemas.service_commission import (
    ServiceCommissionCreateUpdate,
    ServiceCommissionResponse,
)
from app.services.service_commission_service import ServiceCommissionService
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    laravel_response
)
from loguru import logger


router = APIRouter(prefix="/admin/services", tags=["Admin - Services"])


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


@router.post(
    "",
    response_model=ServiceSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service",
    description="Create a new service in the catalog (Admin only)"
)
async def create_service(
    data: ServiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new service
    
    **Admin only endpoint**
    
    Creates a new service in the service catalog for the specified clinic.
    
    Args:
        data: Service creation data
        
    Returns:
        Created service with success message
    """
    try:
        service_catalog = ServiceCatalogService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        service = service_catalog.create_service(
            user=current_user,
            clinic_id=data.clinic_id,
            name=data.name,
            nickname=data.nickname,
            service_mode=data.service_mode,
            appointment_type=data.appointment_type,
            is_bookable=data.is_bookable,
            advance_booking_days=data.advance_booking_days,
            minimum_notice_minutes=data.minimum_notice_minutes,
            payment_type=data.payment_type,
            price=data.price,
            currency=data.currency,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return ServiceSingleResponse(
            success=True,
            message="Service created successfully",
            data=ServiceResponse.model_validate(service),
            errors=None
        )
    
    except (ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to create service: {str(e)}")
        raise


@router.get(
    "",
    response_model=ServiceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all services",
    description="Retrieve all services with optional filters (Admin only)"
)
async def get_services(
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID"),
    service_mode: Optional[str] = Query(None, description=f"Filter by service mode ({ConsultationMode.IN_CLINIC.value}, {ConsultationMode.TELECONSULTATION.value})"),
    appointment_type: Optional[str] = Query(None, description="Filter by appointment type (REGULAR, FOLLOW_UP)"),
    is_bookable: Optional[bool] = Query(None, description="Filter by bookable status"),
    payment_type: Optional[str] = Query(None, description="Filter by payment type (PREPAID, POSTPAID)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all services
    
    **Admin only endpoint**
    
    Retrieves all services with optional filtering.
    Clinic admins can only see services in their own clinic.
    Super admins can see all services across clinics.
    
    Returns:
        List of services matching the filters
    """
    try:
        service_catalog = ServiceCatalogService(db)
        
        services = service_catalog.get_services(
            user=current_user,
            clinic_id=clinic_id,
            service_mode=service_mode,
            appointment_type=appointment_type,
            is_bookable=is_bookable,
            payment_type=payment_type
        )
        
        data = [
            ServiceResponse.model_validate(service)
            for service in services
        ]
        
        return ServiceListResponse(
            success=True,
            message=f"Retrieved {len(data)} services",
            data=data,
            errors=None
        )
    
    except Exception as e:
        logger.error(f"Failed to get services: {str(e)}")
        raise


@router.get(
    "/{service_id}",
    response_model=ServiceSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get service by ID",
    description="Retrieve a specific service by ID (Admin only)"
)
async def get_service(
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get service by ID
    
    **Admin only endpoint**
    
    Retrieves a specific service by its ID.
    
    Args:
        service_id: UUID of the service
        
    Returns:
        Service details
    """
    try:
        service_catalog = ServiceCatalogService(db)
        
        service = service_catalog.get_service_by_id(
            user=current_user,
            service_id=service_id
        )
        
        return ServiceSingleResponse(
            success=True,
            message="Service retrieved successfully",
            data=ServiceResponse.model_validate(service),
            errors=None
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to get service: {str(e)}")
        raise


@router.get(
    "/{service_id}/commission",
    status_code=status.HTTP_200_OK,
    summary="Get commission for a service",
    description="Get commission configuration for a service (Admin only). Returns 404 if not set.",
)
async def get_service_commission(
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get commission for a service. 404 if no commission configured."""
    try:
        svc = ServiceCommissionService(db)
        commission = svc.get_by_service_id(user=current_user, service_id=service_id)
        if not commission:
            raise NotFoundException(
                message="Commission not found for this service",
                errors={"service_id": ["No commission configured for this service"]},
            )
        return laravel_response(
            success=True,
            message="Commission retrieved",
            data=ServiceCommissionResponse.model_validate(commission),
        )
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to get service commission: {str(e)}")
        raise


@router.put(
    "/{service_id}/commission",
    status_code=status.HTTP_200_OK,
    summary="Create or update commission for a service",
    description="Create or update commission for a service. Rate 1-100 (decimal), status ACTIVE/INACTIVE (Admin only).",
)
async def create_or_update_service_commission(
    service_id: UUID,
    data: ServiceCommissionCreateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create or update commission for a service (upsert)."""
    try:
        svc = ServiceCommissionService(db)
        commission = svc.create_or_update(
            user=current_user,
            service_id=service_id,
            rate=data.rate,
            status=data.status,
        )
        return laravel_response(
            success=True,
            message="Commission saved successfully",
            data=ServiceCommissionResponse.model_validate(commission),
        )
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to save service commission: {str(e)}")
        raise


@router.delete(
    "/{service_id}/commission",
    status_code=status.HTTP_200_OK,
    summary="Delete commission for a service",
    description="Soft-delete commission for a service (Admin only). Returns 404 if no commission configured.",
)
async def delete_service_commission(
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete commission for a service (soft delete)."""
    try:
        svc = ServiceCommissionService(db)
        svc.delete(user=current_user, service_id=service_id)
        return laravel_response(
            success=True,
            message="Commission deleted successfully",
            data=None,
        )
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to delete service commission: {str(e)}")
        raise


@router.patch(
    "/{service_id}",
    response_model=ServiceSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update service",
    description="Update a service in the catalog (Admin only)"
)
async def update_service(
    service_id: UUID,
    data: ServiceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update a service
    
    **Admin only endpoint**
    
    Updates an existing service in the catalog.
    Setting is_bookable to false will trigger SERVICE_DISABLED audit event.
    
    Args:
        service_id: UUID of the service
        data: Service update data
        
    Returns:
        Updated service with success message
    """
    try:
        service_catalog = ServiceCatalogService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        service = service_catalog.update_service(
            user=current_user,
            service_id=service_id,
            name=data.name,
            nickname=data.nickname,
            service_mode=data.service_mode,
            appointment_type=data.appointment_type,
            is_bookable=data.is_bookable,
            advance_booking_days=data.advance_booking_days,
            minimum_notice_minutes=data.minimum_notice_minutes,
            payment_type=data.payment_type,
            price=data.price,
            currency=data.currency,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return ServiceSingleResponse(
            success=True,
            message="Service updated successfully",
            data=ServiceResponse.model_validate(service),
            errors=None
        )
    
    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to update service: {str(e)}")
        raise


@router.delete(
    "/{service_id}",
    response_model=ServiceDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete service",
    description="Delete a service from the catalog (soft delete, Admin only)"
)
async def delete_service(
    service_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a service (soft delete)
    
    **Admin only endpoint**
    
    Soft deletes a service from the catalog. The service will be marked as deleted
    but not removed from the database.
    
    Args:
        service_id: UUID of the service to delete
        
    Returns:
        Success message
    """
    try:
        service_catalog = ServiceCatalogService(db)
        ip_address, user_agent = _extract_request_info(request)
        
        service_catalog.delete_service(
            user=current_user,
            service_id=service_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return ServiceDeleteResponse(
            success=True,
            message="Service deleted successfully",
            data=None,
            errors=None
        )
    
    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Failed to delete service: {str(e)}")
        raise
