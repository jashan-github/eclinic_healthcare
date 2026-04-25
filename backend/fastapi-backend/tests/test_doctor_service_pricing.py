"""
Comprehensive test cases for Doctor Service Pricing endpoints
Tests doctor service pricing management
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
from app.core.security import get_password_hash, UserRole
from app.core.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_doctor_service_pricing.db"
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
        service_mode="IN_CLINIC",
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


class TestListDoctorServicePricing:
    """Test listing doctor service pricing"""
    
    def test_list_pricing_success(self, doctor_token):
        """Test successful listing of pricing"""
        response = client.get(
            "/api/v1/doctor/service-pricing",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_list_pricing_unauthorized(self):
        """Test listing without authentication"""
        response = client.get("/api/v1/doctor/service-pricing")
        
        assert response.status_code == 401


class TestSetDoctorServicePrice:
    """Test setting doctor service price"""
    
    def test_set_price_success(self, doctor_token, test_service):
        """Test successful price setting"""
        response = client.post(
            "/api/v1/doctor/service-pricing",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "price": 150.00,
                "currency": "USD"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_set_price_invalid_service(self, doctor_token):
        """Test setting price for invalid service"""
        response = client.post(
            "/api/v1/doctor/service-pricing",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(uuid4()),
                "price": 150.00,
                "currency": "USD"
            }
        )
        
        assert response.status_code in [404, 400]
    
    def test_set_price_unauthorized(self, test_service):
        """Test setting price without authentication"""
        response = client.post(
            "/api/v1/doctor/service-pricing",
            json={
                "service_id": str(test_service),
                "price": 150.00,
                "currency": "USD"
            }
        )
        
        assert response.status_code == 401
    
    def test_set_price_missing_fields(self, doctor_token):
        """Test setting price with missing fields"""
        response = client.post(
            "/api/v1/doctor/service-pricing",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={}
        )
        
        assert response.status_code == 422


class TestUpdateDoctorServicePrice:
    """Test updating doctor service price"""
    
    def test_update_price_success(self, doctor_token, test_service):
        """Test successful price update"""
        # Set price first
        create_response = client.post(
            "/api/v1/doctor/service-pricing",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "price": 150.00,
                "currency": "USD"
            }
        )
        
        if create_response.status_code == 201:
            pricing_id = create_response.json()["data"]["id"]
            
            # Update price
            response = client.patch(
                f"/api/v1/doctor/service-pricing/{pricing_id}",
                headers={"Authorization": f"Bearer {doctor_token}"},
                json={
                    "price": 200.00
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_update_price_not_found(self, doctor_token):
        """Test updating non-existent pricing"""
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/doctor/service-pricing/{fake_id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"price": 200.00}
        )
        
        assert response.status_code == 404


class TestDeleteDoctorServicePrice:
    """Test deleting doctor service price"""
    
    def test_delete_price_success(self, doctor_token, test_service):
        """Test successful price deletion"""
        # Set price first
        create_response = client.post(
            "/api/v1/doctor/service-pricing",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "service_id": str(test_service),
                "price": 150.00,
                "currency": "USD"
            }
        )
        
        if create_response.status_code == 201:
            pricing_id = create_response.json()["data"]["id"]
            
            # Delete price
            response = client.delete(
                f"/api/v1/doctor/service-pricing/{pricing_id}",
                headers={"Authorization": f"Bearer {doctor_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_delete_price_not_found(self, doctor_token):
        """Test deleting non-existent pricing"""
        fake_id = uuid4()
        response = client.delete(
            f"/api/v1/doctor/service-pricing/{fake_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 404
