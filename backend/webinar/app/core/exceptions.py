"""
Custom exceptions with Laravel-compatible error format
All exceptions return consistent JSON structure
"""

from typing import Any, Dict, Optional, List
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
    
    def __init__(self, message: str = "Unauthorized", errors: Optional[Dict[str, List[str]]] = None):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, message=message, errors=errors)


class ForbiddenException(LaravelHTTPException):
    """403 Forbidden - Valid authentication but insufficient permissions"""
    
    def __init__(self, message: str = "Forbidden", errors: Optional[Dict[str, List[str]]] = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message, errors=errors)


class NotFoundException(LaravelHTTPException):
    """404 Not Found - Resource not found"""
    
    def __init__(self, message: str = "Resource not found", errors: Optional[Dict[str, List[str]]] = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message, errors=errors)


class ValidationException(LaravelHTTPException):
    """422 Unprocessable Entity - Validation errors"""
    
    def __init__(self, message: str = "Validation failed", errors: Optional[Dict[str, List[str]]] = None):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message=message, errors=errors)
