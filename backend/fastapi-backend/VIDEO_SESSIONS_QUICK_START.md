# Video Sessions - Quick Start Guide

## 🚀 Quick Setup

### 1. Install Agora Token Package

```bash
pip install agora-token
```

### 2. Update AgoraService

See `AGORA_TOKEN_SETUP.md` for instructions to update `app/services/agora_service.py` to use the official Agora token SDK.

### 3. Configure Environment Variables

Add to `.env`:

```bash
# Agora
AGORA_APP_ID=your_app_id
AGORA_APP_CERTIFICATE=your_app_certificate
AGORA_TOKEN_EXPIRY_MINUTES=60

# Video Settings
VIDEO_DOCTOR_EARLY_JOIN_MINUTES=5
VIDEO_JOIN_WATCHDOG_SECONDS=30
VIDEO_GRACE_PERIOD_SECONDS=300

# Encryption (for token storage)
ENCRYPTION_KEY=your_fernet_key_base64
```

### 4. Run Migration

```bash
cd /var/www/backend/fastapi-backend
alembic upgrade head
```

### 5. Restart Service

```bash
docker compose restart backend
```

## 📋 API Endpoints

All endpoints are under `/api/v1/video-sessions`:

- `POST /` - Create session
- `POST /{id}/join` - Request join
- `POST /{id}/join-success` - Confirm join success
- `POST /{id}/join-failure` - Report failure
- `GET /{id}/waiting-room` - Get waiting room status
- `POST /retry` - Retry failed call
- `POST /{id}/end` - End call
- `WS /ws/{id}` - WebSocket notifications

## ✅ Key Features

- ✅ Server-side token generation (NEVER on frontend)
- ✅ Secure channel names (hash-based, no PHI)
- ✅ Billing starts only when doctor joins
- ✅ Patient waiting room enforced
- ✅ 30-second join watchdog
- ✅ Full audit logging
- ✅ Retry with new session instance

## 📖 Full Documentation

See `VIDEO_SESSIONS_README.md` for complete documentation with React.js examples.
