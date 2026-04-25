"""
WhatsApp Notification Service (Twilio)
Sends event-based WhatsApp notifications: appointment made, approved, amount paid,
video appointment in 15 mins, webinar starting in 15 mins.
Uses Twilio WhatsApp API; config from env (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM)
or from notification channel settings in DB.
"""

from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.core.config import settings
from app.services.notification.providers import TwilioWhatsAppProvider
from app.services.notification.dispatcher import get_notification_dispatcher
from app.utils.encryption import get_encryption_service


def _normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Ensure phone has + for E.164; strip spaces."""
    if not phone or not str(phone).strip():
        return None
    p = str(phone).strip().replace(" ", "")
    if p.startswith("+"):
        return p
    if p.startswith("00"):
        return "+" + p[2:]
    return "+" + p


def _get_twilio_whatsapp_client() -> Optional[TwilioWhatsAppProvider]:
    """Build Twilio WhatsApp provider from env (for direct send without DB channel)."""
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    from_number = (
        getattr(settings, "TWILIO_WHATSAPP_FROM", None)
        or getattr(settings, "WHATSAPP_PHONE_NUMBER", None)
        or getattr(settings, "TWILIO_PHONE_NUMBER", None)
    )
    if not all([account_sid, auth_token, from_number]):
        return None
    return TwilioWhatsAppProvider({
        "account_sid": account_sid,
        "auth_token": auth_token,
        "phone_number": from_number,
    })


async def _send_whatsapp(phone: str, message: str, db: Optional[Session] = None) -> bool:
    """
    Send WhatsApp message. Prefer dispatcher (DB channel) if db given and channel enabled;
    otherwise use env-based Twilio client.
    """
    phone = _normalize_phone(phone)
    if not phone:
        logger.warning("WhatsApp send skipped: no phone number")
        return False

    if db:
        try:
            encryption_service = get_encryption_service()
            dispatcher = get_notification_dispatcher(db, encryption_service)
            if dispatcher.is_channel_enabled("whatsapp"):
                return await dispatcher.send_whatsapp(phone=phone, message=message)
        except Exception as e:
            logger.warning(f"WhatsApp via dispatcher failed: {e}, falling back to env client")

    client = _get_twilio_whatsapp_client()
    if not client:
        logger.warning("WhatsApp send skipped: Twilio not configured (env or channel)")
        return False
    return await client.send(recipient=phone, message=message)


# -----------------------------------------------------------------------------
# Event templates and send functions
# -----------------------------------------------------------------------------


async def send_appointment_made_whatsapp(
    to_phone: str,
    patient_name: str,
    appointment_date: str,
    appointment_time: str,
    service_name: Optional[str] = None,
    db: Optional[Session] = None,
) -> bool:
    """
    Notify (e.g. doctor) that an appointment was made.
    """
    service = service_name or "Appointment"
    msg = (
        f"*New appointment request*\n\n"
        f"Patient: {patient_name}\n"
        f"Date: {appointment_date}\n"
        f"Time: {appointment_time}\n"
        f"Service: {service}\n\n"
        f"Please accept or reject in the portal."
    )
    return await _send_whatsapp(to_phone, msg, db=db)


async def send_appointment_approved_whatsapp(
    to_phone: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    amount: Optional[str] = None,
    service_name: Optional[str] = None,
    db: Optional[Session] = None,
) -> bool:
    """
    Notify (e.g. patient) that the appointment was approved.
    """
    service = service_name or "Appointment"
    amount_line = f"Amount: {amount}\n" if amount else ""
    msg = (
        f"*Appointment confirmed*\n\n"
        f"Dr. {doctor_name}\n"
        f"Date: {appointment_date}\n"
        f"Time: {appointment_time}\n"
        f"Service: {service}\n"
        f"{amount_line}\n"
        f"Please complete payment if required."
    )
    return await _send_whatsapp(to_phone, msg, db=db)


async def send_appointment_rejected_whatsapp(
    to_phone: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    rejection_reason: Optional[str] = None,
    db: Optional[Session] = None,
) -> bool:
    """
    Notify (e.g. patient) that the appointment request was rejected.
    """
    reason_line = f"Reason: {rejection_reason}\n" if rejection_reason else ""
    msg = (
        f"*Appointment request rejected*\n\n"
        f"Dr. {doctor_name}\n"
        f"Date: {appointment_date}\n"
        f"Time: {appointment_time}\n"
        f"{reason_line}\n"
        f"Please select another time slot."
    )
    return await _send_whatsapp(to_phone, msg, db=db)


async def send_appointment_amount_paid_whatsapp(
    to_phone: str,
    amount: str,
    service_name: Optional[str] = None,
    appointment_date: Optional[str] = None,
    appointment_time: Optional[str] = None,
    db: Optional[Session] = None,
) -> bool:
    """
    Notify (e.g. patient) that the appointment amount was paid.
    """
    service = service_name or "Appointment"
    date_time = ""
    if appointment_date and appointment_time:
        date_time = f"\nDate: {appointment_date}\nTime: {appointment_time}"
    msg = (
        f"*Payment received*\n\n"
        f"Amount: {amount}\n"
        f"Service: {service}{date_time}\n\n"
        f"Your appointment is confirmed. Thank you!"
    )
    return await _send_whatsapp(to_phone, msg, db=db)


async def send_video_appointment_reminder_15min_whatsapp(
    to_phone: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    join_url_or_instruction: Optional[str] = None,
    db: Optional[Session] = None,
) -> bool:
    """
    Remind (e.g. patient) that video appointment is in 15 minutes.
    """
    extra = ""
    if join_url_or_instruction:
        extra = f"\n\n{join_url_or_instruction}"
    msg = (
        f"*Video appointment in 15 minutes*\n\n"
        f"Dr. {doctor_name}\n"
        f"Date: {appointment_date}\n"
        f"Time: {appointment_time}\n\n"
        f"Please join the video call from your appointment page.{extra}"
    )
    return await _send_whatsapp(to_phone, msg, db=db)


async def send_webinar_reminder_15min_whatsapp(
    to_phone: str,
    webinar_title: str,
    start_time: str,
    join_url_or_instruction: Optional[str] = None,
    db: Optional[Session] = None,
) -> bool:
    """
    Remind that webinar starts in 15 minutes.
    """
    extra = ""
    if join_url_or_instruction:
        extra = f"\n\n{join_url_or_instruction}"
    msg = (
        f"*Webinar starting in 15 minutes*\n\n"
        f"*{webinar_title}*\n"
        f"Start: {start_time}\n\n"
        f"Join from the webinar page when it goes live.{extra}"
    )
    return await _send_whatsapp(to_phone, msg, db=db)
