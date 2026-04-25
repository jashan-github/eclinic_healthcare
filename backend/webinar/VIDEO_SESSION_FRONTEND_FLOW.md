# Video Session Frontend Flow

## Overview
This document describes the frontend flow for the simplified video session join process. The new flow ensures that both doctor and patient must be ready before the video call starts, and all join parameters are published via Redis when both parties are ready.

## Flow Diagram

```
┌─────────────┐
│   Doctor    │
│   Joins     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ doctor_ready = true          │
│ status: SCHEDULED/WAITING    │
│ token: null                  │
│ message: "Waiting for        │
│          patient..."         │
└─────────────────────────────┘
       │
       │ (Patient joins)
       ▼
┌─────────────┐
│  Patient    │
│   Joins     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ patient_ready = true         │
│ Both ready detected!         │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ System automatically:        │
│ - Generates tokens for both  │
│ - Starts 30s watchdog        │
│ - Publishes via Redis        │
│ - Returns tokens             │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Both parties receive:        │
│ - token                      │
│ - channel_name               │
│ - watchdog_expires_at        │
│ - status: JOINING            │
└──────┬──────────────────────┘
       │
       │ (Both call join-success)
       ▼
┌─────────────────────────────┐
│ status: IN_CALL              │
│ Video call active            │
└─────────────────────────────┘
```

## API Endpoints

### 1. Doctor Joins Session
**Endpoint:** `POST /api/v1/video-sessions/{session_id}/join`

**Request:**
```json
{
  // Optional body (can be empty)
}
```

**Response (Doctor not ready yet):**
```json
{
  "success": true,
  "message": "Join request processed",
  "data": {
    "status": "scheduled",
    "token": null,
    "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_...",
    "waiting_room": true,
    "message": "Waiting for patient to join. Call will start when both parties are ready.",
    "doctor_ready": true,
    "patient_ready": false,
    "both_ready": false
  }
}
```

**Response (Both ready - call starting):**
```json
{
  "success": true,
  "message": "Join request processed",
  "data": {
    "status": "joining",
    "token": "006e3143b8450bd4cdc8d0565052d627c7bIAA...",
    "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_...",
    "waiting_room": false,
    "message": "Both parties are ready. Video call is starting. You have 30 seconds to join successfully.",
    "doctor_ready": true,
    "patient_ready": true,
    "both_ready": true,
    "watchdog_expires_at": "2025-01-22T13:00:30Z",
    "join_data": {
      "type": "call_started",
      "session_id": "31f9b6a1-49a8-4cad-8253-1c9e3be38c23",
      "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_...",
      "doctor_token": "006e3143b8450bd4cdc8d0565052d627c7bIAA...",
      "patient_token": "006e3143b8450bd4cdc8d0565052d627c7bIAB...",
      "watchdog_expires_at": "2025-01-22T13:00:30Z",
      "status": "joining",
      "message": "Both parties are ready. Video call is starting."
    }
  }
}
```

### 2. Patient Joins Session
**Endpoint:** `POST /api/v1/video-sessions/{session_id}/join`

**Request:**
```json
{
  // Optional body (can be empty)
}
```

**Response (Patient not ready yet):**
```json
{
  "success": true,
  "message": "Join request processed",
  "data": {
    "status": "scheduled",
    "token": null,
    "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_...",
    "waiting_room": true,
    "message": "Waiting for doctor to join. Call will start when both parties are ready.",
    "doctor_ready": false,
    "patient_ready": true,
    "both_ready": false
  }
}
```

**Response (Both ready - call starting):**
```json
{
  "success": true,
  "message": "Join request processed",
  "data": {
    "status": "joining",
    "token": "006e3143b8450bd4cdc8d0565052d627c7bIAB...",
    "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_...",
    "waiting_room": false,
    "message": "Both parties are ready. Video call is starting. You have 30 seconds to join successfully.",
    "doctor_ready": true,
    "patient_ready": true,
    "both_ready": true,
    "watchdog_expires_at": "2025-01-22T13:00:30Z",
    "join_data": {
      "type": "call_started",
      "session_id": "31f9b6a1-49a8-4cad-8253-1c9e3be38c23",
      "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_...",
      "doctor_token": "006e3143b8450bd4cdc8d0565052d627c7bIAA...",
      "patient_token": "006e3143b8450bd4cdc8d0565052d627c7bIAB...",
      "watchdog_expires_at": "2025-01-22T13:00:30Z",
      "status": "joining",
      "message": "Both parties are ready. Video call is starting."
    }
  }
}
```

