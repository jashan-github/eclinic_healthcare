"""
Video Session Model
HIPAA-compliant video call and webinar session management
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum as SQLEnum, Text, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime, timedelta
from app.db.session import Base


class VideoSessionStatus(str, enum.Enum):
    """Video session state machine states"""
    SCHEDULED = "scheduled"          # Session is scheduled but not started
    WAITING_ROOM = "waiting_room"     # Patient in waiting room, doctor not joined
    JOINING = "joining"              # Join attempt in progress (30s watchdog active)
    DOCTOR_JOINED = "doctor_joined"  # Doctor successfully joined, billing started
    IN_CALL = "in_call"              # Both parties in call
    JOIN_FAILED = "join_failed"       # Join attempt failed within 30s
    GRACE = "grace"                   # Call ended, in grace period
    COMPLETED = "completed"           # Call completed successfully
    EXPIRED = "expired"               # Session expired (doctor no-show, timeout, etc.)
    CANCELLED = "cancelled"            # Session cancelled before start


class VideoSessionType(str, enum.Enum):
    """Type of video session"""
    APPOINTMENT = "appointment"       # One-on-one appointment call
    WEBINAR = "webinar"               # Webinar with host and audience
    EMERGENCY = "emergency"           # Emergency/on-demand call


class VideoSession(Base):
    """
    Video session model for HIPAA-compliant video calls and webinars
    
    Key Features:
    - State machine enforced transitions
    - Secure channel naming (hash-based, no PHI)
    - Billing starts only when doctor joins
    - Patient waiting room enforcement
    - 30-second join watchdog
    - Full audit trail
    """
    
    __tablename__ = "video_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4(), nullable=False)
    
    # Session identification
    session_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True,
                       comment="Unique session identifier (UUID)")
    
    # Secure channel name (hash of session_id, no PHI)
    channel_name = Column(String(255), unique=True, nullable=False, index=True,
                         comment="Agora channel name (secure hash, no PHI)")
    
    # Session type
    session_type = Column(SQLEnum(VideoSessionType, native_enum=False, 
                                 values_callable=lambda x: [e.value for e in x]),
                         nullable=False, default=VideoSessionType.APPOINTMENT,
                         comment="Type of video session")
    
    # State machine
    status = Column(SQLEnum(VideoSessionStatus, native_enum=False,
                           values_callable=lambda x: [e.value for e in x]),
                   nullable=False, default=VideoSessionStatus.SCHEDULED, index=True,
                   comment="Current state in state machine")
    
    # Participants (no FK constraints - users table in separate service)
    doctor_id = Column(UUID(as_uuid=True), nullable=False, index=True,
                      comment="Doctor/host user ID")
    
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True,
                       comment="Patient/participant user ID (null for webinars)")
    
    # Appointment reference (if applicable) - no FK constraint
    appointment_id = Column(UUID(as_uuid=True), nullable=True, index=True,
                           comment="Associated appointment ID")
    
    # Webinar reference (if applicable)
    webinar_id = Column(UUID(as_uuid=True), ForeignKey("webinars.id", ondelete="SET NULL"),
                       nullable=True, index=True,
                       comment="Associated webinar ID")
    
    # Scheduling
    scheduled_start_time = Column(DateTime(timezone=True), nullable=True, index=True,
                                 comment="Scheduled start time (null for emergency calls)")
    
    scheduled_end_time = Column(DateTime(timezone=True), nullable=True,
                               comment="Scheduled end time")
    
    # Actual timestamps (for billing and audit)
    doctor_joined_at = Column(DateTime(timezone=True), nullable=True,
                             comment="Timestamp when doctor successfully joined (billing starts here)")
    
    patient_joined_at = Column(DateTime(timezone=True), nullable=True,
                              comment="Timestamp when patient successfully joined")
    
    call_started_at = Column(DateTime(timezone=True), nullable=True,
                            comment="Timestamp when both parties in call")
    
    call_ended_at = Column(DateTime(timezone=True), nullable=True,
                          comment="Timestamp when call ended")
    
    # Waiting room
    patient_entered_waiting_room_at = Column(DateTime(timezone=True), nullable=True,
                                            comment="When patient entered waiting room")
    
    waiting_room_duration_seconds = Column(Integer, nullable=True, default=0,
                                          comment="Total time patient spent in waiting room (not billed)")
    
    # Join watchdog (30-second timeout)
    join_attempt_started_at = Column(DateTime(timezone=True), nullable=True,
                                     comment="When join attempt started (for 30s watchdog)")
    
    join_watchdog_expires_at = Column(DateTime(timezone=True), nullable=True,
                                     comment="When join watchdog expires (30s after attempt start)")
    
    # Billing
    billing_started_at = Column(DateTime(timezone=True), nullable=True,
                               comment="When billing started (same as doctor_joined_at)")
    
    billable_duration_seconds = Column(Integer, nullable=True, default=0,
                                      comment="Total billable duration in seconds")
    
    # Agora tokens (encrypted, short-lived)
    doctor_token = Column(Text, nullable=True,
                         comment="Agora token for doctor (encrypted, expires in 15-60 min)")
    
    patient_token = Column(Text, nullable=True,
                          comment="Agora token for patient (encrypted, expires in 15-60 min)")
    
    doctor_token_expires_at = Column(DateTime(timezone=True), nullable=True,
                                    comment="Doctor token expiration")
    
    patient_token_expires_at = Column(DateTime(timezone=True), nullable=True,
                                     comment="Patient token expiration")
    
    # Retry logic
    retry_count = Column(Integer, nullable=False, default=0,
                        comment="Number of retry attempts")
    
    previous_session_id = Column(UUID(as_uuid=True), nullable=True,
                               comment="Previous session ID if this is a retry")
    
    # Grace period
    grace_period_seconds = Column(Integer, nullable=True, default=300,
                                 comment="Grace period after end_time before expiry (default 5 min)")
    
    # Readiness flags (for simplified join flow)
    doctor_ready = Column(Boolean, nullable=False, default=False,
                         comment="Doctor has indicated readiness to join")
    
    patient_ready = Column(Boolean, nullable=False, default=False,
                          comment="Patient has indicated readiness to join")
    
    # Confirmation flags (for join-success)
    doctor_confirmed_join = Column(Boolean, nullable=False, default=False,
                                   comment="Doctor has confirmed successful join via Agora")
    
    patient_confirmed_join = Column(Boolean, nullable=False, default=False,
                                    comment="Patient has confirmed successful join via Agora")
    
    # In-channel (for rejoin logic): True when user is currently in Agora channel, False on leave
    doctor_in_channel = Column(Boolean, nullable=False, default=False,
                               comment="Doctor is currently in Agora channel (set on join-success, clear on leave)")
    patient_in_channel = Column(Boolean, nullable=False, default=False,
                               comment="Patient is currently in Agora channel (set on join-success, clear on leave)")
    
    # Recording (with consent)
    recording_enabled = Column(Boolean, nullable=False, default=False,
                              comment="Whether recording is enabled (requires consent)")
    
    recording_started_at = Column(DateTime(timezone=True), nullable=True,
                                 comment="When recording started")
    
    recording_stopped_at = Column(DateTime(timezone=True), nullable=True,
                                 comment="When recording stopped")
    
    recording_resource_id = Column(String(255), nullable=True,
                                 comment="Agora recording resource ID")
    
    # Error handling
    last_error = Column(Text, nullable=True,
                       comment="Last error message if join failed")
    
    error_code = Column(String(50), nullable=True,
                       comment="Error code for join failure")
    
    # Metadata (using session_metadata as attribute name to avoid SQLAlchemy reserved word conflict)
    session_metadata = Column(JSONB, nullable=True, name="metadata",
                             comment="Additional metadata (device info, network, etc.)")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships (no FK constraints for users/appointments - they're in separate service)
    webinar = relationship("Webinar", foreign_keys=[webinar_id], lazy="select")
    
    def __repr__(self):
        return f"<VideoSession(session_id={self.session_id}, status={self.status.value}, type={self.session_type.value})>"
    
    def is_doctor_early_join_allowed(self, early_join_minutes: int = 5) -> bool:
        """Check if doctor can join early (5-10 minutes before scheduled start)"""
        if not self.scheduled_start_time:
            return True  # Emergency/on-demand calls
        
        # Use timezone-aware datetime for comparison
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # Ensure scheduled_start_time is timezone-aware
        scheduled_time = self.scheduled_start_time
        if scheduled_time.tzinfo is None:
            # If naive, assume UTC
            scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
        else:
            # If already timezone-aware, convert to UTC for comparison
            scheduled_time = scheduled_time.astimezone(timezone.utc)
        early_join_time = scheduled_time - timedelta(minutes=early_join_minutes)
        return now >= early_join_time
    
    def is_patient_early_join_allowed(self) -> bool:
        """Patient cannot join early - must wait in waiting room"""
        if not self.scheduled_start_time:
            return True  # Emergency/on-demand calls
        
        # Use timezone-aware datetime for comparison
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # Ensure scheduled_start_time is timezone-aware
        scheduled_time = self.scheduled_start_time
        if scheduled_time.tzinfo is None:
            # If naive, assume UTC
            scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
        else:
            # If already timezone-aware, convert to UTC for comparison
            scheduled_time = scheduled_time.astimezone(timezone.utc)
        return now >= scheduled_time
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        if self.status == VideoSessionStatus.EXPIRED:
            return True
        
        if self.scheduled_end_time:
            # Use timezone-aware datetime for comparison
            from datetime import timezone
            now = datetime.now(timezone.utc)
            # Ensure scheduled_end_time is timezone-aware
            end_time = self.scheduled_end_time
            if end_time.tzinfo is None:
                # If naive, assume UTC
                end_time = end_time.replace(tzinfo=timezone.utc)
            else:
                # If already timezone-aware, convert to UTC for comparison
                end_time = end_time.astimezone(timezone.utc)
            
            # Check if end_time is before start_time (invalid data)
            if self.scheduled_start_time:
                start_time = self.scheduled_start_time
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                else:
                    start_time = start_time.astimezone(timezone.utc)
                
                # If end_time is before start_time, don't expire based on end_time
                # This handles cases where invalid data was set
                if end_time < start_time:
                    # Only expire if we're past the start_time + a reasonable duration (e.g., 2 hours)
                    # This prevents immediate expiry for sessions with invalid end_time
                    reasonable_end = start_time + timedelta(hours=2)
                    grace_end = reasonable_end + timedelta(seconds=self.grace_period_seconds or 300)
                    return now > grace_end
            
            grace_end = end_time + timedelta(seconds=self.grace_period_seconds or 300)
            return now > grace_end
        
        return False
    
    def is_join_watchdog_expired(self) -> bool:
        """Check if 30-second join watchdog has expired"""
        if not self.join_watchdog_expires_at:
            return False
        
        # Use timezone-aware datetime for comparison
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # Ensure join_watchdog_expires_at is timezone-aware
        watchdog_time = self.join_watchdog_expires_at
        if watchdog_time.tzinfo is None:
            # If naive, assume UTC
            watchdog_time = watchdog_time.replace(tzinfo=timezone.utc)
        else:
            # If already timezone-aware, convert to UTC for comparison
            watchdog_time = watchdog_time.astimezone(timezone.utc)
        return now > watchdog_time
    
    def get_billable_duration(self) -> int:
        """Calculate billable duration in seconds"""
        if not self.billing_started_at:
            return 0
        
        # Use timezone-aware datetime
        from datetime import timezone
        end_time = self.call_ended_at or datetime.now(timezone.utc)
        # Ensure both times are timezone-aware
        billing_start = self.billing_started_at
        if billing_start.tzinfo is None:
            billing_start = billing_start.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        duration = (end_time - billing_start).total_seconds()
        return max(0, int(duration))
