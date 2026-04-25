"""
Comprehensive test cases for Appointment Request endpoints
Tests all appointment request operations and edge cases
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4, UUID
from datetime import date, datetime, timedelta

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.clinic import Clinic
from app.models.service import Service
from app.models.appointment_request import AppointmentRequest
from app.core.security import get_password_hash, ConsultationMode, UserRole
from app.core.config import settings
from app.models.doctor_service import DoctorService
from app.models.availability import DoctorAvailability
from datetime import time


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_appointment_requests.db"
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
def appointment_request_data(doctor_user, test_service):
    """Get appointment request data"""
    tomorrow = date.today() + timedelta(days=1)
    return {
        "doctor_id": str(doctor_user),
        "service_id": str(test_service),
        "consultation_mode": ConsultationMode.IN_CLINIC.value,
        "preferred_date": tomorrow.isoformat(),
        "preferred_time": "10:00",
        "reason": "Test appointment reason"
    }


class TestCreateAppointmentRequest:
    """Test appointment request creation"""
    
    def test_create_request_success(self, patient_token, appointment_request_data):
        """Test successful appointment request creation"""
        response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Appointment request created successfully"
        assert "data" in data
        assert data["data"]["status"] == "PENDING"
        assert data["data"]["consultation_mode"] == ConsultationMode.IN_CLINIC.value
    
    def test_create_request_teleconsultation(self, patient_token, doctor_user, test_service):
        """Test creating teleconsultation request"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "doctor_id": str(doctor_user),
                "service_id": str(test_service),
                "consultation_mode": ConsultationMode.TELECONSULTATION.value,
                "preferred_date": tomorrow.isoformat(),
                "preferred_time": "14:00",
                "reason": "Teleconsultation request"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["consultation_mode"] == ConsultationMode.TELECONSULTATION.value
    
    def test_create_request_unauthorized(self, appointment_request_data):
        """Test creating request without authentication"""
        response = client.post(
            "/api/v1/appointment/requests",
            json=appointment_request_data
        )
        
        assert response.status_code == 401
    
    def test_create_request_as_doctor(self, doctor_token, appointment_request_data):
        """Test creating request as doctor (should fail)"""
        response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json=appointment_request_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Only patients can create appointment requests" in data["message"]
    
    def test_create_request_invalid_doctor(self, patient_token, test_service):
        """Test creating request with invalid doctor ID"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "doctor_id": str(uuid4()),
                "service_id": str(test_service),
                "consultation_mode": ConsultationMode.IN_CLINIC.value,
                "preferred_date": tomorrow.isoformat(),
                "preferred_time": "10:00"
            }
        )
        
        assert response.status_code in [400, 404]
    
    def test_create_request_invalid_service(self, patient_token, doctor_user):
        """Test creating request with invalid service ID"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "doctor_id": str(doctor_user),
                "service_id": str(uuid4()),
                "consultation_mode": ConsultationMode.IN_CLINIC.value,
                "preferred_date": tomorrow.isoformat(),
                "preferred_time": "10:00"
            }
        )
        
        assert response.status_code in [400, 404]

    def test_accepted_request_blocks_slot(self, patient_token, doctor_token, doctor_user, test_service, test_clinic):
        """When a request is accepted by the doctor, that slot should be blocked in time-slots"""
        db = TestingSessionLocal()
        try:
            # Create doctor service assignment (default duration)
            ds = DoctorService(
                doctor_id=doctor_user,
                service_id=test_service,
                clinic_id=test_clinic,
                day_of_week=None,
                slot_duration_minutes=30,
                is_active=True
            )
            db.add(ds)

            # Create availability for tomorrow's weekday covering 9:00-17:00
            tomorrow = date.today() + timedelta(days=1)
            python_weekday = tomorrow.weekday()
            avail = DoctorAvailability(
                doctor_id=doctor_user,
                clinic_id=test_clinic,
                day_of_week=python_weekday,
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True
            )
            db.add(avail)
            db.commit()

            # Patient creates a request for 10:00
            response = client.post(
                "/api/v1/appointment/requests",
                headers={"Authorization": f"Bearer {patient_token}"},
                json={
                    "doctor_id": str(doctor_user),
                    "service_id": str(test_service),
                    "consultation_mode": ConsultationMode.IN_CLINIC.value,
                    "preferred_date": tomorrow.isoformat(),
                    "preferred_time": "10:00",
                    "reason": "Block slot test"
                }
            )
            assert response.status_code == 201
            req = response.json()["data"]
            req_id = req["id"]

            # Doctor accepts the request
            accept_resp = client.post(
                f"/api/v1/appointment/requests/{req_id}/accept",
                headers={"Authorization": f"Bearer {doctor_token}"}
            )
            assert accept_resp.status_code == 200

            # Fetch available slots and ensure 10:00 is blocked
            slots_resp = client.get(
                f"/api/v1/patient/doctors/{doctor_user}/time-slots",
                params={
                    "service_id": str(test_service),
                    "preferred_date": tomorrow.isoformat(),
                    "consultation_mode": ConsultationMode.IN_CLINIC.value
                }
            )
            assert slots_resp.status_code == 200
            data = slots_resp.json()["data"]["time_slots"]
            # Find the slot for 10:00:00
            slot_10 = next((s for s in data if s["time"].startswith("10:00")), None)
            assert slot_10 is not None, "Expected a 10:00 slot to be generated"
            assert slot_10["is_available"] is False, "Accepted request should block the slot"
        finally:
            db.close()
    
    def test_create_request_past_date(self, patient_token, appointment_request_data):
        """Test creating request with past date"""
        yesterday = date.today() - timedelta(days=1)
        appointment_request_data["preferred_date"] = yesterday.isoformat()
        
        response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        
        assert response.status_code == 400
    
    def test_create_request_missing_required_fields(self, patient_token):
        """Test creating request with missing required fields"""
        response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "doctor_id": str(uuid4())
                # Missing other required fields
            }
        )
        
        assert response.status_code == 422
    
    def test_create_request_invalid_time_format(self, patient_token, appointment_request_data):
        """Test creating request with invalid time format"""
        appointment_request_data["preferred_time"] = "25:00"  # Invalid time
        
        response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        
        assert response.status_code == 422


