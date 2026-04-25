# WhatsApp Notifications (Twilio)

The WhatsApp notification service sends event-based messages via Twilio WhatsApp API.

## Configuration

**Option A – Environment (direct send)**  
Set in `.env`:

- `TWILIO_ACCOUNT_SID` – Twilio Account SID  
- `TWILIO_AUTH_TOKEN` – Twilio Auth Token  
- `TWILIO_WHATSAPP_FROM` – WhatsApp sender (E.164, e.g. `+14155238886` for sandbox)  
  Fallback: `WHATSAPP_PHONE_NUMBER` or `TWILIO_PHONE_NUMBER`

**Option B – Notification channel (DB)**  
Configure the `whatsapp` channel in `notification_settings` with provider `twilio` and encrypted config (`account_sid`, `auth_token`, `phone_number`). The service will use the dispatcher when the channel is enabled.

## Event types and usage

| Event | Function | When to call |
|-------|----------|-------------------------------|
| Appointment made | `send_appointment_made_whatsapp` | After patient creates appointment request (notify doctor) |
| Appointment approved | `send_appointment_approved_whatsapp` | After doctor accepts request (notify patient) |
| Amount paid | `send_appointment_amount_paid_whatsapp` | After payment success (notify patient) |
| Video in 15 mins | `send_video_appointment_reminder_15min_whatsapp` | From a cron/scheduler for appointments in 15 mins |
| Webinar in 15 mins | `send_webinar_reminder_15min_whatsapp` | From a cron/scheduler for webinars starting in 15 mins |

## Wiring

- **Appointment made / approved / amount paid**  
  Already called from `notification_helper` when sending email (doctor/patient phone required).

- **Video appointment in 15 mins**  
  Call from a scheduled job that finds appointments with `consultation_mode` = TELECONSULTATION (or video) and `appointment_date` + `start_time` in ~15 minutes, then call:

  `send_video_appointment_reminder_15min_whatsapp(to_phone=patient.phone, doctor_name=..., appointment_date=..., appointment_time=..., db=db)`

- **Webinar in 15 mins**  
  Call from a scheduled job that finds webinars with `webinar_date` + `start_time` in ~15 minutes, then call:

  `send_webinar_reminder_15min_whatsapp(to_phone=recipient_phone, webinar_title=..., start_time=..., db=db)`

## Phone numbers

Recipient numbers should be E.164 (e.g. `+1234567890`). The service adds `whatsapp:` when needed for Twilio.
