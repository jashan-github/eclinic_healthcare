"""
HTTP client for webinar (video) service: create session, get by webinar, join.
Uses JWT for the current user so the webinar service can identify role and user_id.
"""

from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime
import httpx
from loguru import logger

from app.core.config import settings
from app.core.security import create_access_token


def _base_url() -> str:
    url = getattr(settings, "WEBINAR_SERVICE_URL", "http://localhost:8002")
    if not url.startswith("http"):
        url = f"http://{url}"
    return url.rstrip("/")


def _token_for_user(user_id: str, role: str) -> str:
    """Build JWT for the given user so webinar service can authenticate."""
    role_value = role.value if hasattr(role, "value") else role
    token_data = {
        "sub": str(user_id),
        "user_id": str(user_id),
        "role": role_value,
    }
    return create_access_token(data=token_data)


def create_webinar_video_session(
    user_id: str,
    role: str,
    webinar_id: UUID,
    scheduled_start_time: Optional[datetime] = None,
    scheduled_end_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Create a video session for a webinar (host only).
    Returns dict with session_id, channel_name, status, session_type.
    """
    url = f"{_base_url()}/api/v1/video-sessions"
    payload = {
        "webinar_id": str(webinar_id),
        "session_type": "webinar",
    }
    if scheduled_start_time is not None:
        payload["scheduled_start_time"] = scheduled_start_time.isoformat()
    if scheduled_end_time is not None:
        payload["scheduled_end_time"] = scheduled_end_time.isoformat()

    token = _token_for_user(user_id, role)
    with httpx.Client(timeout=15.0) as client:
        response = client.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
    if response.status_code != 201:
        logger.error(
            f"Webinar video create failed: {response.status_code} - {response.text}"
        )
        from app.core.exceptions import BadRequestException

        raise BadRequestException(
            message="Failed to start webinar video session",
            errors={"video": [response.text or "Webinar service error"]},
        )
    data = response.json()
    if not data.get("success") or not data.get("data"):
        from app.core.exceptions import BadRequestException

        raise BadRequestException(
            message=data.get("message", "Failed to create video session"),
            errors={"video": [data.get("message", "Unknown error")]},
        )
    return data["data"]


def get_video_session_by_webinar(
    user_id: str,
    role: str,
    webinar_id: UUID,
) -> Dict[str, Any]:
    """
    Get active video session for a webinar (for audience join).
    Returns dict with session_id, channel_name, status, session_type.
    Raises NotFoundException if no active session.
    """
    url = f"{_base_url()}/api/v1/video-sessions/by-webinar/{webinar_id}"
    token = _token_for_user(user_id, role)
    with httpx.Client(timeout=10.0) as client:
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code == 404:
        from app.core.exceptions import NotFoundException

        raise NotFoundException(
            message="No active video session for this webinar",
            errors={
                "webinar_id": [
                    "The host has not started this webinar yet, or the session has ended."
                ]
            },
        )
    if response.status_code != 200:
        logger.error(
            f"Webinar get by webinar failed: {response.status_code} - {response.text}"
        )
        from app.core.exceptions import BadRequestException

        raise BadRequestException(
            message="Failed to get webinar video session",
            errors={"video": [response.text or "Webinar service error"]},
        )
    data = response.json()
    if not data.get("success") or not data.get("data"):
        from app.core.exceptions import NotFoundException

        raise NotFoundException(
            message="No active video session for this webinar",
            errors={"webinar_id": ["No active session found"]},
        )
    return data["data"]


def join_video_session(
    user_id: str,
    role: str,
    session_id: UUID,
    as_webinar_host: bool = False,
) -> Dict[str, Any]:
    """
    Request to join a video session (host or audience).
    When as_webinar_host=True, sends X-Webinar-Host-Id so the webinar service treats this user as host (for go-live).
    Returns dict with token, channel_name, app_id, waiting_room, message, etc.
    """
    url = f"{_base_url()}/api/v1/video-sessions/{session_id}/join"
    token = _token_for_user(user_id, role)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    if as_webinar_host:
        headers["X-Webinar-Host-Id"] = str(user_id)
    with httpx.Client(timeout=15.0) as client:
        response = client.post(
            url,
            json={},
            headers=headers,
        )
    if response.status_code != 200:
        logger.error(
            f"Webinar join failed: {response.status_code} - {response.text}"
        )
        from app.core.exceptions import BadRequestException

        raise BadRequestException(
            message="Failed to join webinar",
            errors={"video": [response.text or "Webinar service error"]},
        )
    data = response.json()
    if not data.get("success"):
        from app.core.exceptions import ValidationException

        raise ValidationException(
            message=data.get("message", "Join request failed"),
            errors={"join": [data.get("message", "Unknown error")]},
        )
    return data.get("data", {})
