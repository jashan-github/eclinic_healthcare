"""
Comprehensive test cases for Availability endpoints
Tests doctor availability and time-off management
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4, UUID
from datetime import date, time, timedelta

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.clinic import Clinic
from app.core.security import get_password_hash, UserRole
from app.core.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_availability.db"
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


@pytest.fixture
def doctor_user(test_clinic):
    """Create a doctor user"""
    db = TestingSessionLocal()
    user = User(
        id=uuid4(),
        email="doctor@test.com",
        password=get_password_hash("password123"),
        name="Doctor User",
        role=UserRole.DOCTOR.value,
        clinic_id=test_clinic,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    db.close()
    return user_id


@pytest.fixture
def doctor_token(doctor_user):
    """Get doctor authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "doctor@test.com",
            "password": "password123"
        }
    )
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    return None


class TestGetDoctorAvailability:
    """Test getting doctor availability"""
    
    def test_get_availability_success(self, doctor_token, doctor_user):
        """Test successful retrieval of availability"""
        response = client.get(
            f"/api/v1/doctors/{doctor_user}/availability",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_get_availability_unauthorized(self, doctor_user):
        """Test getting availability without authentication"""
        response = client.get(f"/api/v1/doctors/{doctor_user}/availability")
        
        assert response.status_code == 401
    
    def test_get_availability_not_found(self, doctor_token):
        """Test getting availability for non-existent doctor"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/doctors/{fake_id}/availability",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 404


class TestCreateAvailability:
    """Test creating availability"""
    
    def test_create_availability_success(self, doctor_token, doctor_user, test_clinic):
        """Test successful availability creation"""
        response = client.post(
            "/api/v1/availability",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "doctor_id": str(doctor_user),
                "clinic_id": str(test_clinic),
                "day_of_week": "monday",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "is_active": True
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_create_availability_unauthorized(self, doctor_user, test_clinic):
        """Test creating availability without authentication"""
        response = client.post(
            "/api/v1/availability",
            json={
                "doctor_id": str(doctor_user),
                "clinic_id": str(test_clinic),
                "day_of_week": "monday",
                "start_time": "09:00:00",
                "end_time": "17:00:00"
            }
        )
        
        assert response.status_code == 401
    
    def test_create_availability_missing_fields(self, doctor_token):
        """Test creating availability with missing fields"""
        response = client.post(
            "/api/v1/availability",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={}
        )
        
        assert response.status_code == 422
    
    def test_create_availability_invalid_time_range(self, doctor_token, doctor_user, test_clinic):
        """Test creating availability with invalid time range"""
        response = client.post(
            "/api/v1/availability",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "doctor_id": str(doctor_user),
                "clinic_id": str(test_clinic),
                "day_of_week": "monday",
                "start_time": "17:00:00",
                "end_time": "09:00:00"  # End before start
            }
        )
        
        assert response.status_code in [400, 422]


class TestUpdateAvailability:
    """Test updating availability"""
    
    def test_update_availability_success(self, doctor_token, doctor_user, test_clinic):
        """Test successful availability update"""
        # Create availability first
        create_response = client.post(
            "/api/v1/availability",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "doctor_id": str(doctor_user),
                "clinic_id": str(test_clinic),
                "day_of_week": "monday",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "is_active": True
            }
        )
        
        if create_response.status_code == 201:
            availability_id = create_response.json()["data"]["id"]
            
            # Update availability
            response = client.put(
                f"/api/v1/availability/{availability_id}",
                headers={"Authorization": f"Bearer {doctor_token}"},
                json={
                    "day_of_week": "tuesday",
                    "start_time": "10:00:00",
                    "end_time": "18:00:00",
                    "is_active": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_update_availability_not_found(self, doctor_token):
        """Test updating non-existent availability"""
        fake_id = uuid4()
        response = client.put(
            f"/api/v1/availability/{fake_id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "day_of_week": "tuesday",
                "start_time": "10:00:00",
                "end_time": "18:00:00"
            }
        )
        
        assert response.status_code == 404


class TestDeleteAvailability:
    """Test deleting availability"""
    
    def test_delete_availability_success(self, doctor_token, doctor_user, test_clinic):
        """Test successful availability deletion"""
        # Create availability first
        create_response = client.post(
            "/api/v1/availability",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "doctor_id": str(doctor_user),
                "clinic_id": str(test_clinic),
                "day_of_week": "monday",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "is_active": True
            }
        )
        
        if create_response.status_code == 201:
            availability_id = create_response.json()["data"]["id"]
            
            # Delete availability
            response = client.delete(
                f"/api/v1/availability/{availability_id}",
                headers={"Authorization": f"Bearer {doctor_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_delete_availability_not_found(self, doctor_token):
        """Test deleting non-existent availability"""
        fake_id = uuid4()
        response = client.delete(
            f"/api/v1/availability/{fake_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 404


class TestTimeOffManagement:
    """Test time-off management"""
    
    def test_get_time_off_success(self, doctor_token, doctor_user):
        """Test successful retrieval of time-off"""
        response = client.get(
            f"/api/v1/doctors/{doctor_user}/time-off",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_create_time_off_success(self, doctor_token, doctor_user, test_clinic):
        """Test successful time-off creation"""
        tomorrow = date.today() + timedelta(days=1)
        next_week = tomorrow + timedelta(days=7)
        
        response = client.post(
            "/api/v1/time-off",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "doctor_id": str(doctor_user),
                "clinic_id": str(test_clinic),
                "start_date": tomorrow.isoformat(),
                "end_date": next_week.isoformat(),
                "reason": "Vacation"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
    
    def test_create_time_off_past_date(self, doctor_token, doctor_user, test_clinic):
        """Test creating time-off with past date"""
        yesterday = date.today() - timedelta(days=1)
        
        response = client.post(
            "/api/v1/time-off",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "doctor_id": str(doctor_user),
                "clinic_id": str(test_clinic),
                "start_date": yesterday.isoformat(),
                "end_date": date.today().isoformat(),
                "reason": "Past vacation"
            }
        )
        
        assert response.status_code in [400, 422]
    
    def test_delete_time_off_success(self, doctor_token, doctor_user, test_clinic):
        """Test successful time-off deletion"""
        # Create time-off first
        tomorrow = date.today() + timedelta(days=1)
        next_week = tomorrow + timedelta(days=7)
        
        create_response = client.post(
            "/api/v1/time-off",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "doctor_id": str(doctor_user),
                "clinic_id": str(test_clinic),
                "start_date": tomorrow.isoformat(),
                "end_date": next_week.isoformat(),
                "reason": "Vacation"
            }
        )
        
        if create_response.status_code == 201:
            time_off_id = create_response.json()["data"]["id"]
            
            # Delete time-off
            response = client.delete(
                f"/api/v1/time-off/{time_off_id}",
                headers={"Authorization": f"Bearer {doctor_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
