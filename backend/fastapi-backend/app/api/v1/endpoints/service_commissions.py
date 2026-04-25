"""
Admin service commissions list API.
List all service commissions (optional clinic_id, status filter).
Commission earned: by service and by doctor (from COMPLETED appointment payments).
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.services.service_commission_service import ServiceCommissionService
from app.core.exceptions import laravel_response
from loguru import logger


router = APIRouter(prefix="/admin/service-commissions", tags=["Admin - Service Commissions"])


def _parse_date(value: Optional[str]):
    """Parse YYYY-MM-DD to date or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Commission stats (dashboard)",
    description="Stats for Commission Management: total commissions this month, count of commission rates, average commission % (Admin only). Optional: month, year, clinic_id.",
)
async def get_commission_stats(
    month: Optional[int] = Query(None, ge=1, le=12, description="Month (1-12); default current month"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Year; default current year"),
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Commission dashboard stats: total commissions (month), total rates count, average commission %."""
    try:
        svc = ServiceCommissionService(db)
        data = svc.get_commission_stats(
            user=current_user,
            clinic_id=clinic_id,
            month=month,
            year=year,
        )
        return laravel_response(
            success=True,
            message="Commission stats",
            data=data,
        )
    except Exception as e:
        logger.error(f"Failed to get commission stats: {str(e)}", exc_info=True)
        raise


@router.get(
    "/by-service",
    status_code=status.HTTP_200_OK,
    summary="Commission earned by service",
    description="Commission earned from COMPLETED appointment payments, grouped by service (Admin only). Optional: date_from, date_to (YYYY-MM-DD), clinic_id.",
)
async def get_commission_earned_by_service(
    date_from: Optional[str] = Query(None, description="From date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="To date (YYYY-MM-DD)"),
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Commission earned by service (from COMPLETED payments, using ACTIVE service commission rate)."""
    try:
        svc = ServiceCommissionService(db)
        data = svc.get_commission_earned_by_service(
            user=current_user,
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
            clinic_id=clinic_id,
        )
        return laravel_response(
            success=True,
            message="Commission earned by service",
            data=data,
        )
    except Exception as e:
        logger.error(f"Failed to get commission earned by service: {str(e)}", exc_info=True)
        raise


@router.get(
    "/by-doctor",
    status_code=status.HTTP_200_OK,
    summary="Commission earned by doctor (breakdown)",
    description="Commission earned from COMPLETED appointment payments, grouped by doctor with optional per-service breakdown (Admin only). Optional: date_from, date_to, clinic_id, service_id, include_service_breakdown.",
)
async def get_commission_earned_by_doctor(
    date_from: Optional[str] = Query(None, description="From date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="To date (YYYY-MM-DD)"),
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID"),
    service_id: Optional[UUID] = Query(None, description="Filter by service ID"),
    include_service_breakdown: bool = Query(True, description="Include per-service breakdown for each doctor"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Commission earned by doctor with optional breakdown by service."""
    try:
        svc = ServiceCommissionService(db)
        data = svc.get_commission_earned_by_doctor(
            user=current_user,
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
            clinic_id=clinic_id,
            service_id=service_id,
            include_service_breakdown=include_service_breakdown,
        )
        return laravel_response(
            success=True,
            message="Commission earned by doctor",
            data=data,
        )
    except Exception as e:
        logger.error(f"Failed to get commission earned by doctor: {str(e)}", exc_info=True)
        raise


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List service commissions",
    description="List all service commissions (Admin only). Optional filters: clinic_id, status (ACTIVE/INACTIVE).",
)
async def list_service_commissions(
    clinic_id: Optional[UUID] = Query(None, description="Filter by clinic ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: ACTIVE or INACTIVE"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """List commissions for services the admin can access."""
    try:
        svc = ServiceCommissionService(db)
        commissions = svc.list_by_clinic(
            user=current_user,
            clinic_id=clinic_id,
            status=status_filter,
        )
        data = []
        for c in commissions:
            item = {
                "id": c.id,
                "service_id": c.service_id,
                "service_name": c.service.name if c.service else None,
                "rate": float(c.rate),
                "status": c.status,
            }
            data.append(item)
        return laravel_response(
            success=True,
            message=f"Retrieved {len(data)} commission(s)",
            data=data,
        )
    except Exception as e:
        logger.error(f"Failed to list service commissions: {str(e)}", exc_info=True)
        raise
