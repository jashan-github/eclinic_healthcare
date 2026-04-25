"""
Admin Advanced Analytics API
Stats: summary cards (total webinars, appointments, revenue, active patients).
Graph: monthly revenue (primary = appointments, secondary = webinars).
Graph/appointments: monthly appointment volume (total_appointments, amount_collected).
Graph/webinars: monthly webinar volume (total_webinars, amount_collected).
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.services.admin_analytics_service import AdminAnalyticsService
from app.core.exceptions import laravel_response
from loguru import logger


router = APIRouter(prefix="/admin/analytics", tags=["Admin - Analytics"])


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Get analytics stats (admin)",
    description="Summary cards: total_webinars, total_appointments, revenue (appointment + webinar), active_patients, currency.",
)
async def get_admin_analytics_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin: get Advanced Analytics summary stats for dashboard cards."""
    try:
        service = AdminAnalyticsService(db)
        data = service.get_stats()
        return laravel_response(
            success=True,
            message="Analytics stats",
            data=data,
        )
    except Exception as e:
        logger.error(f"Failed to get admin analytics stats: {str(e)}", exc_info=True)
        raise


@router.get(
    "/graph",
    status_code=status.HTTP_200_OK,
    summary="Get revenue graph data (admin)",
    description="Monthly revenue for chart: primary_revenue (appointments), secondary_revenue (webinars). Optional: year (full year) or months (rolling window).",
)
async def get_admin_analytics_graph(
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Year; if set, returns all 12 months of that year"),
    months: int = Query(12, ge=1, le=24, description="Rolling window in months when year is not set"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin: get monthly revenue data for the analytics graph."""
    try:
        service = AdminAnalyticsService(db)
        data = service.get_revenue_graph(year=year, months=months)
        return laravel_response(
            success=True,
            message="Revenue graph data",
            data=data,
        )
    except Exception as e:
        logger.error(f"Failed to get admin analytics graph: {str(e)}", exc_info=True)
        raise


@router.get(
    "/graph/appointments",
    status_code=status.HTTP_200_OK,
    summary="Get appointment volume graph data (admin)",
    description="Monthly appointment trends: total_appointments and amount_collected (revenue from completed appointment payments). Optional: year (full year) or months (rolling window).",
)
async def get_admin_analytics_appointment_volume(
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Year; if set, returns all 12 months of that year"),
    months: int = Query(12, ge=1, le=24, description="Rolling window in months when year is not set"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin: get monthly appointment volume data for the Appointment Volume chart."""
    try:
        service = AdminAnalyticsService(db)
        data = service.get_appointment_volume_graph(year=year, months=months)
        return laravel_response(
            success=True,
            message="Appointment volume graph data",
            data=data,
        )
    except Exception as e:
        logger.error(f"Failed to get admin analytics appointment volume: {str(e)}", exc_info=True)
        raise


@router.get(
    "/graph/webinars",
    status_code=status.HTTP_200_OK,
    summary="Get webinar volume graph data (admin)",
    description="Monthly webinar trends: total_webinars and amount_collected (revenue from completed webinar payments). Optional: year (full year) or months (rolling window).",
)
async def get_admin_analytics_webinar_volume(
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Year; if set, returns all 12 months of that year"),
    months: int = Query(12, ge=1, le=24, description="Rolling window in months when year is not set"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin: get monthly webinar volume data for the Webinar Performance chart."""
    try:
        service = AdminAnalyticsService(db)
        data = service.get_webinar_volume_graph(year=year, months=months)
        return laravel_response(
            success=True,
            message="Webinar volume graph data",
            data=data,
        )
    except Exception as e:
        logger.error(f"Failed to get admin analytics webinar volume: {str(e)}", exc_info=True)
        raise
