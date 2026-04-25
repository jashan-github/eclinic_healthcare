# Webinar Service (webinar-service)

**This service owns all Agora and video session APIs** in the application. In the microservice architecture, all video call and webinar live-streaming (Agora tokens, channels, session state) are implemented here—not in the main backend (api-fast).

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ eclinic-backend │         │ webinar-service │         │  chat-service   │
│   (Port 8000)   │         │   (Port 8002)   │         │   (Port 8001)   │
└────────┬────────┘         └────────┬────────┘         └────────┬────────┘
         │                            │                            │
         └────────────────────────────┴────────────────────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │   Shared Services       │
                         │  ┌──────────┐          │
                         │  │PostgreSQL│          │
                         │  │eclinic_db│          │
                         │  └──────────┘          │
                         │  ┌──────────┐          │
                         │  │  Redis   │          │
                         │  │eclinic-  │          │
                         │  │redis     │          │
                         │  └──────────┘          │
                         └────────────────────────┘
```

## Features

- **Webinar Management**: Create, update, delete, and list webinars
- **Agora Integration**: Server-side token generation for secure video streaming
- **Role-Based Access**: Admin, Doctor, and Patient endpoints
- **Async Architecture**: Fully async SQLAlchemy for high performance
- **JWT Authentication**: Shared JWT tokens with `eclinic-backend`
- **Swagger UI**: Interactive API documentation with Authorize button

## Prerequisites

- Docker and Docker Compose
- Shared PostgreSQL database (`eclinic-postgres`)
- Shared Redis instance (`eclinic-redis`)
- Docker network `eclinic-network` (created by `eclinic-backend`)

## Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```env
# JWT Configuration (must match eclinic-backend)
SECRET_KEY=your-secret-key-min-32-characters-change-in-production
ALGORITHM=HS256

# Encryption Key for Agora Tokens
# Generate using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
ENCRYPTION_KEY=your-fernet-encryption-key

# Agora Configuration
AGORA_APP_ID=your-agora-app-id
AGORA_APP_CERTIFICATE=your-agora-app-certificate
AGORA_TOKEN_EXPIRY_MINUTES=60

# Base URL for generating absolute URLs
BASE_URL=https://portal.salutogenahealthcareltd.com/backend/api-fast/
```

### 2. Database Migration

The `webinars` table will be created in the shared `eclinic_db` database. Run migrations:

```bash
# From webinar-service directory
alembic upgrade head
```

Or if running in Docker:

```bash
docker compose exec webinar-service alembic upgrade head
```

### 3. Docker Setup

Ensure the `eclinic-network` exists (created by `eclinic-backend`):

```bash
# If network doesn't exist, create it:
docker network create eclinic-network
```

Build and start the service:

```bash
docker compose up -d --build
```

### 4. Verify Service

Check service health:

```bash
curl -X GET "http://localhost:8002/health" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Access Swagger UI:

```
http://localhost:8002/docs
```

## API Endpoints

### Webinar CRUD and live (this service)

#### Admin (`/api/v1/admin/webinars`)

- `POST /` - Create a new webinar
- `GET /` - List all webinars (with filters)
- `GET /{webinar_id}` - Get webinar details
- `PUT /{webinar_id}` - Update webinar
- `DELETE /{webinar_id}` - Delete webinar (soft delete)
- `POST /{webinar_id}/go-live` - Go live as host (returns Agora token/channel)
- `POST /{webinar_id}/registered-count` - Update registered count (internal)

#### Doctor (`/api/v1/doctor/webinars`)

- `GET /` - Get upcoming webinars
- `GET /{webinar_id}/join` - Get live webinar details
- `POST /{webinar_id}/go-live` - Go live as host (returns Agora token/channel)
- `POST /{webinar_id}/join` - Join as audience (returns Agora token or waiting room)

#### Patient (`/api/v1/patient/webinars`)

- `GET /` - Get upcoming public webinars
- `POST /{webinar_id}/join` - Join as audience (returns Agora token or waiting room)

### Agora / Video Sessions (all in this service)

**All Agora and video session APIs live in webinar-service.** The main backend (api-fast) does not implement video or token generation; it calls this service when needed (e.g. appointment video session creation).

