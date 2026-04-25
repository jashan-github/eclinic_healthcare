"""
Notification Helper
Helper functions for sending appointment-related notifications
"""

from typing import Optional, Any
from sqlalchemy.orm import Session
from loguru import logger

from app.models.user import User
from app.services.notification.dispatcher import NotificationDispatcher
from app.utils.encryption import EncryptionService


async def send_appointment_request_notification(
    db: Session,
    doctor_id: str,
    request_id: str,
    patient_name: str,
    appointment_date: str,
    appointment_time: str,
    service_name: Optional[str] = None,
    consultation_mode: Optional[str] = None
) -> None:
    """
    Send notification to doctor about new appointment request using SendGrid
    
    Args:
        db: Database session
        doctor_id: Doctor user ID
        request_id: Appointment request ID
        patient_name: Patient name (for notification)
        appointment_date: Appointment date
        appointment_time: Appointment time
        service_name: Service name (optional)
        consultation_mode: Consultation mode (optional)
    """
    try:
        # Get doctor
        doctor = db.query(User).filter(User.id == doctor_id).first()
        if not doctor:
            logger.warning(f"Doctor {doctor_id} not found for notification")
            return
        
        if not doctor.email:
            logger.warning(f"Doctor {doctor_id} has no email address")
            return
        
        # Check admin setting: allow new appointment request email to doctor
        from app.services.admin_settings_service import AdminSettingsService
        admin_settings = AdminSettingsService(db).get_settings()
        email_notify_new_request = getattr(admin_settings, "email_notify_new_appointment_request", True)
        
        # Get doctor name
        doctor_name = doctor.name or "Doctor"
        
        # Use EmailService to send email via SendGrid (only if enabled)
        if email_notify_new_request:
            from app.services.email_service import EmailService
            email_service = EmailService()
        
        # Format date and time for email
        try:
            from datetime import datetime, date as date_type, time as time_type
            # Parse date (could be ISO format string or already a date)
            if isinstance(appointment_date, str):
                date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            elif isinstance(appointment_date, date_type):
                date_obj = appointment_date
            else:
                date_obj = datetime.strptime(str(appointment_date), "%Y-%m-%d").date()
            formatted_date = date_obj.strftime("%B %d, %Y")
        except Exception as e:
            logger.warning(f"Failed to parse appointment date: {appointment_date}, error: {str(e)}")
            formatted_date = str(appointment_date)
        
        try:
            from datetime import datetime, time as time_type
            # Parse time (could be ISO format string like "14:30:00" or "14:30", or already a time object)
            if isinstance(appointment_time, str):
                # Try different formats
                if len(appointment_time.split(":")) == 3:
                    time_obj = datetime.strptime(appointment_time, "%H:%M:%S").time()
                else:
                    time_obj = datetime.strptime(appointment_time, "%H:%M").time()
            elif isinstance(appointment_time, time_type):
                time_obj = appointment_time
            else:
                # Try to parse as string
                time_str = str(appointment_time)
                if len(time_str.split(":")) == 3:
                    time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
                else:
                    time_obj = datetime.strptime(time_str, "%H:%M").time()
            formatted_time = time_obj.strftime("%I:%M %p")
        except Exception as e:
            logger.warning(f"Failed to parse appointment time: {appointment_time}, error: {str(e)}")
            formatted_time = str(appointment_time)
        
        # Send email using EmailService (only if admin enabled)
        if email_notify_new_request:
            logger.info(
                f"Preparing to send appointment email to doctor {doctor_id}: "
                f"email='{doctor.email}', name='{doctor_name}', "
                f"service='{service_name}', date='{formatted_date}', time='{formatted_time}'"
            )
            try:
                result = await email_service.send_new_appointment_email(
                    recipient_email=doctor.email,
                    recipient_name=doctor_name,
                    doctor_name=doctor_name,
                    appointment_date=formatted_date,
                    appointment_time=formatted_time,
                    service_name=service_name or "Appointment",
                    consultation_mode=consultation_mode or "IN_CLINIC",
                    appointment_id=request_id
                )
                if result:
                    logger.info(
                        f"✓ New appointment email successfully sent to doctor {doctor_id} "
                        f"(email: {doctor.email}) for request {request_id}"
                    )
                else:
                    logger.warning(
                        f"⚠ Email service returned False for doctor {doctor_id} "
                        f"(email: {doctor.email}) for request {request_id}"
                    )
            except Exception as email_error:
                logger.error(
                    f"✗ Failed to send email to doctor {doctor_id} (email: {doctor.email}): {str(email_error)}",
                    exc_info=True
                )
                raise
        else:
            logger.info(f"New appointment request email to doctor disabled by admin; skipping for request {request_id}")

        # WhatsApp: appointment made (to doctor)
        try:
            from app.services.whatsapp_notification_service import send_appointment_made_whatsapp
            if doctor.phone:
                await send_appointment_made_whatsapp(
                    to_phone=doctor.phone,
                    patient_name=patient_name,
                    appointment_date=formatted_date,
                    appointment_time=formatted_time,
                    service_name=service_name,
                    db=db,
                )
        except Exception as wa_err:
            logger.warning(f"WhatsApp appointment-made notification failed: {wa_err}")

        # FCM push: appointment made (to doctor)
        try:
            from app.services.fcm_push_notification_service import send_push_to_user
            await send_push_to_user(
                db=db,
                user_id=doctor_id,
                title="New appointment request",
                body=f"{patient_name} requested an appointment for {formatted_date} at {formatted_time}.",
                data={"type": "appointment_request", "request_id": request_id},
            )
        except Exception as fcm_err:
            logger.warning(f"FCM appointment-made notification failed: {fcm_err}")
        
    except Exception as e:
        logger.error(f"Failed to send appointment request notification: {str(e)}", exc_info=True)
        # Don't fail the request if notification fails


