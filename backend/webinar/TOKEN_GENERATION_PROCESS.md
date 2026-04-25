# Agora Token Generation Process

This document describes how Agora RTC tokens are generated and used in the webinar service, aligned with [Agora's token authentication workflow](https://docs.agora.io/en/interactive-live-streaming/token-authentication/authentication-workflow?platform=web).

## Rule from Agora

> **The user ID and channel name used to join a channel must be consistent with the values used to generate the token.**

So: **token(channelName, uid) → client must call `join(token, channelName, uid)`** with the same `channelName` and `uid`.

---

## 1. Where Tokens Are Generated

Tokens are **only** created on the server (webinar service), never on the frontend.

| Component | File | Role |
|-----------|------|------|
| **AgoraService** | `app/services/agora_service.py` | Builds and signs the token payload |
| **VideoSessionService** | `app/services/video_session_service.py` | Decides *when* to generate (which user, which channel) and calls AgoraService |

---

## 2. End-to-End Flow

### Step 1: Channel name is fixed at session creation

- **Appointment sessions:**  
  `DoctorName_PatientName_YYYYMMDD_HHmm_<6-char-suffix>`  
  (from `generate_channel_name_from_participants()`)
- **Webinars / no names:**  
  `generate_secure_channel_name(session_id)` (hash-based)

That value is stored in `video_sessions.channel_name` and is **the** channel name used for the rest of the flow.

### Step 2: When a user is allowed to join, we generate a token for that channel and uid

- **Appointment, both ready:**  
  `_start_call_when_both_ready()`  
  → generates doctor token and patient token **using `session.channel_name`** (and doctor/patient user IDs).
- **Appointment, doctor already in, patient joins:**  
  `_generate_patient_token()`  
  → generates patient token **using `session.channel_name`** and patient user ID.
- **Webinar audience:**  
  `_handle_webinar_audience_join()`  
  → generates token **using `session.channel_name`** and audience user ID.

So every token is built for the **same** channel name the client will use to join.

### Step 3: Low-level token build (AgoraService)

`agora_service.generate_token_for_user(...)` (or direct `generate_token(...)`) does:

1. **Inputs**
   - `channel_name`: from `session.channel_name` (so it matches what the client will use).
   - `user_id`: string (e.g. `str(doctor_id)` or `str(patient_id)`).
   - `role`: `"publisher"` (can send audio/video).
   - `expire_timestamp` / `expiry_minutes`: e.g. 15–60 minutes.

2. **Payload (logical content)**
   - `app_id`: from `AGORA_APP_ID`
   - `channel`: `channel_name`
   - `uid`: `user_id`
   - `expire`, `issue_ts`, `salt`
   - `services[].privileges`: e.g. `join_channel`, `publish_audio_stream`, `publish_video_stream`, `publish_data_stream` (for publisher).

3. **Signing**
   - HMAC-SHA256 of the payload using `AGORA_APP_CERTIFICATE`.
   - Result is base64-encoded and wrapped with the payload into the final token string.

4. **Optional**
   - Token can be encrypted (Fernet) before storing in the DB; the **plain** token is what the client gets and uses in `join(token, channelName, uid)`.

---

## 3. Call Paths in Code

```
VideoSessionService (when both ready / patient join / webinar join)
    → agora_service.generate_token_for_user(
          session_id,
          user_id,
          role="publisher",
          expiry_minutes=...,
          channel_name=session.channel_name,   # must match client join
      )
    → AgoraService.generate_token(channel_name, user_id, role, expire_ts)
    → _generate_token_fallback(...)  # build payload, HMAC sign, base64
    → encrypt_token(...) for DB; return token_plain for API
```

The API returns to the client:

- `token` — plain token string to pass to `client.join(appId, channelName, token, uid)`
- `channel_name` — must be exactly `session.channel_name`
- `app_id` — for `AgoraRTC.createClient({ appId })`

---

## 4. Summary Table

| Step | What happens |
|------|----------------|
| 1 | Session is created → `channel_name` is set (participant-based or hash) and stored. |
| 2 | When user is allowed to join, backend calls `generate_token_for_user(..., channel_name=session.channel_name)`. |
| 3 | AgoraService builds payload with that `channel_name` and `uid`, signs with App Certificate, returns token. |
| 4 | API sends `token`, `channel_name`, `app_id` to client. |
| 5 | Client does `client.join(appId, channel_name, token, uid)` — channel and uid match what the token was built for. |

---

## 5. Configuration

- `AGORA_APP_ID` — Agora project App ID.
- `AGORA_APP_CERTIFICATE` — Used to sign tokens; keep secret.
- `AGORA_TOKEN_EXPIRY_MINUTES` (optional) — Token lifetime, e.g. 60.
- `ENCRYPTION_KEY` — If set, tokens are encrypted at rest in the DB; clients always receive the decrypted token.

Token generation uses these in `app/core/config.py` and `app/services/agora_service.py`.
