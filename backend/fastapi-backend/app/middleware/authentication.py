"""
JWT Authentication Middleware
Validates JWT tokens and attaches user context to requests
"""

from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from app.core.config import settings
from app.core.security import decode_token, verify_token_type, UserRole
from app.core.redis import redis_client
from app.core.exceptions import UnauthorizedException


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware
    Validates tokens and attaches user context to request.state
    
    This middleware runs before route handlers and makes user info
    available throughout the request lifecycle
    """
    
    # Paths that don't require authentication
    PUBLIC_PATHS = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
    ]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate JWT token and attach user context"""
        
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Extract token from Authorization header
        token = self._extract_token(request)
        
        if not token:
            # No token provided - let route handle it (may be optional auth)
            return await call_next(request)
        
        # Validate token
        try:
            user_context = self._validate_token(token)
            
            if user_context:
                # Attach user context to request state
                request.state.user_id = user_context["user_id"]
                request.state.user_email = user_context["email"]
                request.state.user_role = user_context["role"]
                request.state.clinic_id = user_context.get("clinic_id")
                request.state.is_authenticated = True
                
                # Bind user context to logger for this request
                logger.bind(
                    user_id=user_context["user_id"],
                    user_role=user_context["role"],
                    clinic_id=user_context.get("clinic_id")
                )
            
        except UnauthorizedException:
            # Invalid token - let route handle it
            pass
        except Exception as e:
            logger.warning(f"Token validation error: {str(e)}")
        
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)"""
        # Exact match
        if path in self.PUBLIC_PATHS:
            return True
        
        # Prefix match for versioned auth endpoints
        if path.startswith("/api/v") and "/auth/" in path:
            return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header
        
        Supports formats:
        - Bearer <token>
        - JWT <token>
        """
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return None
        
        parts = auth_header.split()
        
        if len(parts) != 2:
            return None
        
        scheme, token = parts
        
        if scheme.lower() not in ["bearer", "jwt"]:
            return None
        
        return token
    
    def _validate_token(self, token: str) -> Optional[dict]:
        """
        Validate JWT token and return user context
        
        Args:
            token: JWT token string
        
        Returns:
            User context dictionary or None if invalid
        
        Raises:
            UnauthorizedException: If token is invalid
        """
        try:
            # Decode token
            payload = decode_token(token)
            
            # Verify token type
            verify_token_type(payload, "access")
            
            # Check if token is blacklisted (for logout/revocation)
            token_jti = payload.get("jti")
            if token_jti and redis_client.is_token_blacklisted(token_jti):
                logger.warning(f"Blacklisted token used: jti={token_jti}")
                raise UnauthorizedException("Token has been revoked")
            
            # Extract user data
            user_id = payload.get("user_id")
            email = payload.get("email")
            role = payload.get("role")
            
            if not user_id or not email or not role:
                raise UnauthorizedException("Invalid token payload")
            
            # Validate role
            try:
                UserRole(role)
            except ValueError:
                logger.warning(f"Invalid role in token: {role}")
                raise UnauthorizedException("Invalid role")
            
            return {
                "user_id": user_id,
                "email": email,
                "role": role,
                "clinic_id": payload.get("clinic_id"),
                "jti": token_jti
            }
        
        except UnauthorizedException:
            raise
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            raise UnauthorizedException("Invalid token")


class RequireAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce authentication on all routes (except public)
    Place this AFTER JWTAuthenticationMiddleware
    """
    
    PUBLIC_PATHS = JWTAuthenticationMiddleware.PUBLIC_PATHS
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enforce authentication"""
        
        # Skip for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Check if user is authenticated
        is_authenticated = getattr(request.state, "is_authenticated", False)
        
        if not is_authenticated:
            logger.warning(
                f"Unauthenticated access attempt: {request.method} {request.url.path}"
            )
            
            return Response(
                content='{"success": false, "message": "Authentication required", '
                        '"errors": {"auth": ["You must be logged in to access this resource"]}, '
                        '"data": null}',
                status_code=401,
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public"""
        if path in self.PUBLIC_PATHS:
            return True
        
        if path.startswith("/api/v") and "/auth/" in path:
            return True
        
        return False
