"""
Security module for JWT authentication and authorization
Placeholder for JWT implementation - business logic to be added later
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from enum import Enum
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User roles for RBAC"""
    SUPER_ADMIN = "super_admin"
    CLINIC_ADMIN = "clinic_admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    STAFF = "staff"
    RECEPTIONIST = "receptionist"
    PATIENT = "patient"


class PermissionLevel(str, Enum):
    """Permission levels"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class ConsultationMode(str, Enum):
    """Consultation modes for services"""
    IN_CLINIC = "IN_CLINIC"
    TELECONSULTATION = "TELECONSULTATION"
    
    @classmethod
    def default(cls) -> str:
        """Get default consultation mode"""
        return cls.IN_CLINIC.value


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Token payload (user_id, role, clinic_id, etc.)
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token
    
    Args:
        data: Token payload (user_id, role, clinic_id, etc.)
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def create_webinar_redirect_token(
    user_id: Union[str, UUID],
    webinar_id: Union[str, UUID],
    expires_minutes: int = 15
) -> str:
    """
    Create a short-lived JWT for webinar payment-success redirect.
    Used when Sentoo redirects the browser to the backend URL (no Bearer token sent).
    """
    to_encode = {
        "user_id": str(user_id),
        "webinar_id": str(webinar_id),
        "type": "webinar_redirect",
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_webinar_redirect_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify webinar redirect token. Returns None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "webinar_redirect":
            return None
        return payload
    except JWTError:
        return None


def verify_token_type(payload: Dict[str, Any], expected_type: str):
    """
    Verify token type (access or refresh)
    
    Args:
        payload: Decoded token payload
        expected_type: Expected token type
    
    Raises:
        HTTPException: If token type doesn't match
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def has_permission(user_role: UserRole, required_role: UserRole) -> bool:
    """
    Check if user role has required permission
    Hierarchical role check
    
    Args:
        user_role: User's role
        required_role: Required role for access
    
    Returns:
        True if user has permission
    """
    role_hierarchy = {
        UserRole.SUPER_ADMIN: 100,
        UserRole.CLINIC_ADMIN: 80,
        UserRole.DOCTOR: 60,
        UserRole.NURSE: 40,
        UserRole.RECEPTIONIST: 20,
        UserRole.PATIENT: 10,
    }
    
    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)


def check_clinic_access(user_clinic_id: Optional[Union[str, UUID]], resource_clinic_id: Union[str, UUID]) -> bool:
    """
    Check if user has access to resource in specific clinic
    Enforces multi-clinic isolation
    
    Args:
        user_clinic_id: User's clinic ID
        resource_clinic_id: Resource's clinic ID
    
    Returns:
        True if user has access
    """
    # Super admins can access all clinics
    # For single-clinic mode, always allow access
    if not settings.MULTI_CLINIC_ENABLED:
        return True
    
    # In multi-clinic mode, user must belong to the same clinic
    # Convert both to strings for comparison
    if not user_clinic_id or not resource_clinic_id:
        return False
    
    user_clinic_id_str = str(user_clinic_id) if isinstance(user_clinic_id, UUID) else user_clinic_id
    resource_clinic_id_str = str(resource_clinic_id) if isinstance(resource_clinic_id, UUID) else resource_clinic_id
    
    return user_clinic_id_str == resource_clinic_id_str


# Placeholder classes for dependency injection
# These will be implemented with actual business logic later

class TokenData:
    """Token data structure"""
    
    def __init__(
        self,
        user_id: int,
        email: str,
        role: UserRole,
        clinic_id: Optional[int] = None,
        permissions: Optional[list[str]] = None
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.clinic_id = clinic_id
        self.permissions = permissions or []


class CurrentUser:
    """
    Current user context
    Will be populated by dependency injection in routes
    """
    
    def __init__(
        self,
        id: Union[str, UUID],
        email: str,
        role: UserRole,
        clinic_id: Optional[Union[str, UUID]] = None,
        is_active: bool = True
    ):
        self.id = str(id) if isinstance(id, UUID) else id
        self.email = email
        self.role = role
        self.clinic_id = clinic_id
        self.is_active = is_active
    
    def has_role(self, required_role: UserRole) -> bool:
        """Check if user has required role"""
        return has_permission(self.role, required_role)
    
    def can_access_clinic(self, clinic_id: Union[str, UUID]) -> bool:
        """Check if user can access specific clinic"""
        return check_clinic_access(self.clinic_id, clinic_id)
