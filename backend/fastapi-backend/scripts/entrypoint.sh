#!/bin/bash
# Docker entrypoint script - Fast startup (migrations disabled by default)

# Change to app directory
cd /app

# Create uploads directory if it doesn't exist (for file uploads)
mkdir -p /app/uploads/avatars 2>/dev/null || true

# Check if migrations should be run (disabled by default)
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running database migrations..."
    python3 /app/scripts/migrate.py 2>&1 || echo "⚠ Migration failed (continuing startup)"
fi

# Start the application
exec "$@"

