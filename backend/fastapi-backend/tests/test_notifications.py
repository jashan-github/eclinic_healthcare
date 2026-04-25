"""
Comprehensive test cases for Notifications endpoints
Tests notification management and settings
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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_notifications.db"
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
        role=UserRole.ADMIN.value,
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
def regular_user(test_clinic):
    """Create a regular user"""
    db = TestingSessionLocal()
    user = User(
        id=uuid4(),
        email="user@test.com",
        password=get_password_hash("password123"),
        name="Regular User",
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
def regular_token(regular_user):
    """Get regular user authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@test.com",
            "password": "password123"
        }
    )
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    return None


class TestListNotifications:
    """Test listing notifications"""
    
    def test_list_notifications_success(self, admin_token):
        """Test successful notification listing"""
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_list_notifications_with_pagination(self, admin_token):
        """Test listing with pagination"""
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_notifications_unauthorized(self):
        """Test listing without authentication"""
        response = client.get("/api/v1/notifications")
        
        assert response.status_code == 401


class TestGetNotification:
    """Test getting a specific notification"""
    
    def test_get_notification_success(self, admin_token):
        """Test successful notification retrieval"""
        # First list notifications to get an ID
        list_response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if list_response.status_code == 200:
            notifications = list_response.json()["data"]
            if notifications:
                notification_id = notifications[0]["id"]
                
                # Get the notification
                response = client.get(
                    f"/api/v1/notifications/{notification_id}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
    
    def test_get_notification_not_found(self, admin_token):
        """Test getting non-existent notification"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/notifications/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404


class TestCreateNotification:
    """Test creating notifications"""
    
    def test_create_notification_success(self, admin_token):
        """Test successful notification creation"""
        response = client.post(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Test Notification",
                "message": "This is a test notification",
                "type": "info",
                "user_id": str(uuid4())
            }
        )
        
        assert response.status_code in [201, 200]
        if response.status_code in [201, 200]:
            data = response.json()
            assert data["success"] is True
    
    def test_create_notification_missing_fields(self, admin_token):
        """Test creating notification with missing fields"""
        response = client.post(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={}
        )
        
        assert response.status_code == 422
    
    def test_create_notification_unauthorized(self):
        """Test creating notification without authentication"""
        response = client.post(
            "/api/v1/notifications",
            json={
                "title": "Test",
                "message": "Test message"
            }
        )
        
        assert response.status_code == 401
    
    def test_create_notification_non_admin(self, regular_token):
        """Test creating notification as non-admin (should fail)"""
        response = client.post(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {regular_token}"},
            json={
                "title": "Test",
                "message": "Test message"
            }
        )
        
        assert response.status_code in [403, 400]


class TestUpdateNotification:
    """Test updating notifications"""
    
    def test_update_notification_success(self, admin_token):
        """Test successful notification update"""
        # Create notification first
        create_response = client.post(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Test Notification",
                "message": "This is a test",
                "type": "info",
                "user_id": str(uuid4())
            }
        )
        
        if create_response.status_code in [201, 200]:
            notification_id = create_response.json()["data"]["id"]
            
            # Update notification
            response = client.patch(
                f"/api/v1/notifications/{notification_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "read": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_update_notification_not_found(self, admin_token):
        """Test updating non-existent notification"""
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/notifications/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"read": True}
        )
        
        assert response.status_code == 404


class TestNotificationSettings:
    """Test notification settings"""
    
    def test_get_notification_settings_success(self, admin_token):
        """Test getting notification settings"""
        response = client.get(
            "/api/v1/notifications/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_notification_settings_success(self, admin_token):
        """Test updating notification settings"""
        response = client.put(
            "/api/v1/notifications/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email_enabled": True,
                "sms_enabled": False,
                "whatsapp_enabled": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_notification_settings_unauthorized(self):
        """Test updating settings without authentication"""
        response = client.put(
            "/api/v1/notifications/settings",
            json={
                "email_enabled": True
            }
        )
        
        assert response.status_code == 401


class TestMarkNotificationsRead:
    """Test marking notifications as read"""
    
    def test_mark_all_read_success(self, admin_token):
        """Test marking all notifications as read"""
        response = client.put(
            "/api/v1/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_mark_all_read_unauthorized(self):
        """Test marking all read without authentication"""
        response = client.put("/api/v1/notifications/mark-all-read")
        
        assert response.status_code == 401
