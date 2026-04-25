"""
Pydantic schemas for FCM push notification subscribe/unsubscribe.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class FCMSubscribeRequest(BaseModel):
    """Request body for registering an FCM token for the current user."""

    token: str = Field(..., min_length=1, max_length=512, description="FCM registration token")
    platform: Optional[Literal["web", "android", "ios"]] = Field(
        None, description="Device platform"
    )
    device_label: Optional[str] = Field(None, max_length=255, description="Optional device label")


class FCMUnsubscribeRequest(BaseModel):
    """Request body for removing an FCM token."""

    token: str = Field(..., min_length=1, max_length=512, description="FCM registration token to remove")
