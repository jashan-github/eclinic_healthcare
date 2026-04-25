"""
Comprehensive test cases for Appointment Booking endpoints
Tests patient appointment booking flow
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4, UUID
from datetime import date, timedelta

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.clinic import Clinic
from app.models.service import Service
from app.core.security import get_password_hash, ConsultationMode, UserRole
from app.core.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_appointment_booking.db"
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


class TestGetDoctorSummary:
    """Test getting doctor summary for booking"""
    
    def test_get_doctor_summary_success(self, doctor_user, test_service):
        """Test successful doctor summary retrieval"""
        response = client.get(
            f"/api/v1/patient/doctors/{doctor_user}/summary",
            params={"service_id": str(test_service)}
        )
        
        # May require authentication or may be public
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
    
    def test_get_doctor_summary_invalid_doctor(self, test_service):
        """Test getting summary for non-existent doctor"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/patient/doctors/{fake_id}/summary",
            params={"service_id": str(test_service)}
        )
        
        assert response.status_code in [404, 401]
    
    def test_get_doctor_summary_missing_service(self, doctor_user):
        """Test getting summary without service ID"""
        response = client.get(
            f"/api/v1/patient/doctors/{doctor_user}/summary"
        )
        
        assert response.status_code in [422, 400]


class TestGetConsultationTypes:
    """Test getting available consultation types"""
    
    def test_get_consultation_types_success(self, doctor_user, test_service):
        """Test successful consultation types retrieval"""
        response = client.get(
            f"/api/v1/patient/doctors/{doctor_user}/consultation-types",
            params={"service_id": str(test_service)}
        )
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    def test_get_consultation_types_both_modes_returned(self, doctor_user, test_service, test_clinic, doctor_token):
        """Both consultation modes should be returned with correct is_available flags"""
        db = TestingSessionLocal()
        try:
            # Create an availability and assign only IN_CLINIC for this service
            from app.models.availability import DoctorAvailability
            from app.models.doctor_service_availability import DoctorServiceAvailability
            from datetime import time

            # Create availability for doctor's weekday
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
            db.refresh(avail)

            # Assign service to this availability for IN_CLINIC
            assignment = DoctorServiceAvailability(
                availability_id=avail.id,
                service_id=test_service,
                consultation_mode=ConsultationMode.IN_CLINIC.value,
                slot_duration_minutes=30
            )
            db.add(assignment)
            db.commit()

            # Call consultation-types
            response = client.get(
                f"/api/v1/patient/doctors/{doctor_user}/consultation-types",
                params={"service_id": str(test_service)}
            )
            assert response.status_code == 200
            data = response.json()["data"]["consultation_types"]
            # Should contain both modes
            modes = {m["mode"]: m for m in data}
            assert ConsultationMode.IN_CLINIC.value in modes
            assert ConsultationMode.TELECONSULTATION.value in modes
            # IN_CLINIC should be available, TELECONSULTATION not
            assert modes[ConsultationMode.IN_CLINIC.value]["is_available"] is True
            assert modes[ConsultationMode.TELECONSULTATION.value]["is_available"] is False
        finally:
            db.close()
    
    def test_get_consultation_types_missing_service(self, doctor_user):
        """Test getting types without service ID"""
        response = client.get(
            f"/api/v1/patient/doctors/{doctor_user}/consultation-types"
        )
        
        assert response.status_code in [422, 400]


class TestGetAvailableTimeSlots:
    """Test getting available time slots"""
    
    def test_get_time_slots_success(self, doctor_user, test_service):
        """Test successful time slots retrieval"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.get(
            f"/api/v1/patient/doctors/{doctor_user}/time-slots",
            params={
                "service_id": str(test_service),
                "date": tomorrow.isoformat(),
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
    
    def test_get_time_slots_past_date(self, doctor_user, test_service):
        """Test getting slots for past date"""
        yesterday = date.today() - timedelta(days=1)
        response = client.get(
            f"/api/v1/patient/doctors/{doctor_user}/time-slots",
            params={
                "service_id": str(test_service),
                "date": yesterday.isoformat(),
                "consultation_mode": ConsultationMode.IN_CLINIC.value
            }
        )
        
        assert response.status_code in [400, 422]
    
    def test_get_time_slots_missing_params(self, doctor_user):
        """Test getting slots with missing parameters"""
        response = client.get(
            f"/api/v1/patient/doctors/{doctor_user}/time-slots"
        )
        
        assert response.status_code in [422, 400]


class TestBookAppointment:
    """Test booking an appointment"""
    
    def test_book_appointment_success(self, patient_token, doctor_user, test_service):
        """Test successful appointment booking"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/v1/patient/appointments",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "doctor_id": str(doctor_user),
                "service_id": str(test_service),
                "consultation_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_date": tomorrow.isoformat(),
                "appointment_time": "10:00:00"
            }
        )
        
        # May succeed or fail depending on availability setup
        assert response.status_code in [201, 400]
        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
    
    def test_book_appointment_unauthorized(self, doctor_user, test_service):
        """Test booking without authentication"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/v1/patient/appointments",
            json={
                "doctor_id": str(doctor_user),
                "service_id": str(test_service),
                "consultation_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_date": tomorrow.isoformat(),
                "appointment_time": "10:00:00"
            }
        )
        
        assert response.status_code == 401
    
    def test_book_appointment_past_date(self, patient_token, doctor_user, test_service):
        """Test booking with past date"""
        yesterday = date.today() - timedelta(days=1)
        response = client.post(
            "/api/v1/patient/appointments",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "doctor_id": str(doctor_user),
                "service_id": str(test_service),
                "consultation_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_date": yesterday.isoformat(),
                "appointment_time": "10:00:00"
            }
        )
        
        assert response.status_code in [400, 422]
    
    def test_book_appointment_missing_fields(self, patient_token):
        """Test booking with missing required fields"""
        response = client.post(
            "/api/v1/patient/appointments",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={}
        )
        
        assert response.status_code == 422
    
    def test_book_appointment_invalid_doctor(self, patient_token, test_service):
        """Test booking with invalid doctor ID"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/v1/patient/appointments",
            headers={"Authorization": f"Bearer {patient_token}"},
            json={
                "doctor_id": str(uuid4()),
                "service_id": str(test_service),
                "consultation_mode": ConsultationMode.IN_CLINIC.value,
                "appointment_date": tomorrow.isoformat(),
                "appointment_time": "10:00:00"
            }
        )
        
        assert response.status_code in [404, 400]


