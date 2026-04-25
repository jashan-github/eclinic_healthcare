"""
eClinic Backend - FastAPI Application
Main application entry point
"""

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, status, Depends, Query
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.redis import redis_client
from app.core.database import get_db
from app.models.user import User
from app.core.exceptions import (
    LaravelHTTPException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    ValidationException,
    format_validation_errors,
    laravel_response
)
from sqlalchemy.exc import IntegrityError
from app.services.audit_service import AuditService
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import (
    SecurityHeadersMiddleware,
    CORSSecurityMiddleware,
    InputSanitizationMiddleware
)
from app.middleware.authentication import JWTAuthenticationMiddleware
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("=" * 50)
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info("=" * 50)
    
    # Initialize Redis connection
    if settings.REDIS_ENABLED:
        redis_client.connect()
        if redis_client.is_available():
            logger.info("✓ Redis connected and available")
        else:
            logger.warning("✗ Redis connection failed - rate limiting disabled")
    
    # TODO: Initialize database connection pool
    # TODO: Run database migrations check
    # TODO: Load notification provider configurations
    
    yield
    
    # Shutdown
    logger.info("=" * 50)
    logger.info(f"Shutting down {settings.APP_NAME}")
    logger.info("=" * 50)
    
    # Close Redis connection
    if settings.REDIS_ENABLED:
        redis_client.disconnect()
    
    # TODO: Close database connections
    # TODO: Cleanup resources


