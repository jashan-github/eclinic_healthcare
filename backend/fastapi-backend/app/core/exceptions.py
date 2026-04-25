"""
Custom exceptions with Laravel-compatible error format
All exceptions return consistent JSON structure
"""

from typing import Any, Dict, Optional, List, Union
from fastapi import HTTPException, status


class LaravelHTTPException(HTTPException):
    """
    Base exception that returns Laravel-compatible error format
    
    Response format:
    {
        "success": false,
        "message": "Error message",
        "errors": {"field": ["error1", "error2"]},
        "data": null
    }
    """
    
    def __init__(
        self,
        status_code: int,
        message: str,
        errors: Optional[Dict[str, List[str]]] = None,
        data: Any = None
    ):
        self.status_code = status_code
        self.message = message
        self.errors = errors
        self.data = data
        super().__init__(status_code=status_code, detail=message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Laravel-compatible dictionary"""
        return {
            "success": False,
            "message": self.message,
            "errors": self.errors,
            "data": self.data
        }


class UnauthorizedException(LaravelHTTPException):
    """401 Unauthorized - Invalid or missing authentication"""
    
    def __init__(
        self,
        message: str = "Unauthorized",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            errors=errors
        )


class ForbiddenException(LaravelHTTPException):
    """403 Forbidden - Insufficient permissions"""
    
    def __init__(
        self,
        message: str = "Forbidden",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            errors=errors
        )


class NotFoundException(LaravelHTTPException):
    """404 Not Found - Resource not found"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            errors=errors
        )


class ValidationException(LaravelHTTPException):
    """422 Unprocessable Entity - Validation failed"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            errors=errors or {}
        )


class RateLimitException(LaravelHTTPException):
    """429 Too Many Requests - Rate limit exceeded"""
    
    def __init__(
        self,
        message: str = "Too many requests",
        retry_after: Optional[int] = None
    ):
        self.retry_after = retry_after
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            errors={"rate_limit": ["Rate limit exceeded. Please try again later."]}
        )


class InternalServerException(LaravelHTTPException):
    """500 Internal Server Error"""
    
    def __init__(
        self,
        message: str = "Internal server error",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            errors=errors
        )


class BadRequestException(LaravelHTTPException):
    """400 Bad Request"""
    
    def __init__(
        self,
        message: str = "Bad request",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            errors=errors
        )


class ConflictException(LaravelHTTPException):
    """409 Conflict - Resource already exists"""
    
    def __init__(
        self,
        message: str = "Resource already exists",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            errors=errors
        )


def format_validation_errors(errors: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Format Pydantic validation errors to Laravel format
    
    Args:
        errors: List of Pydantic error dictionaries
    
    Returns:
        Dictionary with field names as keys and error messages as values
    """
    formatted_errors: Dict[str, List[str]] = {}
    
    for error in errors:
        # Get field path - filter out 'body' and numeric indices
        loc_parts = [str(x) for x in error["loc"] if x != "body" and not isinstance(x, int)]
        field = ".".join(loc_parts) if loc_parts else "general"
        
        # If field is still empty or is a number, use a more descriptive name
        if not field or field.isdigit():
            # Try to get the field name from the location
            loc_list = list(error["loc"])
            if len(loc_list) > 1:
                # Get the last non-body, non-numeric part
                for part in reversed(loc_list):
                    if part != "body" and not isinstance(part, int):
                        field = str(part)
                        break
            if not field or field.isdigit():
                field = "request_body"
        
        # Get error message
        message = error["msg"]
        error_type = error.get("type", "")
        
        # Make error messages more user-friendly
        if error_type == "value_error.missing":
            message = f"{field} is required"
        elif error_type == "type_error":
            message = f"{field} has invalid type"
        elif error_type.startswith("value_error.email"):
            message = f"{field} must be a valid email address"
        elif "json" in error_type.lower() or "decode" in error_type.lower():
            message = f"Invalid JSON format for {field}" if field != "request_body" else "Invalid JSON format in request body"
        elif "uuid" in error_type.lower() or "uuid" in message.lower():
            message = f"{field} must be a valid UUID format"
        
        # Add to formatted errors
        if field in formatted_errors:
            formatted_errors[field].append(message)
        else:
            formatted_errors[field] = [message]
    
    return formatted_errors


def laravel_response(
    success: bool = True,
    message: str = "",
    data: Any = None,
    errors: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate Laravel-compatible response format
    
    Args:
        success: Success status
        message: Response message
        data: Response data
        errors: Validation errors
    
    Returns:
        Laravel-compatible response dictionary
    """
    return {
        "success": success,
        "message": message,
        "errors": errors,
        "data": data
    }


# ============================================================================
# NOTIFICATION EXCEPTIONS
# ============================================================================


class NotificationChannelDisabledError(LaravelHTTPException):
    """Raised when a notification channel is disabled"""
    
    def __init__(
        self,
        message: str = "Notification channel is disabled",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            errors=errors or {"channel": ["This notification channel is currently disabled"]}
        )


class NotificationProviderNotConfiguredError(LaravelHTTPException):
    """Raised when a notification provider is not configured"""
    
    def __init__(
        self,
        message: str = "Notification provider not configured",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            errors=errors or {"provider": ["Notification provider not configured properly"]}
        )


class NotificationSendError(LaravelHTTPException):
    """Raised when notification sending fails"""
    
    def __init__(
        self,
        message: str = "Failed to send notification",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            errors=errors or {"notification": ["Failed to send notification"]}
        )