### 3. Get Waiting Room Status
**Endpoint:** `GET /api/v1/video-sessions/{session_id}/waiting-room`

**Response:**
```json
{
  "success": true,
  "message": "Waiting room status retrieved",
  "data": {
    "status": "joining",
    "waiting_room": false,
    "doctor_ready": true,
    "patient_ready": true,
    "both_ready": true,
    "token": "006e3143b8450bd4cdc8d0565052d627c7bIAB...",
    "channel_name": "e3143b8450bd4cdc8d0565052d627c7b_...",
    "message": "Both parties ready. Call is starting.",
    "watchdog_expires_at": "2025-01-22T13:00:30Z"
  }
}
```

### 4. Confirm Join Success
**Endpoint:** `POST /api/v1/video-sessions/{session_id}/join-success`

**Request:**
```json
{
  // Optional body (can be empty)
}
```

**Response:**
```json
{
  "success": true,
  "message": "Join success confirmed",
  "data": {
    "session_id": "31f9b6a1-49a8-4cad-8253-1c9e3be38c23",
    "status": "in_call",
    "doctor_confirmed": true,
    "patient_confirmed": false,
    "both_confirmed": false
  }
}
```

**Response (Both confirmed):**
```json
{
  "success": true,
  "message": "Join success confirmed",
  "data": {
    "session_id": "31f9b6a1-49a8-4cad-8253-1c9e3be38c23",
    "status": "in_call",
    "doctor_confirmed": true,
    "patient_confirmed": true,
    "both_confirmed": true
  }
}
```

## Frontend Implementation Steps

### Step 1: Doctor Initiates Join
```javascript
// Doctor clicks "Join Call" button
async function doctorJoinSession(sessionId) {
  try {
    const response = await fetch(
      `/api/v1/video-sessions/${sessionId}/join`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      }
    );
    
    const data = await response.json();
    
    if (data.success) {
      if (data.data.both_ready) {
        // Both parties ready - call is starting
        await initializeAgoraCall(data.data);
      } else {
        // Waiting for patient
        showWaitingMessage("Waiting for patient to join...");
        // Poll or subscribe to Redis for updates
        subscribeToSessionUpdates(sessionId);
      }
    }
  } catch (error) {
    console.error('Join error:', error);
  }
}
```

### Step 2: Patient Joins
```javascript
// Patient clicks "Join Call" button
async function patientJoinSession(sessionId) {
  try {
    const response = await fetch(
      `/api/v1/video-sessions/${sessionId}/join`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      }
    );
    
    const data = await response.json();
    
    if (data.success) {
      if (data.data.both_ready) {
        // Both parties ready - call is starting
        await initializeAgoraCall(data.data);
      } else {
        // Waiting for doctor
        showWaitingMessage("Waiting for doctor to join...");
        // Poll or subscribe to Redis for updates
        subscribeToSessionUpdates(sessionId);
      }
    }
  } catch (error) {
    console.error('Join error:', error);
  }
}
```

### Step 3: Initialize Agora Call
```javascript
async function initializeAgoraCall(joinData) {
  const { token, channel_name, watchdog_expires_at } = joinData;
  
  // Initialize Agora client
  const client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
  
  // Join channel
  await client.join(
    AGORA_APP_ID,
    channel_name,
    token,
    userId
  );
  
  // Set up local video/audio tracks
  const localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack();
  const localVideoTrack = await AgoraRTC.createCameraVideoTrack();
  
  // Publish tracks
  await client.publish([localAudioTrack, localVideoTrack]);
  
  // Display local video
  localVideoTrack.play("local-video-container");
  
  // Listen for remote users
  client.on("user-published", async (user, mediaType) => {
    await client.subscribe(user, mediaType);
    
    if (mediaType === "video") {
      const remoteVideoTrack = user.videoTrack;
      remoteVideoTrack.play(`remote-video-container-${user.uid}`);
    }
    
    if (mediaType === "audio") {
      const remoteAudioTrack = user.audioTrack;
      remoteAudioTrack.play();
    }
  });
  
  // Confirm join success after successful Agora join
  await confirmJoinSuccess(sessionId);
}
```

