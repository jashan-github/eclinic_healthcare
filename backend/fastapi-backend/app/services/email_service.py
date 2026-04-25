"""
Email Service
Service for sending emails using SendGrid
"""

from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from app.core.config import settings
from app.services.notification.providers import SendGridEmailProvider


class EmailService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        """Initialize email service with SendGrid provider"""
        if not settings.SENDGRID_API_KEY:
            raise ValueError("SendGrid API key not configured. Please set SENDGRID_API_KEY in environment variables.")
        
        from_email = settings.SENDGRID_FROM_EMAIL or settings.SMTP_FROM_EMAIL
        if not from_email:
            raise ValueError("SendGrid from email not configured. Please set SENDGRID_FROM_EMAIL in environment variables.")
        
        self.provider = SendGridEmailProvider({
            "api_key": settings.SENDGRID_API_KEY,
            "from_email": from_email,
            "from_name": settings.SENDGRID_FROM_NAME or settings.SMTP_FROM_NAME
        })
    
    async def send_reset_password_email(
        self,
        recipient_email: str,
        recipient_name: str,
        reset_token: str,
        reset_url: Optional[str] = None
    ) -> bool:
        """
        Send password reset email
        
        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            reset_token: Password reset token
            reset_url: Full reset URL (if None, will be constructed from BASE_URL)
        
        Returns:
            True if sent successfully
        """
        try:
            # Construct reset URL if not provided
            if not reset_url:
                base_url = settings.BASE_URL.rstrip('/')
                reset_url = f"{base_url}/reset-password?token={reset_token}"
            
            # Email subject
            subject = "Reset Your Password - eClinic"
            
            # Email HTML content
            html_content = self._get_reset_password_template(
                recipient_name=recipient_name,
                reset_url=reset_url
            )
            
            # Plain text content
            plain_content = f"""
Hello {recipient_name},

You requested to reset your password for your eClinic account.

Click the following link to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
eClinic Team
"""
            
            # Send email
            return await self.provider.send(
                recipient=recipient_email,
                message=html_content,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content
            )
        
        except Exception as e:
            logger.error(f"Failed to send reset password email: {str(e)}")
            raise
    
    async def send_new_appointment_email(
        self,
        recipient_email: str,
        recipient_name: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        service_name: str,
        consultation_mode: str,
        appointment_id: Optional[str] = None
    ) -> bool:
        """
        Send new appointment notification email
        
        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            doctor_name: Doctor name
            appointment_date: Appointment date (formatted string)
            appointment_time: Appointment time (formatted string)
            service_name: Service name
            consultation_mode: Consultation mode (IN_CLINIC or TELECONSULTATION)
            appointment_id: Appointment ID (optional)
        
        Returns:
            True if sent successfully
        """
        try:
            # Email subject
            subject = f"New Appointment Scheduled - {service_name}"
            
            # Email HTML content
            html_content = self._get_new_appointment_template(
                recipient_name=recipient_name,
                doctor_name=doctor_name,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                service_name=service_name,
                consultation_mode=consultation_mode,
                appointment_id=appointment_id
            )
            
            # Plain text content
            mode_text = "In-Clinic Visit" if consultation_mode == "IN_CLINIC" else "Teleconsultation"
            plain_content = f"""
Hello {recipient_name},

A new appointment has been scheduled for you.

Appointment Details:
- Doctor: {doctor_name}
- Service: {service_name}
- Date: {appointment_date}
- Time: {appointment_time}
- Mode: {mode_text}

Please make sure to arrive on time or be ready for your teleconsultation.

Best regards,
eClinic Team
"""
            
            # Send email
            return await self.provider.send(
                recipient=recipient_email,
                message=html_content,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content
            )
        
        except Exception as e:
            logger.error(f"Failed to send new appointment email: {str(e)}")
            raise
    
    async def send_appointment_confirmed_email(
        self,
        recipient_email: str,
        recipient_name: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        service_name: str,
        consultation_mode: str,
        appointment_id: Optional[str] = None
    ) -> bool:
        """
        Send appointment confirmed email
        
        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            doctor_name: Doctor name
            appointment_date: Appointment date (formatted string)
            appointment_time: Appointment time (formatted string)
            service_name: Service name
            consultation_mode: Consultation mode (IN_CLINIC or TELECONSULTATION)
            appointment_id: Appointment ID (optional)
        
        Returns:
            True if sent successfully
        """
        try:
            # Email subject
            subject = f"Appointment Confirmed - {service_name}"
            
            # Email HTML content
            html_content = self._get_appointment_confirmed_template(
                recipient_name=recipient_name,
                doctor_name=doctor_name,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                service_name=service_name,
                consultation_mode=consultation_mode,
                appointment_id=appointment_id
            )
            
            # Plain text content
            mode_text = "In-Clinic Visit" if consultation_mode == "IN_CLINIC" else "Teleconsultation"
            plain_content = f"""
Hello {recipient_name},

Your appointment has been confirmed!

Appointment Details:
- Doctor: {doctor_name}
- Service: {service_name}
- Date: {appointment_date}
- Time: {appointment_time}
- Mode: {mode_text}

Your appointment is confirmed and ready. Please make sure to arrive on time or be ready for your teleconsultation.

Best regards,
eClinic Team
"""
            
            # Send email
            return await self.provider.send(
                recipient=recipient_email,
                message=html_content,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content
            )
        
        except Exception as e:
            logger.error(f"Failed to send appointment confirmed email: {str(e)}")
            raise
    
    async def send_appointment_rejected_email(
        self,
        recipient_email: str,
        recipient_name: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        service_name: str,
        rejection_reason: Optional[str] = None,
        appointment_id: Optional[str] = None
    ) -> bool:
        """
        Send appointment rejected email to patient
        
        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            doctor_name: Doctor name
            appointment_date: Appointment date (formatted string)
            appointment_time: Appointment time (formatted string)
            service_name: Service name
            rejection_reason: Optional rejection reason
            appointment_id: Appointment ID (optional)
        
        Returns:
            True if sent successfully
        """
        try:
            # Email subject
            subject = "Appointment Request Rejected"
            
            # Email HTML content
            html_content = self._get_appointment_rejected_template(
                recipient_name=recipient_name,
                doctor_name=doctor_name,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                service_name=service_name,
                rejection_reason=rejection_reason,
                appointment_id=appointment_id
            )
            
            # Plain text content
            reason_text = f"\nReason: {rejection_reason}" if rejection_reason else ""
            plain_content = f"""
Hello {recipient_name},

Unfortunately, your appointment request has been rejected.

Appointment Details:
- Doctor: {doctor_name}
- Service: {service_name}
- Date: {appointment_date}
- Time: {appointment_time}{reason_text}

Please select another time slot or contact us for assistance.

Best regards,
eClinic Team
"""
            
            # Send email
            return await self.provider.send(
                recipient=recipient_email,
                message=html_content,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content
            )
        
        except Exception as e:
            logger.error(f"Failed to send appointment rejected email: {str(e)}")
            raise
    
    def _get_reset_password_template(
        self,
        recipient_name: str,
        reset_url: str
    ) -> str:
        """Generate reset password email HTML template"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
        <h2 style="color: #2c3e50;">Reset Your Password</h2>
        <p>Hello {recipient_name},</p>
        <p>You requested to reset your password for your eClinic account.</p>
        <p>Click the button below to reset your password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
        </div>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #7f8c8d;">{reset_url}</p>
        <p><strong>This link will expire in 1 hour.</strong></p>
        <p>If you did not request this password reset, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">Best regards,<br>eClinic Team</p>
    </div>
</body>
</html>
"""
    
    def _get_new_appointment_template(
        self,
        recipient_name: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        service_name: str,
        consultation_mode: str,
        appointment_id: Optional[str] = None
    ) -> str:
        """Generate new appointment email HTML template"""
        mode_text = "In-Clinic Visit" if consultation_mode == "IN_CLINIC" else "Teleconsultation"
        mode_badge_color = "#27ae60" if consultation_mode == "IN_CLINIC" else "#3498db"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Appointment Scheduled</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
        <h2 style="color: #2c3e50;">New Appointment Scheduled</h2>
        <p>Hello {recipient_name},</p>
        <p>A new appointment has been scheduled for you.</p>
        <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #2c3e50; margin-top: 0;">Appointment Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; width: 120px;">Doctor:</td>
                    <td style="padding: 8px 0;">{doctor_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Service:</td>
                    <td style="padding: 8px 0;">{service_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Date:</td>
                    <td style="padding: 8px 0;">{appointment_date}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Time:</td>
                    <td style="padding: 8px 0;">{appointment_time}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Mode:</td>
                    <td style="padding: 8px 0;">
                        <span style="background-color: {mode_badge_color}; color: white; padding: 4px 12px; border-radius: 3px; font-size: 12px;">{mode_text}</span>
                    </td>
                </tr>
            </table>
        </div>
        <p>Please make sure to arrive on time or be ready for your teleconsultation.</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">Best regards,<br>eClinic Team</p>
    </div>
</body>
</html>
"""
    
    def _get_appointment_confirmed_template(
        self,
        recipient_name: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        service_name: str,
        consultation_mode: str,
        appointment_id: Optional[str] = None
    ) -> str:
        """Generate appointment confirmed email HTML template"""
        mode_text = "In-Clinic Visit" if consultation_mode == "IN_CLINIC" else "Teleconsultation"
        mode_badge_color = "#27ae60" if consultation_mode == "IN_CLINIC" else "#3498db"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Confirmed</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
        <h2 style="color: #27ae60;">✓ Appointment Confirmed</h2>
        <p>Hello {recipient_name},</p>
        <p>Your appointment has been confirmed!</p>
        <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #27ae60;">
            <h3 style="color: #2c3e50; margin-top: 0;">Appointment Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; width: 120px;">Doctor:</td>
                    <td style="padding: 8px 0;">{doctor_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Service:</td>
                    <td style="padding: 8px 0;">{service_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Date:</td>
                    <td style="padding: 8px 0;">{appointment_date}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Time:</td>
                    <td style="padding: 8px 0;">{appointment_time}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Mode:</td>
                    <td style="padding: 8px 0;">
                        <span style="background-color: {mode_badge_color}; color: white; padding: 4px 12px; border-radius: 3px; font-size: 12px;">{mode_text}</span>
                    </td>
                </tr>
            </table>
        </div>
        <p>Your appointment is confirmed and ready. Please make sure to arrive on time or be ready for your teleconsultation.</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">Best regards,<br>eClinic Team</p>
    </div>
</body>
</html>
"""
    
    def _get_appointment_rejected_template(
        self,
        recipient_name: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        service_name: str,
        rejection_reason: Optional[str] = None,
        appointment_id: Optional[str] = None
    ) -> str:
        """Generate appointment rejected email HTML template"""
        reason_html = ""
        if rejection_reason:
            reason_html = f"""
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Reason:</td>
                    <td style="padding: 8px 0; color: #7f8c8d;">{rejection_reason}</td>
                </tr>"""
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Request Rejected</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
        <h2 style="color: #e74c3c;">Appointment Request Rejected</h2>
        <p>Hello {recipient_name},</p>
        <p>Unfortunately, your appointment request has been rejected.</p>
        <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #e74c3c;">
            <h3 style="color: #2c3e50; margin-top: 0;">Appointment Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; width: 120px;">Doctor:</td>
                    <td style="padding: 8px 0;">{doctor_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Service:</td>
                    <td style="padding: 8px 0;">{service_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Date:</td>
                    <td style="padding: 8px 0;">{appointment_date}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Time:</td>
                    <td style="padding: 8px 0;">{appointment_time}</td>
                </tr>{reason_html}
            </table>
        </div>
        <p>Please select another time slot or contact us for assistance.</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">Best regards,<br>eClinic Team</p>
    </div>
</body>
</html>
"""
