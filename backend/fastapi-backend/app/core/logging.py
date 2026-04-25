"""
Structured JSON logging with PHI protection
HIPAA-compliant logging that redacts sensitive health information
"""

import sys
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union
from uuid import UUID
from pathlib import Path

from loguru import logger

from app.core.config import settings


class PHIFilter:
    """Filter to redact PHI (Protected Health Information) from logs"""
    
    def __init__(self, phi_fields: list[str]):
        self.phi_fields = [field.lower() for field in phi_fields]
    
    def redact_phi(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact PHI from log records"""
        if isinstance(record, dict):
            return {
                key: self._redact_value(key, value)
                for key, value in record.items()
            }
        return record
    
    def _redact_value(self, key: str, value: Any) -> Any:
        """Redact value if key matches PHI field"""
        if isinstance(key, str) and key.lower() in self.phi_fields:
            return "***REDACTED***"
        
        if isinstance(value, dict):
            return self.redact_phi(value)
        
        if isinstance(value, list):
            return [
                self.redact_phi(item) if isinstance(item, dict) else item
                for item in value
            ]
        
        return value


class StructuredLogger:
    """Structured logger with JSON formatting and PHI protection"""
    
    def __init__(self):
        self.phi_filter = PHIFilter(settings.PHI_FIELDS)
        self._configure_logger()
    
    def _configure_logger(self):
        """Configure loguru logger"""
        # Remove default logger
        logger.remove()
        
        # Text formatter for development (use format string, not function)
        text_format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>\n"
        )
        
        # JSON format string for console (simpler than custom formatter)
        json_format_string = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}\n"
        
        # Choose formatter
        formatter = json_format_string if settings.LOG_FORMAT == "json" else text_format_string
        
        # Console handler
        logger.add(
            sys.stdout,
            format=formatter,
            level=settings.LOG_LEVEL,
            colorize=settings.LOG_FORMAT == "text",
            backtrace=settings.DEBUG,
            diagnose=settings.DEBUG,
        )
        
        # File handler (optional)
        if settings.LOG_FILE_PATH:
            log_path = Path(settings.LOG_FILE_PATH)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use serialize=True for JSON output (loguru's built-in JSON serialization)
            # This is more reliable than custom formatters
            logger.add(
                settings.LOG_FILE_PATH,
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
                serialize=True,  # Output as JSON lines
                level=settings.LOG_LEVEL,
                rotation=settings.LOG_ROTATION,
                retention=settings.LOG_RETENTION,
                compression="gz",
                backtrace=True,
                diagnose=settings.DEBUG,
            )
    
    def bind(self, **kwargs) -> Any:
        """Bind context to logger"""
        filtered_kwargs = self.phi_filter.redact_phi(kwargs)
        return logger.bind(**filtered_kwargs)
    
    def log(self, level: str, message: str, **kwargs):
        """Log with PHI filtering"""
        filtered_kwargs = self.phi_filter.redact_phi(kwargs)
        logger.bind(**filtered_kwargs).log(level, message)


# Global logger instance
structured_logger = StructuredLogger()


def get_logger():
    """Get logger instance (for dependency injection)"""
    return logger


def log_phi_access(
    user_id: Union[str, UUID],
    resource_type: str,
    resource_id: Union[str, UUID],
    action: str,
    ip_address: Optional[str] = None
):
    """
    Log PHI access for HIPAA audit trail
    This creates an audit log entry that tracks access to protected health information
    """
    logger.bind(
        event_type="phi_access",
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        ip_address=ip_address,
        timestamp=datetime.utcnow().isoformat()
    ).info(f"PHI Access: {action} on {resource_type} {resource_id}")


def log_admin_action(
    user_id: Union[str, UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[Union[str, UUID]] = None,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """
    Log administrative actions for audit trail
    Required by rule #6: Every admin config change is audited
    """
    logger.bind(
        event_type="admin_action",
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=ip_address,
        timestamp=datetime.utcnow().isoformat()
    ).info(f"Admin Action: {action} on {resource_type}")


def log_notification_event(
    channel: str,
    recipient: str,
    event_type: str,
    status: str,
    error: Optional[str] = None
):
    """
    Log notification events (SMS, Email, WhatsApp)
    Redacts recipient information for PHI compliance
    """
    # Redact recipient (PHI)
    redacted_recipient = recipient[:3] + "***" if recipient else "unknown"
    
    logger.bind(
        event_type="notification",
        channel=channel,
        recipient=redacted_recipient,
        notification_type=event_type,
        status=status,
        error=error,
        timestamp=datetime.utcnow().isoformat()
    ).info(f"Notification {status}: {channel} to {redacted_recipient}")


# Intercept standard logging
class InterceptHandler(logging.Handler):
    """Intercept standard logging and route to loguru"""
    
    def emit(self, record: logging.LogRecord):
        # Skip uvicorn access logs that cause formatting issues
        if record.name == "uvicorn.access":
            return
        
        # Get corresponding Loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # Find caller
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """Setup logging for the application"""
    # Intercept standard library logging
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOG_LEVEL)
    
    # Disable uvicorn access logging completely (we handle it in middleware)
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False
    
    # Intercept other uvicorn logging
    for name in logging.root.manager.loggerDict.keys():
        if name.startswith("uvicorn"):
            if name != "uvicorn.access":  # Already handled above
                logging.getLogger(name).handlers = []
                logging.getLogger(name).propagate = True
    
    logger.info(
        f"Logging initialized - Environment: {settings.ENVIRONMENT}, "
        f"Level: {settings.LOG_LEVEL}, Format: {settings.LOG_FORMAT}"
    )
