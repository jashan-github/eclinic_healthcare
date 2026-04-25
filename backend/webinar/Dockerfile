FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (cron for mark-expired-webinars job)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Entrypoints
RUN chmod +x /app/docker/cron-entrypoint.sh /app/docker/entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8002

# Wait for Postgres then run app (webinar-service only; webinar-cron uses cron-entrypoint.sh)
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