async def send_appointment_acceptance_notification(
    db: Session,
    patient_id: str,
    request_id: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    price_amount: float,
    currency: str,
    service_name: Optional[str] = None,
    consultation_mode: Optional[str] = None
) -> None:
    """
    Send notification to patient about accepted appointment request using SendGrid
    
    Args:
        db: Database session
        patient_id: Patient user ID
        request_id: Appointment request ID
        doctor_name: Doctor name
        appointment_date: Appointment date
        appointment_time: Appointment time
        price_amount: Price amount
        currency: Currency code
        service_name: Service name (optional)
        consultation_mode: Consultation mode (optional)
    """
    try:
        # Get patient
        patient = db.query(User).filter(User.id == patient_id).first()
        if not patient:
            logger.warning(f"Patient {patient_id} not found for notification")
            return
        
        if not patient.email:
            logger.warning(f"Patient {patient_id} has no email address")
            return
        
        # Check admin setting: allow appointment accepted email to patient
        from app.services.admin_settings_service import AdminSettingsService
        admin_settings = AdminSettingsService(db).get_settings()
        email_notify_accepted = getattr(admin_settings, "email_notify_appointment_accepted", True)
        
        # Get patient name
        patient_name = patient.name or "Patient"
        
        # Format date and time (used for email and WhatsApp)
        try:
            from datetime import datetime, date as date_type, time as time_type
            # Parse date (could be ISO format string or already a date)
            if isinstance(appointment_date, str):
                date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            elif isinstance(appointment_date, date_type):
                date_obj = appointment_date
            else:
                date_obj = datetime.strptime(str(appointment_date), "%Y-%m-%d").date()
            formatted_date = date_obj.strftime("%B %d, %Y")
        except Exception as e:
            logger.warning(f"Failed to parse appointment date: {appointment_date}, error: {str(e)}")
            formatted_date = str(appointment_date)
        
        try:
            from datetime import datetime, time as time_type
            # Parse time (could be ISO format string like "14:30:00" or "14:30", or already a time object)
            if isinstance(appointment_time, str):
                # Try different formats
                if len(appointment_time.split(":")) == 3:
                    time_obj = datetime.strptime(appointment_time, "%H:%M:%S").time()
                else:
                    time_obj = datetime.strptime(appointment_time, "%H:%M").time()
            elif isinstance(appointment_time, time_type):
                time_obj = appointment_time
            else:
                # Try to parse as string
                time_str = str(appointment_time)
                if len(time_str.split(":")) == 3:
                    time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
                else:
                    time_obj = datetime.strptime(time_str, "%H:%M").time()
            formatted_time = time_obj.strftime("%I:%M %p")
        except Exception as e:
            logger.warning(f"Failed to parse appointment time: {appointment_time}, error: {str(e)}")
            formatted_time = str(appointment_time)
        
        # Send email using EmailService (only if admin enabled)
        if email_notify_accepted:
            from app.services.email_service import EmailService
            email_service = EmailService()
            logger.info(
                f"Preparing to send appointment acceptance email to patient {patient_id}: "
                f"email='{patient.email}', name='{patient_name}', "
                f"doctor='{doctor_name}', service='{service_name}', "
                f"date='{formatted_date}', time='{formatted_time}', "
                f"price={price_amount} {currency}"
            )
            try:
                result = await email_service.send_appointment_confirmed_email(
                    recipient_email=patient.email,
                    recipient_name=patient_name,
                    doctor_name=doctor_name,
                    appointment_date=formatted_date,
                    appointment_time=formatted_time,
                    service_name=service_name or "Appointment",
                    consultation_mode=consultation_mode or "IN_CLINIC",
                    appointment_id=request_id
                )
                if result:
                    logger.info(
                        f"✓ Appointment acceptance email successfully sent to patient {patient_id} "
                        f"(email: {patient.email}) for request {request_id}"
                    )
                else:
                    logger.warning(
                        f"⚠ Email service returned False for patient {patient_id} "
                        f"(email: {patient.email}) for request {request_id}"
                    )
            except Exception as email_error:
                logger.error(
                    f"✗ Failed to send email to patient {patient_id} (email: {patient.email}): {str(email_error)}",
                    exc_info=True
                )
                raise
        else:
            logger.info(f"Appointment accepted email to patient disabled by admin; skipping for request {request_id}")

        # WhatsApp: appointment approved (to patient)
        try:
            from app.services.whatsapp_notification_service import send_appointment_approved_whatsapp
            if patient.phone:
                amount_str = f"{price_amount} {currency}" if price_amount is not None else None
                await send_appointment_approved_whatsapp(
                    to_phone=patient.phone,
                    doctor_name=doctor_name,
                    appointment_date=formatted_date,
                    appointment_time=formatted_time,
                    amount=amount_str,
                    service_name=service_name,
                    db=db,
                )
        except Exception as wa_err:
            logger.warning(f"WhatsApp appointment-approved notification failed: {wa_err}")

        # FCM push: appointment approved (to patient)
        try:
            from app.services.fcm_push_notification_service import send_push_to_user
            await send_push_to_user(
                db=db,
                user_id=patient_id,
                title="Appointment approved",
                body=f"Dr. {doctor_name} approved your appointment for {formatted_date} at {formatted_time}.",
                data={"type": "appointment_approved", "request_id": request_id},
            )
        except Exception as fcm_err:
            logger.warning(f"FCM appointment-approved notification failed: {fcm_err}")
        
    except Exception as e:
        logger.error(f"Failed to send acceptance notification: {str(e)}", exc_info=True)
        # Don't fail the request if notification fails


