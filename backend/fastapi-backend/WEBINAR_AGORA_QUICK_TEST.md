# Webinar Agora Integration - Quick Test Guide

## ✅ Implementation Complete

The webinar end-to-end integration with Agora has been fixed and is ready for testing.

## 🔧 Setup Required

### 1. Get Agora App Certificate

1. Go to https://console.agora.io/
2. Login and select your project
3. Go to "Project Management" > "Edit"
4. Copy the **App Certificate** (not Access Key or Secret)
5. Update `.env` file:

```bash
cd /var/www/backend/fastapi-backend
# Edit .env file
AGORA_APP_ID=e3143b8450bd4cdc8d0565052d627c7b
AGORA_APP_CERTIFICATE=<paste_your_certificate_here>
```

### 2. Restart Backend

```bash
docker compose restart backend
```

## 🧪 Quick Test Steps

### Step 1: Create Webinar

```bash
# Login as admin/doctor
TOKEN=$(curl -X POST http://139.59.25.254/backend/api-fast/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' | jq -r '.data.access_token')

# Create webinar
WEBINAR_ID=$(curl -X POST http://139.59.25.254/backend/api-fast/api/v1/webinars \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Agora Webinar",
    "description": "Testing Agora integration",
    "webinar_date": "2026-01-15",
    "start_time": "14:00:00",
    "end_time": "15:00:00",
    "host_id": "<host_uuid>",
    "visibility": "public",
    "is_free": true
  }' | jq -r '.data.id')

echo "Webinar ID: $WEBINAR_ID"
```

### Step 2: Create Video Session

```bash
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

echo "Session ID: $SESSION_ID"
```

### Step 3: Host Joins

```bash
# Host requests join
RESPONSE=$(curl -X POST "http://139.59.25.254/backend/api-fast/api/v1/video-sessions/$SESSION_ID/join" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_role": "doctor"}')

echo $RESPONSE | jq '.'

# Extract token and channel
TOKEN=$(echo $RESPONSE | jq -r '.data.token')
CHANNEL=$(echo $RESPONSE | jq -r '.data.channel_name')
echo "Token: $TOKEN"
echo "Channel: $CHANNEL"
```

### Step 4: Audience Joins

```bash
# Login as participant
PARTICIPANT_TOKEN=$(curl -X POST http://139.59.25.254/backend/api-fast/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@example.com","password":"password"}' | jq -r '.data.access_token')

# Participant requests join
curl -X POST "http://139.59.25.254/backend/api-fast/api/v1/video-sessions/$SESSION_ID/join" \
  -H "Authorization: Bearer $PARTICIPANT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_role": "patient"}'
```

## 📱 Frontend Integration

### React/JavaScript Example

```javascript
import AgoraRTC from 'agora-rtc-sdk-ng';

const APP_ID = 'e3143b8450bd4cdc8d0565052d627c7b';
const channelName = 'channel_from_api';
const token = 'token_from_api';

// Create client
const client = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' });

// Join channel
await client.join(APP_ID, channelName, token, null);

// Create and publish local tracks
const [audioTrack, videoTrack] = await Promise.all([
  AgoraRTC.createMicrophoneAudioTrack(),
  AgoraRTC.createCameraVideoTrack()
]);

await client.publish([audioTrack, videoTrack]);

// Play local video
videoTrack.play('local-video');

// Listen for remote users
client.on('user-published', async (user, mediaType) => {
  await client.subscribe(user, mediaType);
  if (mediaType === 'video') {
    user.videoTrack.play(`remote-${user.uid}`);
  }
  if (mediaType === 'audio') {
    user.audioTrack.play();
  }
});
```

## ✅ What Was Fixed

1. **Webinar Join Logic**: Fixed to handle webinars without patient_id
2. **Audience Join**: Added `_handle_webinar_audience_join()` method
3. **Host Join**: Removed early join restriction for webinars
4. **Token Generation**: Using custom implementation (no external SDK needed)
5. **Access Control**: Webinars allow any authenticated user to join as audience

## 🔍 Verify Configuration

```bash
# Check Agora config is loaded
docker compose exec backend python3 -c "
from app.core.config import settings
print('App ID:', settings.AGORA_APP_ID)
print('Certificate:', 'SET' if settings.AGORA_APP_CERTIFICATE else 'NOT SET')
"
```

## 📝 Important Notes

1. **App Certificate Required**: You must get the App Certificate from Agora Console
2. **Token Format**: Tokens are generated using Agora's token specification
3. **Channel Names**: Secure hash-based (no PHI)
4. **Webinar Access**: Public webinars allow any authenticated user to join
5. **Waiting Room**: Audience waits until host joins

## 🐛 Troubleshooting

### "Agora credentials not configured"
- Check `.env` has both `AGORA_APP_ID` and `AGORA_APP_CERTIFICATE`
- Restart backend: `docker compose restart backend`

### "Invalid token" in Agora SDK
- Verify App Certificate matches Agora Console
- Check token hasn't expired
- Ensure using correct App ID

### "Access denied" for webinar
- Verify user is authenticated
- Check webinar visibility (public/private)
- For private webinars, ensure user has access
