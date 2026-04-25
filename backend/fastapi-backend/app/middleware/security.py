"""
Security headers middleware
Adds security headers to all responses for protection against common attacks
"""

from typing import Callable
from urllib.parse import urlparse
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses
    
    Headers added:
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-XSS-Protection: XSS filter
    - Strict-Transport-Security: Force HTTPS
    - Content-Security-Policy: Control resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.is_production = settings.is_production
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Force HTTPS in production
        if self.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Content Security Policy - more permissive for API docs
        is_docs_page = request.url.path in ["/docs", "/redoc", "/openapi.json"]
        
        if is_docs_page:
            # Relaxed CSP for Swagger UI and ReDoc
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
                "img-src 'self' data: https: https://cdn.jsdelivr.net",
                "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
        else:
            # Strict CSP for all other pages
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
        
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (formerly Feature-Policy)
        permissions_directives = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)
        
        # Remove server header (hide backend technology)
        if "Server" in response.headers:
            del response.headers["Server"]
        
        # Add custom security header
        response.headers["X-Powered-By"] = "eClinic"
        
        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with strict validation
    Ensures only allowed origins can access the API
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Parse CORS origins from comma-separated string to set
        cors_origins_list = settings.cors_origins_list if hasattr(settings, 'cors_origins_list') else []
        if isinstance(settings.CORS_ORIGINS, str):
            cors_origins_list = [origin.strip().rstrip('/') for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
        self.allowed_origins = set(cors_origins_list)
        self.is_production = settings.is_production
        self.is_development = settings.is_development
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate CORS requests"""
        
        origin = request.headers.get("origin")
        host = request.headers.get("host", "")
        
        # In development, allow requests without origin (same-origin) or from common dev ports
        is_allowed_origin = False
        if origin:
            # Normalize origin (remove trailing slash)
            origin_normalized = origin.rstrip('/')
            is_allowed_origin = origin_normalized in self.allowed_origins
            
            # If not explicitly allowed, check for same-origin requests
            if not is_allowed_origin:
                # Extract host from origin (remove protocol and path)
                try:
                    origin_parsed = urlparse(origin_normalized)
                    origin_host = origin_parsed.netloc or origin_parsed.hostname
                    
                    # Check if origin matches the request host (same-origin)
                    if origin_host and host:
                        # Remove port if present for comparison
                        origin_host_clean = origin_host.split(":")[0]
                        host_clean = host.split(":")[0]
                        if origin_host_clean == host_clean:
                            is_allowed_origin = True
                except Exception:
                    pass
            
            # In development, also allow common localhost variations (more permissive for Next.js)
            if self.is_development and not is_allowed_origin:
                # Check if it's a localhost origin (any port) - case-insensitive, supports http/https
                origin_lower = origin_normalized.lower()
                if (origin_lower.startswith("http://localhost") or 
                    origin_lower.startswith("http://127.0.0.1") or
                    origin_lower.startswith("https://localhost") or
                    origin_lower.startswith("https://127.0.0.1")):
                    is_allowed_origin = True
        elif self.is_development:
            # Allow same-origin requests in development (no origin header)
            is_allowed_origin = True
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            if is_allowed_origin:
                response = Response(status_code=200)
                # When credentials are allowed, we MUST use the specific origin, not *
                if origin:
                    response.headers["Access-Control-Allow-Origin"] = origin
                elif not settings.CORS_ALLOW_CREDENTIALS:
                    # Only use * if credentials are NOT allowed
                    response.headers["Access-Control-Allow-Origin"] = "*"
                else:
                    # For same-origin requests with credentials, use the request host
                    response.headers["Access-Control-Allow-Origin"] = f"http://{host}" if host else "*"
                
                # Handle methods
                # Support both ["*"] and explicit list of methods
                # Check if methods list contains "*" or is exactly ["*"]
                is_wildcard = (
                    settings.CORS_ALLOW_METHODS == ["*"] or 
                    (len(settings.CORS_ALLOW_METHODS) == 1 and settings.CORS_ALLOW_METHODS[0] == "*") or
                    "*" in settings.CORS_ALLOW_METHODS
                )
                
                if is_wildcard:
                    # Allow all common HTTP methods (explicitly list them for browser compatibility)
                    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
                else:
                    # Use explicit list, ensuring PATCH and OPTIONS are included
                    methods = list(settings.CORS_ALLOW_METHODS)
                    # Always include OPTIONS for preflight
                    if "OPTIONS" not in methods:
                        methods.append("OPTIONS")
                    # Ensure PATCH is included
                    if "PATCH" not in methods:
                        methods.append("PATCH")
                    response.headers["Access-Control-Allow-Methods"] = ", ".join(methods)
                
                # Handle headers
                if settings.CORS_ALLOW_HEADERS == ["*"]:
                    response.headers["Access-Control-Allow-Headers"] = (
                        "Content-Type, Authorization, X-Requested-With, "
                        "Accept, Origin, X-Request-ID"
                    )
                else:
                    response.headers["Access-Control-Allow-Headers"] = ", ".join(
                        settings.CORS_ALLOW_HEADERS
                    )
                
                response.headers["Access-Control-Max-Age"] = "600"  # 10 minutes
                
                if settings.CORS_ALLOW_CREDENTIALS:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                
                return response
            elif not origin:
                # Same-origin request (no origin header) - allow it
                response = Response(status_code=200)
                return response
            else:
                # Block unknown origins in production
                if self.is_production:
                    return Response(
                        content='{"success": false, "message": "CORS origin not allowed", '
                                '"errors": null, "data": null}',
                        status_code=403,
                        media_type="application/json"
                    )
                # In development, still allow but log warning
                response = Response(status_code=200)
                if origin:
                    response.headers["Access-Control-Allow-Origin"] = origin
                # Always include all methods in development fallback
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
                # Handle headers
                if settings.CORS_ALLOW_HEADERS == ["*"]:
                    response.headers["Access-Control-Allow-Headers"] = (
                        "Content-Type, Authorization, X-Requested-With, "
                        "Accept, Origin, X-Request-ID"
                    )
                else:
                    response.headers["Access-Control-Allow-Headers"] = ", ".join(
                        settings.CORS_ALLOW_HEADERS
                    )
                response.headers["Access-Control-Max-Age"] = "600"  # 10 minutes
                if settings.CORS_ALLOW_CREDENTIALS:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers if origin is allowed
        if is_allowed_origin:
            # When credentials are allowed, we MUST use the specific origin, not *
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
            elif not settings.CORS_ALLOW_CREDENTIALS:
                # Only use * if credentials are NOT allowed
                response.headers["Access-Control-Allow-Origin"] = "*"
            else:
                # For same-origin requests with credentials, use the request host
                response.headers["Access-Control-Allow-Origin"] = f"http://{host}" if host else "*"
            
            if settings.CORS_ALLOW_CREDENTIALS:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            # Expose custom headers
            response.headers["Access-Control-Expose-Headers"] = (
                "X-Request-ID, X-Process-Time, X-RateLimit-Limit, "
                "X-RateLimit-Remaining, X-RateLimit-Reset"
            )
        elif self.is_development:
            # In development, be more permissive - allow any localhost origin
            if origin:
                # Check if it's a localhost origin (for Next.js and other local dev)
                origin_normalized = origin.rstrip('/')
                origin_lower = origin_normalized.lower()
                if (origin_lower.startswith("http://localhost") or 
                    origin_lower.startswith("http://127.0.0.1") or
                    origin_lower.startswith("https://localhost") or
                    origin_lower.startswith("https://127.0.0.1")):
                    response.headers["Access-Control-Allow-Origin"] = origin
                    if settings.CORS_ALLOW_CREDENTIALS:
                        response.headers["Access-Control-Allow-Credentials"] = "true"
                    # Expose custom headers
                    response.headers["Access-Control-Expose-Headers"] = (
                        "X-Request-ID, X-Process-Time, X-RateLimit-Limit, "
                        "X-RateLimit-Remaining, X-RateLimit-Reset"
                    )
            elif not settings.CORS_ALLOW_CREDENTIALS:
                # Allow same-origin requests in development (no origin header)
                response.headers["Access-Control-Allow-Origin"] = "*"
            else:
                response.headers["Access-Control-Allow-Origin"] = f"http://{host}" if host else "*"
                if settings.CORS_ALLOW_CREDENTIALS:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Input sanitization middleware
    Checks for common attack patterns in request data
    """
    
    SUSPICIOUS_PATTERNS = [
        # SQL injection patterns
        "' OR '1'='1",
        "'; DROP TABLE",
        "UNION SELECT",
        "1=1--",
        
        # XSS patterns
        "<script>",
        "javascript:",
        "onerror=",
        "onload=",
        
        # Path traversal
        "../",
        "..\\",
        
        # Command injection
        "; rm -rf",
        "| cat /etc",
        "&& wget",
    ]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check for suspicious patterns in request"""
        
        # Check query parameters
        query_string = str(request.url.query).lower()
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.lower() in query_string:
                return Response(
                    content='{"success": false, "message": "Invalid request", '
                            '"errors": {"security": ["Suspicious input detected"]}, "data": null}',
                    status_code=400,
                    media_type="application/json"
                )
        
        # Check path
        path = str(request.url.path).lower()
        if "../" in path or "..\\" in path:
            return Response(
                content='{"success": false, "message": "Invalid request path", '
                        '"errors": {"security": ["Invalid path"]}, "data": null}',
                status_code=400,
                media_type="application/json"
            )
        
        # Check headers for suspicious content
        user_agent = request.headers.get("user-agent", "").lower()
        if any(bot in user_agent for bot in ["sqlmap", "nikto", "nmap", "masscan"]):
            return Response(
                content='{"success": false, "message": "Access denied", '
                        '"errors": {"security": ["Suspicious activity detected"]}, "data": null}',
                status_code=403,
                media_type="application/json"
            )
        
        return await call_next(request)
