"""
Comprehensive test cases for Admin Services endpoints
Tests all CRUD operations and edge cases
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4, UUID
from datetime import datetime

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.clinic import Clinic
from app.models.service import Service
from app.core.security import get_password_hash, ConsultationMode
from app.core.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_services.db"
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
def admin_user(test_clinic):
    """Create an admin user"""
    db = TestingSessionLocal()
    user = User(
        id=uuid4(),
        email="admin@test.com",
        password=get_password_hash("password123"),
        name="Admin User",
        role="admin",
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
def admin_token(admin_user):
    """Get admin authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.com",
            "password": "password123"
        }
    )
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    return None


@pytest.fixture
def test_service(test_clinic, admin_user, admin_token):
    """Create a test service"""
    response = client.post(
        "/api/v1/admin/services",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "clinic_id": str(test_clinic),
            "name": "Test Service",
            "nickname": "TS",
            "service_mode": ConsultationMode.IN_CLINIC.value,
            "appointment_type": "REGULAR",
            "is_bookable": True,
            "advance_booking_days": 30,
            "minimum_notice_minutes": 60,
            "payment_type": "PREPAID",
            "price": 100.00
        }
    )
    if response.status_code == 201:
        return response.json()["data"]["id"]
    return None


class TestCreateService:
    """Test service creation"""
    
    def test_create_service_success(self, test_clinic, admin_token):
        """Test successful service creation"""
        response = client.post(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "clinic_id": str(test_clinic),
                "name": "New Service",
                "nickname": "NS",
                "service_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_type": "REGULAR",
                "is_bookable": True,
                "advance_booking_days": 30,
                "minimum_notice_minutes": 60,
                "payment_type": "PREPAID",
                "price": 150.00
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Service created successfully"
        assert "data" in data
        assert data["data"]["name"] == "New Service"
        assert data["data"]["service_mode"] == ConsultationMode.IN_CLINIC.value
    
    def test_create_service_teleconsultation(self, test_clinic, admin_token):
        """Test creating teleconsultation service"""
        response = client.post(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "clinic_id": str(test_clinic),
                "name": "Teleconsultation Service",
                "nickname": "TC",
                "service_mode": ConsultationMode.TELECONSULTATION.value,
                "appointment_type": "REGULAR",
                "is_bookable": True,
                "advance_booking_days": 7,
                "minimum_notice_minutes": 30,
                "payment_type": "PREPAID",
                "price": 80.00
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["service_mode"] == ConsultationMode.TELECONSULTATION.value
    
    def test_create_service_unauthorized(self, test_clinic):
        """Test creating service without authentication"""
        response = client.post(
            "/api/v1/admin/services",
            json={
                "clinic_id": str(test_clinic),
                "name": "New Service",
                "nickname": "NS",
                "service_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_type": "REGULAR",
                "is_bookable": True,
                "advance_booking_days": 30,
                "minimum_notice_minutes": 60,
                "payment_type": "PREPAID",
                "price": 150.00
            }
        )
        
        assert response.status_code == 401
    
    def test_create_service_invalid_clinic(self, admin_token):
        """Test creating service with invalid clinic ID"""
        response = client.post(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "clinic_id": str(uuid4()),
                "name": "New Service",
                "nickname": "NS",
                "service_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_type": "REGULAR",
                "is_bookable": True,
                "advance_booking_days": 30,
                "minimum_notice_minutes": 60,
                "payment_type": "PREPAID",
                "price": 150.00
            }
        )
        
        assert response.status_code in [404, 403]
    
    def test_create_service_missing_required_fields(self, test_clinic, admin_token):
        """Test creating service with missing required fields"""
        response = client.post(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "clinic_id": str(test_clinic),
                "name": "New Service"
                # Missing other required fields
            }
        )
        
        assert response.status_code == 422
    
    def test_create_service_invalid_service_mode(self, test_clinic, admin_token):
        """Test creating service with invalid service mode"""
        response = client.post(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "clinic_id": str(test_clinic),
                "name": "New Service",
                "nickname": "NS",
                "service_mode": "INVALID_MODE",
                "appointment_type": "REGULAR",
                "is_bookable": True,
                "advance_booking_days": 30,
                "minimum_notice_minutes": 60,
                "payment_type": "PREPAID",
                "price": 150.00
            }
        )
        
        assert response.status_code == 422


