# eClinic Backend - Makefile

.PHONY: help install dev run test lint format clean migrate

help:
	@echo "eClinic Backend - Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run development server"
	@echo "  make run        - Run production server"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"
	@echo "  make clean      - Clean cache files"
	@echo "  make migrate    - Run database migrations"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

test:
	pytest tests/ -v --cov=app --cov-report=html

lint:
	flake8 app/
	mypy app/

format:
	black app/ tests/
	isort app/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

migrate-rollback:
	alembic downgrade -1

db-reset:
	alembic downgrade base
	alembic upgrade head

# Docker migration commands
migrate-docker:
	docker-compose exec backend alembic upgrade head

migrate-create-docker:
	@read -p "Enter migration message: " message; \
	docker-compose exec backend alembic revision --autogenerate -m "$$message"

migrate-rollback-docker:
	docker-compose exec backend alembic downgrade -1

db-reset-docker:
	docker-compose exec backend alembic downgrade base
	docker-compose exec backend alembic upgrade head

migrate-status-docker:
	docker-compose exec backend alembic current
	docker-compose exec backend alembic history
