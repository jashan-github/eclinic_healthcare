"""
Dependency injection patterns for FastAPI
Provides reusable dependencies for routes
"""

from typing import Optional, Generator, Annotated
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token, verify_token_type, TokenData, CurrentUser, UserRole
from loguru import logger


# Database session (imported from database module)
from app.core.database import get_db


# HTTP Bearer token security
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[CurrentUser]:
    """
    Get current user from JWT token (optional)
    Returns None if no token or invalid token
    
    Usage:
        @router.get("/public-endpoint")
        def endpoint(user: Optional[CurrentUser] = Depends(get_current_user_optional)):
            if user:
                # Authenticated user
            else:
                # Anonymous user
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        verify_token_type(payload, "access")
        
        # Extract user data from token
        user_id = payload.get("user_id")
        email = payload.get("email")
        role = payload.get("role")
        clinic_id = payload.get("clinic_id")
        
        if not user_id or not email or not role:
            return None
        
        # Create CurrentUser instance
        current_user = CurrentUser(
            id=user_id,
            email=email,
            role=UserRole(role),
            clinic_id=clinic_id
        )
        
        # Bind user context to logger
        logger.bind(
            user_id=user_id,
            user_role=role,
            clinic_id=clinic_id,
            ip_address=request.client.host if request.client else None
        )
        
        return current_user
    
    except Exception as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None


async def get_current_user(
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
) -> CurrentUser:
    """
    Get current authenticated user (required)
    Raises 401 if not authenticated
    
    Usage:
        @router.get("/protected")
        def endpoint(user: CurrentUser = Depends(get_current_user)):
            # User is guaranteed to be authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access control
    
    Usage:
        @router.post("/admin/settings")
        def endpoint(user: CurrentUser = Depends(require_role(UserRole.CLINIC_ADMIN))):
            # User is guaranteed to have admin role
    """
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if not current_user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


def require_clinic_access(clinic_id: int):
    """
    Dependency factory to check clinic access
    Enforces multi-clinic isolation

    Usage:
        @router.get("/clinics/{clinic_id}/patients")
        def endpoint(
            clinic_id: int,
            user: CurrentUser = Depends(require_clinic_access(clinic_id))
        ):
            # User is guaranteed to have access to this clinic
    """
    async def clinic_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if not current_user.can_access_clinic(clinic_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this clinic"
            )
        return current_user

    return clinic_checker


def require_feature(feature_key: str):
    """
    Dependency factory to enforce role feature permission (doctor/staff tab visibility).
    Returns 403 if the current user is doctor or staff and that feature is disabled by admin.

    Usage:
        router = APIRouter(prefix="/doctor/appointments", dependencies=[Depends(require_feature("appointments"))])
        # or per-route:
        @router.get("/invoices")
        def list_invoices(_: None = Depends(require_feature("payments"))):
    """
    async def _check(
        db: Session = Depends(get_db),
        current_user: CurrentUser = Depends(get_current_user),
    ) -> None:
        from app.services.role_permission_service import RolePermissionService

        service = RolePermissionService(db)
        permissions = service.get_for_current_user(current_user.role)
        if permissions is None:
            # Admin, patient, etc. - no tab filtering
            return None
        if feature_key not in permissions:
            # Feature not defined for this role (e.g. staff has no "appointments")
            return None
        if not permissions[feature_key]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this feature (disabled for your role)",
            )
        return None

    return _check


async def get_api_key(
    x_api_key: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Get API key from header (for service-to-service communication)
    
    Usage:
        @router.post("/webhooks/twilio")
        def endpoint(api_key: str = Depends(get_api_key)):
            ...
    """
    return x_api_key


def verify_api_key(
    api_key: Optional[str] = Depends(get_api_key)
) -> str:
    """
    Verify API key (required)
    
    Usage:
        @router.post("/internal/sync")
        def endpoint(api_key: str = Depends(verify_api_key)):
            # API key is verified
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # TODO: Implement actual API key verification against database
    # For now, just a placeholder check
    # valid_keys = get_valid_api_keys()
    # if api_key not in valid_keys:
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key


# Type aliases for cleaner route signatures
DBSession = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
OptionalUserDep = Annotated[Optional[CurrentUser], Depends(get_current_user_optional)]


# Role-based dependencies (pre-configured)
AdminUser = Annotated[CurrentUser, Depends(require_role(UserRole.CLINIC_ADMIN))]
DoctorUser = Annotated[CurrentUser, Depends(require_role(UserRole.DOCTOR))]
NurseUser = Annotated[CurrentUser, Depends(require_role(UserRole.NURSE))]
ReceptionistUser = Annotated[CurrentUser, Depends(require_role(UserRole.RECEPTIONIST))]


async def get_current_admin_user(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current admin user (requires admin role and returns full User model)
    
    This dependency is used for admin endpoints that need the full User model
    from the database (not just the token data).
    
    Usage:
        @router.post("/admin/settings")
        def endpoint(current_user: User = Depends(get_current_admin_user)):
            # User is guaranteed to be admin
    """
    from app.models.user import User
    
    # Check admin role from token
    if not current_user.has_role(UserRole.CLINIC_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get full user from database
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_request_id(request: Request) -> str:
    """
    Get or generate request ID for tracing
    
    Usage:
        @router.get("/endpoint")
        def endpoint(request_id: str = Depends(get_request_id)):
            logger.bind(request_id=request_id).info("Processing request")
    """
    # Check if request ID is provided in header
    request_id = request.headers.get("X-Request-ID")
    
    if not request_id:
        # Generate request ID from request state (set by middleware)
        request_id = getattr(request.state, "request_id", "unknown")
    
    return request_id


async def get_client_ip(request: Request) -> Optional[str]:
    """
    Get client IP address (considering proxies)
    
    Usage:
        @router.post("/login")
        def endpoint(ip: str = Depends(get_client_ip)):
            log_login_attempt(ip)
    """
    # Check X-Forwarded-For header (if behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get first IP (client IP)
        return forwarded_for.split(",")[0].strip()
    
    # Direct connection
    if request.client:
        return request.client.host
    
    return None