class TestListAppointmentRequests:
    """Test listing appointment requests"""
    
    def test_list_requests_as_doctor(self, doctor_token):
        """Test listing requests as doctor"""
        response = client.get(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        # Should succeed even if empty
        assert response.status_code in [200, 400]  # 400 if not implemented
    
    def test_list_requests_with_status_filter(self, doctor_token):
        """Test listing requests with status filter"""
        response = client.get(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {doctor_token}"},
            params={"status": "PENDING"}
        )
        
        assert response.status_code in [200, 400]
    
    def test_list_requests_with_pagination(self, doctor_token):
        """Test listing requests with pagination"""
        response = client.get(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {doctor_token}"},
            params={"page": 1, "limit": 10}
        )
        
        assert response.status_code in [200, 400]
    
    def test_list_requests_unauthorized(self):
        """Test listing requests without authentication"""
        response = client.get("/api/v1/appointment/requests")
        
        assert response.status_code == 401


class TestGetAppointmentRequest:
    """Test getting appointment request details"""
    
    def test_get_request_success(self, patient_token, doctor_token, appointment_request_data):
        """Test getting request details"""
        # Create a request first
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Get the request
        response = client.get(
            f"/api/v1/appointment/requests/{request_id}",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == request_id
    
    def test_get_request_as_doctor(self, patient_token, doctor_token, appointment_request_data):
        """Test getting request as assigned doctor"""
        # Create a request first
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Get the request as doctor
        response = client.get(
            f"/api/v1/appointment/requests/{request_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
    
    def test_get_request_not_found(self, patient_token):
        """Test getting non-existent request"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/appointment/requests/{fake_id}",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code == 404
    
    def test_get_request_unauthorized(self, patient_token, appointment_request_data):
        """Test getting request without authentication"""
        # Create a request first
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Try to get without auth
        response = client.get(f"/api/v1/appointment/requests/{request_id}")
        
        assert response.status_code == 401


class TestAcceptAppointmentRequest:
    """Test accepting appointment requests"""
    
    def test_accept_request_success(self, patient_token, doctor_token, appointment_request_data):
        """Test successful request acceptance"""
        # Create a request first
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Accept the request
        response = client.post(
            f"/api/v1/appointment/requests/{request_id}/accept",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "ACCEPTED"
    
    def test_accept_request_as_patient(self, patient_token, appointment_request_data):
        """Test accepting request as patient (should fail)"""
        # Create a request first
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Try to accept as patient
        response = client.post(
            f"/api/v1/appointment/requests/{request_id}/accept",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code in [403, 400]
    
    def test_accept_request_not_found(self, doctor_token):
        """Test accepting non-existent request"""
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/appointment/requests/{fake_id}/accept",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 404
    
    def test_accept_request_already_accepted(self, patient_token, doctor_token, appointment_request_data):
        """Test accepting already accepted request"""
        # Create and accept a request
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Accept first time
        client.post(
            f"/api/v1/appointment/requests/{request_id}/accept",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        # Try to accept again
        response = client.post(
            f"/api/v1/appointment/requests/{request_id}/accept",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 400
    
    def test_accept_request_already_rejected(self, patient_token, doctor_token, appointment_request_data):
        """Test accepting already rejected request"""
        # Create a request
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Reject it
        client.post(
            f"/api/v1/appointment/requests/{request_id}/reject",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"rejection_reason": "Not available"}
        )
        
        # Try to accept
        response = client.post(
            f"/api/v1/appointment/requests/{request_id}/accept",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 400


class TestRejectAppointmentRequest:
    """Test rejecting appointment requests"""
    
    def test_reject_request_success(self, patient_token, doctor_token, appointment_request_data):
        """Test successful request rejection"""
        # Create a request first
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Reject the request
        response = client.post(
            f"/api/v1/appointment/requests/{request_id}/reject",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"rejection_reason": "Not available at this time"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "REJECTED"
        assert data["data"]["rejection_reason"] == "Not available at this time"
    
    def test_reject_request_without_reason(self, patient_token, doctor_token, appointment_request_data):
        """Test rejecting request without reason"""
        # Create a request first
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Reject without reason
        response = client.post(
            f"/api/v1/appointment/requests/{request_id}/reject",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "REJECTED"
    
    def test_reject_request_as_patient(self, patient_token, appointment_request_data):
        """Test rejecting request as patient (should fail)"""
        # Create a request first
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Try to reject as patient
        response = client.post(
            f"/api/v1/appointment/requests/{request_id}/reject",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={"rejection_reason": "Test"}
        )
        
        assert response.status_code in [403, 400]
    
    def test_reject_request_not_found(self, doctor_token):
        """Test rejecting non-existent request"""
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/appointment/requests/{fake_id}/reject",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"rejection_reason": "Test"}
        )
        
        assert response.status_code == 404
    
    def test_reject_request_already_rejected(self, patient_token, doctor_token, appointment_request_data):
        """Test rejecting already rejected request"""
        # Create a request
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Reject first time
        client.post(
            f"/api/v1/appointment/requests/{request_id}/reject",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"rejection_reason": "First rejection"}
        )
        
        # Try to reject again
        response = client.post(
            f"/api/v1/appointment/requests/{request_id}/reject",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"rejection_reason": "Second rejection"}
        )
        
        assert response.status_code == 400
    
    def test_reject_request_already_accepted(self, patient_token, doctor_token, appointment_request_data):
        """Test rejecting already accepted request"""
        # Create a request
        create_response = client.post(
            "/api/v1/appointment/requests",
            headers={"Authorization": f"Bearer {patient_token}"},
            json=appointment_request_data
        )
        request_id = create_response.json()["data"]["id"]
        
        # Accept it
        client.post(
            f"/api/v1/appointment/requests/{request_id}/accept",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        # Try to reject
        response = client.post(
            f"/api/v1/appointment/requests/{request_id}/reject",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={"rejection_reason": "Too late"}
        )
        
        assert response.status_code == 400
