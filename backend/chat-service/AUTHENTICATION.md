# Authentication Protection - Chat Service

All API endpoints in the chat service are now protected with JWT authentication.

## Protected Endpoints

### 1. Health Check
- **Endpoint**: `GET /health`
- **Authentication**: Required (JWT Bearer token)
- **Response**: Returns health status with authenticated user ID

**Example**:
```bash
curl -X GET http://localhost:8001/health \
  -H "Authorization: Bearer <your-jwt-token>"
```

**Response**:
```json
{
  "status": "healthy",
  "service": "chat-service",
  "version": "1.0.0",
  "authenticated_user": "user-uuid"
}
```

### 2. REST API Endpoints

All REST API endpoints require JWT authentication via `Authorization: Bearer <token>` header.

#### Start Chat Room
- **Endpoint**: `POST /api/chat/start`
- **Authentication**: Required
- **Role**: Doctor only

#### Get Chat Rooms
- **Endpoint**: `GET /api/chat/rooms`
- **Authentication**: Required
- **Role**: Any authenticated user

#### Get Chat Messages
- **Endpoint**: `GET /api/chat/{room_id}/messages`
- **Authentication**: Required
- **Access**: User must be part of the chat room

#### Close Chat Room
- **Endpoint**: `POST /api/chat/{room_id}/close`
- **Authentication**: Required
- **Role**: Doctor only

### 3. WebSocket Endpoint

- **Endpoint**: `WS /ws/chat/{room_id}?token=<jwt-token>`
- **Authentication**: Required (token as query parameter)
- **Access**: User must be part of the chat room

## Authentication Flow

1. **Get JWT Token** from main backend:
   ```bash
   curl -X POST http://localhost:8000/backend/api-fast/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password"}'
   ```

2. **Use Token** in all chat service requests:
   ```bash
   curl -X GET http://localhost:8001/api/chat/rooms \
     -H "Authorization: Bearer <token-from-step-1>"
   ```

## Error Responses

### Missing Authentication
```json
{
  "detail": "Authorization header missing"
}
```
**Status Code**: 401 Unauthorized

### Invalid Token
```json
{
  "detail": "Invalid authentication token"
}
```
**Status Code**: 401 Unauthorized

### Access Denied
```json
{
  "detail": "Access denied to this chat room"
}
```
**Status Code**: 403 Forbidden

## Security Notes

1. **Shared Secret Key**: Both main backend and chat service must use the same `SECRET_KEY` for JWT validation
2. **Token Expiration**: Tokens expire based on `ACCESS_TOKEN_EXPIRE_MINUTES` setting
3. **HTTPS**: In production, always use HTTPS to protect tokens in transit
4. **Token Storage**: Store tokens securely (e.g., httpOnly cookies or secure storage)

## Testing Protected Endpoints

### Test Without Token (Should Fail)
```bash
curl http://localhost:8001/health
# Expected: 401 Unauthorized
```

### Test With Invalid Token (Should Fail)
```bash
curl http://localhost:8001/health \
  -H "Authorization: Bearer invalid-token"
# Expected: 401 Unauthorized
```

### Test With Valid Token (Should Succeed)
```bash
TOKEN="<valid-jwt-token>"
curl http://localhost:8001/health \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 OK with health status
```

## Implementation Details

All endpoints use the `get_current_user` dependency or `extract_token_from_header` function which:
1. Extracts the Bearer token from the `Authorization` header
2. Validates the JWT token using the shared `SECRET_KEY`
3. Extracts user ID and role from the token payload
4. Raises `HTTPException` (401) if authentication fails

The WebSocket endpoint validates the token from the query parameter before establishing the connection.