class TestGetServices:
    """Test getting services"""
    
    def test_get_services_success(self, admin_token, test_service):
        """Test successful retrieval of services"""
        response = client.get(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_services_with_filters(self, admin_token, test_service):
        """Test getting services with filters"""
        response = client.get(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "service_mode": ConsultationMode.IN_CLINIC.value,
                "is_bookable": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_services_unauthorized(self):
        """Test getting services without authentication"""
        response = client.get("/api/v1/admin/services")
        
        assert response.status_code == 401
    
    def test_get_service_by_id_success(self, admin_token, test_service):
        """Test getting a specific service by ID"""
        response = client.get(
            f"/api/v1/admin/services/{test_service}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_service
    
    def test_get_service_by_id_not_found(self, admin_token):
        """Test getting non-existent service"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/admin/services/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404


class TestUpdateService:
    """Test service updates"""
    
    def test_update_service_success(self, admin_token, test_service):
        """Test successful service update"""
        response = client.patch(
            f"/api/v1/admin/services/{test_service}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Updated Service Name",
                "price": 200.00
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Service Name"
        assert float(data["data"]["price"]) == 200.00
    
    def test_update_service_all_fields(self, admin_token, test_service):
        """Test updating all service fields"""
        response = client.patch(
            f"/api/v1/admin/services/{test_service}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Fully Updated Service",
                "nickname": "FUS",
                "service_mode": ConsultationMode.TELECONSULTATION.value,
                "appointment_type": "FOLLOW_UP",
                "is_bookable": False,
                "advance_booking_days": 14,
                "minimum_notice_minutes": 120,
                "payment_type": "POSTPAID",
                "price": 250.00
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_bookable"] is False
    
    def test_update_service_not_found(self, admin_token):
        """Test updating non-existent service"""
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/admin/services/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 404
    
    def test_update_service_unauthorized(self, test_service):
        """Test updating service without authentication"""
        response = client.patch(
            f"/api/v1/admin/services/{test_service}",
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 401
    
    def test_update_service_invalid_data(self, admin_token, test_service):
        """Test updating service with invalid data"""
        response = client.patch(
            f"/api/v1/admin/services/{test_service}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "service_mode": "INVALID_MODE",
                "price": -100.00
            }
        )
        
        assert response.status_code == 422


class TestDeleteService:
    """Test service deletion"""
    
    def test_delete_service_success(self, admin_token, test_clinic):
        """Test successful service deletion"""
        # Create a service first
        create_response = client.post(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "clinic_id": str(test_clinic),
                "name": "Service to Delete",
                "nickname": "STD",
                "service_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_type": "REGULAR",
                "is_bookable": True,
                "advance_booking_days": 30,
                "minimum_notice_minutes": 60,
                "payment_type": "PREPAID",
                "price": 100.00
            }
        )
        service_id = create_response.json()["data"]["id"]
        
        # Delete the service
        response = client.delete(
            f"/api/v1/admin/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Service deleted successfully"
    
    def test_delete_service_not_found(self, admin_token):
        """Test deleting non-existent service"""
        fake_id = uuid4()
        response = client.delete(
            f"/api/v1/admin/services/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    def test_delete_service_unauthorized(self, test_service):
        """Test deleting service without authentication"""
        response = client.delete(f"/api/v1/admin/services/{test_service}")
        
        assert response.status_code == 401


class TestServiceEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_create_service_zero_price(self, test_clinic, admin_token):
        """Test creating service with zero price"""
        response = client.post(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "clinic_id": str(test_clinic),
                "name": "Free Service",
                "nickname": "FS",
                "service_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_type": "REGULAR",
                "is_bookable": True,
                "advance_booking_days": 30,
                "minimum_notice_minutes": 60,
                "payment_type": "PREPAID",
                "price": 0.00
            }
        )
        
        # Should succeed as zero price might be valid for free services
        assert response.status_code in [201, 422]
    
    def test_create_service_very_long_name(self, test_clinic, admin_token):
        """Test creating service with very long name"""
        long_name = "A" * 500
        response = client.post(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "clinic_id": str(test_clinic),
                "name": long_name,
                "nickname": "VLN",
                "service_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_type": "REGULAR",
                "is_bookable": True,
                "advance_booking_days": 30,
                "minimum_notice_minutes": 60,
                "payment_type": "PREPAID",
                "price": 100.00
            }
        )
        
        # Should either succeed or fail with validation error
        assert response.status_code in [201, 422]
    
    def test_get_services_empty_result(self, admin_token):
        """Test getting services when none exist"""
        response = client.get(
            "/api/v1/admin/services",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
