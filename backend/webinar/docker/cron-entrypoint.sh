#!/bin/sh
# Inject container env into crontab so the Python script can connect to DB.
# Cron jobs do not inherit the full container environment by default.
set -e
ENV_FILE="/app/docker/cron-env.sh"
printenv | grep -E '^[A-Za-z_][A-Za-z0-9_]*=' | sed 's/^/export /' > "$ENV_FILE" || true
echo "*/5 * * * * . $ENV_FILE 2>/dev/null; cd /app && /usr/local/bin/python -m app.scripts.mark_expired_webinars" | crontab -
exec cron -f
