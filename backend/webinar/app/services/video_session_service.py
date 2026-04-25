"""
Video Session Service
Main service for HIPAA-compliant video call management (Async)

Orchestrates:
- Session creation
- Token generation
- Waiting room management
- Join handling
- Billing control
- Retry logic
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, text
from loguru import logger

from app.db.models_video_session import VideoSession, VideoSessionStatus, VideoSessionType
from app.db.models import Webinar
from app.services.agora_service import agora_service
from app.services.video_session_state_service import VideoSessionStateService
from app.core.exceptions import ValidationException, NotFoundException, ForbiddenException
from app.core.config import settings


class VideoSessionService:
    """
    Main video session service (async)
    
    Handles all video call operations with HIPAA compliance:
    - No PHI in channel names
    - Server-side token generation only
    - Billing starts only when doctor joins
    - Patient waiting room enforcement
    - 30-second join watchdog
    - Retry with new session instances
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_service = VideoSessionStateService(db)
    
    def _get_agora_app_id(self) -> str:
        """Get Agora App ID from settings"""
        return getattr(settings, 'AGORA_APP_ID', '')
    
    async def create_session(
        self,
        doctor_id: UUID,
        patient_id: Optional[UUID] = None,
        appointment_id: Optional[UUID] = None,
        webinar_id: Optional[UUID] = None,
        session_type: VideoSessionType = VideoSessionType.APPOINTMENT,
        scheduled_start_time: Optional[datetime] = None,
        scheduled_end_time: Optional[datetime] = None,
        recording_enabled: bool = False,
        doctor_display_name: Optional[str] = None,
        patient_display_name: Optional[str] = None,
    ) -> VideoSession:
        """
        Create a new video session
        
        Args:
            doctor_id: Doctor/host user ID
            patient_id: Patient user ID (null for webinars)
            appointment_id: Associated appointment ID
            webinar_id: Associated webinar ID
            session_type: Type of session
            scheduled_start_time: Scheduled start time
            scheduled_end_time: Scheduled end time
            recording_enabled: Whether recording is enabled
            doctor_display_name: Doctor name for channel label (DoctorName_PatientName_YYYYMMDD_HHmm)
            patient_display_name: Patient name for channel label
            
        Returns:
            Created video session
        """
        # Validate appointment/webinar ownership
        if appointment_id:
            # Query appointment from shared database using raw SQL
            appointment_query = text("""
                SELECT id, doctor_id, patient_id, deleted_at
                FROM appointments
                WHERE id = :appointment_id AND deleted_at IS NULL
            """)
            result = await self.db.execute(appointment_query, {"appointment_id": str(appointment_id)})
            appointment_row = result.fetchone()
            
            if not appointment_row:
                raise NotFoundException(
                    message="Appointment not found",
                    errors={"appointment_id": ["Appointment does not exist"]}
                )
            
            # Verify doctor owns appointment
            if str(appointment_row.doctor_id) != str(doctor_id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"appointment_id": ["You do not have access to this appointment"]}
                )
            
            # Verify patient matches if provided
            if patient_id and str(appointment_row.patient_id) != str(patient_id):
                raise ValidationException(
                    message="Patient mismatch",
                    errors={"patient_id": ["Patient does not match appointment"]}
                )
            
            # Use appointment patient if not provided
            if not patient_id:
                patient_id = appointment_row.patient_id
        
        if webinar_id:
            # Query webinar from local database
            result = await self.db.execute(
                select(Webinar).where(
                    and_(
                        Webinar.id == webinar_id,
                        Webinar.deleted_at.is_(None)
                    )
                )
            )
            webinar = result.scalar_one_or_none()
            
            if not webinar:
                raise NotFoundException(
                    message="Webinar not found",
                    errors={"webinar_id": ["Webinar does not exist"]}
                )
            
            # Verify doctor is webinar host
            if str(webinar.host_id) != str(doctor_id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"webinar_id": ["You are not the host of this webinar"]}
                )
        
        # Create session
        session_id = uuid4()
        
        # Channel name: doctor/patient names + appointment datetime when provided (appointment only); else hash-based
        use_participant_channel = (
            session_type == VideoSessionType.APPOINTMENT
            and doctor_display_name
            and patient_display_name
        )
        if use_participant_channel:
            channel_name = agora_service.generate_channel_name_from_participants(
                doctor_name=doctor_display_name,
                patient_name=patient_display_name,
                scheduled_start=scheduled_start_time,
                session_id=session_id,
            )
        else:
            channel_name = agora_service.generate_secure_channel_name(session_id)
        
        # Check for existing channel (shouldn't happen, but be safe)
        result = await self.db.execute(
            select(VideoSession).where(VideoSession.channel_name == channel_name)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            if use_participant_channel:
                # Collision on participant-based name: append extra suffix from new session_id
                session_id = uuid4()
                channel_name = agora_service.generate_channel_name_from_participants(
                    doctor_name=doctor_display_name,
                    patient_name=patient_display_name,
                    scheduled_start=scheduled_start_time,
                    session_id=session_id,
                )
            else:
                session_id = uuid4()
                channel_name = agora_service.generate_secure_channel_name(session_id)
        
        # Validate scheduled times
        if scheduled_start_time and scheduled_end_time:
            from datetime import timezone
            start = scheduled_start_time
            end = scheduled_end_time
            
            # Ensure both are timezone-aware for comparison
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            else:
                start = start.astimezone(timezone.utc)
            
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            else:
                end = end.astimezone(timezone.utc)
            
            if end < start:
                logger.warning(
                    f"Invalid scheduled times: end_time ({end}) is before start_time ({start}). "
                    f"Setting end_time to start_time + 1 hour as fallback."
                )
                # Set end_time to start_time + 1 hour as fallback
                scheduled_end_time = start + timedelta(hours=1)
        
        session = VideoSession(
            session_id=session_id,
            channel_name=channel_name,
            session_type=session_type,
            status=VideoSessionStatus.SCHEDULED,
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            webinar_id=webinar_id,
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            recording_enabled=recording_enabled,
            grace_period_seconds=getattr(settings, 'VIDEO_GRACE_PERIOD_SECONDS', 300)
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(
            f"Created video session {session_id} for doctor {doctor_id}, "
            f"type: {session_type.value}, channel: {channel_name}"
        )
        
        return session

    async def get_session_by_webinar_id(self, webinar_id: UUID) -> Optional[VideoSession]:
        """
        Get the active video session for a webinar (if any).
        Returns the most recent non-terminal session for this webinar.
        """
        result = await self.db.execute(
            select(VideoSession)
            .where(
                and_(
                    VideoSession.webinar_id == webinar_id,
                    VideoSession.session_type == VideoSessionType.WEBINAR,
                    VideoSession.deleted_at.is_(None),
                    VideoSession.status.notin_([
                        VideoSessionStatus.EXPIRED,
                        VideoSessionStatus.CANCELLED,
                    ]),
                )
            )
            .order_by(VideoSession.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def request_join(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str,
        webinar_host_user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Request to join a video session.

        When webinar_host_user_id is set (from X-Webinar-Host-Id header), treat that user as webinar host
        and return host token. Used when admin created the webinar for a doctor and doctor calls go-live.
        """
        result = await self.db.execute(
            select(VideoSession).where(VideoSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise NotFoundException(
                message="Video session not found",
                errors={"session_id": ["Session does not exist"]}
            )
        
        # Check expiry (with error handling for timezone issues)
        try:
            await self.state_service.check_expiry(session)
        except TypeError as e:
            # Catch timezone comparison errors in check_expiry
            if "offset-naive" in str(e) or "offset-aware" in str(e):
                logger.warning(
                    f"Timezone comparison error in check_expiry for session {session.session_id}: {e}. "
                    f"Skipping expiry check as fallback."
                )
                # Skip expiry check if there's a timezone error
            else:
                raise
        
        # Handle GRACE, COMPLETED, or JOIN_FAILED state - allow rejoining by resetting session
        if session.status in [VideoSessionStatus.GRACE, VideoSessionStatus.COMPLETED, VideoSessionStatus.JOIN_FAILED]:
            logger.info(
                f"Session {session.session_id} is in {session.status.value} state. Resetting to allow rejoining."
            )
            # Reset session state to allow rejoining
            await self._reset_session_for_rejoin(session)
        
        # When both have left but session still IN_CALL/JOINING (e.g. leave_channel not called), reset for rejoin.
        # Skip for webinars: host may not have called join-success yet, so doctor_in_channel can be False
        # while host is actually live; we must not reset and must give audience a token when DOCTOR_JOINED.
        if (
            session.session_type != VideoSessionType.WEBINAR
            and session.status in [
                VideoSessionStatus.IN_CALL,
                VideoSessionStatus.DOCTOR_JOINED,
                VideoSessionStatus.JOINING,
            ]
        ):
            doctor_in = getattr(session, "doctor_in_channel", False)
            patient_in = getattr(session, "patient_in_channel", False)
            if not doctor_in and not patient_in:
                logger.info(
                    f"Session {session.session_id} in {session.status.value} with both left; "
                    f"transitioning to GRACE and resetting for rejoin."
                )
                await self.state_service.transition(session, VideoSessionStatus.GRACE)
                await self._reset_session_for_rejoin(session)
        
        if session.status == VideoSessionStatus.EXPIRED:
            # Provide detailed expiry information
            expiry_details = {}
            if session.scheduled_end_time:
                from datetime import timezone
                end_time = session.scheduled_end_time
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)
                else:
                    end_time = end_time.astimezone(timezone.utc)
                grace_period = session.grace_period_seconds or 300
                grace_end = end_time + timedelta(seconds=grace_period)
                expiry_details = {
                    "scheduled_end_time": end_time.isoformat(),
                    "grace_period_seconds": grace_period,
                    "grace_end_time": grace_end.isoformat(),
                    "current_time": datetime.now(timezone.utc).isoformat()
                }
            
            raise ValidationException(
                message="Session has expired",
                errors={
                    "session": [
                        f"This video session has expired. "
                        f"Scheduled end time: {session.scheduled_end_time.strftime('%Y-%m-%d %H:%M:%S UTC') if session.scheduled_end_time else 'Not set'}. "
                        f"Grace period ended: {(session.scheduled_end_time + timedelta(seconds=session.grace_period_seconds or 300)).strftime('%Y-%m-%d %H:%M:%S UTC') if session.scheduled_end_time else 'N/A'}. "
                        f"Current time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}. "
                        f"You cannot join an expired session."
                    ],
                    "session_status": ["Session status is EXPIRED"],
                    "expiry_details": expiry_details,
                    "action": ["This session is no longer available. Please create a new session if needed."]
                }
            )
        
        # Verify user has access
        # For webinars: treat as host if backend sent X-Webinar-Host-Id (go-live), or session creator, or webinar host
        if session.session_type == VideoSessionType.WEBINAR:
            if webinar_host_user_id is not None and str(webinar_host_user_id) == str(user_id):
                return await self._handle_doctor_join(session, user_id)
            if str(session.doctor_id) == str(user_id):
                return await self._handle_doctor_join(session, user_id)
            if session.webinar_id:
                result = await self.db.execute(
                    select(Webinar).where(Webinar.id == session.webinar_id)
                )
                webinar = result.scalar_one_or_none()
                if webinar and str(webinar.host_id) == str(user_id):
                    return await self._handle_doctor_join(session, user_id)
        if user_role == "doctor":
            # For appointments: doctor must be the session doctor
            # For webinars: doctor who is not host joins as audience (handled above)
            if session.session_type == VideoSessionType.APPOINTMENT:
                if str(session.doctor_id) != str(user_id):
                    raise ForbiddenException(
                        message="Access denied",
                        errors={"user": ["You are not the doctor/host for this session"]}
                    )
            elif session.session_type == VideoSessionType.WEBINAR:
                # Doctor as participant (not host): route to audience flow
                return await self._handle_webinar_audience_join(session, user_id)
        else:
            # Patient or other role: for appointments must be the patient; for webinars join as audience
            if session.session_type == VideoSessionType.APPOINTMENT:
                if session.patient_id and str(session.patient_id) != str(user_id):
                    raise ForbiddenException(
                        message="Access denied",
                        errors={"user": ["You are not the patient for this session"]}
                    )
            elif session.session_type == VideoSessionType.WEBINAR:
                # For webinars, any authenticated user can join as audience
                if session.webinar_id:
                    result = await self.db.execute(
                        select(Webinar).where(Webinar.id == session.webinar_id)
                    )
                    webinar = result.scalar_one_or_none()
                    if webinar and webinar.visibility == "private":
                        # For private webinars, allow if registered (payment check is in _handle_webinar_audience_join)
                        pass
        
        # Rejoin: if call is active (IN_CALL or JOINING) and the other participant is still in channel, return token directly
        if session.session_type == VideoSessionType.APPOINTMENT and session.status in [
            VideoSessionStatus.IN_CALL,
            VideoSessionStatus.JOINING,
        ]:
            patient_in = getattr(session, "patient_in_channel", False)
            doctor_in = getattr(session, "doctor_in_channel", False)
            other_in_channel = patient_in if user_role == "doctor" else doctor_in
            if other_in_channel:
                # Other participant still in call → rejoin with fresh token, no waiting room
                pkg = agora_service.generate_token_for_user(
                    session_id=session.session_id,
                    user_id=user_id,
                    role="publisher",
                    expiry_minutes=getattr(settings, "AGORA_TOKEN_EXPIRY_MINUTES", 60),
                    channel_name=session.channel_name,
                )
                await self.db.commit()
                logger.info(
                    f"Rejoin: {user_role} {user_id} rejoining session {session.session_id} "
                    f"(other participant still in channel)"
                )
                return {
                    "status": session.status.value,
                    "token": pkg["token_plain"],
                    "channel_name": session.channel_name,
                    "app_id": self._get_agora_app_id(),
                    "waiting_room": False,
                    "both_ready": True,
                    "message": "Rejoining call. Other participant is still in the channel.",
                    "doctor_ready": session.doctor_ready,
                    "patient_ready": session.patient_ready,
                }
        
        # Handle doctor/host join
        if user_role == "doctor":
            return await self._handle_doctor_join(session, user_id)
        
        # Handle patient/audience join
        else:
            # For webinars, treat as audience join
            if session.session_type == VideoSessionType.WEBINAR:
                return await self._handle_webinar_audience_join(session, user_id)
            else:
                return await self._handle_patient_join(session, user_id)
    
    async def _handle_doctor_join(
        self,
        session: VideoSession,
        doctor_id: UUID
    ) -> Dict[str, Any]:
        """Handle doctor/host join request - simplified flow"""
        from datetime import timezone

        # Webinar host: no patient to wait for — give host token immediately
        if session.session_type == VideoSessionType.WEBINAR:
            session.doctor_ready = True
            session.doctor_joined_at = datetime.now(timezone.utc)
            if session.status != VideoSessionStatus.DOCTOR_JOINED and session.status != VideoSessionStatus.IN_CALL:
                await self.state_service.transition(session, VideoSessionStatus.DOCTOR_JOINED)
            token_pkg = agora_service.generate_token_for_user(
                session_id=session.session_id,
                user_id=doctor_id,
                role="publisher",
                expiry_minutes=getattr(settings, "AGORA_TOKEN_EXPIRY_MINUTES", 60),
                channel_name=session.channel_name,
            )
            await self.db.commit()
            logger.info(
                f"Webinar host {doctor_id} joined session {session.session_id}"
            )
            return {
                "status": session.status.value,
                "token": token_pkg["token_plain"],
                "channel_name": session.channel_name,
                "app_id": self._get_agora_app_id(),
                "waiting_room": False,
                "message": "You are the host. You can now stream to the audience.",
                "doctor_ready": True,
                "patient_ready": False,
                "both_ready": True,
                "session_type": "webinar",
            }
        # Appointment flow: mark doctor ready and wait for patient
        session.doctor_ready = True
        session.doctor_joined_at = datetime.now(timezone.utc)

        logger.info(
            f"Doctor {doctor_id} marked as ready for session {session.session_id}"
        )

        # Check if both are ready - if so, start the call
        if session.doctor_ready and session.patient_ready:
            return await self._start_call_when_both_ready(session, doctor_id)

        # If patient not ready yet, wait
        await self.db.commit()

        return {
            "status": session.status.value,
            "token": None,  # Token will be generated when both are ready
            "channel_name": session.channel_name,
            "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
            "waiting_room": True,
            "message": "Waiting for patient to join. Call will start when both parties are ready.",
            "doctor_ready": True,
            "patient_ready": session.patient_ready,
            "both_ready": False
        }
    
    async def _handle_patient_join(
        self,
        session: VideoSession,
        patient_id: UUID
    ) -> Dict[str, Any]:
        """Handle patient join request - simplified flow"""
        # Mark patient as ready (don't generate token yet)
        session.patient_ready = True
        from datetime import timezone
        session.patient_joined_at = datetime.now(timezone.utc)
        
        logger.info(
            f"Patient {patient_id} marked as ready for session {session.session_id}"
        )
        
        # Check if both are ready - if so, start the call
        if session.doctor_ready and session.patient_ready:
            return await self._start_call_when_both_ready(session, patient_id)
        
        # If doctor not ready yet, wait
        await self.db.commit()
        
        return {
            "status": session.status.value,
            "token": None,  # Token will be generated when both are ready
            "channel_name": session.channel_name,
            "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
            "waiting_room": True,
            "message": "Waiting for doctor to join. Call will start when both parties are ready.",
            "doctor_ready": session.doctor_ready,
            "patient_ready": True,
            "both_ready": False
        }
    
    async def _start_call_when_both_ready(
        self,
        session: VideoSession,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Start the video call when both doctor and patient are ready.
        This method:
        1. Generates tokens for both parties
        2. Starts the watchdog
        3. Transitions to JOINING state
        4. Publishes join data via Redis
        """
        from datetime import timezone, timedelta
        
        logger.info(
            f"Both parties ready for session {session.session_id}. Starting call..."
        )
        
        # Transition to JOINING state
        if session.status != VideoSessionStatus.JOINING:
            await self.state_service.transition(session, VideoSessionStatus.JOINING)
        
        # Generate doctor token (channel_name must match session.channel_name for client join)
        doctor_token_package = agora_service.generate_token_for_user(
            session_id=session.session_id,
            user_id=session.doctor_id,
            role="publisher",
            expiry_minutes=getattr(settings, 'AGORA_TOKEN_EXPIRY_MINUTES', 60),
            channel_name=session.channel_name,
        )
        
        # Generate patient token
        patient_token_package = agora_service.generate_token_for_user(
            session_id=session.session_id,
            user_id=session.patient_id,
            role="publisher",
            expiry_minutes=getattr(settings, 'AGORA_TOKEN_EXPIRY_MINUTES', 60),
            channel_name=session.channel_name,
        )
        
        # Store encrypted tokens
        session.doctor_token = doctor_token_package["token"]
        session.doctor_token_expires_at = doctor_token_package["expires_at"]
        session.patient_token = patient_token_package["token"]
        session.patient_token_expires_at = patient_token_package["expires_at"]
        
        # Start watchdog (30 seconds)
        now = datetime.now(timezone.utc)
        session.join_attempt_started_at = now
        session.join_watchdog_expires_at = now + timedelta(seconds=30)
        
        # Set call started timestamp
        session.call_started_at = now
        session.billing_started_at = now
        
        await self.db.commit()
        
        # Prepare join data to publish
        join_data = {
            "type": "call_started",
            "session_id": str(session.session_id),
            "channel_name": session.channel_name,
            "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
            "doctor_token": doctor_token_package["token_plain"],
            "patient_token": patient_token_package["token_plain"],
            "watchdog_expires_at": session.join_watchdog_expires_at.isoformat(),
            "status": session.status.value,
            "message": "Both parties are ready. Video call is starting."
        }
        
        # Publish join data via Redis
        try:
            from app.services.video_session_redis_service import VideoSessionRedisService
            redis_service = VideoSessionRedisService()
            await redis_service.connect()
            await redis_service.publish_waiting_room_event(
                session_id=session.session_id,
                event_type="call_started",
                data=join_data
            )
            logger.info(
                f"Published call start data for session {session.session_id} via Redis"
            )
        except Exception as e:
            logger.warning(
                f"Failed to publish call start data via Redis for session {session.session_id}: {e}"
            )
        
        # Determine which token to return based on user role
        is_doctor = str(user_id) == str(session.doctor_id)
        user_token = doctor_token_package["token_plain"] if is_doctor else patient_token_package["token_plain"]
        
        logger.info(
            f"Call started for session {session.session_id}. "
            f"Watchdog expires at {session.join_watchdog_expires_at.isoformat()}"
        )
        
        return {
            "status": session.status.value,
            "token": user_token,
            "channel_name": session.channel_name,
            "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
            "waiting_room": False,
            "message": "Both parties are ready. Video call is starting. You have 30 seconds to join successfully.",
            "doctor_ready": True,
            "patient_ready": True,
            "both_ready": True,
            "watchdog_expires_at": session.join_watchdog_expires_at.isoformat(),
            "join_data": join_data  # Include full join data for reference
        }
    
    async def _generate_patient_token(
        self,
        session: VideoSession,
        patient_id: UUID
    ) -> Dict[str, Any]:
        """Generate patient token (only after doctor joined)"""
        # Generate patient token (channel_name must match session.channel_name for client join)
        token_package = agora_service.generate_token_for_user(
            session_id=session.session_id,
            user_id=patient_id,
            role="publisher",
            expiry_minutes=getattr(settings, 'AGORA_TOKEN_EXPIRY_MINUTES', 60),
            channel_name=session.channel_name,
        )
        
        # Store encrypted token
        session.patient_token = token_package["token"]
        session.patient_token_expires_at = token_package["expires_at"]
        
        # Transition to IN_CALL if not already
        if session.status == VideoSessionStatus.DOCTOR_JOINED:
            await self.state_service.transition(session, VideoSessionStatus.IN_CALL)
        
        await self.db.commit()
        
        logger.info(
            f"Patient token generated for session {session.session_id} "
            f"(doctor already joined)"
        )
        
        return {
            "status": session.status.value,
            "token": token_package["token_plain"],
            "channel_name": session.channel_name,
            "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
            "waiting_room": False,
            "message": "Doctor has joined. You can now join the call.",
            "doctor_joined": True
        }
    
    async def _handle_webinar_audience_join(
        self,
        session: VideoSession,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Handle webinar audience/participant join request"""
        # For webinars, audience can join if:
        # 1. Doctor/host has already joined, OR
        # 2. It's after scheduled start time
        
        # Check if webinar is paid and user has paid (host bypasses payment check)
        if session.webinar_id:
            result = await self.db.execute(
                select(Webinar).where(Webinar.id == session.webinar_id)
            )
            webinar = result.scalar_one_or_none()
            
            # Host can always join without payment check
            is_host = webinar and str(webinar.host_id) == str(user_id)
            
            if webinar and webinar.pricing_type == "paid" and not is_host:
                # Check if user has completed payment for this webinar
                # Query webinar_payments table from shared database
                payment_query = text("""
                    SELECT id, status, amount, currency
                    FROM webinar_payments
                    WHERE webinar_id = :webinar_id 
                      AND user_id = :user_id 
                      AND status = 'COMPLETED'
                    LIMIT 1
                """)
                payment_result = await self.db.execute(
                    payment_query,
                    {
                        "webinar_id": str(session.webinar_id),
                        "user_id": str(user_id)
                    }
                )
                payment_row = payment_result.fetchone()
                
                if not payment_row:
                    # User hasn't paid for this paid webinar
                    raise ForbiddenException(
                        message="Payment required",
                        errors={
                            "payment": [
                                f"This is a paid webinar. Please complete payment to join. "
                                f"Webinar price: {webinar.price}"
                            ],
                            "webinar_id": [str(session.webinar_id)],
                            "pricing_type": ["paid"],
                            "action": ["Please complete payment before joining this webinar"]
                        }
                    )
                
                logger.info(
                    f"User {user_id} has completed payment for paid webinar {session.webinar_id}. "
                    f"Payment ID: {payment_row.id}"
                )
            elif is_host and webinar and webinar.pricing_type == "paid":
                logger.info(
                    f"Host {user_id} joining paid webinar {session.webinar_id} (payment check bypassed)"
                )
        
        # Check if doctor/host has joined
        if session.status in [VideoSessionStatus.DOCTOR_JOINED, VideoSessionStatus.IN_CALL]:
            # Generate audience token (channel_name must match session.channel_name for client join)
            token_package = agora_service.generate_token_for_user(
                session_id=session.session_id,
                user_id=user_id,
                role="publisher",  # Audience can publish (speak/share video)
                expiry_minutes=getattr(settings, 'AGORA_TOKEN_EXPIRY_MINUTES', 60),
                channel_name=session.channel_name,
            )
            
            # For webinars, we don't store individual audience tokens
            # Each participant gets a fresh token on join
            
            logger.info(
                f"Webinar audience {user_id} joined session {session.session_id} "
                f"(host already joined)"
            )
            
            return {
                "status": session.status.value,
                "token": token_package["token_plain"],
                "channel_name": session.channel_name,
                "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
                "waiting_room": False,
                "message": "Host has joined. You can now join the webinar.",
                "doctor_joined": True,
                "session_type": "webinar"
            }
        
        # If host not joined yet, check if it's after scheduled start time
        if session.scheduled_start_time:
            now = datetime.now(timezone.utc)
            # Ensure scheduled_start_time is timezone-aware for comparison
            scheduled_time = session.scheduled_start_time
            if scheduled_time.tzinfo is None:
                scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
            else:
                scheduled_time = scheduled_time.astimezone(timezone.utc)
            if now < scheduled_time:
                # Too early - enter waiting room
                if session.status == VideoSessionStatus.SCHEDULED:
                    await self.state_service.transition(session, VideoSessionStatus.WAITING_ROOM)
                
                logger.info(
                    f"Webinar audience {user_id} entered waiting room for session {session.session_id}"
                )
                
                return {
                    "status": session.status.value,
                    "token": None,
                    "channel_name": session.channel_name,
                    "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
                    "waiting_room": True,
                    "message": "Waiting for host to join. You will be notified when ready.",
                    "doctor_joined": False,
                    "session_type": "webinar"
                }
        
        # If no scheduled time or after start time, allow join but no token until host joins
        if session.status == VideoSessionStatus.SCHEDULED:
            await self.state_service.transition(session, VideoSessionStatus.WAITING_ROOM)
        
        logger.info(
            f"Webinar audience {user_id} entered waiting room for session {session.session_id}"
        )
        
        return {
            "status": session.status.value,
            "token": None,
            "channel_name": session.channel_name,
            "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
            "waiting_room": True,
            "message": "Waiting for host to join. You will be notified when ready.",
            "doctor_joined": False,
            "session_type": "webinar"
        }
    
    async def confirm_join_success(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str
    ) -> VideoSession:
        """
        Confirm successful join (called when Agora reports join success)
        
        This is critical for billing - billing starts when doctor confirms join
        
        Args:
            session_id: Video session ID
            user_id: User who joined
            user_role: User role
            
        Returns:
            Updated session
        """
        result = await self.db.execute(
            select(VideoSession).where(VideoSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise NotFoundException(
                message="Video session not found",
                errors={"session_id": ["Session does not exist"]}
            )
        
        # Check watchdog manually (don't auto-transition to JOIN_FAILED in join-success)
        # Allow a grace period (60 seconds total) for network delays and Agora connection
        from datetime import timezone
        now = datetime.now(timezone.utc)
        watchdog_expired = False
        
        if session.join_watchdog_expires_at:
            watchdog_time = session.join_watchdog_expires_at
            if watchdog_time.tzinfo is None:
                watchdog_time = watchdog_time.replace(tzinfo=timezone.utc)
            else:
                watchdog_time = watchdog_time.astimezone(timezone.utc)
            
            # Extended grace period: 30 seconds watchdog + 30 seconds grace = 60 seconds total
            grace_period = timedelta(seconds=30)
            elapsed_seconds = (now - watchdog_time).total_seconds()
            
            if now > watchdog_time + grace_period:
                # Truly expired - reject with detailed error
                watchdog_expired = True
                raise ValidationException(
                    message="Join attempt timed out",
                    errors={
                        "join": [
                            f"Join attempt timed out. You have 60 seconds total (30s watchdog + 30s grace period) "
                            f"to complete the join process after requesting. "
                            f"Watchdog expired at {watchdog_time.strftime('%Y-%m-%d %H:%M:%S UTC')}, "
                            f"current time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}, "
                            f"elapsed: {int(elapsed_seconds)} seconds. "
                            f"Please call /join endpoint again to start a new join attempt."
                        ],
                        "timeout_details": {
                            "watchdog_expired_at": watchdog_time.isoformat(),
                            "current_time": now.isoformat(),
                            "elapsed_seconds": int(elapsed_seconds),
                            "grace_period_seconds": 30,
                            "total_allowed_seconds": 60
                        },
                        "action": ["Call /join endpoint again to start a new join attempt"]
                    }
                )
            elif now > watchdog_time:
                # Within grace period - allow but log warning
                logger.warning(
                    f"Join success confirmed after watchdog expiry but within grace period "
                    f"for session {session.session_id}. Watchdog: {watchdog_time.isoformat()}, "
                    f"Current: {now.isoformat()}"
                )
        else:
            # No watchdog set - shouldn't happen, but allow
            logger.warning(
                f"No watchdog set for session {session.session_id} during join success confirmation"
            )
        
        # Simplified flow: Mark confirmation and check if both confirmed
        is_doctor = user_role == "doctor"
        
        # Mark confirmation and in-channel (for rejoin logic)
        if is_doctor:
            session.doctor_confirmed_join = True
            session.doctor_in_channel = True
            if not session.doctor_joined_at:
                session.doctor_joined_at = now
        else:
            session.patient_confirmed_join = True
            session.patient_in_channel = True
            if not session.patient_joined_at:
                session.patient_joined_at = now
        
        # Check if both confirmed - if so, transition to IN_CALL
        both_confirmed = session.doctor_confirmed_join and session.patient_confirmed_join
        
        if both_confirmed:
            # Both confirmed - transition to IN_CALL
            if session.status == VideoSessionStatus.JOINING:
                await self.state_service.transition(session, VideoSessionStatus.IN_CALL)
            elif session.status == VideoSessionStatus.DOCTOR_JOINED:
                await self.state_service.transition(session, VideoSessionStatus.IN_CALL)
            
            # Publish call started event
            try:
                from app.services.video_session_redis_service import VideoSessionRedisService
                redis_service = VideoSessionRedisService()
                await redis_service.connect()
                await redis_service.publish_waiting_room_event(
                    session_id=session.session_id,
                    event_type="both_joined",
                    data={
                        "session_id": str(session.session_id),
                        "status": session.status.value,
                        "message": "Both parties have successfully joined the call."
                    }
                )
                logger.info(
                    f"Published both_joined event for session {session.session_id} via Redis"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to publish both_joined event via Redis for session {session.session_id}: {e}"
                )
        elif is_doctor:
            # Only doctor confirmed - transition to DOCTOR_JOINED (billing starts)
            if session.status == VideoSessionStatus.JOINING:
                await self.state_service.transition(session, VideoSessionStatus.DOCTOR_JOINED)
        
        # Commit changes
        await self.db.commit()
        
        # Log confirmation
        logger.info(
            f"{user_role.capitalize()} {user_id} confirmed join success for session {session.session_id}. "
            f"Doctor confirmed: {session.doctor_confirmed_join}, Patient confirmed: {session.patient_confirmed_join}, "
            f"Both confirmed: {both_confirmed}, Status: {session.status.value}"
        )
        
        return session
    
    async def handle_join_failure(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str,
        error: str,
        error_code: str = "JOIN_FAILED"
    ) -> VideoSession:
        """
        Handle join failure (called when Agora reports join failure or timeout)
        
        Args:
            session_id: Video session ID
            user_id: User who failed to join
            user_role: User role
            error: Error message
            error_code: Error code
            
        Returns:
            Updated session
        """
        result = await self.db.execute(
            select(VideoSession).where(VideoSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise NotFoundException(
                message="Video session not found",
                errors={"session_id": ["Session does not exist"]}
            )
        
        # Only transition to JOIN_FAILED if in JOINING state
        if session.status == VideoSessionStatus.JOINING:
            await self.state_service.transition(
                session,
                VideoSessionStatus.JOIN_FAILED,
                metadata={"error": error, "error_code": error_code}
            )
            
            logger.warning(
                f"Join failed for {user_role} {user_id} in session {session.session_id}: {error}"
            )
        
        return session
    
    async def retry_call(
        self,
        previous_session_id: UUID,
        user_id: UUID,
        user_role: str
    ) -> VideoSession:
        """
        Retry a failed call by creating a new session instance
        
        CRITICAL: Creates NEW session with NEW channel and NEW tokens
        Previous session is marked as failed
        
        Args:
            previous_session_id: Previous failed session ID
            user_id: User requesting retry
            user_role: User role
            
        Returns:
            New video session
        """
        # Get previous session
        result = await self.db.execute(
            select(VideoSession).where(VideoSession.session_id == previous_session_id)
        )
        previous_session = result.scalar_one_or_none()
        
        if not previous_session:
            raise NotFoundException(
                message="Previous session not found",
                errors={"session_id": ["Previous session does not exist"]}
            )
        
        # Verify user has access
        if user_role == "doctor":
            if str(previous_session.doctor_id) != str(user_id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"user": ["You are not the doctor for this session"]}
                )
        else:
            if previous_session.patient_id and str(previous_session.patient_id) != str(user_id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"user": ["You are not the patient for this session"]}
                )
        
        # Create new session (new channel, new tokens)
        new_session = await self.create_session(
            doctor_id=previous_session.doctor_id,
            patient_id=previous_session.patient_id,
            appointment_id=previous_session.appointment_id,
            webinar_id=previous_session.webinar_id,
            session_type=previous_session.session_type,
            scheduled_start_time=previous_session.scheduled_start_time,
            scheduled_end_time=previous_session.scheduled_end_time,
            recording_enabled=previous_session.recording_enabled
        )
        
        # Link to previous session
        new_session.previous_session_id = previous_session_id
        new_session.retry_count = previous_session.retry_count + 1
        
        await self.db.commit()
        
        logger.info(
            f"Retry call created: new session {new_session.session_id} "
            f"(retry #{new_session.retry_count} from {previous_session_id})"
        )
        
        return new_session
    
    async def end_call(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str
    ) -> VideoSession:
        """
        End a video call
        
        Transitions to GRACE period, then COMPLETED
        
        Args:
            session_id: Video session ID
            user_id: User ending the call
            user_role: User role
            
        Returns:
            Updated session
        """
        result = await self.db.execute(
            select(VideoSession).where(VideoSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise NotFoundException(
                message="Video session not found",
                errors={"session_id": ["Session does not exist"]}
            )
        
        # Verify user has access
        if user_role == "doctor":
            if str(session.doctor_id) != str(user_id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"user": ["You are not the doctor for this session"]}
                )
        else:
            if session.patient_id and str(session.patient_id) != str(user_id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"user": ["You are not the patient for this session"]}
                )
        
        # Transition to GRACE and clear in-channel (so rejoin goes to waiting room if both left)
        if session.status in [VideoSessionStatus.IN_CALL, VideoSessionStatus.DOCTOR_JOINED]:
            session.doctor_in_channel = False
            session.patient_in_channel = False
            await self.state_service.transition(session, VideoSessionStatus.GRACE)
            logger.info(
                f"Call ended for session {session.session_id} by {user_role} {user_id}, "
                f"billable duration: {session.billable_duration_seconds}s"
            )
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def leave_channel(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str
    ) -> VideoSession:
        """
        Mark user as left the Agora channel (e.g. page close, disconnect).
        Called by frontend when user leaves the channel, or by Agora webhook.
        Used for rejoin logic: if other participant is still in_channel, rejoining
        user gets both_ready + token; if none in channel, they go to waiting room.
        """
        result = await self.db.execute(
            select(VideoSession).where(VideoSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise NotFoundException(
                message="Video session not found",
                errors={"session_id": ["Session does not exist"]}
            )
        if user_role == "doctor":
            if str(session.doctor_id) != str(user_id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"user": ["You are not the doctor for this session"]}
                )
            session.doctor_in_channel = False
            logger.info(f"Doctor {user_id} left channel for session {session.session_id}")
        else:
            if session.patient_id and str(session.patient_id) != str(user_id):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"user": ["You are not the patient for this session"]}
                )
            session.patient_in_channel = False
            logger.info(f"Patient {user_id} left channel for session {session.session_id}")
        # When both have left, transition to GRACE so next request_join can reset and allow rejoin
        if (
            not session.doctor_in_channel
            and not session.patient_in_channel
            and session.status in [
                VideoSessionStatus.IN_CALL,
                VideoSessionStatus.DOCTOR_JOINED,
                VideoSessionStatus.JOINING,
            ]
        ):
            await self.state_service.transition(session, VideoSessionStatus.GRACE)
            logger.info(
                f"Both left channel for session {session.session_id}; transitioned to GRACE for rejoin"
            )
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def _reset_session_for_rejoin(
        self,
        session: VideoSession
    ) -> VideoSession:
        """
        Reset session state to allow rejoining from GRACE, COMPLETED, or JOIN_FAILED state
        
        This method:
        1. Transitions GRACE/COMPLETED/JOIN_FAILED → SCHEDULED
        2. Resets all readiness flags
        3. Clears tokens
        4. Resets timestamps (except scheduled times)
        """
        from datetime import timezone
        
        old_status = session.status.value
        logger.info(
            f"Resetting session {session.session_id} from {old_status} to SCHEDULED for rejoining"
        )
        
        # Transition to SCHEDULED
        await self.state_service.transition(session, VideoSessionStatus.SCHEDULED)
        
        # Reset readiness and in-channel flags
        session.doctor_ready = False
        session.patient_ready = False
        session.doctor_confirmed_join = False
        session.patient_confirmed_join = False
        session.doctor_in_channel = False
        session.patient_in_channel = False
        
        # Clear tokens
        session.doctor_token = None
        session.patient_token = None
        session.doctor_token_expires_at = None
        session.patient_token_expires_at = None
        
        # Reset join-related timestamps (keep scheduled times)
        session.join_attempt_started_at = None
        session.join_watchdog_expires_at = None
        session.doctor_joined_at = None
        session.patient_joined_at = None
        session.call_started_at = None
        session.call_ended_at = None
        
        # Reset billing (will start fresh when doctor joins)
        session.billing_started_at = None
        session.billable_duration_seconds = None
        session.waiting_room_duration_seconds = None
        
        # Clear errors
        session.last_error = None
        session.error_code = None
        
        # Reset waiting room timestamp
        session.patient_entered_waiting_room_at = None
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(
            f"Session {session.session_id} reset successfully. Ready for rejoining."
        )
        
        return session
    
    async def get_waiting_room_status(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get waiting room status for patient or doctor
        
        Returns:
            Dictionary with waiting room status and doctor join status
        """
        result = await self.db.execute(
            select(VideoSession).where(VideoSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise NotFoundException(
                message="Video session not found",
                errors={"session_id": ["Session does not exist"]}
            )
        
        # Verify access: user must be either the patient or the doctor
        is_patient = session.patient_id and str(session.patient_id) == str(user_id)
        is_doctor = session.doctor_id and str(session.doctor_id) == str(user_id)
        
        if not (is_patient or is_doctor):
            raise ForbiddenException(
                message="Access denied",
                errors={"user": ["You are not authorized to access this session"]}
            )
        
        # Determine if user is doctor or patient
        is_doctor_user = is_doctor
        
        # Check readiness status (simplified flow)
        both_ready = session.doctor_ready and session.patient_ready
        
        # If both are ready and call has started, return appropriate token
        token_plain = None
        if both_ready and session.status == VideoSessionStatus.JOINING:
            # Check if watchdog expired
            if session.is_join_watchdog_expired():
                # Watchdog expired - call failed
                return {
                    "status": session.status.value,
                    "waiting_room": False,
                    "doctor_ready": session.doctor_ready,
                    "patient_ready": session.patient_ready,
                    "both_ready": True,
                    "token": None,
                    "channel_name": session.channel_name,
                    "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
                    "message": "Join attempt timed out. Please try joining again.",
                    "watchdog_expired": True
                }
            
            # Generate a fresh token for this user (do not reuse stored token)
            try:
                if is_doctor_user:
                    pkg = agora_service.generate_token_for_user(
                        session_id=session.session_id,
                        user_id=session.doctor_id,
                        role="publisher",
                        expiry_minutes=getattr(settings, 'AGORA_TOKEN_EXPIRY_MINUTES', 60),
                        channel_name=session.channel_name,
                    )
                    token_plain = pkg["token_plain"]
                    session.doctor_token = pkg["token"]
                    session.doctor_token_expires_at = pkg["expires_at"]
                else:
                    pkg = agora_service.generate_token_for_user(
                        session_id=session.session_id,
                        user_id=session.patient_id,
                        role="publisher",
                        expiry_minutes=getattr(settings, 'AGORA_TOKEN_EXPIRY_MINUTES', 60),
                        channel_name=session.channel_name,
                    )
                    token_plain = pkg["token_plain"]
                    session.patient_token = pkg["token"]
                    session.patient_token_expires_at = pkg["expires_at"]
                await self.db.commit()
            except Exception as e:
                logger.warning(
                    f"Failed to generate fresh token for session {session.session_id}: {e}"
                )

        return {
            "status": session.status.value,
            "waiting_room": not both_ready,
            "doctor_ready": session.doctor_ready,
            "patient_ready": session.patient_ready,
            "both_ready": both_ready,
            "token": token_plain,  # Return appropriate token (doctor or patient) if both ready and call started, None otherwise
            "channel_name": session.channel_name,
            "app_id": self._get_agora_app_id(),  # Agora App ID for frontend initialization
            "message": (
                "Waiting for doctor to join" if not session.doctor_ready 
                else "Waiting for patient to join" if not session.patient_ready
                else "Both parties ready. Call is starting." if both_ready and session.status == VideoSessionStatus.JOINING
                else "Waiting for call to start"
            ),
            "watchdog_expires_at": session.join_watchdog_expires_at.isoformat() if session.join_watchdog_expires_at else None
        }
