# Deployment — Vercel (frontend) + Render (backend) for demo

Both providers use the config files committed to this repo so deploys are reproducible. The frontend reads `frontend/vercel.json`; the backend reads `render.yaml` at the repo root.

Total demo cost: **$0** (free tiers). After demo / production hardening: ~$35-40/mo.

---

## 1. Deploy backend on Render

### a. Import the repo as a Blueprint

1. Go to https://dashboard.render.com → **New → Blueprint**
2. Connect your GitHub and pick `noutiyal/e-clinic`
3. Render detects `render.yaml` and shows what it'll create:
   - Postgres database `eclinic-db` (Singapore region, free plan, 90 days)
   - Web service `eclinic-api` (Docker, free plan)
4. Click **Apply**

### b. Fill in the secret env vars

After the first build kicks off, open **eclinic-api → Environment** and set the `sync: false` vars (these aren't in the YAML on purpose):

| Key | Value |
|---|---|
| `CORS_ORIGINS` | `https://<your-vercel-url>.vercel.app,http://localhost:5173` (you'll know the Vercel URL after step 2 — come back and update) |
| `AGORA_APP_ID` | from your local `.env` |
| `AGORA_APP_CERTIFICATE` | from your local `.env` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `FROM_EMAIL` | from your local `.env` (only if email features in demo) |

`DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, `RUN_MIGRATIONS`, `PYTHON_VERSION` are all set automatically by the Blueprint — don't touch them.

### c. Migrations

The Dockerfile's entrypoint (`scripts/entrypoint.sh`) runs `python scripts/migrate.py` on every cold start because `RUN_MIGRATIONS=true` is set in `render.yaml`. No manual step needed.

### d. Seed test users

After the first successful deploy, open **eclinic-api → Shell** and run:

```bash
python scripts/seed_test_users.py
```

Creates `doctor@yopmail.com`, `patient@yopmail.com`, `staff@yopmail.com` (all password `password`).

### e. Note the URL

Render will give you `https://eclinic-api.onrender.com` (or `eclinic-api-<random>` if name collision). Copy it for the next step.

---

## 2. Deploy frontend on Vercel

### a. Import the repo

1. https://vercel.com/new → import `noutiyal/e-clinic`
2. Vercel auto-detects the Vite framework. The only thing to change:
   - **Root Directory:** `frontend` (so it reads `frontend/vercel.json`)
3. Don't click Deploy yet — set env vars first.

### b. Set environment variables (Project → Settings → Environment Variables)

| Key | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://eclinic-api.onrender.com/api/eclinic` (URL from step 1e) |
| `VITE_SECURE_LOCAL_STORAGE_HASH_KEY` | from your local `frontend/.env.local` |
| `VITE_SECURE_LOCAL_STORAGE_PREFIX` | from your local `frontend/.env.local` |

Apply to all three environments: **Production, Preview, Development**.

### c. Deploy

Click **Deploy**. ~2 minutes. You'll get `https://e-clinic-<random>.vercel.app`.

### d. Wire CORS back to Render

Go back to Render → `eclinic-api` → Environment, update:

```
CORS_ORIGINS=https://e-clinic-<random>.vercel.app,http://localhost:5173
```

Render auto-redeploys (≈1 min).

---

## 3. Verify

### Smoke test

1. Visit the Vercel URL → login page renders
2. Login as `doctor@yopmail.com` / `password` → lands on dashboard
3. Open DevTools → Network → confirm API calls hit `eclinic-api.onrender.com`, not localhost
4. Walk Loop 1 of `DEMO_SCRIPT.md` end-to-end

### If anything 5xx that worked locally

Order to check:
1. **CORS** — backend env `CORS_ORIGINS` must include the exact Vercel URL with `https://` and no trailing slash
2. **Cold start** — first request after 15 min idle takes ~30s on free tier; just wait
3. **Missing env var** — Render Logs tab will say which key is missing
4. **Migrations failed** — Render Shell, run `python scripts/migrate.py` manually and read the output

---

## Demo-day rituals

### 5 minutes before going live

Open these three URLs to warm up the Render dyno (which spins down after 15 min idle):

- `https://eclinic-api.onrender.com/health`
- `https://eclinic-api.onrender.com/docs`
- Your Vercel URL → login as `doctor@yopmail.com`

Now the backend is hot and won't have a cold start during the demo.

### Optional: keep warm with a cron ping

Free service `https://cron-job.org` — schedule a `GET https://eclinic-api.onrender.com/health` every 14 minutes. Never cold-starts again.

---

## Promoting to production (after demo)

| Change | Cost | Why |
|---|---|---|
| Vercel Pro plan | $20/mo | Required for commercial use per ToS |
| Render Starter plan for web service | $7/mo | No cold starts |
| Render Postgres paid plan | $7/mo | Free tier expires after 90 days |
| Custom domain on Vercel | free | DNS provider charges may apply |
| Custom domain on Render | free | Set in service settings |

**Total: ~$35/mo for both running 24/7 with no cold starts.**

The YAML and JSON config files don't change — just upgrade the plans in each provider's dashboard. Auto-deploys keep working.

---

## What's NOT covered here

The repo also has `backend/chat-service` and `backend/webinar` as separate Python services. They're **not** in `render.yaml` on purpose — the main fastapi-backend is enough for 95% of the demo flow. If your demo touches:

- **Realtime chat (WebSocket)** → deploy `backend/chat-service` as another Render Web Service following the same pattern. Add a `chat-service/render.yaml` or extend the root one.
- **Webinar / video room features** → same for `backend/webinar`. Note Agora handles the actual A/V — the webinar service just signs tokens and tracks rooms.

For demo on Loop 1-4 of `DEMO_SCRIPT.md`, **you don't need the other two services running** — only chat history and live webinar features need them.
