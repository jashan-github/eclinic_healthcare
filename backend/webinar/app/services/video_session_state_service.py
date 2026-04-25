"""
Video Session State Machine Service
Enforces strict state transitions for HIPAA compliance

State Machine:
SCHEDULED → WAITING_ROOM → JOINING → DOCTOR_JOINED → IN_CALL → COMPLETED
    |            ↓              ↓
    |        EXPIRED        JOIN_FAILED
    |            ↓              ↓
    +--------→ DOCTOR_JOINED  (webinar: host go-live first, no waiting room)
    |        CANCELLED      (retry creates new session)
    +--------→ CANCELLED, EXPIRED
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from loguru import logger

from app.db.models_video_session import VideoSession, VideoSessionStatus, VideoSessionType
from app.core.exceptions import ValidationException, ForbiddenException
from app.core.config import settings


class VideoSessionStateService:
    """
    State machine service for video sessions
    
    Enforces strict state transitions to ensure:
    - No unauthorized state changes
    - Billing only starts when doctor joins
    - Patient waiting room is enforced
    - Join failures are handled correctly
    """
    
    # Valid state transitions (from_state -> [to_states])
    # SCHEDULED → DOCTOR_JOINED: allowed for webinars when host goes live first (no patient in waiting room)
    VALID_TRANSITIONS = {
        VideoSessionStatus.SCHEDULED: [
            VideoSessionStatus.WAITING_ROOM,
            VideoSessionStatus.JOINING,
            VideoSessionStatus.DOCTOR_JOINED,  # Webinar host go-live: host joins first
            VideoSessionStatus.CANCELLED,
            VideoSessionStatus.EXPIRED
        ],
        VideoSessionStatus.WAITING_ROOM: [
            VideoSessionStatus.JOINING,
            VideoSessionStatus.DOCTOR_JOINED,  # Host re-join: host goes live while audience in waiting room
            VideoSessionStatus.EXPIRED,
            VideoSessionStatus.CANCELLED
        ],
        VideoSessionStatus.JOINING: [
            VideoSessionStatus.DOCTOR_JOINED,
            VideoSessionStatus.IN_CALL,
            VideoSessionStatus.JOIN_FAILED,
            VideoSessionStatus.GRACE,  # Both left during join attempt – allow rejoin
            VideoSessionStatus.EXPIRED
        ],
        VideoSessionStatus.DOCTOR_JOINED: [
            VideoSessionStatus.IN_CALL,
            VideoSessionStatus.GRACE,
            VideoSessionStatus.COMPLETED,
            VideoSessionStatus.EXPIRED
        ],
        VideoSessionStatus.IN_CALL: [
            VideoSessionStatus.GRACE,
            VideoSessionStatus.COMPLETED,
            VideoSessionStatus.EXPIRED
        ],
        VideoSessionStatus.JOIN_FAILED: [
            VideoSessionStatus.SCHEDULED,  # Retry creates new session or allow rejoining
            VideoSessionStatus.EXPIRED,
            VideoSessionStatus.JOINING  # Allow direct rejoining from JOIN_FAILED
        ],
        VideoSessionStatus.GRACE: [
            VideoSessionStatus.COMPLETED,
            VideoSessionStatus.EXPIRED,
            VideoSessionStatus.SCHEDULED  # Allow rejoining by resetting to SCHEDULED
        ],
        VideoSessionStatus.COMPLETED: [
            VideoSessionStatus.SCHEDULED  # Allow rejoining by resetting to SCHEDULED
        ],
        VideoSessionStatus.EXPIRED: [],    # Terminal state
        VideoSessionStatus.CANCELLED: []   # Terminal state
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def can_transition(
        self,
        current_status: VideoSessionStatus,
        target_status: VideoSessionStatus
    ) -> bool:
        """
        Check if state transition is valid
        
        Args:
            current_status: Current state
            target_status: Target state
            
        Returns:
            True if transition is valid
        """
        allowed = self.VALID_TRANSITIONS.get(current_status, [])
        return target_status in allowed
    
    async def transition(
        self,
        session: VideoSession,
        target_status: VideoSessionStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VideoSession:
        """
        Transition session to new state
        
        This method enforces:
        - Valid state transitions only
        - Automatic timestamp updates
        - Billing start on DOCTOR_JOINED
        - Join watchdog setup on JOINING
        
        Args:
            session: Video session object
            target_status: Target state
            metadata: Optional metadata for state change
            
        Returns:
            Updated session object
            
        Raises:
            ValidationException: If transition is invalid
        """
        current_status = session.status
        
        # Check if transition is valid
        if not self.can_transition(current_status, target_status):
            raise ValidationException(
                message=f"Invalid state transition: {current_status.value} → {target_status.value}",
                errors={
                    "state": [
                        f"Cannot transition from {current_status.value} to {target_status.value}"
                    ]
                }
            )
        
        # Log transition
        logger.info(
            f"State transition: session {session.session_id} "
            f"{current_status.value} → {target_status.value}"
        )
        
        # Update status
        session.status = target_status
        
        # Handle state-specific logic
        # Use timezone-aware datetime
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        if target_status == VideoSessionStatus.WAITING_ROOM:
            # Patient entered waiting room
            if not session.patient_entered_waiting_room_at:
                session.patient_entered_waiting_room_at = now
                logger.info(f"Patient entered waiting room for session {session.session_id}")
        
        elif target_status == VideoSessionStatus.JOINING:
            # Join attempt started - set up 30-second watchdog
            session.join_attempt_started_at = now
            watchdog_seconds = getattr(settings, 'VIDEO_JOIN_WATCHDOG_SECONDS', 30)
            session.join_watchdog_expires_at = now + timedelta(seconds=watchdog_seconds)
            logger.info(
                f"Join attempt started for session {session.session_id}, "
                f"watchdog expires at {session.join_watchdog_expires_at}"
            )
        
        elif target_status == VideoSessionStatus.DOCTOR_JOINED:
            # Doctor successfully joined - START BILLING
            session.doctor_joined_at = now
            session.billing_started_at = now
            session.patient_token_expires_at = None  # Patient token not generated yet
            
            # Calculate waiting room duration (not billable)
            if session.patient_entered_waiting_room_at:
                waiting_duration = (now - session.patient_entered_waiting_room_at).total_seconds()
                session.waiting_room_duration_seconds = int(waiting_duration)
            
            logger.info(
                f"Doctor joined session {session.session_id} - BILLING STARTED at {now}"
            )
        
        elif target_status == VideoSessionStatus.IN_CALL:
            # Both parties in call
            if not session.call_started_at:
                session.call_started_at = now
            
            # Set patient joined timestamp if not set
            if not session.patient_joined_at:
                session.patient_joined_at = now
            
            logger.info(f"Call started for session {session.session_id}")
        
        elif target_status == VideoSessionStatus.JOIN_FAILED:
            # Join failed within 30 seconds
            session.last_error = metadata.get("error") if metadata else "Join attempt failed"
            session.error_code = metadata.get("error_code") if metadata else "JOIN_TIMEOUT"
            
            # Clear tokens (security: revoke access)
            session.doctor_token = None
            session.patient_token = None
            session.doctor_token_expires_at = None
            session.patient_token_expires_at = None
            
            # DO NOT start billing
            session.billing_started_at = None
            
            logger.warning(
                f"Join failed for session {session.session_id}: {session.last_error}"
            )
        
        elif target_status == VideoSessionStatus.GRACE:
            # Call ended, in grace period
            if not session.call_ended_at:
                session.call_ended_at = now
            
            # Calculate billable duration
            if session.billing_started_at:
                billable_seconds = (now - session.billing_started_at).total_seconds()
                session.billable_duration_seconds = max(0, int(billable_seconds))
            
            logger.info(
                f"Call ended for session {session.session_id}, "
                f"billable duration: {session.billable_duration_seconds}s"
            )
        
        elif target_status == VideoSessionStatus.COMPLETED:
            # Session completed successfully
            if not session.call_ended_at:
                session.call_ended_at = now
            
            # Final billing calculation
            if session.billing_started_at:
                billable_seconds = (now - session.billing_started_at).total_seconds()
                session.billable_duration_seconds = max(0, int(billable_seconds))
            
            logger.info(
                f"Session {session.session_id} completed, "
                f"total billable: {session.billable_duration_seconds}s"
            )
        
        elif target_status == VideoSessionStatus.EXPIRED:
            # Session expired (doctor no-show, timeout, etc.)
            if not session.call_ended_at:
                session.call_ended_at = now
            
            # No billing if doctor never joined
            if not session.billing_started_at:
                session.billable_duration_seconds = 0
                logger.info(f"Session {session.session_id} expired - NO BILLING (doctor never joined)")
            else:
                # Calculate partial billing if doctor joined but session expired
                billable_seconds = (now - session.billing_started_at).total_seconds()
                session.billable_duration_seconds = max(0, int(billable_seconds))
                logger.info(
                    f"Session {session.session_id} expired after doctor joined, "
                    f"billable: {session.billable_duration_seconds}s"
                )
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def check_join_watchdog(self, session: VideoSession) -> bool:
        """
        Check if join watchdog has expired
        
        If expired, automatically transition to JOIN_FAILED
        
        Args:
            session: Video session to check
            
        Returns:
            True if watchdog expired and session was updated
        """
        if session.status != VideoSessionStatus.JOINING:
            return False
        
        if not session.join_watchdog_expires_at:
            return False
        
        # Use timezone-aware datetime for comparison
        from datetime import timezone
        now = datetime.now(timezone.utc)
        watchdog_time = session.join_watchdog_expires_at
        if watchdog_time:
            if watchdog_time.tzinfo is None:
                # If naive, assume UTC
                watchdog_time = watchdog_time.replace(tzinfo=timezone.utc)
            else:
                # If already timezone-aware, convert to UTC for comparison
                watchdog_time = watchdog_time.astimezone(timezone.utc)
        if watchdog_time and now > watchdog_time:
            logger.warning(
                f"Join watchdog expired for session {session.session_id}, "
                f"transitioning to JOIN_FAILED"
            )
            await self.transition(
                session,
                VideoSessionStatus.JOIN_FAILED,
                metadata={
                    "error": "Join attempt timed out (30 seconds)",
                    "error_code": "JOIN_WATCHDOG_EXPIRED"
                }
            )
            return True
        
        return False
    
    async def check_expiry(self, session: VideoSession) -> bool:
        """
        Check if session has expired and transition if needed
        
        Args:
            session: Video session to check
            
        Returns:
            True if session was expired
        """
        if session.status in [
            VideoSessionStatus.COMPLETED,
            VideoSessionStatus.EXPIRED,
            VideoSessionStatus.CANCELLED
        ]:
            return False
        
        if session.is_expired():
            logger.info(f"Session {session.session_id} has expired")
            await self.transition(session, VideoSessionStatus.EXPIRED)
            return True
        
        return False