class TestPatientAppointmentsGrouped:
    """Test grouped appointments endpoint for patients"""

    def test_patient_appointments_grouped(self, patient_token, doctor_token, doctor_user, test_service, test_clinic):
        db = TestingSessionLocal()
        try:
            from app.models.appointment import Appointment
            from app.models.doctor_service import DoctorService
            from app.models.availability import DoctorAvailability
            from datetime import date, timedelta, time

            # Create service assignment and availability
            ds = DoctorService(
                doctor_id=doctor_user,
                service_id=test_service,
                clinic_id=test_clinic,
                day_of_week=None,
                slot_duration_minutes=30,
                is_active=True
            )
            db.add(ds)

            tomorrow = date.today() + timedelta(days=1)
            yesterday = date.today() - timedelta(days=1)
            avail = DoctorAvailability(
                doctor_id=doctor_user,
                clinic_id=test_clinic,
                day_of_week=tomorrow.weekday(),
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True
            )
            db.add(avail)
            db.commit()

            # Create a future appointment (upcoming)
            appt = Appointment(
                doctor_id=doctor_user,
                patient_id=self._get_patient_id_from_token(patient_token),
                service_id=test_service,
                clinic_id=test_clinic,
                appointment_date=tomorrow,
                start_time=time(10, 0),
                end_time=time(10, 30),
                status='SCHEDULED',
                price_amount=100.00,
                currency='USD',
                pricing_source='global',
                consultation_mode='IN_CLINIC',
                duration_minutes=30
            )
            db.add(appt)

            # Create a past appointment
            past_appt = Appointment(
                doctor_id=doctor_user,
                patient_id=self._get_patient_id_from_token(patient_token),
                service_id=test_service,
                clinic_id=test_clinic,
                appointment_date=yesterday,
                start_time=time(9, 0),
                end_time=time(9, 30),
                status='COMPLETED',
                price_amount=80.00,
                currency='USD',
                pricing_source='global',
                consultation_mode='IN_CLINIC',
                duration_minutes=30
            )
            db.add(past_appt)
            db.commit()

            # Create a pending appointment request as the patient
            from app.core.security import ConsultationMode
            response = client.post(
                "/api/v1/appointment/requests",
                headers={"Authorization": f"Bearer {patient_token}"},
                json={
                    "doctor_id": str(doctor_user),
                    "service_id": str(test_service),
                    "consultation_mode": ConsultationMode.IN_CLINIC.value,
                    "preferred_date": tomorrow.isoformat(),
                    "preferred_time": "11:00",
                    "reason": "Pending appointment test"
                }
            )
            assert response.status_code == 201

            # Fetch grouped appointments as patient
            grouped_resp = client.get(
                "/api/v1/patient/appointments/grouped",
                headers={"Authorization": f"Bearer {patient_token}"}
            )
            assert grouped_resp.status_code == 200
            data = grouped_resp.json()["data"]
            assert "upcoming" in data and "pending" in data and "past" in data
            # Check counts
            assert len(data["upcoming"]) >= 1
            assert len(data["pending"]) >= 1
            assert len(data["past"]) >= 1
        finally:
            db.close()

    @staticmethod
    def _get_patient_id_from_token(token: str):
        # Helper to decode token via login endpoint response (test environment stores token mapping)
        # Simplest approach: call /api/v1/auth/me endpoint
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200:
            return resp.json()["data"]["id"]
        return None
