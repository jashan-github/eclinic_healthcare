# eClinic — Windows Setup Prerequisites

This project has **2 parts**: a FastAPI backend (Python) and a React/Vite frontend (Node.js). Both must run at the same time.

---

## 1. Software to install (one-time)

| Tool | Version | Download |
|---|---|---|
| **Python** | 3.11 or 3.12 | https://www.python.org/downloads/windows/ — during install, tick **"Add Python to PATH"** |
| **Node.js** | 22.12+ (LTS) | https://nodejs.org/en/download — Windows installer, includes `npm` |
| **Git** | latest | https://git-scm.com/download/win |
| **Docker Desktop** | latest | https://www.docker.com/products/docker-desktop/ — needed for PostgreSQL. Requires Windows 10/11 with WSL2 |
| **PostgreSQL client** (optional) | 15+ | https://www.postgresql.org/download/windows/ — only if you want `psql` CLI |
| **VS Code** (recommended) | latest | https://code.visualstudio.com/ |

After installing, open **PowerShell** and verify:
```powershell
python --version     # 3.11.x or 3.12.x
node --version       # v22.12.x or higher
npm --version
git --version
docker --version
```

---

## 2. Get the code

Unzip the project folder, then open PowerShell inside it:
```powershell
cd C:\path\to\eclinic-project
```

You should see two folders:
- `backend-full\fastapt-backend`
- `frontend-23-04\bizdesire-eclinic-frontend-7641a6fca00a`

---

## 3. Start PostgreSQL (Docker)

Make sure **Docker Desktop** is running (whale icon in taskbar).

```powershell
docker run -d --name eclinic-postgres `
  -e POSTGRES_USER=eclinic_user `
  -e POSTGRES_PASSWORD=eclinic_password `
  -e POSTGRES_DB=eclinic_db `
  -p 5436:5432 `
  postgres:15
```

To stop/start later:
```powershell
docker stop eclinic-postgres
docker start eclinic-postgres
```

---

## 4. Backend setup

```powershell
cd backend-full\fastapt-backend

# Create .env from the example
copy env.example .env
```

**Edit `.env`** and set:
```
DATABASE_URL=postgresql://eclinic_user:eclinic_password@localhost:5436/eclinic_db
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
DEBUG=true
```

Also fill in any 3rd-party keys you need (Agora, Twilio, SendGrid, Sentoo). Leave blank for local dev if not using those features.

Create a virtual environment and install deps:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If PowerShell blocks the activation script, run once:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

Run migrations + seeders:
```powershell
alembic upgrade head
python scripts\seed_data.py
python scripts\seed_language_data.py
python scripts\seed_location_data.py
python scripts\seed_medical_services_data.py
python scripts\seed_vital_names.py
python scripts\seed_vital_signs.py
python scripts\seed_test_users.py
```

Start the backend:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check it works: open http://localhost:8000/docs

---

## 5. Redis (optional)

Redis is **not required** — the backend will start without it. You only lose:

- Rate limiting (disabled silently)
- Logout token blacklisting (tokens stay valid until their 30-min expiry)
- Response caching

### If you skip Redis

Add these to `.env`:

```ini
REDIS_ENABLED=false
RATE_LIMIT_ENABLED=false
```

### If you want Redis

Run it in Docker:

```powershell
docker run -d --name eclinic-redis -p 6379:6379 redis:7-alpine
```

Keep `REDIS_URL=redis://localhost:6379/0` in `.env`.

---

## 6. Frontend setup

Open a **second** PowerShell window:

```powershell
cd frontend-23-04\bizdesire-eclinic-frontend-7641a6fca00a
npm install
npm run dev
```

Open http://localhost:5173

---

## 7. Test logins (seeded users)

| Role | URL | Email | Password |
|---|---|---|---|
| Admin | http://localhost:5173/auth/admin-login | `admin@yopmail.com` | `password` |
| Doctor | http://localhost:5173/auth/login → *Healthcare Provider* tab | `doctor@yopmail.com` | `password` |
| Patient | http://localhost:5173/auth/login → *Patient* tab | `patient@yopmail.com` | `password` |
| Staff | http://localhost:5173/auth/login → *Staff* tab | `staff@yopmail.com` | `password` |

---

## Common issues

- **`docker: command not found`** → Start Docker Desktop first.
- **Port 5436/5432/6379 already in use** → Change the port in the `docker run` command and update `.env` to match.
- **`alembic: command not found`** → Activate the venv: `.\venv\Scripts\Activate.ps1`
- **`psycopg2` install fails on Windows** → Install the binary wheel: `pip install psycopg2-binary`
- **Vite says "Node 22.12+ required"** → Upgrade Node from https://nodejs.org
- **CORS / 401 on frontend** → Confirm `CORS_ORIGINS` in `.env` includes `http://localhost:5173`.
- **`Invalid credentials for role: X`** → You're on the wrong login page. Admin → `/auth/admin-login`; everyone else → `/auth/login`.

---

## Daily startup (after first-time setup)

```powershell
# 1. Ensure Docker Desktop is running, then:
docker start eclinic-postgres
docker start eclinic-redis

# 2. Backend (PowerShell window 1)
cd backend-full\fastapt-backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# 3. Frontend (PowerShell window 2)
cd frontend-23-04\bizdesire-eclinic-frontend-7641a6fca00a
npm run dev
```

That's it. Open http://localhost:5173 and log in.