def create_application() -> FastAPI:
    """
    Application factory
    Creates and configures FastAPI application
    """
    
    # Initialize logging
    setup_logging()
    
    # Create FastAPI app
    # Note: When behind reverse proxy, we use custom docs to handle the proxy path correctly
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Healthcare platform backend with HIPAA-ready architecture",
        docs_url=None,  # Disable default docs - we'll create custom ones
        redoc_url=None,  # Disable default redoc
        openapi_url="/openapi.json" if settings.DEBUG else None,
        root_path=settings.ROOT_PATH,  # For reverse proxy support (e.g., "/backend/api-fast")
        lifespan=lifespan,
    )
    
    # Add middleware in correct order (LIFO - Last In, First Out)
    # Middleware execution order: bottom to top for requests, top to bottom for responses
    
    # 1. Request logging (outermost - logs everything)
    app.add_middleware(RequestLoggingMiddleware)
    
    # 2. Security headers (add security headers to all responses)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 3. CORS (handle cross-origin requests)
    if settings.CORS_ORIGINS:
        app.add_middleware(CORSSecurityMiddleware)
        logger.info(f"CORS enabled for origins: {settings.CORS_ORIGINS}")
    
    # 4. Trusted host (validate host header in production)
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # TODO: Configure actual allowed hosts from env
        )
    
    # 5. Input sanitization (check for malicious input)
    app.add_middleware(InputSanitizationMiddleware)
    
    # 6. Rate limiting (prevent abuse)
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)
        logger.info(f"Rate limiting enabled: {settings.RATE_LIMIT_PER_MINUTE} req/min")
    
    # 7. JWT authentication (validate tokens, set user context)
    app.add_middleware(JWTAuthenticationMiddleware)
    logger.info("JWT authentication middleware enabled")
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Serve uploaded files via custom endpoint (works better with ROOT_PATH)
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    uploads_dir = Path("/app/uploads")
    
    @app.api_route("/uploads/{file_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_uploaded_file(file_path: str, request: Request):
        """
        Serve uploaded files (avatars, etc.)
        Works correctly with ROOT_PATH reverse proxy configuration
        """
        file_full_path = uploads_dir / file_path
        
        # Security: Ensure the file is within the uploads directory
        try:
            file_full_path.resolve().relative_to(uploads_dir.resolve())
        except (ValueError, OSError):
            raise StarletteHTTPException(status_code=404, detail="File not found")
        
        if not file_full_path.exists() or not file_full_path.is_file():
            raise StarletteHTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_full_path),
            media_type=None,  # Let FastAPI detect content type
            filename=file_full_path.name
        )
    
    if uploads_dir.exists():
        logger.info(f"Upload file serving enabled at /uploads from {uploads_dir}")
    else:
        logger.warning(f"Uploads directory not found at {uploads_dir}, file serving disabled")
    
    # Password reset token verification endpoint (at root level, not under /api/v1)
    @app.get(
        "/reset-password",
        status_code=307,
        summary="Verify reset password token and redirect",
        description="Verifies the password reset token and redirects to frontend reset password page or error page",
        tags=["Authentication"]
    )
    async def verify_reset_password_token(
        token: str = Query(..., description="Password reset token"),
        db: Session = Depends(get_db)
    ):
        """
        Verify reset password token and redirect
        
        **Public endpoint** (no authentication required)
        
        This endpoint is called when a user clicks on the password reset link in their email.
        It verifies the token and redirects to the appropriate frontend page.
        
        **Query Parameters:**
        - **token**: Password reset token from email link
        
        **Redirects:**
        - If token is valid: Redirects to `FRONTEND_URL/auth/reset-password?token={token}`
        - If token is invalid/expired: Redirects to `FRONTEND_URL/auth/reset-password-verification-failed`
        
        **Token Validation:**
        - Token must exist in user record
        - Token must not be expired (reset_token_expires_at > current time)
        - User must be active
        """
        try:
            # Get user by reset token
            user = db.query(User).filter(
                User.reset_token == token,
                User.deleted_at.is_(None)
            ).first()
            
            # Check if token exists
            if not user:
                logger.warning(f"Password reset token verification failed: token not found")
                frontend_url = settings.FRONTEND_URL.rstrip('/')
                return RedirectResponse(
                    url=f"{frontend_url}/auth/reset-password-verification-failed",
                    status_code=307
                )
            
            # Check if token is expired (use timezone-aware datetime)
            current_time = datetime.now(timezone.utc)
            if not user.reset_token_expires_at or user.reset_token_expires_at < current_time:
                logger.warning(f"Password reset token verification failed: token expired for user {user.id} (expires: {user.reset_token_expires_at}, now: {current_time})")
                frontend_url = settings.FRONTEND_URL.rstrip('/')
                return RedirectResponse(
                    url=f"{frontend_url}/auth/reset-password-verification-failed",
                    status_code=307
                )
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Password reset token verification failed: user {user.id} is inactive")
                frontend_url = settings.FRONTEND_URL.rstrip('/')
                return RedirectResponse(
                    url=f"{frontend_url}/auth/reset-password-verification-failed",
                    status_code=307
                )
            
            # Token is valid - redirect to frontend reset password page with token
            logger.info(f"Password reset token verified successfully for user {user.id}")
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            return RedirectResponse(
                url=f"{frontend_url}/auth/reset-password?token={token}",
                status_code=307
            )
        
        except Exception as e:
            logger.error(f"Error verifying reset password token: {str(e)}", exc_info=True)
            # On any error, redirect to failure page
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            return RedirectResponse(
                url=f"{frontend_url}/auth/reset-password-verification-failed",
                status_code=307
            )
    
    # Include API routers AFTER static file mount
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    # Custom Swagger UI endpoint that works with reverse proxy
    if settings.DEBUG:
        @app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html():
            """Custom Swagger UI that correctly handles reverse proxy paths"""
            openapi_url = f"{settings.ROOT_PATH}/openapi.json" if settings.ROOT_PATH else "/openapi.json"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css">
            <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
            <title>{settings.APP_NAME} - Swagger UI</title>
            </head>
            <body>
            <div id="swagger-ui">
            </div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
            <script>
            const ui = SwaggerUIBundle({{
                url: '{openapi_url}',
                dom_id: '#swagger-ui',
                layout: 'BaseLayout',
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
            }})
            </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
    
    logger.info("Application configuration completed")
    
    return app


