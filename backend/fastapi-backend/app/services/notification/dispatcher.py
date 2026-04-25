"""
Central Notification Dispatcher Service
Handles notification routing with channel enforcement and provider management
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from app.models.notification import NotificationSetting
from app.services.notification.providers import (
    get_provider_class,
    NotificationProvider
)
from app.utils.encryption import EncryptionService
from app.core.exceptions import (
    NotificationChannelDisabledError,
    NotificationProviderNotConfiguredError,
    NotificationSendError
)


class NotificationDispatcher:
    """
    Central notification dispatcher
    
    Responsibilities:
    - Receive notification requests
    - Check clinic-level channel enablement
    - Abort if disabled
    - Route to provider implementation
    - Mask sensitive values in logs
    - Raise controlled exceptions
    
    Security:
    - All provider keys are encrypted in database
    - Decrypted only in-memory when needed
    - Sensitive values masked in all logs
    """
    
    def __init__(self, db: Session, encryption_service: EncryptionService):
        """
        Initialize dispatcher
        
        Args:
            db: Database session
            encryption_service: Encryption service for decrypting provider configs
        """
        self.db = db
        self.encryption_service = encryption_service
    
    def _get_channel_settings(self, channel: str) -> Optional[NotificationSetting]:
        """
        Get notification settings for a channel
        
        Args:
            channel: Channel name (sms, email, whatsapp)
        
        Returns:
            NotificationSetting or None if not found
        """
        return self.db.query(NotificationSetting).filter(
            NotificationSetting.channel == channel.lower(),
            NotificationSetting.deleted_at.is_(None)
        ).first()
    
    def _decrypt_provider_config(self, encrypted_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt provider configuration
        
        Args:
            encrypted_config: Encrypted configuration from database
        
        Returns:
            Decrypted configuration dictionary
        
        Raises:
            ValueError: If decryption fails
        """
        try:
            # The encrypted_config is stored as JSONB with encrypted values
            # We need to decrypt each encrypted field
            if not encrypted_config or "encrypted_data" not in encrypted_config:
                return {}
            
            encrypted_data = encrypted_config["encrypted_data"]
            decrypted_config = self.encryption_service.decrypt(encrypted_data)
            
            return decrypted_config
        
        except Exception as e:
            logger.error(f"Failed to decrypt provider config: {str(e)}")
            raise ValueError("Invalid encrypted configuration")
    
    def _get_provider_instance(
        self,
        channel: str,
        provider_name: str,
        config: Dict[str, Any]
    ) -> NotificationProvider:
        """
        Get provider instance
        
        Args:
            channel: Channel name
            provider_name: Provider name
            config: Decrypted provider configuration
        
        Returns:
            Provider instance
        
        Raises:
            NotificationProviderNotConfiguredError: If provider not found
        """
        provider_class = get_provider_class(channel, provider_name)
        
        if not provider_class:
            raise NotificationProviderNotConfiguredError(
                f"Provider '{provider_name}' not found for channel '{channel}'"
            )
        
        return provider_class(config)
    
    async def send_sms(
        self,
        phone: str,
        message: str,
        clinic_id: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Send SMS notification
        
        Args:
            phone: Phone number
            message: SMS message
            clinic_id: Clinic ID (for future multi-clinic support)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            True if sent successfully
        
        Raises:
            NotificationChannelDisabledError: If SMS is disabled
            NotificationProviderNotConfiguredError: If provider not configured
            NotificationSendError: If sending fails
        """
        return await self._dispatch_notification(
            channel="sms",
            recipient=phone,
            message=message,
            clinic_id=clinic_id,
            **kwargs
        )
    
    async def send_email(
        self,
        email: str,
        message: str,
        subject: str = None,
        clinic_id: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Send email notification
        
        Args:
            email: Email address
            message: Email body (HTML supported)
            subject: Email subject
            clinic_id: Clinic ID (for future multi-clinic support)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            True if sent successfully
        
        Raises:
            NotificationChannelDisabledError: If email is disabled
            NotificationProviderNotConfiguredError: If provider not configured
            NotificationSendError: If sending fails
        """
        return await self._dispatch_notification(
            channel="email",
            recipient=email,
            message=message,
            clinic_id=clinic_id,
            subject=subject,
            **kwargs
        )
    
    async def send_whatsapp(
        self,
        phone: str,
        message: str,
        clinic_id: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Send WhatsApp notification
        
        Args:
            phone: WhatsApp phone number
            message: WhatsApp message
            clinic_id: Clinic ID (for future multi-clinic support)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            True if sent successfully
        
        Raises:
            NotificationChannelDisabledError: If WhatsApp is disabled
            NotificationProviderNotConfiguredError: If provider not configured
            NotificationSendError: If sending fails
        """
        return await self._dispatch_notification(
            channel="whatsapp",
            recipient=phone,
            message=message,
            clinic_id=clinic_id,
            **kwargs
        )
    
    async def _dispatch_notification(
        self,
        channel: str,
        recipient: str,
        message: str,
        clinic_id: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Internal method to dispatch notification
        
        Args:
            channel: Channel name (sms, email, whatsapp)
            recipient: Recipient identifier
            message: Message content
            clinic_id: Clinic ID (for future multi-clinic support)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            True if sent successfully
        
        Raises:
            NotificationChannelDisabledError: If channel is disabled
            NotificationProviderNotConfiguredError: If provider not configured
            NotificationSendError: If sending fails
        """
        try:
            # Get channel settings
            settings = self._get_channel_settings(channel)
            
            if not settings:
                raise NotificationProviderNotConfiguredError(
                    f"Channel '{channel}' not configured"
                )
            
            # Check if channel is enabled
            if not settings.enabled:
                logger.warning(
                    f"Notification channel '{channel}' is disabled. "
                    f"Notification to {self._mask_recipient(recipient)} aborted."
                )
                raise NotificationChannelDisabledError(
                    f"Notification channel '{channel}' is currently disabled"
                )
            
            # Check if provider is configured
            if not settings.provider:
                raise NotificationProviderNotConfiguredError(
                    f"No provider configured for channel '{channel}'"
                )
            
            # Decrypt provider configuration
            if not settings.config_encrypted:
                raise NotificationProviderNotConfiguredError(
                    f"Provider configuration missing for channel '{channel}'"
                )
            
            decrypted_config = self._decrypt_provider_config(settings.config_encrypted)
            
            # Get provider instance
            provider = self._get_provider_instance(
                channel=channel,
                provider_name=settings.provider,
                config=decrypted_config
            )
            
            # Log dispatch (with masked recipient)
            logger.info(
                f"Dispatching {channel} notification via {settings.provider} "
                f"to {self._mask_recipient(recipient)}"
            )
            
            # Send notification
            result = await provider.send(recipient=recipient, message=message, **kwargs)
            
            if result:
                logger.info(
                    f"Successfully sent {channel} notification to "
                    f"{self._mask_recipient(recipient)}"
                )
            else:
                logger.error(
                    f"Failed to send {channel} notification to "
                    f"{self._mask_recipient(recipient)}"
                )
            
            return result
        
        except (NotificationChannelDisabledError, NotificationProviderNotConfiguredError):
            # Re-raise controlled exceptions
            raise
        
        except Exception as e:
            logger.error(
                f"Notification dispatch failed for channel '{channel}': {str(e)}"
            )
            raise NotificationSendError(
                f"Failed to send {channel} notification: {str(e)}"
            ) from e
    
    def _mask_recipient(self, recipient: str) -> str:
        """
        Mask recipient for logging (PHI protection)
        
        Args:
            recipient: Recipient identifier
        
        Returns:
            Masked string
        """
        if not recipient or len(recipient) < 4:
            return "***"
        return recipient[:3] + "***"
    
    def is_channel_enabled(self, channel: str) -> bool:
        """
        Check if a notification channel is enabled
        
        Args:
            channel: Channel name (sms, email, whatsapp)
        
        Returns:
            True if channel is enabled and configured
        """
        settings = self._get_channel_settings(channel)
        return settings is not None and settings.enabled


# Global dispatcher instance (initialized per request with DB session)
def get_notification_dispatcher(
    db: Session,
    encryption_service: Optional[EncryptionService] = None
) -> NotificationDispatcher:
    """
    Get notification dispatcher instance (for dependency injection)
    
    Args:
        db: Database session
        encryption_service: Encryption service (optional)
    
    Returns:
        NotificationDispatcher instance
    """
    if encryption_service is None:
        from app.utils.encryption import get_encryption_service
        encryption_service = get_encryption_service()
    
    return NotificationDispatcher(db=db, encryption_service=encryption_service)
