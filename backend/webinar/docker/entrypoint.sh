#!/bin/bash
# Wait for Postgres (and optionally Redis) to be reachable before starting uvicorn.
# Prevents 502 when webinar starts before eclinic-postgres is ready.

set -e
cd /app

# Parse DATABASE_URL for host:port (e.g. postgresql+asyncpg://user:pass@eclinic-postgres:5432/eclinic_db)
DB_HOST_PORT="${DATABASE_URL#*@}"
DB_HOST_PORT="${DB_HOST_PORT%%/*}"
DB_HOST="${DB_HOST_PORT%:*}"
DB_PORT="${DB_HOST_PORT#*:}"
if [ -z "$DB_PORT" ] || [ "$DB_PORT" = "$DB_HOST" ]; then
  DB_PORT=5432
fi

# Wait for Postgres (max 60s)
echo "Waiting for Postgres at $DB_HOST:${DB_PORT}..."
for i in $(seq 1 60); do
  if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; then
      echo "Postgres is ready."
      break
    fi
  else
    if python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
  s.connect(('$DB_HOST', $DB_PORT))
  s.close()
  exit(0)
except Exception:
  exit(1)
" 2>/dev/null; then
      echo "Postgres is ready."
      break
    fi
  fi
  if [ "$i" -eq 60 ]; then
    echo "Warning: Postgres not reachable after 60s; starting anyway."
  fi
  sleep 1
done

exec "$@"
