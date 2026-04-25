"""
Comprehensive test cases for Doctor Service Availability endpoints
Tests assigning services to availability blocks
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4, UUID
from datetime import time

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.clinic import Clinic
from app.models.service import Service
from app.models.availability import Availability
from app.core.security import get_password_hash, ConsultationMode, UserRole
from app.core.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_doctor_service_availability.db"
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


@pytest.fixture
def test_service(test_clinic):
    """Create a test service"""
    db = TestingSessionLocal()
    service = Service(
        id=uuid4(),
        clinic_id=test_clinic,
        name="Test Service",
        nickname="TS",
        service_mode=ConsultationMode.IN_CLINIC.value,
        appointment_type="REGULAR",
        is_bookable=True,
        advance_booking_days=30,
        minimum_notice_minutes=60,
        payment_type="PREPAID",
        price=100.00
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    service_id = service.id
    db.close()
    return service_id


@pytest.fixture
def test_availability(doctor_user, test_clinic):
    """Create a test availability"""
    db = TestingSessionLocal()
    availability = Availability(
        id=uuid4(),
        doctor_id=doctor_user,
        clinic_id=test_clinic,
        day_of_week="monday",
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_active=True
    )
    db.add(availability)
    db.commit()
    db.refresh(availability)
    availability_id = availability.id
    db.close()
    return availability_id


class TestListAvailabilityServices:
    """Test listing service availability assignments"""
    
    def test_list_availability_services_success(self, doctor_token):
        """Test successful listing of availability services"""
        response = client.get(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_list_availability_services_with_filter(self, doctor_token, test_availability):
        """Test listing with availability ID filter"""
        response = client.get(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            params={"availability_id": str(test_availability)}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_availability_services_unauthorized(self):
        """Test listing without authentication"""
        response = client.get("/api/v1/doctor/availability-services")
        
        assert response.status_code == 401


class TestAssignServiceToAvailability:
    """Test assigning service to availability"""
    
    def test_assign_service_success(self, doctor_token, test_availability, test_service):
        """Test successful service assignment"""
        response = client.post(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "availability_id": str(test_availability),
                "service_id": str(test_service),
                "slot_duration_minutes": 30,
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["availability_id"] == str(test_availability)
        assert data["data"]["service_id"] == str(test_service)
    
    def test_assign_service_teleconsultation(self, doctor_token, test_availability, test_service):
        """Test assigning service with teleconsultation mode"""
        response = client.post(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "availability_id": str(test_availability),
                "service_id": str(test_service),
                "slot_duration_minutes": 30,
                "consultation_mode": ConsultationMode.TELECONSULTATION.value
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["consultation_mode"] == ConsultationMode.TELECONSULTATION.value
    
    def test_assign_service_duplicate(self, doctor_token, test_availability, test_service):
        """Test assigning duplicate service to same availability"""
        # Assign first time
        client.post(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "availability_id": str(test_availability),
                "service_id": str(test_service),
                "slot_duration_minutes": 30,
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        # Try to assign again
        response = client.post(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "availability_id": str(test_availability),
                "service_id": str(test_service),
                "slot_duration_minutes": 30,
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        assert response.status_code in [409, 400]
    
    def test_assign_service_invalid_availability(self, doctor_token, test_service):
        """Test assigning with invalid availability ID"""
        response = client.post(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "availability_id": str(uuid4()),
                "service_id": str(test_service),
                "slot_duration_minutes": 30,
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        assert response.status_code in [404, 400]
    
    def test_assign_service_invalid_service(self, doctor_token, test_availability):
        """Test assigning with invalid service ID"""
        response = client.post(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "availability_id": str(test_availability),
                "service_id": str(uuid4()),
                "slot_duration_minutes": 30,
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        assert response.status_code in [404, 400]
    
    def test_assign_service_unauthorized(self, test_availability, test_service):
        """Test assigning without authentication"""
        response = client.post(
            "/api/v1/doctor/availability-services",
            json={
                "availability_id": str(test_availability),
                "service_id": str(test_service),
                "slot_duration_minutes": 30,
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        assert response.status_code == 401
    
    def test_assign_service_missing_fields(self, doctor_token):
        """Test assigning with missing required fields"""
        response = client.post(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={}
        )
        
        assert response.status_code == 422


class TestUpdateAvailabilityService:
    """Test updating service availability assignment"""
    
    def test_update_availability_service_success(self, doctor_token, test_availability, test_service):
        """Test successful update"""
        # Create assignment first
        create_response = client.post(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "availability_id": str(test_availability),
                "service_id": str(test_service),
                "slot_duration_minutes": 30,
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        if create_response.status_code == 201:
            assignment_id = create_response.json()["data"]["id"]
            
            # Update the assignment
            response = client.patch(
                f"/api/v1/doctor/availability-services/{assignment_id}",
                headers={"Authorization": f"Bearer {doctor_token}"},
                json={
                    "slot_duration_minutes": 45
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["slot_duration_minutes"] == 45
    
    def test_update_availability_service_not_found(self, doctor_token):
        """Test updating non-existent assignment"""
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/doctor/availability-services/{fake_id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"slot_duration_minutes": 45}
        )
        
        assert response.status_code == 404


class TestDeleteAvailabilityService:
    """Test deleting service availability assignment"""
    
    def test_delete_availability_service_success(self, doctor_token, test_availability, test_service):
        """Test successful deletion"""
        # Create assignment first
        create_response = client.post(
            "/api/v1/doctor/availability-services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "availability_id": str(test_availability),
                "service_id": str(test_service),
                "slot_duration_minutes": 30,
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        if create_response.status_code == 201:
            assignment_id = create_response.json()["data"]["id"]
            
            # Delete the assignment
            response = client.delete(
                f"/api/v1/doctor/availability-services/{assignment_id}",
                headers={"Authorization": f"Bearer {doctor_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_delete_availability_service_not_found(self, doctor_token):
        """Test deleting non-existent assignment"""
        fake_id = uuid4()
        response = client.delete(
            f"/api/v1/doctor/availability-services/{fake_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 404
