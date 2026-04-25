"""
Admin Notification Settings API Endpoints
Laravel-compatible routes for notification channel management
"""

from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.models.notification import NotificationSetting
from app.services.audit_service import AuditService
from app.schemas.notification import (
    NotificationChannelResponse,
    NotificationChannelListResponse,
    NotificationChannelSingleResponse,
    NotificationChannelUpdate,
    NotificationChannelToggle,
    NotificationKeyRotation,
    SmtpConfigUpdate
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    laravel_response
)
from app.utils.encryption import get_encryption_service, EncryptionService
from loguru import logger


router = APIRouter(prefix="/admin/notifications", tags=["Admin - Notifications"])


def _create_audit_log(
    db: Session,
    user: User,
    action: str,
    channel: str,
    request: Request,
    metadata: dict = None
):
    """
    Create audit log entry for notification operations (HIPAA FIX 4: Use AuditService)
    
    Args:
        db: Database session
        user: Current user
        action: Action type
        channel: Notification channel
        request: HTTP request
        metadata: Additional metadata (masked)
    """
    try:
        audit_service = AuditService(db)
        
        # Extract IP address
        ip_address = None
        if request.client:
            ip_address = request.client.host
        # Check X-Forwarded-For header (if behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        
        # Extract user agent
        user_agent = request.headers.get("user-agent")
        
        # Create audit log using AuditService
        audit_service.create_audit_log(
            actor_user_id=user.id,
            action=action,
            entity_type="notification_settings",
            entity_id=None,
            audit_metadata=metadata or {"channel": channel},
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        # Don't fail the operation if audit logging fails


def _format_channel_response(
    setting: NotificationSetting,
    encryption_service: EncryptionService = None
) -> NotificationChannelResponse:
    """
    Format notification setting to response schema
    
    Args:
        setting: NotificationSetting model
        encryption_service: Encryption service (for checking config)
    
    Returns:
        NotificationChannelResponse
    """
    return NotificationChannelResponse(
        id=setting.id,
        channel=setting.channel,
        enabled=setting.enabled,
        provider=setting.provider,
        has_config=bool(setting.config_encrypted),
        updated_by=setting.updated_by,
        updated_at=setting.updated_at,
        created_at=setting.created_at
    )


@router.get(
    "",
    response_model=NotificationChannelListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all notification channels",
    description="Retrieve all notification channel settings (Admin only)"
)
async def get_notification_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Get all notification channel settings
    
    **Admin only endpoint**
    
    Returns:
        List of notification channels with their configurations (keys masked)
    """
    try:
        # Get all notification settings
        settings = db.query(NotificationSetting).filter(
            NotificationSetting.deleted_at.is_(None)
        ).order_by(NotificationSetting.channel).all()
        
        # Format response
        data = [
            _format_channel_response(setting, encryption_service)
            for setting in settings
        ]
        
        return NotificationChannelListResponse(
            success=True,
            message="Notification channels retrieved successfully",
            data=data,
            errors=None
        )
    
    except Exception as e:
        logger.error(f"Failed to retrieve notification channels: {str(e)}")
        raise


@router.put(
    "/{channel}",
    response_model=NotificationChannelSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update notification channel",
    description="Update notification channel settings (Admin only)"
)
async def update_notification_channel(
    channel: str,
    data: NotificationChannelUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Update notification channel settings
    
    **Admin only endpoint**
    
    **Laravel compatible:**
    - Same endpoint path: PUT /admin/notifications/{channel}
    - Same request payload structure
    - Same response format
    - Same status codes
    
    Args:
        channel: Channel name (sms, email, whatsapp)
        data: Update data (enabled, provider, config)
    
    Returns:
        Updated notification channel settings
    """
    try:
        # Validate channel
        channel = channel.lower().strip()
        if channel not in ["sms", "email", "whatsapp"]:
            raise ValidationException(
                message="Invalid channel",
                errors={"channel": [f"Channel must be one of: sms, email, whatsapp"]}
            )
        
        # Get or create notification setting
        setting = db.query(NotificationSetting).filter(
            NotificationSetting.channel == channel,
            NotificationSetting.deleted_at.is_(None)
        ).first()
        
        if not setting:
            # Create new setting
            setting = NotificationSetting(
                channel=channel,
                enabled=False,
                provider=None,
                config_encrypted=None
            )
            db.add(setting)
        
        # Track changes for audit
        changes = {}
        
        # Update enabled status
        if data.enabled is not None and data.enabled != setting.enabled:
            changes["enabled"] = {"old": setting.enabled, "new": data.enabled}
            setting.enabled = data.enabled
        
        # Update provider
        if data.provider is not None and data.provider != setting.provider:
            changes["provider"] = {"old": setting.provider, "new": data.provider}
            setting.provider = data.provider
        
        # Update and encrypt configuration
        if data.config is not None:
            # Mask config for audit
            masked_config = encryption_service.mask_config(data.config)
            changes["config"] = {"updated": True, "masked": masked_config}
            
            # Encrypt configuration
            encrypted_data = encryption_service.encrypt(data.config)
            setting.config_encrypted = {"encrypted_data": encrypted_data}
        
        # Update metadata
        setting.updated_by = current_user.id
        
        # Save changes
        db.commit()
        db.refresh(setting)
        
        # Create audit log
        action = "NOTIFICATION_PROVIDER_UPDATED" if changes else "NOTIFICATION_SETTINGS_VIEWED"
        _create_audit_log(
            db=db,
            user=current_user,
            action=action,
            channel=channel,
            request=request,
            metadata={"changes": changes}
        )
        
        logger.info(
            f"Admin {current_user.id} updated notification channel '{channel}': {changes}"
        )
        
        return NotificationChannelSingleResponse(
            success=True,
            message=f"Notification channel '{channel}' updated successfully",
            data=_format_channel_response(setting, encryption_service),
            errors=None
        )
    
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification channel: {str(e)}")
        raise


@router.post(
    "/{channel}/rotate-keys",
    response_model=NotificationChannelSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate provider keys",
    description="Rotate provider API keys/credentials (Admin only)"
)
async def rotate_notification_keys(
    channel: str,
    data: NotificationKeyRotation,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Rotate provider keys for a notification channel
    
    **Admin only endpoint**
    
    **Laravel compatible:**
    - Same endpoint path: POST /admin/notifications/{channel}/rotate-keys
    - Same request payload structure
    - Same response format
    
    This overwrites existing keys with new ones.
    
    Args:
        channel: Channel name (sms, email, whatsapp)
        data: New provider configuration
    
    Returns:
        Updated notification channel settings
    """
    try:
        # Validate channel
        channel = channel.lower().strip()
        if channel not in ["sms", "email", "whatsapp"]:
            raise ValidationException(
                message="Invalid channel",
                errors={"channel": [f"Channel must be one of: sms, email, whatsapp"]}
            )
        
        # Get notification setting
        setting = db.query(NotificationSetting).filter(
            NotificationSetting.channel == channel,
            NotificationSetting.deleted_at.is_(None)
        ).first()
        
        if not setting:
            raise NotFoundException(
                message=f"Notification channel '{channel}' not found",
                errors={"channel": [f"Channel '{channel}' has not been configured yet"]}
            )
        
        # Mask config for audit
        masked_config = encryption_service.mask_config(data.config)
        
        # Encrypt new configuration
        encrypted_data = encryption_service.encrypt(data.config)
        setting.config_encrypted = {"encrypted_data": encrypted_data}
        
        # Update metadata
        setting.updated_by = current_user.id
        
        # Save changes
        db.commit()
        db.refresh(setting)
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="NOTIFICATION_KEYS_ROTATED",
            channel=channel,
            request=request,
            metadata={"masked_config": masked_config}
        )
        
        logger.info(
            f"Admin {current_user.id} rotated keys for notification channel '{channel}'"
        )
        
        return NotificationChannelSingleResponse(
            success=True,
            message=f"Keys rotated successfully for channel '{channel}'",
            data=_format_channel_response(setting, encryption_service),
            errors=None
        )
    
    except (ValidationException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Failed to rotate notification keys: {str(e)}")
        raise


@router.patch(
    "/{channel}/toggle",
    response_model=NotificationChannelSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle notification channel",
    description="Enable or disable a notification channel (Admin only)"
)
async def toggle_notification_channel(
    channel: str,
    data: NotificationChannelToggle,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Toggle notification channel on/off
    
    **Admin only endpoint**
    
    **Laravel compatible:**
    - Same endpoint path: PATCH /admin/notifications/{channel}/toggle
    - Same request payload structure
    - Same response format
    
    When disabled, all notifications for this channel will be blocked immediately.
    
    Args:
        channel: Channel name (sms, email, whatsapp)
        data: Toggle data (enabled: true/false)
    
    Returns:
        Updated notification channel settings
    """
    try:
        # Validate channel
        channel = channel.lower().strip()
        if channel not in ["sms", "email", "whatsapp"]:
            raise ValidationException(
                message="Invalid channel",
                errors={"channel": [f"Channel must be one of: sms, email, whatsapp"]}
            )
        
        # Get notification setting
        setting = db.query(NotificationSetting).filter(
            NotificationSetting.channel == channel,
            NotificationSetting.deleted_at.is_(None)
        ).first()
        
        if not setting:
            # Create new setting if doesn't exist
            setting = NotificationSetting(
                channel=channel,
                enabled=data.enabled,
                provider=None,
                config_encrypted=None
            )
            db.add(setting)
        else:
            # Update enabled status
            setting.enabled = data.enabled
        
        # Update metadata
        setting.updated_by = current_user.id
        
        # Save changes
        db.commit()
        db.refresh(setting)
        
        # Create audit log
        action = "NOTIFICATION_CHANNEL_ENABLED" if data.enabled else "NOTIFICATION_CHANNEL_DISABLED"
        _create_audit_log(
            db=db,
            user=current_user,
            action=action,
            channel=channel,
            request=request,
            metadata={"enabled": data.enabled}
        )
        
        status_text = "enabled" if data.enabled else "disabled"
        logger.info(
            f"Admin {current_user.id} {status_text} notification channel '{channel}'"
        )
        
        return NotificationChannelSingleResponse(
            success=True,
            message=f"Notification channel '{channel}' {status_text} successfully",
            data=_format_channel_response(setting, encryption_service),
            errors=None
        )
    
    except (ValidationException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Failed to toggle notification channel: {str(e)}")
        raise


@router.put(
    "/email/smtp",
    response_model=NotificationChannelSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update SMTP email configuration",
    description="Update SMTP email settings with validation (Admin only)"
)
async def update_smtp_config(
    data: SmtpConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Update SMTP email configuration
    
    **Admin only endpoint**
    
    **Dedicated SMTP endpoint:**
    - Validates all required SMTP fields
    - Provides clear error messages
    - Encrypts credentials before storage
    - Creates audit log entry
    
    **Laravel compatible:**
    - PUT /admin/notifications/email/smtp
    
    Request body:
    - **enabled**: Enable/disable email notifications (optional)
    - **host**: SMTP server host (required, e.g., smtp.gmail.com)
    - **port**: SMTP server port (required, e.g., 587, 465, 2525)
    - **username**: SMTP username/email (required)
    - **password**: SMTP password or app password (required)
    - **from_email**: Sender email address (required)
    - **from_name**: Sender display name (optional, default: "eClinic")
    - **use_tls**: Use TLS encryption (optional, default: true)
    
    Returns:
        Updated notification channel settings
    """
    try:
        channel = "email"
        
        # Get or create notification setting
        setting = db.query(NotificationSetting).filter(
            NotificationSetting.channel == channel,
            NotificationSetting.deleted_at.is_(None)
        ).first()
        
        if not setting:
            # Create new setting
            setting = NotificationSetting(
                channel=channel,
                enabled=data.enabled if data.enabled is not None else False,
                provider="smtp",
                config_encrypted=None
            )
            db.add(setting)
        
        # Track changes for audit
        changes = {}
        
        # Update enabled status
        if data.enabled is not None and data.enabled != setting.enabled:
            changes["enabled"] = {"old": setting.enabled, "new": data.enabled}
            setting.enabled = data.enabled
        
        # Set provider to smtp
        if setting.provider != "smtp":
            changes["provider"] = {"old": setting.provider, "new": "smtp"}
            setting.provider = "smtp"
        
        # Build SMTP configuration
        smtp_config = {
            "host": data.host,
            "port": data.port,
            "username": data.username,
            "password": data.password,
            "from_email": data.from_email,
            "from_name": data.from_name or "eClinic",
            "use_tls": data.use_tls if data.use_tls is not None else True
        }
        
        # Mask config for audit (hide sensitive values)
        masked_config = {
            "host": smtp_config["host"],
            "port": smtp_config["port"],
            "username": smtp_config["username"][:3] + "***" if len(smtp_config["username"]) > 3 else "***",
            "password": "***",
            "from_email": smtp_config["from_email"],
            "from_name": smtp_config["from_name"],
            "use_tls": smtp_config["use_tls"]
        }
        changes["config"] = {"updated": True, "masked": masked_config}
        
        # Encrypt configuration
        encrypted_data = encryption_service.encrypt(smtp_config)
        setting.config_encrypted = {"encrypted_data": encrypted_data}
        
        # Update metadata
        setting.updated_by = current_user.id
        
        # Save changes
        db.commit()
        db.refresh(setting)
        
        # Create audit log
        _create_audit_log(
            db=db,
            user=current_user,
            action="SMTP_CONFIG_UPDATED",
            channel=channel,
            request=request,
            metadata={"changes": changes}
        )
        
        logger.info(
            f"Admin {current_user.id} updated SMTP configuration for email channel"
        )
        
        return NotificationChannelSingleResponse(
            success=True,
            message="SMTP configuration updated successfully",
            data=_format_channel_response(setting, encryption_service),
            errors=None
        )
    
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Failed to update SMTP configuration: {str(e)}")
        raise
