# eClinic Backend

Healthcare platform backend built with FastAPI - HIPAA-ready architecture migrated from Laravel.

## 📚 Documentation

All documentation files are located in the [`README/`](./README/) folder:

- **[Quick Start Guide](./README/QUICKSTART.md)** - Get started quickly
- **[Architecture](./README/ARCHITECTURE.md)** - System architecture and design
- **[Database Standards](./README/DATABASE_STANDARDS.md)** - Database conventions
- **[Docker Setup](./README/DOCKER_MIGRATIONS.md)** - Docker and migration guide
- **[Seed Data](./README/SEED_DATA.md)** - Local testing setup

## 🚀 Quick Start

🔧 ONE-TIME FIX ON SERVER (DO THIS FIRST)
```bash
docker network create eclinic-network
```

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed initial data
docker-compose exec backend python scripts/seed_data.py

# View logs
docker-compose logs -f backend
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

## 🔗 Quick Links

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Admin Login**: `admin@eclinic.local` / `password` (change after first login)

## 📖 Full Documentation

See the [`README/`](./README/) folder for complete documentation.

---

**Built with FastAPI | HIPAA-Compliant | Production-Ready**

