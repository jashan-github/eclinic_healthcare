"""
FCM push notification subscribe/unsubscribe API.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.fcm_token import FCMToken
from app.schemas.push import FCMSubscribeRequest, FCMUnsubscribeRequest
from loguru import logger

router = APIRouter(prefix="/notifications/fcm", tags=["Push Notifications - FCM"])


@router.post("/subscribe", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def fcm_subscribe(
    body: FCMSubscribeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Register an FCM registration token for the current user.
    If the token already exists for another user or same user, it is updated (upsert by token).
    """
    user_id = UUID(str(current_user.id))
    existing = (
        db.query(FCMToken)
        .filter(FCMToken.token == body.token, FCMToken.deleted_at.is_(None))
        .first()
    )
    if existing:
        if existing.user_id != user_id:
            existing.user_id = user_id
        existing.platform = body.platform or existing.platform
        existing.device_label = body.device_label or existing.device_label
        db.commit()
        logger.info(f"FCM token updated for user {current_user.id}")
        return
    token_row = FCMToken(
        user_id=user_id,
        token=body.token,
        platform=body.platform,
        device_label=body.device_label,
    )
    db.add(token_row)
    db.commit()
    logger.info(f"FCM token registered for user {current_user.id}")


@router.delete("/unsubscribe", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def fcm_unsubscribe(
    body: FCMUnsubscribeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Remove an FCM registration token for the current user (soft delete).
    """
    user_id = UUID(str(current_user.id))
    row = (
        db.query(FCMToken)
        .filter(
            FCMToken.token == body.token,
            FCMToken.user_id == user_id,
            FCMToken.deleted_at.is_(None),
        )
        .first()
    )
    if row:
        row.deleted_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"FCM token unsubscribed for user {current_user.id}")
