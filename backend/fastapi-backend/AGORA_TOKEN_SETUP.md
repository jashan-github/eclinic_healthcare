# Agora Token Generation Setup

## Important Note

The current `AgoraService` implementation uses a simplified token format. For production use with Agora, you should use the official `agora-token` Python package.

## Installation

```bash
pip install agora-token
```

## Update AgoraService

Replace the `generate_token` method in `app/services/agora_service.py`:

```python
from agora_token import RtcTokenBuilder, Role

def generate_token(
    self,
    channel_name: str,
    user_id: str,
    role: str = "publisher",
    expire_timestamp: Optional[int] = None
) -> str:
    """
    Generate Agora RTC token using official SDK
    """
    if not self.app_id or not self.app_certificate:
        raise ValidationException(
            message="Agora credentials not configured",
            errors={"agora": ["Agora service is not properly configured"]}
        )
    
    # Default token expiry: 60 minutes from now
    if expire_timestamp is None:
        expire_timestamp = int(time.time()) + 3600
    
    # Convert role string to Agora Role enum
    agora_role = Role.PUBLISHER if role == "publisher" else Role.SUBSCRIBER
    
    # Generate token using official SDK
    token = RtcTokenBuilder.buildTokenWithUid(
        self.app_id,
        self.app_certificate,
        channel_name,
        int(user_id) if user_id.isdigit() else 0,  # Agora UID (0 for string UID)
        agora_role,
        expire_timestamp
    )
    
    return token
```

## Alternative: String UID Token

If using string UIDs:

```python
token = RtcTokenBuilder.buildTokenWithAccount(
    self.app_id,
    self.app_certificate,
    channel_name,
    user_id,  # String UID
    agora_role,
    expire_timestamp
)
```

## Current Implementation

The current implementation uses a custom token format that may not work with Agora SDK. **You must update it** to use the official `agora-token` package for production.
