"""
Webinar Payment endpoints
API endpoints for webinar registration and payment handling
"""

import json
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from uuid import UUID
from loguru import logger

from typing import Optional

# Suffixes Sentoo may append to URL/query param values (e.g. ...?redirect_token=JWTsuccess)
SENTOO_PARAM_SUFFIXES = ["success", "pending", "cancelled", "cancel", "rejected"]


def _clean_sentoo_param(value: str) -> str:
    """Strip trailing suffix Sentoo may append to a query param value."""
    if not value:
        return value
    for suffix in SENTOO_PARAM_SUFFIXES:
        if value.endswith(suffix):
            return value[: -len(suffix)]
    return value

from app.core.dependencies import get_db, get_current_user, get_current_user_optional, get_client_ip
from app.core.security import CurrentUser, UserRole, decode_webinar_redirect_token
from app.core.exceptions import laravel_response, BadRequestException, NotFoundException, ForbiddenException
from app.services.webinar_payment_service import WebinarPaymentService
from app.schemas.webinar_payment import (
    WebinarRegistrationSingleResponse,
    WebinarPaymentInitializeResponse,
    WebinarPaymentSingleResponse,
    WebinarPaymentResponse
)
from app.core.config import settings
from app.models.webinar_payment import WebinarPayment
from app.models.user import User

router = APIRouter()


def _norm_key(s):
    """Normalize key: strip quotes and backslashes from both ends (avoids KeyError for \"webinar_id\" etc)."""
    s = str(s).strip()
    changed = True
    while changed and len(s) >= 2:
        changed = False
        if s[0] in ('"', "\\"):
            s = s[1:].lstrip()
            changed = True
        if s and s[-1] in ('"', "\\"):
            s = s[:-1].rstrip()
            changed = True
    return s.strip()


@router.post(
    "/register",
    response_model=WebinarRegistrationSingleResponse,
    status_code=200,
    summary="Register for webinar",
    description="Register for a webinar (patients and doctors). Creates payment intent if paid."
)
async def register_for_webinar(
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip)
):
    """
    Register user for a webinar (patients and doctors; doctors can attend webinars they are not hosting).
    
    Request body: JSON with "webinar_id" (UUID). Accepts normal or quoted-key variants to avoid KeyError.
    """
    # Read raw body and parse manually so we never trigger KeyError from Pydantic/proxy-quoted keys
    body = {}
    try:
        raw = await request.body()
        if raw:
            body = json.loads(raw) if isinstance(raw, bytes) else raw
    except Exception:
        try:
            body = dict(await request.form())
        except Exception:
            pass
    if not isinstance(body, dict):
        body = {}

    webinar_id_raw = body.get("webinar_id")
    if webinar_id_raw is None:
        for k, v in body.items():
            if _norm_key(k) == "webinar_id":
                webinar_id_raw = v
                break

    if webinar_id_raw is None:
        raise BadRequestException(
            message="Missing webinar_id",
            errors={"webinar_id": ["Request body must include webinar_id (JSON: {\"webinar_id\": \"<uuid>\"})"]}
        )
    try:
        webinar_id = UUID(str(webinar_id_raw))
    except (ValueError, TypeError):
        raise BadRequestException(
            message="Invalid webinar_id",
            errors={"webinar_id": ["webinar_id must be a valid UUID"]}
        )

    payment_service = WebinarPaymentService(
        db,
        sentoo_merchant_id=settings.SENTOO_MERCHANT_ID if hasattr(settings, 'SENTOO_MERCHANT_ID') else None,
        sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET if hasattr(settings, 'SENTOO_MERCHANT_SECRET') else None
    )
    try:
        registration_data = payment_service.register_for_webinar(
            current_user=current_user,
            webinar_id=webinar_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent")
        )
    except (BadRequestException, NotFoundException, ForbiddenException):
        raise
    except KeyError as e:
        logger.warning(f"KeyError during webinar registration: {e}")
        raise BadRequestException(
            message="Invalid request format",
            errors={"webinar_id": ["Request body must include webinar_id. Example: {\"webinar_id\": \"<uuid>\"}"]}
        )
    except Exception as e:
        # Use {} placeholder so Loguru does not interpret braces in str(e) as format keys
        logger.error("Error registering for webinar: {}", str(e), exc_info=True)
        raise BadRequestException(
            message="Error registering for webinar",
            errors={"general": [str(e)]}
        )

    # Build response using .get() only to avoid KeyError
    payment_data = None
    payment_info = registration_data.get("payment") if isinstance(registration_data, dict) else None
    if payment_info and isinstance(payment_info, dict):
        pid = payment_info.get("payment_id")
        wid = payment_info.get("webinar_id")
        if pid is not None and wid is not None:
            payment_data = WebinarPaymentInitializeResponse(
                payment_id=UUID(str(pid)),
                sentoo_payment_id=payment_info.get("sentoo_payment_id") or "",
                payment_url=payment_info.get("payment_url") or "",
                amount=payment_info.get("amount", 0),
                currency=payment_info.get("currency") or "",
                status=payment_info.get("status") or "",
                webinar_id=UUID(str(wid)),
                webinar_title=payment_info.get("webinar_title")
            )
    rid = registration_data.get("webinar_id") if isinstance(registration_data, dict) else None
    uid = registration_data.get("user_id") if isinstance(registration_data, dict) else None
    if rid is None or uid is None:
        logger.error(
            "Registration response missing webinar_id or user_id",
            extra={"registration_data_keys": list(registration_data.keys()) if isinstance(registration_data, dict) else None}
        )
        raise BadRequestException(
            message="Invalid response from registration service",
            errors={"general": ["Registration failed; please try again."]}
        )
    response_data = {
        "webinar_id": UUID(str(rid)),
        "user_id": UUID(str(uid)),
        "registered": registration_data.get("registered", False),
        "payment_required": registration_data.get("payment_required", False),
        "payment": payment_data,
        "message": registration_data.get("message", "Registration completed.")
    }
    return laravel_response(
        success=True,
        message=response_data.get("message", "Registration completed."),
        data=response_data
    )


