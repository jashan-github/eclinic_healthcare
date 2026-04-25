# Chat Service

Independent microservice for real-time doctor-patient chat with WebSocket support.

## Features

- Real-time chat via WebSockets
- Redis Pub/Sub for horizontal scalability
- JWT authentication
- Read receipts
- Typing indicators
- Chat history persistence
- Appointment-linked chat support
- Rate limiting
- Production-ready Docker setup

## Quick Start

1. Copy environment file:
```bash
cp .env.example .env
```

2. Update `.env` with your configuration

3. Start services:
```bash
docker compose up -d
```

4. Run migrations:
```bash
docker compose exec chat-service alembic upgrade head
```

5. Service will be available at `http://localhost:8001`

## API Endpoints

### REST API

- `POST /api/chat/start` - Start a new chat room (doctor only)
- `GET /api/chat/rooms` - Get user's chat rooms
- `GET /api/chat/{room_id}/messages` - Get chat messages
- `POST /api/chat/{room_id}/close` - Close a chat room (doctor only)

### WebSocket

- `WS /ws/chat/{room_id}?token=<jwt_token>` - Real-time chat connection

## WebSocket Message Format

### Send Message
```json
{
  "type": "message",
  "message": "Hello!",
  "message_type": "text"
}
```

### Typing Indicator
```json
{
  "type": "typing",
  "is_typing": true
}
```

### Read Receipt
```json
{
  "type": "read_receipt",
  "message_id": "uuid-here"
}
```

### Ping
```json
{
  "type": "ping"
}
```

## Environment Variables

See `.env.example` for all available configuration options.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --port 8001
```