async def send_appointment_rejection_notification(
    db: Session,
    patient_id: str,
    request_id: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    rejection_reason: Optional[str] = None,
    service_name: Optional[str] = None
) -> None:
    """
    Send notification to patient about rejected appointment request using SendGrid
    
    Args:
        db: Database session
        patient_id: Patient user ID
        request_id: Appointment request ID
        doctor_name: Doctor name
        appointment_date: Appointment date
        appointment_time: Appointment time
        rejection_reason: Optional rejection reason
        service_name: Service name (optional)
    """
    try:
        # Get patient
        patient = db.query(User).filter(User.id == patient_id).first()
        if not patient:
            logger.warning(f"Patient {patient_id} not found for notification")
            return
        
        if not patient.email:
            logger.warning(f"Patient {patient_id} has no email address")
            return
        
        # Check admin setting: allow appointment rejected email to patient
        from app.services.admin_settings_service import AdminSettingsService
        admin_settings = AdminSettingsService(db).get_settings()
        email_notify_rejected = getattr(admin_settings, "email_notify_appointment_rejected", True)
        
        # Get patient name
        patient_name = patient.name or "Patient"
        
        # Format date and time
        try:
            from datetime import datetime, date as date_type, time as time_type
            # Parse date (could be ISO format string or already a date)
            if isinstance(appointment_date, str):
                date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            elif isinstance(appointment_date, date_type):
                date_obj = appointment_date
            else:
                date_obj = datetime.strptime(str(appointment_date), "%Y-%m-%d").date()
            formatted_date = date_obj.strftime("%B %d, %Y")
        except Exception as e:
            logger.warning(f"Failed to parse appointment date: {appointment_date}, error: {str(e)}")
            formatted_date = str(appointment_date)
        
        try:
            from datetime import datetime, time as time_type
            # Parse time (could be ISO format string like "14:30:00" or "14:30", or already a time object)
            if isinstance(appointment_time, str):
                # Try different formats
                if len(appointment_time.split(":")) == 3:
                    time_obj = datetime.strptime(appointment_time, "%H:%M:%S").time()
                else:
                    time_obj = datetime.strptime(appointment_time, "%H:%M").time()
            elif isinstance(appointment_time, time_type):
                time_obj = appointment_time
            else:
                # Try to parse as string
                time_str = str(appointment_time)
                if len(time_str.split(":")) == 3:
                    time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
                else:
                    time_obj = datetime.strptime(time_str, "%H:%M").time()
            formatted_time = time_obj.strftime("%I:%M %p")
        except Exception as e:
            logger.warning(f"Failed to parse appointment time: {appointment_time}, error: {str(e)}")
            formatted_time = str(appointment_time)
        
        # Send email using EmailService (only if admin enabled)
        if email_notify_rejected:
            from app.services.email_service import EmailService
            email_service = EmailService()
            logger.info(
                f"Preparing to send appointment rejection email to patient {patient_id}: "
                f"email='{patient.email}', name='{patient_name}', "
                f"doctor='{doctor_name}', service='{service_name}', "
                f"date='{formatted_date}', time='{formatted_time}'"
            )
            try:
                result = await email_service.send_appointment_rejected_email(
                    recipient_email=patient.email,
                    recipient_name=patient_name,
                    doctor_name=doctor_name,
                    appointment_date=formatted_date,
                    appointment_time=formatted_time,
                    service_name=service_name or "Appointment",
                    rejection_reason=rejection_reason,
                    appointment_id=request_id
                )
                if result:
                    logger.info(
                        f"Appointment rejection email successfully sent to patient {patient_id} "
                        f"(email: {patient.email}) for request {request_id}"
                    )
                else:
                    logger.warning(
                        f"Email service returned False for patient {patient_id} "
                        f"(email: {patient.email}) for request {request_id}"
                    )
            except Exception as email_error:
                logger.error(
                    f"Failed to send rejection email to patient {patient_id} (email: {patient.email}): {str(email_error)}",
                    exc_info=True
                )
        else:
            logger.info(f"Appointment rejected email to patient disabled by admin; skipping for request {request_id}")

        # WhatsApp: appointment rejected (to patient)
        try:
            from app.services.whatsapp_notification_service import send_appointment_rejected_whatsapp
            if patient.phone:
                await send_appointment_rejected_whatsapp(
                    to_phone=patient.phone,
                    doctor_name=doctor_name,
                    appointment_date=formatted_date,
                    appointment_time=formatted_time,
                    rejection_reason=rejection_reason,
                    db=db,
                )
        except Exception as wa_err:
            logger.warning(f"WhatsApp appointment-rejected notification failed: {wa_err}")

        # FCM push: appointment rejected (to patient)
        try:
            from app.services.fcm_push_notification_service import send_push_to_user
            reason_text = f" Reason: {rejection_reason}" if rejection_reason else ""
            await send_push_to_user(
                db=db,
                user_id=patient_id,
                title="Appointment request rejected",
                body=f"Your appointment request with Dr. {doctor_name} for {formatted_date} at {formatted_time} has been rejected.{reason_text}",
                data={"type": "appointment_rejected", "request_id": request_id},
            )
        except Exception as fcm_err:
            logger.warning(f"FCM appointment-rejected notification failed: {fcm_err}")
        
    except Exception as e:
        logger.error(f"Failed to send rejection notification: {str(e)}", exc_info=True)
        # Don't fail the request if notification fails


