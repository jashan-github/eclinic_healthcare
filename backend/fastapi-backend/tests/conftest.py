"""
Pytest configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def test_app():
    """FastAPI test application"""
    return app


@pytest.fixture(scope="session")
def client(test_app):
    """Test client for API requests"""
    return TestClient(test_app)


# TODO: Add database fixtures
# @pytest.fixture(scope="session")
# def test_db():
#     """Test database fixture"""
#     engine = create_engine("postgresql://test_user:test_pass@localhost/test_db")
#     TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#     
#     # Create tables
#     Base.metadata.create_all(bind=engine)
#     
#     yield TestingSessionLocal
#     
#     # Drop tables
#     Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers():
    """
    Authentication headers for testing
    TODO: Generate actual JWT tokens
    """
    return {
        "Authorization": "Bearer test-token"
    }
