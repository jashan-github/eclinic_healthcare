"""
Waiver helper: apply admin or doctor waiver to prices for appointments and webinars.
Returns amount_after_waiver (what patient pays), waiver_percent for tracking, and whether to skip payment gateway.

When admin enables waiver_doctor_decides, the doctor sets waiver (0, 25, 50, 75, 100%) at accept;
admin waiver_percent is ignored for that request.
"""

from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.services.admin_settings_service import AdminSettingsService

# Allowed doctor waiver percentages when waiver_doctor_decides is True
DOCTOR_WAIVER_CHOICES = (0, 25, 50, 75, 100)


def get_waiver_settings(db: Session) -> Tuple[bool, int]:
    """
    Returns (waiver_enabled, waiver_percent 0-100).
    """
    settings = AdminSettingsService(db).get_settings()
    return (bool(settings.waiver_enabled), int(settings.waiver_percent) if settings.waiver_percent is not None else 0)


def get_waiver_settings_full(db: Session) -> Tuple[bool, int, bool]:
    """
    Returns (waiver_enabled, waiver_percent 0-100, waiver_doctor_decides).
    """
    settings = AdminSettingsService(db).get_settings()
    return (
        bool(settings.waiver_enabled),
        int(settings.waiver_percent) if settings.waiver_percent is not None else 0,
        bool(getattr(settings, "waiver_doctor_decides", False)),
    )


def apply_waiver_percent(original_amount: Decimal, waiver_percent: int) -> Tuple[Decimal, bool]:
    """
    Apply a specific waiver percentage to an amount.
    Returns (amount_after_waiver, skip_payment_gateway).
    """
    if waiver_percent <= 0:
        return (original_amount, False)
    if waiver_percent >= 100:
        return (Decimal("0"), True)
    factor = 1 - (waiver_percent / 100)
    amount_after = (original_amount * Decimal(str(factor))).quantize(Decimal("0.01"))
    if amount_after < 0:
        amount_after = Decimal("0")
    return (amount_after, amount_after == 0)


def apply_waiver(
    db: Session,
    original_amount: Decimal,
) -> Tuple[Decimal, int, bool]:
    """
    Apply admin waiver to an amount (used when waiver_doctor_decides is False).

    Returns:
        (amount_after_waiver, waiver_percent_used, skip_payment_gateway)
        - amount_after_waiver: max(0, round(original * (1 - waiver_percent/100), 2))
        - waiver_percent_used: 0 if waiver disabled, else admin waiver_percent
        - skip_payment_gateway: True when amount_after_waiver == 0 (patient not charged)
    """
    waiver_enabled, waiver_percent = get_waiver_settings(db)
    if not waiver_enabled or waiver_percent <= 0:
        return (original_amount, 0, False)
    amount_after, skip_gateway = apply_waiver_percent(original_amount, waiver_percent)
    return (amount_after, waiver_percent, skip_gateway)


def apply_waiver_for_request(
    db: Session,
    original_amount: Decimal,
    doctor_waiver_percent: Optional[int],
) -> Tuple[Decimal, int, bool]:
    """
    Apply waiver for an appointment request: use doctor-set waiver when waiver_doctor_decides
    and doctor_waiver_percent is set; otherwise use admin waiver.

    Returns:
        (amount_after_waiver, waiver_percent_used, skip_payment_gateway)
    """
    waiver_enabled, admin_percent, waiver_doctor_decides = get_waiver_settings_full(db)
    if waiver_doctor_decides and waiver_enabled and doctor_waiver_percent is not None:
        # Doctor-set waiver (0, 25, 50, 75, 100); admin percentage ignored
        amount_after, skip_gateway = apply_waiver_percent(original_amount, doctor_waiver_percent)
        return (amount_after, doctor_waiver_percent, skip_gateway)
    # Admin waiver (existing behavior)
    return apply_waiver(db, original_amount)


def get_display_amounts(
    db: Session,
    original_amount: Decimal,
) -> Tuple[Decimal, int, Decimal]:
    """
    Get amounts for display/API: (amount_after_waiver, waiver_percent, amount_before_waiver).
    Use amount_after_waiver as the price to show and charge. Uses admin waiver only.
    """
    amount_after, waiver_percent, _ = apply_waiver(db, original_amount)
    return (amount_after, waiver_percent, original_amount)


def get_request_price_display(
    db: Session,
    original_amount: Optional[float],
    doctor_waiver_percent: Optional[int] = None,
) -> Tuple[Optional[float], Optional[float], Optional[int]]:
    """
    Return (price_amount_after_waiver, amount_before_waiver, waiver_percent) for API responses.
    When waiver_doctor_decides is True and doctor_waiver_percent is set, uses doctor's waiver;
    otherwise uses admin waiver.
    """
    if original_amount is None:
        return (None, None, None)
    amt = Decimal(str(original_amount))
    waiver_enabled, admin_percent, waiver_doctor_decides = get_waiver_settings_full(db)
    if waiver_doctor_decides and waiver_enabled and doctor_waiver_percent is not None:
        amount_after, _ = apply_waiver_percent(amt, doctor_waiver_percent)
        return (float(amount_after), float(amt), doctor_waiver_percent)
    after, pct, before = get_display_amounts(db, amt)
    return (float(after), float(before), pct)