async def send_payment_success_notification(
    db: Session,
    patient_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
    appointment_id: Optional[str] = None,
    appointment_date: Optional[str] = None,
    appointment_time: Optional[str] = None,
    appointment: Optional[Any] = None,
    payment_amount: Optional[float] = None,
    currency: Optional[str] = None,
) -> None:
    """
    Send notification to both patient and doctor about successful payment and confirmed appointment.
    Call with either (db, patient_id, doctor_id, appointment_id, appointment_date, appointment_time)
    or (db, appointment=..., payment_amount=..., currency=...).
    """
    try:
        if appointment is not None:
            patient_id = str(appointment.patient_id) if appointment.patient_id else None
            doctor_id = str(appointment.doctor_id) if appointment.doctor_id else None
            appointment_id = str(appointment.id) if appointment.id else None
            appointment_date = str(appointment.appointment_date) if getattr(appointment, "appointment_date", None) else None
            appointment_time = str(appointment.start_time) if getattr(appointment, "start_time", None) else None
        if not all([patient_id, doctor_id, appointment_date, appointment_time]):
            logger.warning("send_payment_success_notification: missing required ids or date/time")
            return
        # Get users
        patient = db.query(User).filter(User.id == patient_id).first()
        doctor = db.query(User).filter(User.id == doctor_id).first()
        
        if not patient or not doctor:
            logger.warning(f"User not found for payment success notification (patient: {patient_id}, doctor: {doctor_id})")
            return
        
        # Get notification dispatcher
        from app.core.config import settings
        encryption_service = EncryptionService(key=settings.ENCRYPTION_KEY)
        dispatcher = NotificationDispatcher(db, encryption_service)
        
        # Notify patient
        patient_subject = "Appointment Confirmed"
        patient_message = f"Your appointment with Dr. {doctor.name} for {appointment_date} at {appointment_time} has been confirmed. Payment received successfully."
        
        # Notify patient
        try:
            if dispatcher.is_channel_enabled("email") and patient.email:
                await dispatcher.send_email(
                    email=patient.email,
                    subject=patient_subject,
                    message=patient_message
                )
        except Exception as e:
            logger.warning(f"Failed to send patient email notification: {str(e)}")
        
        try:
            if dispatcher.is_channel_enabled("sms") and patient.phone:
                await dispatcher.send_sms(
                    phone=patient.phone,
                    message=f"Appointment confirmed: {appointment_date} at {appointment_time}. Payment received."
                )
        except Exception as e:
            logger.warning(f"Failed to send patient SMS notification: {str(e)}")

        # WhatsApp: appointment amount paid (to patient)
        try:
            from app.services.whatsapp_notification_service import send_appointment_amount_paid_whatsapp
            if patient.phone:
                amount_str = f"{payment_amount} {currency}" if payment_amount is not None and currency else f"{appointment_date} at {appointment_time}"
                await send_appointment_amount_paid_whatsapp(
                    to_phone=patient.phone,
                    amount=amount_str,
                    service_name="Appointment",
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    db=db,
                )
        except Exception as wa_err:
            logger.warning(f"WhatsApp payment-received notification failed: {wa_err}")

        # FCM push: payment received (to patient)
        try:
            from app.services.fcm_push_notification_service import send_push_to_user
            await send_push_to_user(
                db=db,
                user_id=patient_id,
                title="Payment received",
                body=f"Your appointment for {appointment_date} at {appointment_time} is confirmed. Payment received.",
                data={"type": "payment_success", "appointment_id": appointment_id or ""},
            )
        except Exception as fcm_err:
            logger.warning(f"FCM payment-received notification failed: {fcm_err}")
        
        # Notify doctor
        doctor_subject = "Appointment Confirmed - Payment Received"
        doctor_message = f"Appointment with {patient.name} for {appointment_date} at {appointment_time} has been confirmed. Payment received."
        
        try:
            if dispatcher.is_channel_enabled("email") and doctor.email:
                await dispatcher.send_email(
                    email=doctor.email,
                    subject=doctor_subject,
                    message=doctor_message
                )
        except Exception as e:
            logger.warning(f"Failed to send doctor email notification: {str(e)}")
        
        try:
            if dispatcher.is_channel_enabled("sms") and doctor.phone:
                await dispatcher.send_sms(
                    phone=doctor.phone,
                    message=f"Appointment confirmed: {appointment_date} at {appointment_time}. Patient payment received."
                )
        except Exception as e:
            logger.warning(f"Failed to send doctor SMS notification: {str(e)}")
        
    except Exception as e:
        logger.error(f"Failed to send payment success notification: {str(e)}", exc_info=True)
        # Don't fail the request if notification fails