### Step 4: Confirm Join Success
```javascript
async function confirmJoinSuccess(sessionId) {
  try {
    const response = await fetch(
      `/api/v1/video-sessions/${sessionId}/join-success`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      }
    );
    
    const data = await response.json();
    
    if (data.success && data.data.both_confirmed) {
      // Both parties confirmed - call is fully active
      showCallActive();
    }
  } catch (error) {
    console.error('Confirm join error:', error);
  }
}
```

### Step 5: Subscribe to Redis Updates (Optional)
```javascript
// Using WebSocket to subscribe to Redis PUB/SUB updates
function subscribeToSessionUpdates(sessionId) {
  const ws = new WebSocket(`ws://your-backend/ws/${sessionId}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'call_started') {
      // Both parties ready - initialize call
      initializeAgoraCall(data.data);
    } else if (data.type === 'both_joined') {
      // Both parties confirmed join
      showCallActive();
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    // Fallback to polling
    pollWaitingRoomStatus(sessionId);
  };
}

// Fallback polling
async function pollWaitingRoomStatus(sessionId) {
  const interval = setInterval(async () => {
    try {
      const response = await fetch(
        `/api/v1/video-sessions/${sessionId}/waiting-room`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      const data = await response.json();
      
      if (data.success && data.data.both_ready && data.data.token) {
        clearInterval(interval);
        await initializeAgoraCall(data.data);
      }
    } catch (error) {
      console.error('Polling error:', error);
    }
  }, 2000); // Poll every 2 seconds
}
```

## State Management

### Session States
- `SCHEDULED`: Initial state, waiting for parties to join
- `WAITING_ROOM`: One party ready, waiting for the other
- `JOINING`: Both parties ready, tokens generated, watchdog active
- `DOCTOR_JOINED`: Doctor confirmed join, waiting for patient
- `IN_CALL`: Both parties confirmed, call active
- `COMPLETED`: Call ended successfully
- `JOIN_FAILED`: Join attempt failed (watchdog expired)

### Readiness Flags
- `doctor_ready`: Doctor has indicated readiness (set when doctor calls `/join`)
- `patient_ready`: Patient has indicated readiness (set when patient calls `/join`)
- `both_ready`: Both flags are true (computed, not stored)

### Confirmation Flags
- `doctor_confirmed_join`: Doctor confirmed successful Agora join
- `patient_confirmed_join`: Patient confirmed successful Agora join
- `both_confirmed`: Both flags are true (computed, not stored)

## Error Handling

### Watchdog Expired
If the watchdog expires (30 seconds after both parties are ready), the session status changes to `JOIN_FAILED`. The frontend should:
1. Show error message
2. Allow user to retry by calling `/join` again
3. Optionally call `/retry` endpoint to create a new session

### Network Errors
- Implement retry logic with exponential backoff
- Show user-friendly error messages
- Allow manual retry

## Best Practices

1. **Always check `both_ready` flag** before initializing Agora call
2. **Confirm join success** after successful Agora connection
3. **Handle watchdog expiration** gracefully
4. **Subscribe to Redis updates** for real-time notifications (or use polling as fallback)
5. **Show clear status messages** to users about waiting state
6. **Implement proper error handling** for all API calls
7. **Clean up resources** when call ends (unpublish tracks, leave channel)

## Testing Checklist

- [ ] Doctor can join session
- [ ] Patient can join session
- [ ] Both parties receive tokens when both ready
- [ ] Watchdog expires correctly after 30 seconds
- [ ] Join success confirmation works
- [ ] Status transitions correctly
- [ ] Redis PUB/SUB notifications work (or polling fallback)
- [ ] Error handling works for network failures
- [ ] Retry logic works for failed joins
