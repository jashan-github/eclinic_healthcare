"""
Doctor Payments API Endpoints
Routes for doctors to view their payment transactions
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import DoctorUser, require_feature
from app.core.config import settings
from app.services.payment_service import PaymentService
from app.schemas.doctor_payments import DoctorPaymentsListResponse
from app.core.exceptions import laravel_response, BadRequestException
from loguru import logger


router = APIRouter(
    prefix="/doctor/payments",
    tags=["Doctor - Payments"],
    dependencies=[Depends(require_feature("payments"))],
)


@router.get(
    "/transactions",
    status_code=status.HTTP_200_OK,
    summary="Get doctor's payment transactions",
    description="""
    Get doctor's payment transactions with statistics.
    
    **Doctor Only Endpoint**
    - Only authenticated doctors can access their own payment transactions
    
    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **period**: Date filter - `week` (current week), `month` (current month), `custom` (use date_from & date_to). Omit for all time.
    - **date_from**: Start date for custom range (YYYY-MM-DD). Required when period=custom.
    - **date_to**: End date for custom range (YYYY-MM-DD). Required when period=custom.
    - **search**: Search by patient name or phone number (optional)
    - **paymode**: Filter by payment status/mode - 'COMPLETED', 'PENDING', 'FAILED', 'CANCELLED' (optional)
    - **service_id**: Filter by service ID (optional)
    
    **Response includes:**
    - **stats**: Payment statistics for the selected period (total_earned, growth vs previous period, currency)
    - **transactions**: List of payment transactions in the selected period
    - **pagination**: Pagination information
    - **filter**: Applied period (week/month/custom/all) and date range if applicable
    
    **Note:** Only COMPLETED payments are included in the transactions list.
    """
)
async def get_doctor_payments(
    current_user: DoctorUser,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    period: Optional[str] = Query(
        None,
        description="Date filter: week (current week), month (current month), custom (use date_from & date_to). Omit for all time."
    ),
    date_from: Optional[date] = Query(None, description="Start date for custom range (required when period=custom)"),
    date_to: Optional[date] = Query(None, description="End date for custom range (required when period=custom)"),
    search: Optional[str] = Query(None, description="Search by patient name or phone"),
    paymode: Optional[str] = Query(None, description="Filter by payment status/mode"),
    service_id: Optional[UUID] = Query(None, description="Filter by service ID"),
    db: Session = Depends(get_db)
):
    """
    Get payment transactions for the authenticated doctor with statistics
    
    Returns payment transactions with:
    - Patient details (name, phone, contact)
    - Service information
    - Payment amount and currency
    - Payment status (paymode)
    - Receipt number
    - Creation timestamp
    
    Also includes statistics:
    - Total earned (sum of all completed payments)
    - Growth percentage (comparing last 30 days with previous 30 days)
    
    **Authentication Required**: Yes (Doctor role)
    
    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **search**: Optional search by patient name or phone
    - **paymode**: Optional filter by payment status
    - **service_id**: Optional filter by service ID
    
    Note: DoctorUser dependency already enforces doctor role, so no additional role check needed.
    """
    if period == "custom" and (date_from is None or date_to is None):
        raise BadRequestException(
            message="Custom range requires date_from and date_to",
            errors={"period": ["When period=custom, both date_from and date_to are required"]}
        )
    if period == "custom" and date_from and date_to and date_from > date_to:
        raise BadRequestException(
            message="Invalid date range",
            errors={"date_from": ["date_from must be before or equal to date_to"]}
        )
    if period and period not in ("week", "month", "custom"):
        raise BadRequestException(
            message="Invalid period",
            errors={"period": ["period must be one of: week, month, custom"]}
        )

    # Check if Sentoo is configured (for PaymentService initialization)
    if not settings.SENTOO_MERCHANT_ID or not settings.SENTOO_MERCHANT_SECRET:
        logger.warning("Sentoo credentials not configured, but proceeding with payment retrieval")

    payment_service = PaymentService(
        db,
        sentoo_merchant_id=settings.SENTOO_MERCHANT_ID,
        sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET
    )

    try:
        payments_data = payment_service.get_doctor_payments(
            doctor_id=current_user.id,
            page=page,
            per_page=per_page,
            search=search,
            paymode=paymode,
            service_id=service_id,
            period=period,
            date_from=date_from,
            date_to=date_to
        )
        
        return laravel_response(
            success=True,
            message="Doctor payments retrieved successfully",
            data=payments_data
        )
    except Exception as e:
        logger.error(f"Error retrieving doctor payments: {str(e)}", exc_info=True)
        raise BadRequestException(
            message="Error retrieving doctor payments",
            errors={"general": [str(e)]}
        )
