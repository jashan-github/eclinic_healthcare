"""
Comprehensive test cases for Doctor Services endpoints
Tests doctor service selection and management
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
from app.models.service import Service
from app.core.security import get_password_hash, ConsultationMode, UserRole
from app.core.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_doctor_services.db"
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


class TestGetAvailableServices:
    """Test getting available services for doctor"""
    
    def test_get_available_services_success(self, doctor_token):
        """Test successful retrieval of available services"""
        response = client.get(
            "/api/v1/doctor/services/available",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_available_services_unauthorized(self):
        """Test getting services without authentication"""
        response = client.get("/api/v1/doctor/services/available")
        
        assert response.status_code == 401
    
    def test_get_available_services_as_patient(self, test_clinic):
        """Test getting services as patient (should fail)"""
        # Create patient user
        db = TestingSessionLocal()
        patient = User(
            id=uuid4(),
            email="patient@test.com",
            password=get_password_hash("password123"),
            name="Patient User",
            role=UserRole.PATIENT.value,
            clinic_id=test_clinic,
            is_active=True
        )
        db.add(patient)
        db.commit()
        db.close()
        
        # Login as patient
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "patient@test.com",
                "password": "password123"
            }
        )
        token = login_response.json()["data"]["access_token"]
        
        # Try to get available services
        response = client.get(
            "/api/v1/doctor/services/available",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [403, 400]


class TestListDoctorServices:
    """Test listing doctor's selected services"""
    
    def test_list_doctor_services_success(self, doctor_token):
        """Test successful listing of doctor services"""
        response = client.get(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_list_doctor_services_unauthorized(self):
        """Test listing services without authentication"""
        response = client.get("/api/v1/doctor/services")
        
        assert response.status_code == 401


class TestGetDoctorService:
    """Test getting a specific doctor service"""
    
    def test_get_doctor_service_success(self, doctor_token, test_service):
        """Test getting a specific doctor service"""
        # First create a doctor service
        create_response = client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "is_active": True
            }
        )
        
        if create_response.status_code == 201:
            service_id = create_response.json()["data"]["id"]
            
            # Get the service
            response = client.get(
                f"/api/v1/doctor/services/{service_id}",
                headers={"Authorization": f"Bearer {doctor_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_get_doctor_service_not_found(self, doctor_token):
        """Test getting non-existent doctor service"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/doctor/services/{fake_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 404


class TestCreateDoctorService:
    """Test creating doctor service assignment"""
    
    def test_create_doctor_service_success(self, doctor_token, test_service):
        """Test successful doctor service creation"""
        response = client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "is_active": True
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["service_id"] == str(test_service)
    
    def test_create_doctor_service_duplicate(self, doctor_token, test_service):
        """Test creating duplicate doctor service"""
        # Create first time
        client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "is_active": True
            }
        )
        
        # Try to create again
        response = client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "is_active": True
            }
        )
        
        assert response.status_code in [409, 400]
    
    def test_create_doctor_service_invalid_service(self, doctor_token):
        """Test creating service with invalid service ID"""
        response = client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(uuid4()),
                "is_active": True
            }
        )
        
        assert response.status_code in [404, 400]
    
    def test_create_doctor_service_unauthorized(self, test_service):
        """Test creating service without authentication"""
        response = client.post(
            "/api/v1/doctor/services",
            json={
                "service_id": str(test_service),
                "is_active": True
            }
        )
        
        assert response.status_code == 401
    
    def test_create_doctor_service_missing_fields(self, doctor_token):
        """Test creating service with missing required fields"""
        response = client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={}
        )
        
        assert response.status_code == 422


class TestUpdateDoctorService:
    """Test updating doctor service"""
    
    def test_update_doctor_service_success(self, doctor_token, test_service):
        """Test successful doctor service update"""
        # Create a service first
        create_response = client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "is_active": True
            }
        )
        
        if create_response.status_code == 201:
            service_id = create_response.json()["data"]["id"]
            
            # Update the service
            response = client.patch(
                f"/api/v1/doctor/services/{service_id}",
                headers={"Authorization": f"Bearer {doctor_token}"},
                json={
                    "is_active": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["is_active"] is False
    
    def test_update_doctor_service_not_found(self, doctor_token):
        """Test updating non-existent doctor service"""
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/doctor/services/{fake_id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"is_active": False}
        )
        
        assert response.status_code == 404
    
    def test_update_doctor_service_unauthorized(self, doctor_token, test_service):
        """Test updating service without authentication"""
        # Create a service first
        create_response = client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "is_active": True
            }
        )
        
        if create_response.status_code == 201:
            service_id = create_response.json()["data"]["id"]
            
            # Try to update without auth
            response = client.patch(
                f"/api/v1/doctor/services/{service_id}",
                json={"is_active": False}
            )
            
            assert response.status_code == 401


class TestDeleteDoctorService:
    """Test deleting doctor service"""
    
    def test_delete_doctor_service_success(self, doctor_token, test_service):
        """Test successful doctor service deletion"""
        # Create a service first
        create_response = client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "is_active": True
            }
        )
        
        if create_response.status_code == 201:
            service_id = create_response.json()["data"]["id"]
            
            # Delete the service
            response = client.delete(
                f"/api/v1/doctor/services/{service_id}",
                headers={"Authorization": f"Bearer {doctor_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_delete_doctor_service_not_found(self, doctor_token):
        """Test deleting non-existent doctor service"""
        fake_id = uuid4()
        response = client.delete(
            f"/api/v1/doctor/services/{fake_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 404
    
    def test_delete_doctor_service_unauthorized(self, doctor_token, test_service):
        """Test deleting service without authentication"""
        # Create a service first
        create_response = client.post(
            "/api/v1/doctor/services",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "is_active": True
            }
        )
        
        if create_response.status_code == 201:
            service_id = create_response.json()["data"]["id"]
            
            # Try to delete without auth
            response = client.delete(f"/api/v1/doctor/services/{service_id}")
            
            assert response.status_code == 401