def _resolve_user_for_redirect(
    db: Session,
    current_user: Optional[CurrentUser],
    redirect_token: Optional[str],
    webinar_uuid: Optional[UUID] = None,
) -> CurrentUser:
    """
    Resolve CurrentUser from auth, redirect_token, or (fallback) single PENDING payment for webinar.
    Raises on failure.
    """
    from fastapi import HTTPException

    if current_user:
        return current_user

    if redirect_token:
        # Sentoo may append "success" etc. to the URL, corrupting the last param value
        clean_token = _clean_sentoo_param(redirect_token.strip())
        payload = decode_webinar_redirect_token(clean_token)
        if payload:
            user_id = payload.get("user_id")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.is_active:
                    return CurrentUser(
                        id=user.id,
                        email=user.email,
                        role=UserRole(user.role),
                        clinic_id=user.clinic_id,
                        is_active=user.is_active,
                    )
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired redirect link. Please log in and try again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fallback: old payment links without redirect_token – use single PENDING payment for this webinar
    if webinar_uuid is not None:
        pending = (
            db.query(WebinarPayment)
            .filter(
                WebinarPayment.webinar_id == webinar_uuid,
                WebinarPayment.status == "PENDING",
            )
            .all()
        )
        if len(pending) == 1:
            user = db.query(User).filter(User.id == pending[0].user_id).first()
            if user and user.is_active:
                return CurrentUser(
                    id=user.id,
                    email=user.email,
                    role=UserRole(user.role),
                    clinic_id=user.clinic_id,
                    is_active=user.is_active,
                )

    raise HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get(
    "/payment-success",
    status_code=200,
    summary="Payment success redirect handler",
    description="Handle payment success redirect from Sentoo"
)
async def payment_success(
    webinar_id: str = Query(..., description="Webinar ID (may have suffix like 'success' from Sentoo)"),
    redirect_token: Optional[str] = Query(None, description="Short-lived token for redirect auth"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
    ip_address: str = Depends(get_client_ip)
):
    """
    Handle payment success redirect from Sentoo (same pattern as appointment payment-success).
    Verifies payment with Sentoo API, then redirects browser to frontend success/failure page.
    """
    # Clean params (Sentoo may append "success", "pending", etc. to the whole URL / last param)
    clean_webinar_id = _clean_sentoo_param(webinar_id)
    clean_redirect_token = _clean_sentoo_param(redirect_token.strip()) if redirect_token else None
    try:
        webinar_uuid = UUID(clean_webinar_id)
    except ValueError:
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        return RedirectResponse(
            url=f"{frontend_url}/app/payment/failure?reason=invalid_webinar_id&webinar_id={webinar_id}"
        )

    current_user_resolved = _resolve_user_for_redirect(
        db, current_user, clean_redirect_token, webinar_uuid=webinar_uuid
    )

    payment_service = WebinarPaymentService(
        db,
        sentoo_merchant_id=settings.SENTOO_MERCHANT_ID if hasattr(settings, "SENTOO_MERCHANT_ID") else None,
        sentoo_merchant_secret=settings.SENTOO_MERCHANT_SECRET if hasattr(settings, "SENTOO_MERCHANT_SECRET") else None,
    )
    frontend_url = settings.FRONTEND_URL.rstrip("/")

    try:
        result = payment_service.verify_and_complete_payment(
            current_user=current_user_resolved,
            webinar_id=webinar_uuid,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
        )
        is_paid = result.get("is_paid", False)
        status = result.get("payment_status", result.get("status", "UNKNOWN"))

        if is_paid or status == "COMPLETED":
            return RedirectResponse(
                url=f"{frontend_url}/app/payment/success?webinar_id={webinar_uuid}&status=COMPLETED&type=webinar"
            )
        if status in ["FAILED", "CANCELLED", "EXPIRED"]:
            return RedirectResponse(
                url=f"{frontend_url}/app/payment/failure?webinar_id={webinar_uuid}&status={status}&type=webinar"
            )
        return RedirectResponse(
            url=f"{frontend_url}/app/payment/processing?webinar_id={webinar_uuid}&status={status}&type=webinar"
        )
    except (BadRequestException, NotFoundException, ForbiddenException) as e:
        logger.warning("Payment verification error: {}", str(e))
        return RedirectResponse(
            url=f"{frontend_url}/app/payment/failure?webinar_id={webinar_uuid}&reason=verification_failed&type=webinar"
        )
    except Exception as e:
        logger.error("Error verifying payment: {}", str(e), exc_info=True)
        return RedirectResponse(
            url=f"{frontend_url}/app/payment/failure?webinar_id={webinar_uuid}&reason=verification_failed&type=webinar"
        )


@router.get(
    "/payment-cancelled",
    status_code=200,
    summary="Payment cancellation handler",
    description="Handle payment cancellation redirect from Sentoo"
)
async def payment_cancelled(
    webinar_id: str = Query(..., description="Webinar ID (may have suffix from Sentoo)"),
    redirect_token: Optional[str] = Query(None, description="Short-lived token for redirect auth"),
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Handle payment cancellation redirect from Sentoo.
    """
    clean_webinar_id = _clean_sentoo_param(webinar_id)
    clean_redirect_token = _clean_sentoo_param(redirect_token.strip()) if redirect_token else None
    try:
        webinar_uuid = UUID(clean_webinar_id)
    except ValueError:
        raise BadRequestException(
            message="Invalid webinar_id",
            errors={"webinar_id": ["Must be a valid UUID"]}
        )

    current_user_resolved = _resolve_user_for_redirect(
        db, current_user, clean_redirect_token, webinar_uuid=webinar_uuid
    )

    payment = db.query(WebinarPayment).filter(
        WebinarPayment.webinar_id == webinar_uuid,
        WebinarPayment.user_id == current_user_resolved.id
    ).first()
    
    if payment and payment.status == 'PENDING':
        payment.status = 'CANCELLED'
        db.commit()
        logger.info(f"Payment {payment.id} marked as CANCELLED")
    
    return laravel_response(
        success=True,
        message="Payment was cancelled",
        data={
            "webinar_id": str(webinar_uuid),
            "status": "cancelled"
        }
    )


# Webhook: Use the single payments webhook at POST /api/v1/payments/webhook for Sentoo.
# Sentoo allows only one webhook URL; that endpoint dispatches to appointment or webinar payment handling.


@router.get(
    "/{webinar_id}",
    summary="Get webinar payment status",
    description="Retrieve payment status for a specific webinar"
)
async def get_webinar_payment_status(
    webinar_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get payment status for a webinar registration
    
    Path Parameters:
    - **webinar_id**: Webinar ID (UUID)
    
    Returns:
    - Payment details and registration status
    """
    payment = db.query(WebinarPayment).filter(
        WebinarPayment.webinar_id == webinar_id,
        WebinarPayment.user_id == current_user.id
    ).first()
    
    if not payment:
        raise NotFoundException(
            message="No payment found for this webinar",
            errors={"webinar_id": ["You have not registered for this webinar"]}
        )
    
    # Check access - must be the user who made the payment
    if str(current_user.id) != str(payment.user_id):
        raise ForbiddenException(
            message="Access denied",
            errors={"access": ["You do not have permission to view this payment"]}
        )
    
    payment_response = WebinarPaymentResponse(
        id=payment.id,
        webinar_id=payment.webinar_id,
        user_id=payment.user_id,
        sentoo_payment_id=payment.sentoo_payment_id,
        payment_url=payment.payment_url,
        amount=float(payment.amount) if payment.amount else 0.0,
        currency=payment.currency,
        status=payment.status,
        error_message=payment.error_message,
        created_at=payment.created_at.isoformat() if payment.created_at else None,
        updated_at=payment.updated_at.isoformat() if payment.updated_at else None
    )
    
    return laravel_response(
        success=True,
        message="Payment status retrieved successfully",
        data=payment_response
    )
