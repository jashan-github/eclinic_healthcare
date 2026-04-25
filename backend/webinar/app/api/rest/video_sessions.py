"""
Video Session API Endpoints
HIPAA-compliant video call and webinar management (Async)

All video session and Agora functionality is now in webinar-service.
"""

from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect, Query, Path, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
import json
import asyncio
from loguru import logger

from app.db.session import get_db
from app.core.security import get_current_user_id, get_user_role, extract_token_from_header, decode_jwt_token
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException, UnauthorizedException
from app.db.models_video_session import VideoSession, VideoSessionStatus, VideoSessionType
from app.services.video_session_service import VideoSessionService
from app.services.video_session_audit_service import VideoSessionAuditService
from app.schemas.video_session import (
    VideoSessionCreateRequest,
    VideoSessionCreateResponse,
    VideoSessionJoinRequest,
    VideoSessionJoinResponse,
    VideoSessionStatusResponse,
    VideoSessionRetryRequest,
    VideoSessionRetryResponse
)

router = APIRouter(prefix="/video-sessions", tags=["Video Sessions"])


def laravel_response(
    success: bool = True,
    message: str = "",
    data: Any = None,
    errors: Optional[dict] = None
) -> dict:
    """Generate Laravel-compatible response format"""
    return {
        "success": success,
        "message": message,
        "errors": errors,
        "data": data
    }


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user from JWT token"""
    if not authorization:
        raise UnauthorizedException("Authorization header required")
    
    token = extract_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    role = await get_user_role(token)
    
    return {"id": UUID(user_id), "role": role}


# WebSocket connection manager for real-time notifications
class VideoSessionConnectionManager:
    """Manages WebSocket connections for video session notifications"""
    
    def __init__(self):
        # Map session_id -> set of WebSocket connections
        self.active_connections: dict[UUID, set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: UUID):
        """Accept and register WebSocket connection"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: UUID):
        """Unregister WebSocket connection"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast_to_session(self, session_id: UUID, message: dict):
        """Broadcast message to all connections for a session"""
        if session_id not in self.active_connections:
            return
        
        disconnected = set()
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to session {session_id}: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected connections
        for websocket in disconnected:
            self.active_connections[session_id].discard(websocket)


# Global connection manager
connection_manager = VideoSessionConnectionManager()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create video session",
    description="""Create a new video session for appointment or webinar
    
    **HIPAA Compliance:**
    - Channel name is secure hash (no PHI)
    - Tokens generated server-side only
    - Full audit logging
    """
)
async def create_video_session(
    request: VideoSessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new video session"""
    try:
        service = VideoSessionService(db)
        audit_service = VideoSessionAuditService(db)
        
        # Create session
        session = await service.create_session(
            doctor_id=current_user["id"],
            patient_id=request.patient_id,
            appointment_id=request.appointment_id,
            webinar_id=request.webinar_id,
            session_type=VideoSessionType(request.session_type) if request.session_type else VideoSessionType.APPOINTMENT,
            scheduled_start_time=request.scheduled_start_time,
            scheduled_end_time=request.scheduled_end_time,
            recording_enabled=request.recording_enabled or False,
            doctor_display_name=request.doctor_display_name,
            patient_display_name=request.patient_display_name,
        )
        
        # Audit log
        await audit_service.log_event(
            session_id=session.session_id,
            event_type="session_created",
            user_id=current_user["id"],
            user_role=current_user["role"],
            description="Video session created"
        )
        
        return laravel_response(
            success=True,
            message="Video session created successfully",
            data={
                "session_id": str(session.session_id),
                "channel_name": session.channel_name,
                "status": session.status.value,
                "session_type": session.session_type.value
            }
        )
    
    except (ValidationException, ForbiddenException, NotFoundException) as e:
        raise
    except Exception as e:
        logger.error(f"Error creating video session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video session"
        )