#### Video Sessions (`/api/v1/video-sessions`)

- `POST /` - Create video session (appointment or webinar)
- `GET /by-webinar/{webinar_id}` - Get active video session for a webinar
- `POST /{session_id}/join` - Request to join (returns Agora token, channel_name, app_id)
- `POST /{session_id}/join-success` - Confirm join success
- `GET /{session_id}/waiting-room` - Poll waiting room status
- `POST /{session_id}/end` - End session
- `WS /ws/{session_id}` - WebSocket for real-time updates
- (Other video-session endpoints as in `app/api/rest/video_sessions.py`)

## Authentication

All endpoints require JWT authentication. Get your token from `eclinic-backend`:

```bash
POST /backend/api-fast/api/v1/auth/login
```

Use the token in the Authorization header:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

## Swagger UI

The service includes a custom Swagger UI with an "Authorize" button at the top:

1. Click "Authorize" button
2. Enter your JWT token (without "Bearer" prefix)
3. Click "Authorize"
4. All authenticated endpoints will now use this token

## Development

### Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables (see `.env` file)

3. Run migrations:

```bash
alembic upgrade head
```

4. Start the service:

```bash
uvicorn app.main:app --reload --port 8002
```

### Project Structure

```
webinar-service/
├── app/
│   ├── api/
│   │   └── rest/
│   │       └── webinars.py      # API endpoints
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   ├── security.py          # JWT validation
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── logging.py            # Logging setup
│   ├── db/
│   │   ├── models.py            # Webinar model
│   │   └── session.py           # Async database session
│   ├── schemas/
│   │   └── webinar.py           # Pydantic schemas
│   ├── services/
│   │   ├── webinar_service.py  # Business logic
│   │   └── agora_service.py     # Agora token generation
│   └── main.py                  # FastAPI application
├── alembic/                     # Database migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Database

The service uses the shared `eclinic_db` PostgreSQL database. The `webinars` table is created via Alembic migrations.

**Important**: The `users` table is in the shared database, so foreign key relationships work correctly.

## Agora Integration

The service generates Agora tokens server-side for security:

- **Channel Names**: Hash-based (no PHI)
- **Token Generation**: Server-side only (never on frontend)
- **Token Encryption**: Fernet encryption for database storage
- **Token Expiry**: Configurable (15-60 minutes)

## Cron jobs (Docker)

### Mark past webinars as completed (expired) – every 5 minutes

When using Docker Compose, the **`webinar-cron`** service runs alongside the main app and executes the mark-expired script every 5 minutes. No extra setup is required: start the stack with:

```bash
docker compose up -d --build
```

This starts:

- **webinar-service** – API (port 8002)
- **webinar-cron** – cron that runs `app.scripts.mark_expired_webinars` every 5 minutes

Both use the same image and env (including `DATABASE_URL` from `.env`). Cron output appears in the cron container logs:

```bash
docker compose logs -f webinar-cron
```

**Manual run** (inside the app container):

```bash
docker compose exec webinar-service python -m app.scripts.mark_expired_webinars
```

**Without Docker** (from project root):

```bash
cd /var/www/backend/webinar && python3 -m app.scripts.mark_expired_webinars
```

## Reverse Proxy Support

The service supports reverse proxy deployment with `ROOT_PATH`:

```env
ROOT_PATH=/backend/webinar-service
```

This allows the service to be accessed via:
```
https://yourdomain.com/backend/webinar-service/docs
```

## Troubleshooting

### Service won't start

1. Check Docker network exists:
   ```bash
   docker network ls | grep eclinic-network
   ```

2. Verify PostgreSQL and Redis are running:
   ```bash
   docker ps | grep -E "eclinic-postgres|eclinic-redis"
   ```

3. Check service logs:
   ```bash
   docker compose logs webinar-service
   ```

### Database connection errors

- Ensure `eclinic-postgres` container is running
- Verify `DATABASE_URL` in `docker-compose.yml` matches your setup
- Check network connectivity: `docker network inspect eclinic-network`

### Authentication errors

- Ensure `SECRET_KEY` matches `eclinic-backend`
- Verify JWT token is valid and not expired
- Check token format: `Bearer <token>`

## License

Part of the eClinic healthcare platform.
