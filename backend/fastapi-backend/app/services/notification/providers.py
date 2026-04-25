"""
Notification provider interfaces and implementations
Abstract providers for SMS, Email, and WhatsApp with concrete implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger


class NotificationProvider(ABC):
    """Base class for all notification providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration
        
        Args:
            config: Provider-specific configuration (decrypted)
        """
        self.config = config
    
    @abstractmethod
    async def send(self, recipient: str, message: str, **kwargs) -> bool:
        """
        Send notification
        
        Args:
            recipient: Recipient identifier (phone, email, etc.)
            message: Message content
            **kwargs: Additional provider-specific parameters
        
        Returns:
            True if sent successfully
        
        Raises:
            Exception: If sending fails
        """
        pass
    
    def mask_recipient(self, recipient: str) -> str:
        """Mask recipient for logging (PHI protection)"""
        if not recipient or len(recipient) < 4:
            return "***"
        return recipient[:3] + "***"


class SmsProvider(NotificationProvider):
    """Abstract SMS provider"""
    
    @abstractmethod
    async def send(self, recipient: str, message: str, **kwargs) -> bool:
        """Send SMS message"""
        pass


class EmailProvider(NotificationProvider):
    """Abstract Email provider"""
    
    @abstractmethod
    async def send(self, recipient: str, message: str, subject: str = None, **kwargs) -> bool:
        """Send email message"""
        pass


class WhatsAppProvider(NotificationProvider):
    """Abstract WhatsApp provider"""
    
    @abstractmethod
    async def send(self, recipient: str, message: str, **kwargs) -> bool:
        """Send WhatsApp message"""
        pass


# ============================================================================
# CONCRETE IMPLEMENTATIONS
# ============================================================================


class TwilioSmsProvider(SmsProvider):
    """
    Twilio SMS provider
    
    Required config:
    - account_sid: Twilio account SID
    - auth_token: Twilio auth token
    - phone_number: Twilio phone number (from)
    """
    
    async def send(self, recipient: str, message: str, **kwargs) -> bool:
        """
        Send SMS via Twilio
        
        Args:
            recipient: Phone number (E.164 format recommended)
            message: SMS message content
        
        Returns:
            True if sent successfully
        """
        try:
            account_sid = self.config.get("account_sid")
            auth_token = self.config.get("auth_token")
            from_number = self.config.get("phone_number")
            
            if not all([account_sid, auth_token, from_number]):
                raise ValueError("Missing required Twilio configuration")
            
            # TODO: Implement actual Twilio API call
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(
            #     body=message,
            #     from_=from_number,
            #     to=recipient
            # )
            
            # STUB: Log instead of sending
            logger.info(
                f"[STUB] Twilio SMS to {self.mask_recipient(recipient)}: "
                f"from={from_number}, message_length={len(message)}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send Twilio SMS: {str(e)}")
            raise


class SendGridEmailProvider(EmailProvider):
    """
    SendGrid Email provider
    
    Required config:
    - api_key: SendGrid API key
    - from_email: Sender email address (must be verified in SendGrid)
    - from_name: Sender name (optional)
    """
    
    async def send(self, recipient: str, message: str, subject: str = None, **kwargs) -> bool:
        """
        Send email via SendGrid
        
        Args:
            recipient: Email address
            message: Email body (HTML supported)
            subject: Email subject
            **kwargs: Additional parameters:
                - html_content: HTML content (if different from message)
                - plain_content: Plain text content (optional)
                - reply_to: Reply-to email address (optional)
        
        Returns:
            True if sent successfully
        """
        try:
            api_key = self.config.get("api_key")
            from_email = self.config.get("from_email")
            from_name = self.config.get("from_name", "eClinic")
            
            if not all([api_key, from_email]):
                raise ValueError("Missing required SendGrid configuration")
            
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            # Create SendGrid client
            sg = SendGridAPIClient(api_key)
            
            # Prepare email
            from_email_obj = Email(from_email, from_name)
            to_email_obj = To(recipient)
            
            # Get HTML and plain text content
            html_content = kwargs.get("html_content", message)
            plain_content = kwargs.get("plain_content", None)
            
            # Create mail message
            mail = Mail(
                from_email=from_email_obj,
                to_emails=to_email_obj,
                subject=subject or "Notification from eClinic"
            )
            
            # Add HTML content
            mail.add_content(Content("text/html", html_content))
            
            # Add plain text content if provided
            if plain_content:
                mail.add_content(Content("text/plain", plain_content))
            
            # Add reply-to if provided
            if kwargs.get("reply_to"):
                mail.reply_to = Email(kwargs["reply_to"])
            
            # Send email
            response = sg.send(mail)
            
            # Check response status
            if response.status_code in [200, 201, 202]:
                logger.info(
                    f"SendGrid email sent to {self.mask_recipient(recipient)}: "
                    f"subject='{subject}', from={from_email}, status={response.status_code}"
                )
                # Also log the actual recipient for debugging (unmasked in debug mode)
                logger.debug(
                    f"SendGrid email details - recipient: {recipient}, "
                    f"subject: {subject}, from: {from_email}, status: {response.status_code}"
                )
                return True
            else:
                # Parse error response for better error messages
                error_body = "Unknown error"
                error_details = None
                
                try:
                    if response.body:
                        error_body = response.body.decode('utf-8')
                        # Try to parse JSON error response
                        import json
                        try:
                            error_json = json.loads(error_body)
                            if isinstance(error_json, dict):
                                errors = error_json.get('errors', [])
                                if errors:
                                    error_details = errors[0].get('message', error_body)
                                    error_body = error_details
                        except (json.JSONDecodeError, ValueError):
                            pass
                except Exception:
                    pass
                
                # Provide specific error messages for common issues
                error_message = f"SendGrid API error: {response.status_code}"
                if response.status_code == 403:
                    error_message = "SendGrid API error: 403 Forbidden. This usually means: 1) API key is invalid or missing 'Mail Send' permission, 2) From email address is not verified in SendGrid, or 3) API key has been revoked."
                elif response.status_code == 401:
                    error_message = "SendGrid API error: 401 Unauthorized. API key is invalid or missing."
                elif response.status_code == 400:
                    error_message = f"SendGrid API error: 400 Bad Request. {error_body}"
                else:
                    error_message = f"SendGrid API error: {response.status_code} - {error_body}"
                
                logger.error(f"SendGrid API error: status={response.status_code}, body={error_body}")
                raise Exception(error_message)
        
        except Exception as e:
            logger.error(f"Failed to send SendGrid email: {str(e)}")
            raise


class SmtpEmailProvider(EmailProvider):
    """
    SMTP Email provider
    
    Required config:
    - host: SMTP server host
    - port: SMTP server port
    - username: SMTP username
    - password: SMTP password
    - from_email: Sender email address
    - from_name: Sender name (optional)
    - use_tls: Use TLS (default: True)
    """
    
    async def send(self, recipient: str, message: str, subject: str = None, **kwargs) -> bool:
        """
        Send email via SMTP
        
        Args:
            recipient: Email address
            message: Email body (HTML supported)
            subject: Email subject
        
        Returns:
            True if sent successfully
        """
        try:
            host = self.config.get("host")
            port = self.config.get("port", 587)
            username = self.config.get("username")
            password = self.config.get("password")
            from_email = self.config.get("from_email")
            from_name = self.config.get("from_name", "eClinic")
            use_tls = self.config.get("use_tls", True)
            
            if not all([host, username, password, from_email]):
                raise ValueError("Missing required SMTP configuration")
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject or "Notification from eClinic"
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = recipient
            
            # Add HTML/text content
            html_part = MIMEText(message, "html")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(host, port) as server:
                if use_tls:
                    server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            logger.info(
                f"SMTP email sent to {self.mask_recipient(recipient)}: "
                f"subject='{subject}', from={from_email}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send SMTP email: {str(e)}")
            raise


class TwilioWhatsAppProvider(WhatsAppProvider):
    """
    Twilio WhatsApp provider
    
    Required config:
    - account_sid: Twilio account SID
    - auth_token: Twilio auth token
    - phone_number: Twilio WhatsApp-enabled phone number (E.164, e.g. +14155238886 for sandbox)
    """
    
    async def send(self, recipient: str, message: str, **kwargs) -> bool:
        """
        Send WhatsApp message via Twilio
        
        Args:
            recipient: WhatsApp phone number (E.164 format; whatsapp: prefix added if missing)
            message: WhatsApp message content (plain text; template not required for sandbox)
        
        Returns:
            True if sent successfully
        """
        try:
            account_sid = self.config.get("account_sid")
            auth_token = self.config.get("auth_token")
            from_number = self.config.get("phone_number")
            
            if not all([account_sid, auth_token, from_number]):
                raise ValueError("Missing required Twilio WhatsApp configuration")
            
            # E.164: ensure leading + for numbers
            def to_whatsapp_addr(phone: str) -> str:
                phone = (phone or "").strip()
                if not phone:
                    raise ValueError("Empty phone number")
                if phone.startswith("whatsapp:"):
                    return phone
                if not phone.startswith("+"):
                    phone = f"+{phone}"
                return f"whatsapp:{phone}"
            
            to_addr = to_whatsapp_addr(recipient)
            from_addr = to_whatsapp_addr(from_number)
            
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message,
                from_=from_addr,
                to=to_addr
            )
            
            logger.info(
                f"Twilio WhatsApp sent to {self.mask_recipient(recipient)}: "
                f"from={from_addr}, message_length={len(message)}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send Twilio WhatsApp: {str(e)}")
            raise


# ============================================================================
# PROVIDER REGISTRY
# ============================================================================


PROVIDER_REGISTRY: Dict[str, Dict[str, type]] = {
    "sms": {
        "twilio": TwilioSmsProvider,
    },
    "email": {
        "smtp": SmtpEmailProvider,
    },
    "whatsapp": {
        "twilio": TwilioWhatsAppProvider,
        "twilio_whatsapp": TwilioWhatsAppProvider,  # Alias
    },
}


def get_provider_class(channel: str, provider_name: str) -> Optional[type]:
    """
    Get provider class from registry
    
    Args:
        channel: Channel type (sms, email, whatsapp)
        provider_name: Provider name (twilio, smtp, etc.)
    
    Returns:
        Provider class or None if not found
    """
    channel_providers = PROVIDER_REGISTRY.get(channel.lower())
    if not channel_providers:
        return None
    
    return channel_providers.get(provider_name.lower())


def get_available_providers(channel: str) -> list[str]:
    """
    Get list of available providers for a channel
    
    Args:
        channel: Channel type
    
    Returns:
        List of provider names
    """
    channel_providers = PROVIDER_REGISTRY.get(channel.lower(), {})
    return list(channel_providers.keys())
