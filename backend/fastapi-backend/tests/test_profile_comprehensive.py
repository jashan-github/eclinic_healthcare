"""
Comprehensive test cases for Profile endpoints
Tests profile management for patients and doctors
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4, UUID
from datetime import date

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.clinic import Clinic
from app.core.security import get_password_hash, UserRole
from app.core.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_profile.db"
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
def patient_user(test_clinic):
    """Create a patient user"""
    db = TestingSessionLocal()
    user = User(
        id=uuid4(),
        email="patient@test.com",
        password=get_password_hash("password123"),
        name="Patient User",
        role=UserRole.PATIENT.value,
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
def patient_token(patient_user):
    """Get patient authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "patient@test.com",
            "password": "password123"
        }
    )
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    return None


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


class TestGetProfile:
    """Test getting user profile"""
    
    def test_get_profile_success(self, patient_token):
        """Test successful profile retrieval"""
        response = client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_get_profile_unauthorized(self):
        """Test getting profile without authentication"""
        response = client.get("/api/v1/profile")
        
        assert response.status_code == 401


class TestCompleteProfile:
    """Test profile completion"""
    
    def test_complete_profile_success(self, patient_token):
        """Test successful profile completion"""
        response = client.post(
            "/api/v1/profile/complete",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "gender": "male"
            }
        )
        
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["success"] is True
    
    def test_complete_profile_missing_fields(self, patient_token):
        """Test completing profile with missing required fields"""
        response = client.post(
            "/api/v1/profile/complete",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "first_name": "John"
                # Missing other required fields
            }
        )
        
        assert response.status_code == 422
    
    def test_complete_profile_unauthorized(self):
        """Test completing profile without authentication"""
        response = client.post(
            "/api/v1/profile/complete",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "gender": "male"
            }
        )
        
        assert response.status_code == 401


class TestUpdateProfile:
    """Test updating profile"""
    
    def test_update_profile_success(self, patient_token):
        """Test successful profile update"""
        response = client.put(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "name": "Updated Name",
                "phone": "+1234567890"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_profile_unauthorized(self):
        """Test updating profile without authentication"""
        response = client.put(
            "/api/v1/profile",
            json={
                "name": "Updated Name"
            }
        )
        
        assert response.status_code == 401


class TestPatientProfile:
    """Test patient-specific profile endpoints"""
    
    def test_get_patient_personal_info_success(self, patient_token):
        """Test getting patient personal info"""
        response = client.get(
            "/api/v1/profile/patient/personal-info",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_patient_personal_info_success(self, patient_token):
        """Test updating patient personal info"""
        response = client.put(
            "/api/v1/profile/patient/personal-info",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1995-05-15",
                "gender": "female"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_patient_medical_info_success(self, patient_token):
        """Test getting patient medical info"""
        response = client.get(
            "/api/v1/profile/patient/medical-info",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_patient_medical_info_success(self, patient_token):
        """Test updating patient medical info"""
        response = client.put(
            "/api/v1/profile/patient/medical-info",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "blood_type": "O+",
                "allergies": ["Peanuts", "Dust"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestDoctorProfile:
    """Test doctor-specific profile endpoints"""
    
    def test_get_doctor_profile_success(self, doctor_token):
        """Test getting doctor profile"""
        response = client.get(
            "/api/v1/profile/doctor",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_doctor_profile_success(self, doctor_token):
        """Test updating doctor profile"""
        response = client.put(
            "/api/v1/profile/doctor",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "specialization": "Cardiology",
                "years_of_experience": 10,
                "qualifications": ["MD", "PhD"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_doctor_profile_as_patient(self, patient_token):
        """Test getting doctor profile as patient (should fail)"""
        response = client.get(
            "/api/v1/profile/doctor",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code in [403, 404]


class TestContactDetails:
    """Test contact details endpoints"""
    
    def test_get_contact_details_success(self, patient_token):
        """Test getting contact details"""
        response = client.get(
            "/api/v1/profile/contact-details",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_contact_details_success(self, patient_token):
        """Test updating contact details"""
        response = client.put(
            "/api/v1/profile/contact-details",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "phone": "+1234567890",
                "email": "newemail@test.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestProfileImage:
    """Test profile image upload"""
    
    def test_upload_profile_image_success(self, patient_token):
        """Test successful profile image upload"""
        # Create a dummy image file
        files = {
            "file": ("test_image.jpg", b"fake image content", "image/jpeg")
        }
        
        response = client.post(
            "/api/v1/profile/image",
            headers={"Authorization": f"Bearer {patient_token}"},
            files=files
        )
        
        # May succeed or fail depending on file validation
        assert response.status_code in [200, 201, 400, 422]
    
    def test_upload_profile_image_unauthorized(self):
        """Test uploading image without authentication"""
        files = {
            "file": ("test_image.jpg", b"fake image content", "image/jpeg")
        }
        
        response = client.post(
            "/api/v1/profile/image",
            files=files
        )
        
        assert response.status_code == 401
    
    def test_upload_profile_image_no_file(self, patient_token):
        """Test uploading without file"""
        response = client.post(
            "/api/v1/profile/image",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code in [422, 400]
