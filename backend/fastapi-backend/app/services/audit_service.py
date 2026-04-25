"""
Audit Service
Service for creating audit log entries in the database
"""

from typing import Optional, Dict, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session
from loguru import logger
from fastapi import Request

from app.models.audit import AuditLog
from app.core.config import settings


class AuditService:
    """
    Service for creating audit log entries
    """
    
    def __init__(self, db: Session):
        """
        Initialize audit service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_audit_log(
        self,
        actor_user_id: Optional[Union[str, UUID]],
        action: str,
        entity_type: str,
        entity_id: Optional[Union[str, UUID]] = None,
        audit_metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Create an audit log entry
        
        Args:
            actor_user_id: User who performed the action (None for system actions)
            action: Action performed (e.g., 'create', 'update', 'delete', 'view', 'login', 'logout')
            entity_type: Type of entity affected (e.g., 'user', 'appointment', 'prescription', 'patient')
            entity_id: ID of the affected entity (optional)
            audit_metadata: Additional metadata (JSONB)
            ip_address: IP address of the request
            user_agent: User agent string
        
        Returns:
            Created AuditLog object
        """
        if not settings.AUDIT_LOG_ENABLED:
            logger.debug("Audit logging is disabled, skipping audit log creation")
            return None
        
        try:
            # Convert UUIDs to proper format
            actor_uuid = None
            if actor_user_id:
                if isinstance(actor_user_id, str):
                    actor_uuid = UUID(actor_user_id)
                else:
                    actor_uuid = actor_user_id
            
            entity_uuid = None
            if entity_id:
                if isinstance(entity_id, str):
                    entity_uuid = UUID(entity_id)
                else:
                    entity_uuid = entity_id
            
            audit_log = AuditLog(
                actor_user_id=actor_uuid,
                action=action,
                entity_type=entity_type,
                entity_id=entity_uuid,
                audit_metadata=audit_metadata or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            logger.debug(f"Audit log created: {action} on {entity_type} {entity_id} by {actor_user_id}")
            
            return audit_log
        
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            # Don't fail the operation if audit logging fails
            self.db.rollback()
            return None
    
    def create_audit_log_from_request(
        self,
        request: Request,
        actor_user_id: Optional[Union[str, UUID]],
        action: str,
        entity_type: str,
        entity_id: Optional[Union[str, UUID]] = None,
        audit_metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Create an audit log entry from a FastAPI Request object
        
        Args:
            request: FastAPI Request object
            actor_user_id: User who performed the action
            action: Action performed
            entity_type: Type of entity affected
            entity_id: ID of the affected entity
            audit_metadata: Additional metadata
        
        Returns:
            Created AuditLog object
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
        
        return self.create_audit_log(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            audit_metadata=audit_metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )

