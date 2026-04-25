"""
Login Attempt Service
Service for logging login attempts to the database
"""

from typing import Optional, Union
from uuid import UUID
from sqlalchemy.orm import Session
from loguru import logger
from fastapi import Request

from app.models.auth import LoginAttempt


class LoginAttemptService:
    """
    Service for logging login attempts
    """
    
    def __init__(self, db: Session):
        """
        Initialize login attempt service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def log_login_attempt(
        self,
        email: str,
        success: bool,
        user_id: Optional[Union[str, UUID]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoginAttempt:
        """
        Log a login attempt (successful or failed)
        
        Args:
            email: Email address used for login
            success: Whether the login was successful
            user_id: User ID if login was successful (None for failed attempts)
            ip_address: IP address of the request
            user_agent: User agent string
        
        Returns:
            Created LoginAttempt object
        """
        try:
            # Convert UUID to proper format
            user_uuid = None
            if user_id:
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
            
            login_attempt = LoginAttempt(
                user_id=user_uuid,
                email=email.lower(),
                ip_address=ip_address,
                user_agent=user_agent,
                success=success
            )
            
            self.db.add(login_attempt)
            self.db.commit()
            self.db.refresh(login_attempt)
            
            logger.debug(f"Login attempt logged: {email} - {'SUCCESS' if success else 'FAILED'}")
            
            return login_attempt
        
        except Exception as e:
            logger.error(f"Failed to log login attempt: {str(e)}")
            # Don't fail the login operation if logging fails
            self.db.rollback()
            return None
    
    def log_login_attempt_from_request(
        self,
        request: Request,
        email: str,
        success: bool,
        user_id: Optional[Union[str, UUID]] = None
    ) -> LoginAttempt:
        """
        Log a login attempt from a FastAPI Request object
        
        Args:
            request: FastAPI Request object
            email: Email address used for login
            success: Whether the login was successful
            user_id: User ID if login was successful
        
        Returns:
            Created LoginAttempt object
        """
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
        
        return self.log_login_attempt(
            email=email,
            success=success,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

