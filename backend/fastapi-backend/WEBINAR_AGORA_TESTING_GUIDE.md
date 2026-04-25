# Webinar Agora Integration - Testing Guide

## Prerequisites

1. **Agora Account Setup**
   - App ID: `e3143b8450bd4cdc8d0565052d627c7b` (provided)
   - App Certificate: Get from Agora Console (https://console.agora.io/)

2. **Environment Configuration**
   ```bash
   AGORA_APP_ID=e3143b8450bd4cdc8d0565052d627c7b
   AGORA_APP_CERTIFICATE=your_app_certificate_here
   AGORA_TOKEN_EXPIRY_MINUTES=60
   ```

## Step 1: Configure Agora Credentials

### Get App Certificate

1. Go to https://console.agora.io/
2. Select your project (or create one)
3. Go to "Project Management" > "Edit"
4. Copy the "App Certificate"
5. Add to `.env` file:

```bash
cd /var/www/backend/fastapi-backend
echo "AGORA_APP_ID=e3143b8450bd4cdc8d0565052d627c7b" >> .env
echo "AGORA_APP_CERTIFICATE=your_certificate_here" >> .env
```

### Restart Backend

```bash
cd /var/www/backend/fastapi-backend
docker compose restart backend
```

**Note:** Token generation uses custom implementation (no external SDK required)

## Step 2: Create a Webinar

### API: Create Webinar

```bash
POST /api/v1/webinars
Authorization: Bearer <admin_or_doctor_token>

{
  "title": "Test Webinar with Agora",
  "description": "Testing webinar video integration",
  "webinar_date": "2026-01-15",
  "start_time": "14:00:00",
  "end_time": "15:00:00",
  "host_id": "<doctor_or_admin_uuid>",
  "visibility": "public",
  "is_free": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "webinar-uuid-here",
    "title": "Test Webinar with Agora",
    ...
  }
}
```

## Step 3: Create Video Session for Webinar

### API: Create Video Session

```bash
POST /api/v1/video-sessions
Authorization: Bearer <doctor_or_admin_token>

{
  "session_type": "webinar",
  "doctor_id": "<host_uuid>",
  "webinar_id": "<webinar_uuid_from_step_2>",
  "scheduled_start_time": "2026-01-15T14:00:00Z",
  "scheduled_end_time": "2026-01-15T15:00:00Z",
  "is_recording_enabled": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "session-uuid-here",
    "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_abc123...",
    "status": "scheduled",
    "session_type": "webinar"
  }
}
```

**Save the `session_id` for next steps!**

## Step 4: Host Joins Webinar

### API: Request Join (Host/Doctor)

```bash
POST /api/v1/video-sessions/{session_id}/join
Authorization: Bearer <host_doctor_token>

{
  "user_role": "doctor"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "joining",
    "token": "agora_token_here",
    "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_abc123...",
    "waiting_room": false,
    "message": "Join attempt started. You have 30 seconds to join successfully."
  }
}
```

**Save the `token` and `channel_name` for Agora SDK!**

## Step 5: Audience/Participant Joins Webinar

### API: Request Join (Audience)

```bash
POST /api/v1/video-sessions/{session_id}/join
Authorization: Bearer <participant_token>

{
  "user_role": "patient"
}
```

**If host not joined yet:**
```json
{
  "success": true,
  "data": {
    "status": "waiting_room",
    "token": null,
    "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_abc123...",
    "waiting_room": true,
    "message": "Waiting for host to join. You will be notified when ready."
  }
}
```

**If host already joined:**
```json
{
  "success": true,
  "data": {
    "status": "in_call",
    "token": "agora_token_here",
    "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_abc123...",
    "waiting_room": false,
    "message": "Host has joined. You can now join the webinar."
  }
}
```

## Step 6: Frontend Integration (React/JavaScript)

### Install Agora SDK

```bash
npm install agora-rtc-sdk-ng
# or
yarn add agora-rtc-sdk-ng
```

### Join Webinar Code

```javascript
import AgoraRTC from 'agora-rtc-sdk-ng';

// Get token and channel from API (Step 4 or 5)
const APP_ID = 'e3143b8450bd4cdc8d0565052d627c7b';
const channelName = 'channel_name_from_api';
const token = 'token_from_api';
const uid = null; // Agora will assign UID automatically

// Create Agora client
const client = AgoraRTC.createClient({ 
  mode: 'rtc', 
  codec: 'vp8' 
});

// Join channel
await client.join(APP_ID, channelName, token, uid);

// Create local video track
const localVideoTrack = await AgoraRTC.createCameraVideoTrack();
const localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack();

// Publish local tracks
await client.publish([localVideoTrack, localAudioTrack]);

// Play local video
localVideoTrack.play('local-video-container');

// Listen for remote users
client.on('user-published', async (user, mediaType) => {
  await client.subscribe(user, mediaType);
  
  if (mediaType === 'video') {
    user.videoTrack.play(`remote-video-${user.uid}`);
  }
  if (mediaType === 'audio') {
    user.audioTrack.play();
  }
});

// Leave channel
async function leaveChannel() {
  localVideoTrack.close();
  localAudioTrack.close();
  await client.leave();
}
```

## Step 7: Confirm Join Success

### API: Confirm Join (After successfully joining Agora)

```bash
POST /api/v1/video-sessions/{session_id}/join-success
Authorization: Bearer <user_token>

{
  "user_role": "doctor" // or "patient"
}
```

This updates the session status and starts billing (for appointments).

## Step 8: End Session

### API: End Session

```bash
POST /api/v1/video-sessions/{session_id}/end
Authorization: Bearer <host_token>

{}
```

## Testing Checklist

### ✅ Host Flow

- [ ] Create webinar
- [ ] Create video session for webinar
- [ ] Host requests join → gets token
- [ ] Host joins Agora channel successfully
- [ ] Confirm join success
- [ ] Host can see own video/audio

### ✅ Audience Flow

- [ ] Audience requests join (before host) → enters waiting room
- [ ] Host joins
- [ ] Audience requests join again → gets token
- [ ] Audience joins Agora channel
- [ ] Audience can see host video/audio
- [ ] Host can see audience video/audio

### ✅ Multi-Participant

- [ ] Multiple audience members join
- [ ] All can see each other
- [ ] All can hear each other

## Troubleshooting

### Issue: "Agora credentials not configured"

**Solution:**
1. Check `.env` file has `AGORA_APP_ID` and `AGORA_APP_CERTIFICATE`
2. Restart backend: `docker compose restart backend`
3. Verify: `docker compose exec backend python -c "from app.core.config import settings; print(settings.AGORA_APP_ID)"`

### Issue: "Invalid token" in Agora SDK

**Solution:**
1. Verify App Certificate matches Agora Console
2. Check token expiry (should be 15-60 minutes)
3. Ensure using correct App ID

### Issue: "Channel name not found"

**Solution:**
1. Verify session was created successfully
2. Check `channel_name` in API response
3. Ensure using same `channel_name` in Agora SDK

### Issue: "Access denied" when joining

**Solution:**
1. For webinars: Ensure user is authenticated
2. For private webinars: Check webinar visibility settings
3. Verify user has valid JWT token

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/webinars` | POST | Create webinar |
| `/api/v1/video-sessions` | POST | Create video session |
| `/api/v1/video-sessions/{id}/join` | POST | Request to join |
| `/api/v1/video-sessions/{id}/join-success` | POST | Confirm join success |
| `/api/v1/video-sessions/{id}/status` | GET | Get session status |
| `/api/v1/video-sessions/{id}/end` | POST | End session |
| `/api/v1/video-sessions/{id}/ws` | WS | WebSocket for real-time updates |

## WebSocket Events

Connect to WebSocket for real-time notifications:

```javascript
const ws = new WebSocket(
  `ws://139.59.25.254/backend/api-fast/api/v1/video-sessions/{session_id}/ws?token=<jwt_token>`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
  
  // Events:
  // - "host_joined": Host joined, audience can now join
  // - "participant_joined": New participant joined
  // - "session_ended": Session ended
  // - "join_failed": Join attempt failed
};
```

## Complete Test Flow

```bash
# 1. Login as host
TOKEN=$(curl -X POST http://139.59.25.254/backend/api-fast/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"host@example.com","password":"password"}' | jq -r '.data.access_token')

# 2. Create webinar
WEBINAR_ID=$(curl -X POST http://139.59.25.254/backend/api-fast/api/v1/webinars \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Webinar",
    "webinar_date": "2026-01-15",
    "start_time": "14:00:00",
    "end_time": "15:00:00",
    "host_id": "<host_uuid>",
    "visibility": "public",
    "is_free": true
  }' | jq -r '.data.id')

# 3. Create video session
SESSION_ID=$(curl -X POST http://139.59.25.254/backend/api-fast/api/v1/video-sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_type\": \"webinar\",
    \"doctor_id\": \"<host_uuid>\",
    \"webinar_id\": \"$WEBINAR_ID\",
    \"scheduled_start_time\": \"2026-01-15T14:00:00Z\",
    \"scheduled_end_time\": \"2026-01-15T15:00:00Z\"
  }" | jq -r '.data.session_id')

# 4. Host joins
curl -X POST "http://139.59.25.254/backend/api-fast/api/v1/video-sessions/$SESSION_ID/join" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_role": "doctor"}'

# 5. Get session status
curl -X GET "http://139.59.25.254/backend/api-fast/api/v1/video-sessions/$SESSION_ID/status" \
  -H "Authorization: Bearer $TOKEN"
```

## Next Steps

1. ✅ Configure Agora credentials
2. ✅ Test host join flow
3. ✅ Test audience join flow
4. ✅ Test multi-participant
5. ✅ Integrate with frontend Agora SDK
