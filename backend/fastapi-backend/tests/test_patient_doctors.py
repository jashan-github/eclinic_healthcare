"""
Comprehensive test cases for Patient Doctor Search endpoints
Tests doctor search functionality
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4, UUID

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.clinic import Clinic
from app.core.security import get_password_hash, UserRole
from app.core.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_patient_doctors.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_clinic():
    """Create a test clinic"""
    db = TestingSessionLocal()
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        is_active=True
    )
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    clinic_id = clinic.id
    db.close()
    return clinic_id


class TestDoctorSearch:
    """Test doctor search functionality"""
    
    def test_search_doctors_success(self):
        """Test successful doctor search"""
        response = client.get("/api/v1/patient/doctors/search")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_search_doctors_with_specialty_filter(self):
        """Test searching doctors by specialty"""
        response = client.get(
            "/api/v1/patient/doctors/search",
            params={"specialty": "Cardiology"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_search_doctors_with_availability_day(self):
        """Test searching doctors by availability day"""
        response = client.get(
            "/api/v1/patient/doctors/search",
            params={"availability_day": "monday"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_search_doctors_with_time_filter(self):
        """Test searching doctors by time"""
        response = client.get(
            "/api/v1/patient/doctors/search",
            params={"time": "10:00"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_search_doctors_with_pagination(self):
        """Test searching doctors with pagination"""
        response = client.get(
            "/api/v1/patient/doctors/search",
            params={"page": 1, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_search_doctors_multiple_filters(self):
        """Test searching doctors with multiple filters"""
        response = client.get(
            "/api/v1/patient/doctors/search",
            params={
                "specialty": "Cardiology",
                "availability_day": "monday",
                "time": "10:00",
                "page": 1,
                "limit": 20
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_search_doctors_empty_result(self):
        """Test searching doctors with filters that return no results"""
        response = client.get(
            "/api/v1/patient/doctors/search",
            params={"specialty": "NonExistentSpecialty"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_search_doctors_invalid_page(self):
        """Test searching doctors with invalid page number"""
        response = client.get(
            "/api/v1/patient/doctors/search",
            params={"page": 0}
        )
        
        # Should either fail validation or default to page 1
        assert response.status_code in [200, 422]
    
    def test_search_doctors_invalid_limit(self):
        """Test searching doctors with invalid limit"""
        response = client.get(
            "/api/v1/patient/doctors/search",
            params={"limit": 0}
        )
        
        # Should either fail validation or use default
        assert response.status_code in [200, 422]
    
    def test_search_doctors_very_high_limit(self):
        """Test searching doctors with very high limit"""
        response = client.get(
            "/api/v1/patient/doctors/search",
            params={"limit": 1000}
        )
        
        # Should either succeed or cap at max limit
        assert response.status_code in [200, 422]
