# HIPAA-Compliant Video Call & Webinar System

## Overview

This is a production-ready, HIPAA-compliant video call and webinar system using Agora. It enforces strict security rules, billing controls, and state management to ensure no billable minutes are lost and no unauthorized access occurs.

## Core Security Rules (MUST FOLLOW)

1. ✅ **NEVER** generate Agora tokens on the frontend
2. ✅ **NEVER** include PHI (user names, emails, IDs) in channel names
3. ✅ Channel names are secure hashes of `session_id`
4. ✅ Tokens are short-lived (15-60 minutes)
5. ✅ Billing starts **ONLY** when doctor joins successfully
6. ✅ Patient waiting time is **NEVER** billed
7. ✅ Patient does **NOT** receive token until doctor has joined
8. ✅ Join failures auto-handled with 30-second timeout
9. ✅ Re-join creates **NEW** call instance (new channel + tokens)
10. ✅ All events are audit logged immutably

## State Machine

```
SCHEDULED
    ↓
WAITING_ROOM (patient enters, doctor not joined)
    ↓
JOINING (30-second watchdog active)
    ↓
DOCTOR_JOINED (BILLING STARTS HERE)
    ↓
IN_CALL (both parties connected)
    ↓
GRACE → COMPLETED

Alternative paths:
- JOINING → JOIN_FAILED (if timeout or error)
- Any state → EXPIRED (if timeout or no-show)
- Any state → CANCELLED (if cancelled)
```

## Database Models

### `video_sessions`
Main table for video call sessions with:
- Secure channel name (hash-based, no PHI)
- State machine status
- Billing timestamps
- Token storage (encrypted)
- Join watchdog timestamps
- Retry tracking

### `video_session_audit_logs`
Immutable audit trail with:
- All state transitions
- Join attempts/success/failure
- Billing events
- Error logs
- IP addresses and user agents

## Services

### 1. `AgoraService`
- **Purpose**: Server-side token generation (NEVER on frontend)
- **Key Methods**:
  - `generate_secure_channel_name()`: Creates hash-based channel name
  - `generate_token_for_user()`: Generates encrypted token package
  - `encrypt_token()` / `decrypt_token()`: Token encryption for storage

### 2. `VideoSessionStateService`
- **Purpose**: Enforces strict state transitions
- **Key Methods**:
  - `transition()`: Validates and executes state changes
  - `check_join_watchdog()`: Monitors 30-second timeout
  - `check_expiry()`: Handles session expiration

### 3. `VideoSessionService`
- **Purpose**: Main orchestration service
- **Key Methods**:
  - `create_session()`: Creates new video session
  - `request_join()`: Handles join requests (doctor/patient)
  - `confirm_join_success()`: Confirms successful join (starts billing)
  - `handle_join_failure()`: Handles join failures
  - `retry_call()`: Creates new session for retry
  - `end_call()`: Ends call and calculates billing

### 4. `VideoSessionAuditService`
- **Purpose**: HIPAA-compliant audit logging
- **Key Methods**:
  - `log_join_attempt()`: Log join attempts
  - `log_join_success()`: Log successful joins
  - `log_join_failure()`: Log join failures
  - `log_billing_start()`: Log billing start
  - `log_call_end()`: Log call end with duration

## API Endpoints

### `POST /api/v1/video-sessions`
Create a new video session

**Request:**
```json
{
  "appointment_id": "uuid",
  "session_type": "appointment",
  "scheduled_start_time": "2025-01-15T10:00:00Z",
  "scheduled_end_time": "2025-01-15T10:30:00Z",
  "recording_enabled": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Video session created successfully",
  "data": {
    "session_id": "uuid",
    "channel_name": "secure_hash",
    "status": "scheduled",
    "session_type": "appointment"
  }
}
```

### `POST /api/v1/video-sessions/{session_id}/join`
Request to join video session

**Response (Doctor):**
```json
{
  "success": true,
  "message": "Join attempt started. You have 30 seconds to join successfully.",
  "data": {
    "status": "joining",
    "token": "agora_token_plain",
    "channel_name": "secure_hash",
    "waiting_room": false,
    "watchdog_expires_at": "2025-01-15T10:00:30Z"
  }
}
```

**Response (Patient - Waiting Room):**
```json
{
  "success": true,
  "message": "Waiting for doctor to join. You will be notified when ready.",
  "data": {
    "status": "waiting_room",
    "token": null,
    "channel_name": "secure_hash",
    "waiting_room": true,
    "doctor_joined": false
  }
}
```

### `POST /api/v1/video-sessions/{session_id}/join-success`
Confirm successful join (called when Agora reports success)

**Critical**: Billing starts when doctor confirms join success

### `POST /api/v1/video-sessions/{session_id}/join-failure`
Report join failure

### `GET /api/v1/video-sessions/{session_id}/waiting-room`
Get waiting room status (for patient)

### `POST /api/v1/video-sessions/retry`
Retry failed call (creates new session)

### `POST /api/v1/video-sessions/{session_id}/end`
End video call

### `WS /api/v1/video-sessions/ws/{session_id}?token={jwt}`
WebSocket endpoint for real-time notifications

**Events:**
- `doctor_joined`: Doctor has joined (patient gets token)
- `join_failed`: Join attempt failed
- `call_ended`: Call has ended

## Use Cases Implementation

### UC-1: Doctor Joins First
1. Doctor calls `POST /join`
2. System generates doctor token
3. State → `JOINING`
4. 30-second watchdog starts
5. Doctor calls `POST /join-success` when Agora confirms
6. State → `DOCTOR_JOINED`
7. **BILLING STARTS**