def register_exception_handlers(app: FastAPI):
    """
    Register custom exception handlers
    Ensures consistent error response format (Laravel compatibility)
    """
    
    @app.exception_handler(LaravelHTTPException)
    async def laravel_exception_handler(request: Request, exc: LaravelHTTPException):
        """
        Handle custom Laravel-compatible exceptions
        """
        logger.bind(
            request_id=getattr(request.state, "request_id", "unknown"),
            status_code=exc.status_code,
            path=request.url.path
        ).warning(f"Laravel Exception: {exc.message}")
        
        # HIPAA FIX 1: Log unauthorized and forbidden access attempts
        if isinstance(exc, UnauthorizedException):
            _log_security_event(
                request=request,
                action="UNAUTHORIZED_ACCESS",
                actor_user_id=getattr(request.state, "user_id", None)
            )
        elif isinstance(exc, ForbiddenException):
            _log_security_event(
                request=request,
                action="FORBIDDEN_ACCESS",
                actor_user_id=getattr(request.state, "user_id", None)
            )
        
        response_data = exc.to_dict()
        
        # Add retry-after header for rate limit exceptions
        headers = {}
        if hasattr(exc, "retry_after") and exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
            headers["X-RateLimit-Reset"] = str(exc.retry_after)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data,
            headers=headers if headers else None
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Handle standard HTTP exceptions
        Returns error in Laravel-compatible format
        """
        logger.bind(
            request_id=getattr(request.state, "request_id", "unknown"),
            status_code=exc.status_code,
            path=request.url.path
        ).warning(f"HTTP Exception: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=laravel_response(
                success=False,
                message=str(exc.detail),
                errors=None,
                data=None
            )
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handle Pydantic validation errors
        Returns error in Laravel-compatible format
        """
        # Format validation errors to Laravel format
        errors = format_validation_errors(exc.errors())
        
        logger.bind(
            request_id=getattr(request.state, "request_id", "unknown"),
            path=request.url.path,
            validation_errors=errors
        ).warning("Validation failed")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=laravel_response(
                success=False,
                message="Validation failed",
                errors=errors,
                data=None
            )
        )
    
    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
        """
        Handle Pydantic validation errors (raised when manually creating schema instances)
        Returns error in Laravel-compatible format
        """
        # Format validation errors to Laravel format
        errors = format_validation_errors(exc.errors())
        
        logger.bind(
            request_id=getattr(request.state, "request_id", "unknown"),
            path=request.url.path,
            validation_errors=errors
        ).warning("Schema validation failed")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=laravel_response(
                success=False,
                message="Validation failed",
                errors=errors,
                data=None
            )
        )
    
    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        """
        Handle KeyError exceptions with detailed information
        Helps identify dictionary/mapping access issues
        """
        import traceback
        # Get traceback of where KeyError was raised (not the handler)
        tb_list = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_str = "".join(tb_list)
        tb_lines = tb_str.strip().split("\n")
        # Find file:line (e.g. "  File \"/path/file.py\", line 42, in func")
        location = "unknown"
        for line in reversed(tb_lines):
            if "File " in line and ".py" in line and "line " in line:
                location = line.strip()
                break
        logger.bind(
            request_id=getattr(request.state, "request_id", "unknown"),
            path=request.url.path,
            method=request.method,
            user_id=getattr(request.state, "user_id", None),
            missing_key=str(exc),
            key_error_location=location,
            key_error_traceback=tb_str
        ).exception(
            "KeyError: Missing key '{}' | Location: {}", exc, location
        )
        logger.error("KeyError traceback (file and line where it occurred):\n{}", tb_str)
        
        # In development, show the key that was missing and where it occurred
        if settings.is_production:
            message = "An internal error occurred. Please contact support."
            errors = {"server": ["Internal server error occurred"]}
        else:
            message = f"KeyError: Missing key '{exc}'"
            errors = {
                "key": [f"The key '{exc}' was not found"],
                "location": [location],
            }
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=laravel_response(
                success=False,
                message=message,
                errors=errors,
                data=None
            )
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """
        Handle database integrity constraint violations
        Provides user-friendly error messages for common constraint violations
        """
        # Log full exception with context
        logger.bind(
            request_id=getattr(request.state, "request_id", "unknown"),
            path=request.url.path,
            method=request.method,
            user_id=getattr(request.state, "user_id", None)
        ).exception(f"Database integrity error: {str(exc)}")
        
        # Extract error details from the exception
        error_message = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        
        # Parse common constraint violations
        errors = {"database": ["A database constraint was violated"]}
        message = "Database constraint violation"
        
        # Check for specific constraint types
        if "unique constraint" in error_message.lower() or "duplicate key" in error_message.lower():
            message = "This record already exists"
            errors = {"database": ["A record with this information already exists"]}
        elif "foreign key constraint" in error_message.lower() or "violates foreign key" in error_message.lower():
            message = "Invalid reference"
            errors = {"database": ["Referenced record does not exist"]}
        elif "not null constraint" in error_message.lower() or "null value" in error_message.lower():
            message = "Missing required field"
            errors = {"database": ["A required field is missing"]}
        elif "check constraint" in error_message.lower():
            message = "Invalid value"
            errors = {"database": ["The provided value does not meet the requirements"]}
        
        # In development, include more details
        if settings.DEBUG:
            # Extract constraint name if available
            if "constraint" in error_message.lower():
                # Try to extract constraint name
                import re
                constraint_match = re.search(r'constraint "?(\w+)"?', error_message, re.IGNORECASE)
                if constraint_match:
                    errors["constraint"] = [f"Constraint: {constraint_match.group(1)}"]
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=laravel_response(
                success=False,
                message=message,
                errors=errors,
                data=None
            )
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Handle unexpected exceptions
        Logs full error but returns safe message to client
        CRITICAL: Never expose PHI or internal details in error messages
        """
        # Log full exception with context
        try:
            logger.bind(
                request_id=getattr(request.state, "request_id", "unknown"),
                path=request.url.path,
                method=request.method,
                user_id=getattr(request.state, "user_id", None)
            ).exception(f"Unhandled exception: {type(exc).__name__}")
        except Exception:
            # If logging fails, at least print to stderr
            import sys
            import traceback
            print(f"ERROR in exception handler: {type(exc).__name__}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        
        # Get the actual error message - ULTRA DEFENSIVE
        error_name = "UnknownError"
        error_message = "Unknown error"
        error_details = []
        
        try:
            error_name = type(exc).__name__
        except:
            pass
        
        try:
            # For NameError, get message directly from args[0]
            if isinstance(exc, NameError):
                if hasattr(exc, 'args') and exc.args and len(exc.args) > 0:
                    error_message = str(exc.args[0])
                    error_details.append(f"NameError: {error_message}")
                    # Extract variable name
                    if "'" in error_message or '"' in error_message:
                        import re
                        match = re.search(r"name\s+['\"]([^'\"]+)['\"]", error_message)
                        if match:
                            error_details.append(f"Undefined variable: '{match.group(1)}'")
                else:
                    error_message = repr(exc) if exc else "NameError (no details)"
                    error_details.append(f"NameError: {error_message}")
            else:
                if hasattr(exc, 'args') and exc.args:
                    error_message = str(exc.args[0]) if exc.args else str(exc)
                else:
                    error_message = str(exc) if exc else "Unknown error"
                error_details.append(f"{error_name}: {error_message}")
        except Exception as e:
            error_message = f"Error extracting message: {type(e).__name__}"
            error_details.append(f"Failed to extract error: {repr(e)}")
        
        # Build message
        message = f"Internal error: {error_name}: {error_message}"
        
        # Add traceback
        try:
            import traceback
            tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            error_details.append(f"Traceback: {tb_str[:2000]}")
        except Exception as e:
            error_details.append(f"Could not generate traceback: {type(e).__name__}")
        
        # If we still have no details, add at least something
        if not error_details:
            error_details = [f"{error_name}: {error_message}"]
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=laravel_response(
                success=False,
                message=message,
                errors={"server": error_details},
                data=None
            )
        )


def _log_security_event(
    request: Request,
    action: str,
    actor_user_id: Optional[str] = None
):
    """
    Log security events (401/403) for HIPAA compliance
    
    Args:
        request: FastAPI Request object
        action: Action type (UNAUTHORIZED_ACCESS or FORBIDDEN_ACCESS)
        actor_user_id: User ID if available (from request.state)
    """
    try:
        # Get database session from request state or create new one
        db = next(get_db())
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
        
        # Create audit log
        audit_service.create_audit_log(
            actor_user_id=actor_user_id,
            action=action,
            entity_type="security",
            entity_id=None,
            audit_metadata={
                "path": request.url.path,
                "method": request.method
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Do NOT fail request if logging fails
        logger.error(f"Failed to log security event: {str(e)}")


# Create application instance
app = create_application()


# Root endpoint (outside API versioning)
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "eClinic Backend API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


@app.get("/health", tags=["Health"])
async def health():
    """
    Health check endpoint
    Used by load balancers and monitoring systems
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_config=None,  # Use our custom logging
        workers=1 if settings.RELOAD else settings.WORKERS
    )
