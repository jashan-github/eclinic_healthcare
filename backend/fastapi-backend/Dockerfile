# eClinic Backend - Production Dockerfile

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

# Create logs and uploads directories
RUN mkdir -p logs uploads/avatars && chown -R appuser:appuser logs uploads

# Make entrypoint and migration scripts executable
RUN chmod +x scripts/entrypoint.sh scripts/migrate.py scripts/seed_data.py

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check - faster startup
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=2 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Set entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Run application - single worker for fastest startup (scale workers in production)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
