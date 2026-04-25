"""
Doctor Analytics / Report API
Returns aggregated report data for the doctor dashboard (summary, monthly performance, top metrics, payment breakdown).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import DoctorUser, require_feature
from app.core.exceptions import laravel_response, InternalServerException
from app.services.doctor_analytics_service import DoctorAnalyticsService
from loguru import logger


router = APIRouter(
    prefix="/doctor/analytics",
    tags=["Doctor - Analytics"],
    dependencies=[Depends(require_feature("analytics"))],
)


@router.get(
    "/report",
    status_code=status.HTTP_200_OK,
    summary="Get doctor analytics report",
    description="""
    Get aggregated analytics report for the authenticated doctor.
    
    **Doctor Only**
    - Returns summary (total patients, total appointments, revenue, total waiver)
    - Monthly performance: last 12 months with appointment count and revenue per month
    - Top medical metrics from SOAP notes (top symptom, diagnosis, lab test, drug) when available
    - Payment breakdown (total, cash, online)
    
    **Response structure:**
    - **summary**: total_patients, total_appointments, revenue, total_waiver, currency
    - **monthly_performance**: list of { year, month, month_label, appointments, revenue }
    - **top_medical_metrics**: top_symptom, top_diagnosis, top_lab_test, top_drug (null if no SOAP data)
    - **payment_breakdown**: total_payment, total_cash_payment, total_online_payment, currency
    """
)
async def get_doctor_report(
    current_user: DoctorUser,
    db: Session = Depends(get_db),
):
    """
    Get full analytics report for the current doctor (dashboard data).
    """
    try:
        service = DoctorAnalyticsService(db)
        report = service.get_report(doctor_id=current_user.id)
        return laravel_response(
            success=True,
            message="Report retrieved successfully",
            data=report,
        )
    except Exception as e:
        logger.error(f"Failed to get doctor report: {str(e)}", exc_info=True)
        raise InternalServerException(
            message="Error retrieving report",
            errors={"general": [str(e)]}
        )