### UC-2: Patient Joins First
1. Patient calls `POST /join`
2. System checks: doctor not joined
3. State → `WAITING_ROOM`
4. Patient does **NOT** get token
5. Patient subscribes to WebSocket for notifications

### UC-3: Doctor Joins After Patient
1. Doctor joins (see UC-1)
2. System broadcasts `doctor_joined` via WebSocket
3. Patient calls `GET /waiting-room` (or receives WebSocket event)
4. System generates patient token
5. State → `IN_CALL`

### UC-4: Join Failure
1. If no `join-success` within 30 seconds:
   - System auto-transitions to `JOIN_FAILED`
   - Tokens revoked
   - No billing
   - Retry option available

### UC-5: Retry Call
1. User calls `POST /retry` with previous session ID
2. System creates **NEW** session:
   - New `session_id`
   - New `channel_name`
   - New tokens
   - Retry count incremented

### UC-6: Doctor Never Joins
1. Patient in waiting room
2. Scheduled time passes
3. System checks expiry
4. State → `EXPIRED`
5. No billing

### UC-7: Patient Join Failure After Doctor Joined
1. Doctor already joined (billing active)
2. Patient join fails
3. Doctor stays connected
4. Billing continues
5. Patient can retry

## Configuration

Add to `.env`:

```bash
# Agora Video SDK
AGORA_APP_ID=your_app_id
AGORA_APP_CERTIFICATE=your_app_certificate
AGORA_TOKEN_EXPIRY_MINUTES=60

# Video Call Settings
VIDEO_DOCTOR_EARLY_JOIN_MINUTES=5
VIDEO_JOIN_WATCHDOG_SECONDS=30
VIDEO_GRACE_PERIOD_SECONDS=300

# Encryption (for token storage)
ENCRYPTION_KEY=your_fernet_key_base64
```

## Frontend Integration

### React.js Example

```javascript
// 1. Create session
const createSession = async (appointmentId) => {
  const response = await fetch('/api/v1/video-sessions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      appointment_id: appointmentId,
      session_type: 'appointment'
    })
  });
  return response.json();
};

// 2. Request join
const requestJoin = async (sessionId) => {
  const response = await fetch(`/api/v1/video-sessions/${sessionId}/join`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  const data = await response.json();
  
  if (data.data.waiting_room) {
    // Subscribe to WebSocket for doctor_joined event
    subscribeToSession(sessionId);
  } else {
    // Use token immediately
    joinAgoraCall(data.data.token, data.data.channel_name);
  }
  
  return data;
};

// 3. Confirm join success (after Agora SDK reports success)
const confirmJoinSuccess = async (sessionId) => {
  await fetch(`/api/v1/video-sessions/${sessionId}/join-success`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
};

// 4. WebSocket subscription
const subscribeToSession = (sessionId) => {
  const ws = new WebSocket(
    `ws://your-domain/api/v1/video-sessions/ws/${sessionId}?token=${token}`
  );
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'doctor_joined') {
      // Get patient token
      getWaitingRoomStatus(sessionId).then(result => {
        if (result.data.token) {
          joinAgoraCall(result.data.token, result.data.channel_name);
        }
      });
    }
  };
};

// 5. Join Agora call
const joinAgoraCall = (token, channelName) => {
  const client = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' });
  
  client.join(token, channelName, null, (uid) => {
    // On join success, confirm to backend
    confirmJoinSuccess(sessionId);
  });
};
```

## Background Tasks (Recommended)

Create a background task to:
1. Monitor join watchdogs (check every 5 seconds)
2. Auto-expire sessions
3. Auto-transition GRACE → COMPLETED

Example using Celery or FastAPI BackgroundTasks:

```python
@celery.task
def monitor_video_sessions():
    """Monitor join watchdogs and expirations"""
    sessions = db.query(VideoSession).filter(
        VideoSession.status.in_([
            VideoSessionStatus.JOINING,
            VideoSessionStatus.GRACE
        ])
    ).all()
    
    for session in sessions:
        state_service = VideoSessionStateService(db)
        
        # Check watchdog
        if session.status == VideoSessionStatus.JOINING:
            state_service.check_join_watchdog(session)
        
        # Check expiry
        state_service.check_expiry(session)
```

## Migration

Run the migration:

```bash
cd /var/www/backend/fastapi-backend
alembic upgrade head
```

## Testing

### Test Doctor Join Flow
1. Create session
2. Doctor requests join → gets token
3. Doctor joins Agora → confirms success
4. Verify billing started
5. Verify state = DOCTOR_JOINED

### Test Patient Waiting Room
1. Create session
2. Patient requests join → enters waiting room
3. Verify no token provided
4. Doctor joins
5. Patient gets notification
6. Patient gets token
7. Both join call

### Test Join Failure
1. Create session
2. Doctor requests join
3. Don't confirm success
4. Wait 30+ seconds
5. Verify auto-transition to JOIN_FAILED
6. Verify no billing

## Security Checklist

- [x] Tokens generated server-side only
- [x] Channel names are secure hashes (no PHI)
- [x] Tokens encrypted in database
- [x] Short-lived tokens (15-60 min)
- [x] Billing starts only when doctor joins
- [x] Patient waiting room enforced
- [x] 30-second join watchdog
- [x] Retry creates new session
- [x] Full audit logging
- [x] Role-based access control
- [x] Appointment ownership validation

## Notes

- All timestamps are in UTC
- Billing duration calculated in seconds
- Waiting room duration tracked separately (not billed)
- Tokens are encrypted using Fernet (symmetric encryption)
- Channel names are deterministic hashes (same session_id = same channel)
- WebSocket connections should be authenticated with JWT token
