"""
Admin Dashboard API
Individual endpoints: stats (clinic overview), revenue graph, recent activity, active appointments.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.services.admin_dashboard_service import AdminDashboardService
from app.core.exceptions import laravel_response
from loguru import logger


router = APIRouter(prefix="/admin/dashboard", tags=["Admin - Dashboard"])


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Dashboard stats (clinic overview)",
    description="Total revenue, total referrals, total commissions, total webinars (this month), currency.",
)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin: clinic overview stats for dashboard cards."""
    try:
        service = AdminDashboardService(db)
        data = service.get_stats()
        return laravel_response(
            success=True,
            message="Dashboard stats",
            data=data,
        )
    except Exception as e:
        logger.error("Failed to get dashboard stats: {}", str(e), exc_info=True)
        raise


@router.get(
    "/revenue-graph",
    status_code=status.HTTP_200_OK,
    summary="Dashboard revenue graph",
    description="Monthly revenue for last N months (single series: appointment + webinar). Default 6 months.",
)
async def get_dashboard_revenue_graph(
    months: int = Query(6, ge=1, le=24, description="Number of months"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin: revenue overview graph data."""
    try:
        service = AdminDashboardService(db)
        data = service.get_revenue_graph(months=months)
        return laravel_response(
            success=True,
            message="Revenue graph data",
            data=data,
        )
    except Exception as e:
        logger.error("Failed to get dashboard revenue graph: {}", str(e), exc_info=True)
        raise


@router.get(
    "/recent-activity",
    status_code=status.HTTP_200_OK,
    summary="Recent activity",
    description="Latest actions across the platform (user name, action, time ago). Optional filter: status (all, confirmed, pending, cancelled).",
)
async def get_dashboard_recent_activity(
    limit: int = Query(20, ge=1, le=100, description="Max number of items"),
    status: Optional[str] = Query("all", description="Filter: all, confirmed, pending, cancelled"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin: recent activity list."""
    try:
        service = AdminDashboardService(db)
        data = service.get_recent_activity(limit=limit, status=status)
        return laravel_response(
            success=True,
            message="Recent activity",
            data=data,
        )
    except Exception as e:
        logger.error("Failed to get recent activity: {}", str(e), exc_info=True)
        raise


@router.get(
    "/active-appointments",
    status_code=status.HTTP_200_OK,
    summary="Active appointments",
    description="Today and future appointments only (scheduled, confirmed, in progress). Paginated. Optional filter: status (all, scheduled, confirmed, in_progress).",
)
async def get_dashboard_active_appointments(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query("all", description="Filter: all, scheduled, confirmed, in_progress"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin: active appointments list (today and future, paginated)."""
    try:
        service = AdminDashboardService(db)
        result = service.get_active_appointments(page=page, per_page=per_page, status_filter=status)
        return laravel_response(
            success=True,
            message="Active appointments",
            data=result,
        )
    except Exception as e:
        logger.error("Failed to get active appointments: {}", str(e), exc_info=True)
        raise
