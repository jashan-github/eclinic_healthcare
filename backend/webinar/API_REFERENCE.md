# Webinar Service – API Reference

All webinar CRUD, go-live, and join APIs are provided by the **webinar microservice**.  
Base URL: your webinar service host (e.g. `https://portal.salutogenahealthcareltd.com/backend/webinar-service`).

Authentication: `Authorization: Bearer <JWT>` on all endpoints below.

---

## Admin – Webinar CRUD

| Method | Path | Description |
|--------|------|-------------|
| **POST** | `/api/v1/admin/webinars` | Create a new webinar |
| **GET** | `/api/v1/admin/webinars` | List all webinars (with optional filters) |
| **GET** | `/api/v1/admin/webinars/{webinar_id}` | Get a webinar by ID |
| **PUT** | `/api/v1/admin/webinars/{webinar_id}` | Update a webinar |
| **DELETE** | `/api/v1/admin/webinars/{webinar_id}` | Delete a webinar (soft delete) |
| **POST** | `/api/v1/admin/webinars/{webinar_id}/registered-count` | Update `registered_count` (e.g. after payment) |

---

## Admin – Go-live (Host)

| Method | Path | Description |
|--------|------|-------------|
| **POST** | `/api/v1/admin/webinars/{webinar_id}/go-live` | Start the webinar as host. Returns Agora `session_id`, `channel_name`, `token`, `app_id`. |

---

## Doctor – List & Join

| Method | Path | Description |
|--------|------|-------------|
| **GET** | `/api/v1/doctor/webinars` | List upcoming webinars (scheduled/live; doctor sees own + public) |
| **GET** | `/api/v1/doctor/webinars/{webinar_id}/join` | Get live webinar details (webinar must be `live`; doctor must be host or public) |
| **POST** | `/api/v1/doctor/webinars/{webinar_id}/go-live` | Start the webinar as host. Returns Agora session + token. |
| **POST** | `/api/v1/doctor/webinars/{webinar_id}/join` | Join as **audience**. Returns Agora session + token (or waiting room if host not started). Host must use go-live. |

---

## Patient – List & Join

| Method | Path | Description |
|--------|------|-------------|
| **GET** | `/api/v1/patient/webinars` | List upcoming **public** webinars |
| **POST** | `/api/v1/patient/webinars/{webinar_id}/join` | Join as **audience**. For paid webinars, registration/payment is checked. Returns Agora session + token or waiting room. |

---

## Summary by action

| Action | Admin | Doctor | Patient |
|--------|-------|--------|---------|
| **CRUD** (create, list, get, update, delete) | ✅ `/api/v1/admin/webinars` | — | — |
| **List upcoming** | — | ✅ `GET /api/v1/doctor/webinars` | ✅ `GET /api/v1/patient/webinars` |
| **Go-live (host)** | ✅ `POST .../go-live` | ✅ `POST .../go-live` | — |
| **Join (audience)** | — | ✅ `POST .../join` | ✅ `POST .../join` |
| **Get join info (live)** | — | ✅ `GET .../join` | — |

---

## Go-live vs Join

- **Go-live**: Used by the **host** (admin or doctor) to start the webinar. Creates/gets the video session and returns host Agora token and channel info.
- **Join**: Used by **audience** (doctors or patients) to enter an already live webinar. Returns audience token (or “waiting room” if host has not started). Hosts must use go-live, not join.

All of these APIs live in the **webinar microservice**; the main FastAPI backend only handles **webinar payments** (registration, Sentoo, payment success, webhook).