@router.get(
    "/by-webinar/{webinar_id}",
    status_code=status.HTTP_200_OK,
    summary="Get video session by webinar ID",
    description="""Get the active video session for a webinar (for audience join).
    Returns 404 if no active session exists (e.g. host has not gone live yet).
    Requires authentication.
    """
)
async def get_video_session_by_webinar(
    webinar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get video session by webinar ID (for audience to obtain session_id before join)."""
    try:
        service = VideoSessionService(db)
        session = await service.get_session_by_webinar_id(webinar_id)
        if not session:
            raise NotFoundException(
                message="No active video session for this webinar",
                errors={
                    "webinar_id": [
                        "The host has not started this webinar yet, or the session has ended."
                    ]
                }
            )
        return laravel_response(
            success=True,
            message="Video session found",
            data={
                "session_id": str(session.session_id),
                "channel_name": session.channel_name,
                "status": session.status.value,
                "session_type": session.session_type.value,
            }
        )
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error getting video session by webinar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get video session"
        )


@router.post(
    "/{session_id}/join",
    status_code=status.HTTP_200_OK,
    summary="Request to join video session",
    description="""Request to join a video session
    
    **Behavior:**
    - Doctor: Can join 5-10 min early, gets token immediately, 30s watchdog starts
    - Patient: Enters waiting room if doctor not joined, gets token when doctor joins
    
    **Security:**
    - Tokens generated server-side only
    - 30-second join watchdog enforced
    - Full audit logging
    """
)
async def request_join(
    session_id: UUID,
    request: VideoSessionJoinRequest = Body(default_factory=VideoSessionJoinRequest),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    http_request: Request = None
):
    """Request to join video session"""
    try:
        service = VideoSessionService(db)
        audit_service = VideoSessionAuditService(db)

        # Backend can send X-Webinar-Host-Id when caller is the webinar host (go-live); treat as host for token
        webinar_host_user_id = None
        if http_request:
            raw = http_request.headers.get("X-Webinar-Host-Id")
            if raw:
                try:
                    webinar_host_user_id = UUID(raw)
                except (ValueError, TypeError):
                    pass

        # Get IP address for audit
        ip_address = http_request.client.host if http_request else None
        user_agent = http_request.headers.get("user-agent") if http_request else None

        # Audit log join attempt
        await audit_service.log_join_attempt(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user["role"],
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Request join
        result = await service.request_join(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user["role"],
            webinar_host_user_id=webinar_host_user_id,
        )
        
        # If patient in waiting room, notify via WebSocket (if connected)
        if result.get("waiting_room"):
            await connection_manager.broadcast_to_session(
                session_id,
                {
                    "type": "waiting_room",
                    "session_id": str(session_id),
                    "message": "Waiting for doctor to join"
                }
            )
        
        return laravel_response(
            success=True,
            message=result.get("message", "Join request processed"),
            data=result
        )
    
    except (ValidationException, ForbiddenException, NotFoundException) as e:
        raise
    except Exception as e:
        logger.error(f"Error requesting join: {e}", exc_info=True)
        # Return detailed error message for debugging
        error_message = str(e)
        if "timezone" in error_message.lower() or "offset" in error_message.lower():
            error_message = "Timezone comparison error: " + error_message
        
        # Use laravel_response format for consistency
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Failed to process join request",
                "error": error_message,
                "errors": {
                    "general": [error_message]
                },
                "data": None
            }
        )


@router.post(
    "/{session_id}/join-success",
    status_code=status.HTTP_200_OK,
    summary="Confirm join success",
    description="""Confirm successful join (called when Agora reports join success)
    
    **Critical for Billing:**
    - Billing starts when doctor confirms join success
    - Patient gets token notification when doctor joins
    """
)
async def confirm_join_success(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    http_request: Request = None
):
    """Confirm successful join"""
    try:
        service = VideoSessionService(db)
        audit_service = VideoSessionAuditService(db)
        
        # Get session before update
        from sqlalchemy import select
        result = await db.execute(
            select(VideoSession).where(VideoSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise NotFoundException(
                message="Video session not found",
                errors={"session_id": ["Session does not exist"]}
            )
        
        previous_status = session.status.value
        
        # Confirm join
        session = await service.confirm_join_success(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        
        # Audit log
        await audit_service.log_join_success(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user["role"],
            previous_status=previous_status,
            new_status=session.status.value,
            ip_address=http_request.client.host if http_request else None
        )
        
        # If doctor joined, notify patient (if in waiting room)
        if current_user["role"] == "doctor" and session.status == VideoSessionStatus.DOCTOR_JOINED:
            await connection_manager.broadcast_to_session(
                session_id,
                {
                    "type": "doctor_joined",
                    "session_id": str(session_id),
                    "status": session.status.value,
                    "message": "Doctor has joined. You can now join the call."
                }
            )
        
        return laravel_response(
            success=True,
            message="Join confirmed successfully",
            data={
                "status": session.status.value,
                "billing_started": session.billing_started_at is not None
            }
        )
    
    except (ValidationException, ForbiddenException, NotFoundException) as e:
        raise
    except Exception as e:
        logger.error(f"Error confirming join: {e}", exc_info=True)
        # Return detailed error message for debugging
        error_message = str(e)
        if "timezone" in error_message.lower() or "offset" in error_message.lower():
            error_message = "Timezone comparison error: " + error_message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to confirm join",
                "error": error_message,
                "errors": {
                    "general": [error_message]
                }
            }
        )


@router.post(
    "/{session_id}/join-failure",
    status_code=status.HTTP_200_OK,
    summary="Report join failure",
    description="""Report join failure (called when Agora reports failure or timeout)
    
    **Behavior:**
    - If in JOINING state, transitions to JOIN_FAILED
    - 30-second watchdog also triggers this automatically
    - Tokens are revoked
    - No billing occurs
    
    **Query Parameters:**
    - **error**: (Required) Error message describing the join failure
    - **error_code**: (Optional) Error code for the failure (default: "JOIN_FAILED")
    """
)
async def report_join_failure(
    session_id: UUID = Path(..., description="Video session ID"),
    error: str = Query(..., description="Error message describing the join failure"),
    error_code: str = Query("JOIN_FAILED", description="Error code for the failure"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Report join failure"""
    try:
        service = VideoSessionService(db)
        audit_service = VideoSessionAuditService(db)
        
        # Handle failure
        session = await service.handle_join_failure(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user["role"],
            error=error,
            error_code=error_code
        )
        
        # Audit log
        await audit_service.log_join_failure(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user["role"],
            error=error,
            error_code=error_code
        )
        
        # Notify via WebSocket
        await connection_manager.broadcast_to_session(
            session_id,
            {
                "type": "join_failed",
                "session_id": str(session_id),
                "error": error,
                "error_code": error_code,
                "retry_available": True
            }
        )
        
        return laravel_response(
            success=True,
            message="Join failure recorded",
            data={"status": session.status.value}
        )
    
    except (ValidationException, ForbiddenException, NotFoundException) as e:
        raise
    except Exception as e:
        logger.error(f"Error reporting join failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to report join failure"
        )


@router.get(
    "/{session_id}/waiting-room",
    status_code=status.HTTP_200_OK,
    summary="Get waiting room status",
    description="""Get waiting room status for patient
    
    Returns current status and token if doctor has joined
    """
)
async def get_waiting_room_status(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get waiting room status"""
    try:
        service = VideoSessionService(db)
        
        result = await service.get_waiting_room_status(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user.get("role")
        )
        
        return laravel_response(
            success=True,
            message="Waiting room status retrieved",
            data=result
        )
    
    except (ValidationException, ForbiddenException, NotFoundException) as e:
        raise
    except Exception as e:
        logger.error(f"Error getting waiting room status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get waiting room status"
        )


@router.get(
    "/{session_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Get video session status",
    description="""Get current status of video session"""
)
async def get_video_session_status(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get video session status"""
    try:
        from sqlalchemy import select
        result = await db.execute(
            select(VideoSession).where(VideoSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise NotFoundException(
                message="Video session not found",
                errors={"session_id": ["Session does not exist"]}
            )
        
        # Verify access
        if current_user["role"] == "doctor":
            if str(session.doctor_id) != str(current_user["id"]):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"session_id": ["You do not have access to this session"]}
                )
        else:
            if session.patient_id and str(session.patient_id) != str(current_user["id"]):
                raise ForbiddenException(
                    message="Access denied",
                    errors={"session_id": ["You do not have access to this session"]}
                )
        
        doctor_joined = session.status in [
            VideoSessionStatus.DOCTOR_JOINED,
            VideoSessionStatus.IN_CALL
        ]
        
        return laravel_response(
            success=True,
            message="Session status retrieved",
            data={
                "status": session.status.value,
                "waiting_room": session.status == VideoSessionStatus.WAITING_ROOM,
                "doctor_joined": doctor_joined,
                "channel_name": session.channel_name,
                "message": "Waiting for doctor to join" if not doctor_joined else "Doctor has joined"
            }
        )
    
    except (ValidationException, ForbiddenException, NotFoundException) as e:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session status"
        )


@router.post(
    "/retry",
    status_code=status.HTTP_201_CREATED,
    summary="Retry failed call",
    description="""Retry a failed call by creating new session instance
    
    **Critical:**
    - Creates NEW session with NEW channel and NEW tokens
    - Previous session is marked as failed
    - Retry count is incremented
    """
)
async def retry_call(
    request: VideoSessionRetryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Retry failed call"""
    try:
        service = VideoSessionService(db)
        audit_service = VideoSessionAuditService(db)
        
        # Get previous session for retry count
        from sqlalchemy import select
        result = await db.execute(
            select(VideoSession).where(VideoSession.session_id == request.previous_session_id)
        )
        previous_session = result.scalar_one_or_none()
        
        retry_count = previous_session.retry_count + 1 if previous_session else 1
        
        # Create new session
        new_session = await service.retry_call(
            previous_session_id=request.previous_session_id,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        
        # Audit log
        await audit_service.log_retry(
            previous_session_id=request.previous_session_id,
            new_session_id=new_session.session_id,
            user_id=current_user["id"],
            user_role=current_user["role"],
            retry_count=retry_count
        )
        
        return laravel_response(
            success=True,
            message="Retry session created",
            data={
                "session_id": str(new_session.session_id),
                "channel_name": new_session.channel_name,
                "retry_count": new_session.retry_count
            }
        )
    
    except (ValidationException, ForbiddenException, NotFoundException) as e:
        raise
    except Exception as e:
        logger.error(f"Error retrying call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry call"
        )


@router.post(
    "/{session_id}/end",
    status_code=status.HTTP_200_OK,
    summary="End video call",
    description="""End a video call
    
    Transitions to GRACE period, then COMPLETED
    Calculates final billable duration
    """
)
async def end_call(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """End video call"""
    try:
        service = VideoSessionService(db)
        audit_service = VideoSessionAuditService(db)
        
        # End call
        session = await service.end_call(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        
        # Audit log
        await audit_service.log_call_end(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user["role"],
            billable_duration_seconds=session.billable_duration_seconds or 0
        )
        
        # Notify via WebSocket
        await connection_manager.broadcast_to_session(
            session_id,
            {
                "type": "call_ended",
                "session_id": str(session_id),
                "billable_duration_seconds": session.billable_duration_seconds or 0
            }
        )
        
        return laravel_response(
            success=True,
            message="Call ended successfully",
            data={
                "status": session.status.value,
                "billable_duration_seconds": session.billable_duration_seconds or 0
            }
        )
    
    except (ValidationException, ForbiddenException, NotFoundException) as e:
        raise
    except Exception as e:
        logger.error(f"Error ending call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end call"
        )


@router.post(
    "/{session_id}/leave-channel",
    status_code=status.HTTP_200_OK,
    summary="Leave Agora channel",
    description="""Notify that the user has left the Agora channel (e.g. page reload, disconnect).
    Call this when the user leaves the channel so rejoin logic works: if the other
    participant is still in the channel, they can rejoin directly; if not, they go to waiting room.
    """
)
async def leave_channel(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark current user as left the Agora channel (for rejoin logic)."""
    try:
        service = VideoSessionService(db)
        session = await service.leave_channel(
            session_id=session_id,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        return laravel_response(
            success=True,
            message="Left channel",
            data={"session_id": str(session_id), "in_channel": False}
        )
    except (ValidationException, ForbiddenException, NotFoundException) as e:
        raise
    except Exception as e:
        logger.error(f"Error in leave-channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record leave channel"
        )


@router.post(
    "/agora-webhook",
    status_code=status.HTTP_200_OK,
    summary="Agora channel events webhook (optional)",
    description="""Optional: receive Agora RTN channel events (join/leave).
    When a user leaves the channel, Agora can POST here; implement parsing of
    event_type/channel_name/uid and call leave_channel to keep in_channel in sync.
    For now this is a stub that logs the body and returns 200.
    """
)
async def agora_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Stub for Agora channel-event webhook. Extend to parse body and call leave_channel on user_leave."""
    try:
        body = await request.json()
        logger.info("Agora webhook received: %s", body)
        # TODO: parse event_type, channel_name, uid/account; on user_leave, find session by
        # channel_name and set doctor_in_channel or patient_in_channel = False for that user
        return {"status": "ok"}
    except Exception as e:
        logger.warning("Agora webhook parse error: %s", e)
        return {"status": "ok"}


@router.websocket("/ws/{session_id}")
async def video_session_websocket(
    websocket: WebSocket,
    session_id: UUID = Path(...),
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time video session waiting room notifications
    
    Uses Redis PUB/SUB to broadcast events across multiple instances.
    Subscribes to waiting room status updates when doctor joins.
    
    **Query Parameters:**
    - **token**: JWT authentication token (required)
    
    **Message Types:**
    - **doctor_joined**: Doctor has joined, patient can now join
    - **session_ready**: Session is ready for joining
    - **pong**: Response to ping
    """
    from sqlalchemy import select
    from app.db.session import get_db
    import asyncio
    
    # Verify JWT token
    try:
        payload = await decode_jwt_token(token)
        
        user_id = payload.get("user_id")
        email = payload.get("email")
        role = payload.get("role")
        
        if not user_id or not email or not role:
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
        
        current_user = {"id": UUID(user_id), "role": role}
    except Exception as e:
        logger.error(f"WebSocket token verification failed: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    # Verify user has access to this session
    try:
        async for db in get_db():
            result = await db.execute(
                select(VideoSession).where(VideoSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                await websocket.accept()
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
                return
            
            # Check access
            if current_user["role"] == "doctor":
                if str(session.doctor_id) != str(current_user["id"]):
                    await websocket.accept()
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Access denied")
                    return
            else:
                if session.patient_id and str(session.patient_id) != str(current_user["id"]):
                    await websocket.accept()
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Access denied")
                    return
            
            break
    except Exception as e:
        logger.error(f"Error verifying session access: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal error")
        return
    
    # Connect WebSocket
    await connection_manager.connect(websocket, session_id)
    
    # Subscribe to Redis channel
    from app.services.video_session_redis_service import video_session_redis_service
    
    async def redis_message_handler(message_data: dict):
        """Handle messages received from Redis"""
        try:
            # Forward message to WebSocket
            await connection_manager.send_personal_message(message_data, websocket)
        except Exception as e:
            logger.error(f"Error in Redis message handler: {e}")
    
    # Start Redis subscription in background
    redis_task = asyncio.create_task(
        video_session_redis_service.subscribe_to_session(session_id, redis_message_handler)
    )
    
    try:
        # Send welcome message
        await connection_manager.send_personal_message(
            {
                "type": "connected",
                "session_id": str(session_id),
                "message": "Connected to video session notifications"
            },
            websocket
        )
        
        # Main message loop
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await connection_manager.send_personal_message(
                        {"type": "pong", "message": "Connection alive"},
                        websocket
                    )
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    finally:
        # Cleanup
        redis_task.cancel()
        try:
            await redis_task
        except asyncio.CancelledError:
            pass
        
        connection_manager.disconnect(websocket, session_id)
