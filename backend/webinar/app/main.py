from fastapi import FastAPI, HTTPException, status, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import logger
from app.api.rest import webinars, video_sessions
from app.core.security import get_current_user_id, extract_token_from_header
from app.core.exceptions import LaravelHTTPException, ValidationException, ForbiddenException, NotFoundException, UnauthorizedException
from typing import Optional


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Webinar Service...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Webinar Service...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Webinar service for healthcare platform with Agora integration",
    docs_url=None,  # We'll create custom docs that work with reverse proxy
    redoc_url=None,
    openapi_url="/openapi.json",
    root_path=settings.ROOT_PATH,
    lifespan=lifespan,
)


# Custom OpenAPI schema with security scheme for Swagger UI Authorize button
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Webinar service for healthcare platform with Agora integration",
        routes=app.routes,
    )
    
    # Add server configuration for reverse proxy
    if settings.ROOT_PATH:
        openapi_schema["servers"] = [
            {
                "url": settings.ROOT_PATH,
                "description": "Webinar Service API (via reverse proxy)"
            }
        ]
    
    # Add security scheme for Bearer token authentication
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token. Get your token from the main backend login endpoint: POST /backend/api-fast/api/v1/auth/login"
        }
    }
    
    # Add security requirement to all endpoints that require authentication
    # This makes Swagger UI show the Authorize button
    if "paths" in openapi_schema:
        for path_key, path in openapi_schema["paths"].items():
            # Skip docs and openapi endpoints
            if path_key in ["/docs", "/openapi.json", "/redoc"]:
                continue
            
            for method_key, method in path.items():
                if isinstance(method, dict):
                    # Check if endpoint has authorization parameter or is an API endpoint
                    has_auth_param = False
                    if "parameters" in method:
                        has_auth_param = any(
                            param.get("name") == "authorization" 
                            for param in method.get("parameters", [])
                        )
                    
                    # All /api endpoints and /health require authentication
                    requires_auth = (
                        has_auth_param or 
                        path_key.startswith("/api") or 
                        path_key == "/health"
                    )
                    
                    if requires_auth:
                        method["security"] = [{"BearerAuth": []}]
                        # Also update the authorization parameter to use the security scheme
                        if "parameters" in method:
                            for param in method["parameters"]:
                                if param.get("name") == "authorization":
                                    param["in"] = "header"
                                    param["name"] = "Authorization"
                                    param["required"] = True
                                    param["schema"] = {
                                        "type": "string",
                                        "format": "bearer",
                                        "example": "Bearer <your-jwt-token>"
                                    }
                                    if "description" not in param:
                                        param["description"] = "JWT Bearer token"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Exception handlers for Laravel-compatible error responses
@app.exception_handler(LaravelHTTPException)
async def laravel_exception_handler(request: Request, exc: LaravelHTTPException):
    """Handle Laravel-compatible exceptions and return proper JSON response"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    """Handle forbidden exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    """Handle unauthorized exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Readiness check - no auth (for load balancer / proxy health checks; 401 on /health causes 502)
@app.get("/ready")
async def ready():
    """Unauthenticated readiness; use this for nginx/load-balancer health_check. Returns 200 when process is up."""
    return {"status": "ok", "service": "webinar-service", "version": settings.APP_VERSION}


# Health check endpoint - requires authentication (detailed)
@app.get("/health")
async def health_check(
    authorization: Optional[str] = Header(None)
):
    """
    Health check endpoint - requires authentication.
    Returns service status and health information.
    For proxy/load balancer health checks use GET /ready (no auth).
    """
    try:
        # Verify token is provided and valid
        token = extract_token_from_header(authorization)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Verify token is valid (get user ID)
        user_id = await get_current_user_id(token)
        
        return {
            "status": "healthy",
            "service": "webinar-service",
            "version": settings.APP_VERSION,
            "authenticated_user": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


# Custom Swagger UI endpoint that works with reverse proxy
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI that correctly handles reverse proxy paths"""
    openapi_url = f"{settings.ROOT_PATH}/openapi.json" if settings.ROOT_PATH else "/openapi.json"
    
    return HTMLResponse(content=f"""
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
    """)

# Include routers
app.include_router(webinars.admin_router, prefix="/api/v1")
app.include_router(webinars.doctor_router, prefix="/api/v1")
app.include_router(webinars.patient_router, prefix="/api/v1")
# Video Sessions (proxy to main backend)
app.include_router(video_sessions.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
