"""
Firebase Cloud Messaging (FCM) push notification service.
Sends push notifications to users via FCM registration tokens.
"""

from typing import Optional, Dict, Any, List
import json
from sqlalchemy.orm import Session
from loguru import logger

from app.core.config import settings
from app.models.fcm_token import FCMToken


_firebase_app = None


def _get_firebase_app():
    """Initialize Firebase Admin SDK once and return the app."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    if not settings.FCM_ENABLED:
        return None
    creds = None
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ModuleNotFoundError as e:
        logger.warning(
            "firebase-admin not installed; FCM push disabled. "
            "Install with: pip install firebase-admin"
        )
        return None

    if settings.FIREBASE_CREDENTIALS_PATH:
        try:
            creds = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        except FileNotFoundError:
            logger.warning(
                f"Firebase credentials file not found: {settings.FIREBASE_CREDENTIALS_PATH}"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to load Firebase credentials from path: {e}")
            return None
    elif settings.FIREBASE_CREDENTIALS_JSON:
        try:
            creds_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
            creds = credentials.Certificate(creds_dict)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid FIREBASE_CREDENTIALS_JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load Firebase credentials from JSON: {e}")
            return None
    else:
        logger.warning(
            "FCM enabled but neither FIREBASE_CREDENTIALS_PATH nor FIREBASE_CREDENTIALS_JSON set"
        )
        return None
    if creds is None:
        return None
    try:
        _firebase_app = firebase_admin.initialize_app(creds)
        logger.info("Firebase Admin SDK initialized for FCM")
        return _firebase_app
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        return None


def get_tokens_for_user(db: Session, user_id: str) -> List[str]:
    """
    Return all active FCM tokens for a user (excluding soft-deleted).
    user_id can be UUID string or UUID.
    """
    from uuid import UUID
    uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
    rows = (
        db.query(FCMToken.token)
        .filter(
            FCMToken.user_id == uid,
            FCMToken.deleted_at.is_(None),
        )
        .all()
    )
    return [r[0] for r in rows]


async def send_push_to_user(
    db: Session,
    user_id: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Send a push notification to all FCM tokens registered for the given user.

    Args:
        db: Database session
        user_id: User UUID string
        title: Notification title
        body: Notification body
        data: Optional key-value payload (values must be strings for FCM)

    Returns:
        True if at least one message was sent successfully; False otherwise.
    """
    if not settings.FCM_ENABLED:
        return False
    app = _get_firebase_app()
    if app is None:
        return False
    tokens = get_tokens_for_user(db, user_id)
    if not tokens:
        logger.debug(f"No FCM tokens for user {user_id}")
        return False
    try:
        try:
            from firebase_admin import messaging
        except ModuleNotFoundError:
            logger.debug("firebase_admin not available; skipping FCM send")
            return False
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        success = response.success_count or 0
        failure = response.failure_count or 0
        if success:
            logger.info(
                f"FCM push sent to user {user_id}: {success} success, {failure} failure"
            )
        if failure and response.responses:
            for i, send_response in enumerate(response.responses):
                if not send_response.success and send_response.exception:
                    logger.warning(
                        f"FCM send failed for token index {i}: {send_response.exception}"
                    )
        return success > 0
    except Exception as e:
        logger.error(f"FCM send failed for user {user_id}: {e}", exc_info=True)
        return False
