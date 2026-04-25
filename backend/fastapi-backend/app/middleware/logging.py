"""
Logging middleware for request/response tracking
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from app.core.config import settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses
    Tracks request duration and generates request IDs
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""
        
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=client_ip,
            user_agent=request.headers.get("User-Agent", "unknown")
        ).info(f"Request started: {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.bind(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
                client_ip=client_ip
            ).info(
                f"Request completed: {request.method} {request.url.path} "
                f"- {response.status_code} - {round(duration * 1000, 2)}ms"
            )
            
            # Add headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(duration * 1000, 2))
            
            return response
        
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.bind(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration * 1000, 2),
                client_ip=client_ip,
                error=str(e)
            ).error(
                f"Request failed: {request.method} {request.url.path} - "
                f"{str(e)} - {round(duration * 1000, 2)}ms"
            )
            
            raise


