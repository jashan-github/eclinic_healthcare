"""
Video Session Audit Logging Service
HIPAA-compliant immutable audit trail

Logs all video session events for compliance:
- Join attempts
- Join success/failure
- Waiting room events
- Billing events
- State transitions
- Errors
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.models_video_session_audit import VideoSessionAuditLog


class VideoSessionAuditService:
    """
    Audit logging service for video sessions
    
    Creates immutable audit logs for all video session events
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_event(
        self,
        session_id: UUID,
        event_type: str,
        user_id: Optional[UUID] = None,
        user_role: Optional[str] = None,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> VideoSessionAuditLog:
        """
        Log a video session event
        
        Args:
            session_id: Video session ID
            event_type: Event type (join_attempt, join_success, etc.)
            user_id: User who triggered event
            user_role: User role
            previous_status: Previous session status
            new_status: New session status
            description: Human-readable description
            metadata: Additional metadata
            ip_address: User IP address
            user_agent: User agent string
            
        Returns:
            Created audit log entry
        """
        audit_log = VideoSessionAuditLog(
            session_id=session_id,
            event_type=event_type,
            event_description=description,
            user_id=user_id,
            user_role=user_role,
            previous_status=previous_status,
            new_status=new_status,
            event_timestamp=datetime.now(timezone.utc),
            audit_metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        
        logger.info(
            f"Audit log: session {session_id}, event: {event_type}, "
            f"user: {user_id} ({user_role})"
        )
        
        return audit_log
    
    async def log_join_attempt(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log join attempt"""
        return await self.log_event(
            session_id=session_id,
            event_type="join_attempt",
            user_id=user_id,
            user_role=user_role,
            description=f"{user_role.capitalize()} attempted to join video session",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_join_success(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str,
        previous_status: str,
        new_status: str,
        ip_address: Optional[str] = None
    ):
        """Log successful join"""
        return await self.log_event(
            session_id=session_id,
            event_type="join_success",
            user_id=user_id,
            user_role=user_role,
            previous_status=previous_status,
            new_status=new_status,
            description=f"{user_role.capitalize()} successfully joined video session",
            metadata={"billing_started": user_role == "doctor"},
            ip_address=ip_address
        )
    
    async def log_join_failure(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str,
        error: str,
        error_code: str,
        ip_address: Optional[str] = None
    ):
        """Log join failure"""
        return await self.log_event(
            session_id=session_id,
            event_type="join_failure",
            user_id=user_id,
            user_role=user_role,
            description=f"{user_role.capitalize()} failed to join: {error}",
            metadata={"error": error, "error_code": error_code},
            ip_address=ip_address
        )
    
    async def log_waiting_room_entry(
        self,
        session_id: UUID,
        patient_id: UUID,
        ip_address: Optional[str] = None
    ):
        """Log patient entering waiting room"""
        return await self.log_event(
            session_id=session_id,
            event_type="waiting_room_entry",
            user_id=patient_id,
            user_role="patient",
            description="Patient entered waiting room",
            ip_address=ip_address
        )
    
    async def log_state_transition(
        self,
        session_id: UUID,
        previous_status: str,
        new_status: str,
        triggered_by: Optional[UUID] = None,
        user_role: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log state transition"""
        return await self.log_event(
            session_id=session_id,
            event_type="state_transition",
            user_id=triggered_by,
            user_role=user_role,
            previous_status=previous_status,
            new_status=new_status,
            description=f"State transition: {previous_status} → {new_status}",
            metadata=metadata
        )
    
    async def log_billing_start(
        self,
        session_id: UUID,
        doctor_id: UUID
    ):
        """Log billing start (when doctor joins)"""
        return await self.log_event(
            session_id=session_id,
            event_type="billing_start",
            user_id=doctor_id,
            user_role="doctor",
            description="Billing started (doctor joined)",
            metadata={"billing_started_at": datetime.now(timezone.utc).isoformat()}
        )
    
    async def log_call_end(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str,
        billable_duration_seconds: int
    ):
        """Log call end"""
        return await self.log_event(
            session_id=session_id,
            event_type="call_end",
            user_id=user_id,
            user_role=user_role,
            description=f"Call ended by {user_role}",
            metadata={"billable_duration_seconds": billable_duration_seconds}
        )
    
    async def log_retry(
        self,
        previous_session_id: UUID,
        new_session_id: UUID,
        user_id: UUID,
        user_role: str,
        retry_count: int
    ):
        """Log retry attempt"""
        return await self.log_event(
            session_id=new_session_id,
            event_type="retry",
            user_id=user_id,
            user_role=user_role,
            description=f"Retry attempt #{retry_count}",
            metadata={
                "previous_session_id": str(previous_session_id),
                "retry_count": retry_count
            }
        )
