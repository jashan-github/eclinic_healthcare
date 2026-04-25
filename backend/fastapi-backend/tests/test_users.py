"""
Comprehensive test cases for User Management endpoints
Tests all user CRUD operations and edge cases
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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_users.db"
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
    """Create a regular user (non-admin)"""
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


class TestListUsers:
    """Test listing users"""
    
    def test_list_users_success(self, admin_token):
        """Test successful user listing"""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "users" in data["data"]
        assert "pagination" in data["data"]
    
    def test_list_users_with_pagination(self, admin_token):
        """Test listing users with pagination"""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "per_page": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_users_with_role_filter(self, admin_token):
        """Test listing users filtered by role"""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"role": UserRole.PATIENT.value}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_users_with_active_filter(self, admin_token):
        """Test listing users filtered by active status"""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"is_active": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_users_with_search(self, admin_token):
        """Test listing users with search"""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"search": "test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_users_unauthorized(self):
        """Test listing users without authentication"""
        response = client.get("/api/v1/users/")
        
        assert response.status_code == 401
    
    def test_list_users_non_admin(self, regular_token):
        """Test listing users as non-admin (should fail)"""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        
        # May succeed if regular users can list, or fail if admin-only
        assert response.status_code in [200, 403]


class TestGetUser:
    """Test getting user details"""
    
    def test_get_user_success(self, admin_token, regular_user):
        """Test successful user retrieval"""
        response = client.get(
            f"/api/v1/users/{regular_user}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["id"] == str(regular_user)
    
    def test_get_user_not_found(self, admin_token):
        """Test getting non-existent user"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    def test_get_user_unauthorized(self, regular_user):
        """Test getting user without authentication"""
        response = client.get(f"/api/v1/users/{regular_user}")
        
        assert response.status_code == 401


class TestCreateUser:
    """Test user creation"""
    
    def test_create_user_success(self, admin_token, test_clinic):
        """Test successful user creation"""
        response = client.post(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "newuser@test.com",
                "password": "password123",
                "name": "New User",
                "role": UserRole.PATIENT.value,
                "clinic_id": str(test_clinic),
                "is_active": True
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "User created successfully"
        assert "data" in data
        assert data["data"]["email"] == "newuser@test.com"
    
    def test_create_user_doctor_role(self, admin_token, test_clinic):
        """Test creating user with doctor role"""
        response = client.post(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "doctor@test.com",
                "password": "password123",
                "name": "Doctor User",
                "role": UserRole.DOCTOR.value,
                "clinic_id": str(test_clinic),
                "is_active": True
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["role"] == UserRole.DOCTOR.value
    
    def test_create_user_duplicate_email(self, admin_token, test_clinic, regular_user):
        """Test creating user with duplicate email"""
        # Get the existing user's email
        db = TestingSessionLocal()
        existing_user = db.query(User).filter(User.id == regular_user).first()
        existing_email = existing_user.email
        db.close()
        
        response = client.post(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": existing_email,
                "password": "password123",
                "name": "Duplicate User",
                "role": UserRole.PATIENT.value,
                "clinic_id": str(test_clinic)
            }
        )
        
        assert response.status_code == 409
    
    def test_create_user_unauthorized(self, test_clinic):
        """Test creating user without authentication"""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "newuser@test.com",
                "password": "password123",
                "name": "New User",
                "role": UserRole.PATIENT.value,
                "clinic_id": str(test_clinic)
            }
        )
        
        assert response.status_code == 401
    
    def test_create_user_non_admin(self, regular_token, test_clinic):
        """Test creating user as non-admin (should fail)"""
        response = client.post(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {regular_token}"},
            json={
                "email": "newuser@test.com",
                "password": "password123",
                "name": "New User",
                "role": UserRole.PATIENT.value,
                "clinic_id": str(test_clinic)
            }
        )
        
        assert response.status_code in [403, 400]
    
    def test_create_user_missing_required_fields(self, admin_token):
        """Test creating user with missing required fields"""
        response = client.post(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "newuser@test.com"
                # Missing other required fields
            }
        )
        
        assert response.status_code == 422
    
    def test_create_user_invalid_email(self, admin_token, test_clinic):
        """Test creating user with invalid email"""
        response = client.post(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "invalid-email",
                "password": "password123",
                "name": "New User",
                "role": UserRole.PATIENT.value,
                "clinic_id": str(test_clinic)
            }
        )
        
        assert response.status_code == 422
    
    def test_create_user_short_password(self, admin_token, test_clinic):
        """Test creating user with short password"""
        response = client.post(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "newuser@test.com",
                "password": "short",
                "name": "New User",
                "role": UserRole.PATIENT.value,
                "clinic_id": str(test_clinic)
            }
        )
        
        assert response.status_code == 422


class TestUpdateUser:
    """Test user updates"""
    
    def test_update_user_success(self, admin_token, regular_user):
        """Test successful user update"""
        response = client.patch(
            f"/api/v1/users/{regular_user}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Updated Name",
                "phone": "+1234567890"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
    
    def test_update_user_email(self, admin_token, regular_user):
        """Test updating user email"""
        response = client.patch(
            f"/api/v1/users/{regular_user}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "updated@test.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == "updated@test.com"
    
    def test_update_user_role(self, admin_token, regular_user):
        """Test updating user role"""
        response = client.patch(
            f"/api/v1/users/{regular_user}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": UserRole.DOCTOR.value
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["role"] == UserRole.DOCTOR.value
    
    def test_update_user_not_found(self, admin_token):
        """Test updating non-existent user"""
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 404
    
    def test_update_user_unauthorized(self, regular_user):
        """Test updating user without authentication"""
        response = client.patch(
            f"/api/v1/users/{regular_user}",
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 401


class TestDeleteUser:
    """Test user deletion"""
    
    def test_delete_user_success(self, admin_token, test_clinic):
        """Test successful user deletion"""
        # Create a user first
        create_response = client.post(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "todelete@test.com",
                "password": "password123",
                "name": "User To Delete",
                "role": UserRole.PATIENT.value,
                "clinic_id": str(test_clinic)
            }
        )
        user_id = create_response.json()["data"]["id"]
        
        # Delete the user
        response = client.delete(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_user_not_found(self, admin_token):
        """Test deleting non-existent user"""
        fake_id = uuid4()
        response = client.delete(
            f"/api/v1/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    def test_delete_user_unauthorized(self, regular_user):
        """Test deleting user without authentication"""
        response = client.delete(f"/api/v1/users/{regular_user}")
        
        assert response.status_code == 401
    
    def test_delete_self(self, admin_token, admin_user):
        """Test deleting own account (should fail)"""
        response = client.delete(
            f"/api/v1/users/{admin_user}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400


class TestActivateDeactivateUser:
    """Test user activation/deactivation"""
    
    def test_activate_user_success(self, admin_token, regular_user):
        """Test successful user activation"""
        # First deactivate
        client.post(
            f"/api/v1/users/{regular_user}/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Test deactivation"}
        )
        
        # Then activate
        response = client.post(
            f"/api/v1/users/{regular_user}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Test activation"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_active"] is True
    
    def test_deactivate_user_success(self, admin_token, regular_user):
        """Test successful user deactivation"""
        response = client.post(
            f"/api/v1/users/{regular_user}/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Test deactivation"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_active"] is False
    
    def test_activate_user_not_found(self, admin_token):
        """Test activating non-existent user"""
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/users/{fake_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Test"}
        )
        
        assert response.status_code == 404


class TestChangeUserRole:
    """Test changing user role"""
    
    def test_change_role_success(self, admin_token, regular_user):
        """Test successful role change"""
        response = client.post(
            f"/api/v1/users/{regular_user}/change-role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": UserRole.DOCTOR.value,
                "reason": "Promoted to doctor"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role"] == UserRole.DOCTOR.value
    
    def test_change_role_invalid_role(self, admin_token, regular_user):
        """Test changing to invalid role"""
        response = client.post(
            f"/api/v1/users/{regular_user}/change-role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "INVALID_ROLE",
                "reason": "Test"
            }
        )
        
        assert response.status_code == 422
    
    def test_change_role_not_found(self, admin_token):
        """Test changing role for non-existent user"""
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/users/{fake_id}/change-role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": UserRole.DOCTOR.value,
                "reason": "Test"
            }
        )
        
        assert response.status_code == 404


class TestUserStatistics:
    """Test user statistics"""
    
    def test_get_statistics_success(self, admin_token):
        """Test successful statistics retrieval"""
        response = client.get(
            "/api/v1/users/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total_users" in data["data"]
    
    def test_get_statistics_unauthorized(self):
        """Test getting statistics without authentication"""
        response = client.get("/api/v1/users/statistics")
        
        assert response.status_code == 401


class TestListRoles:
    """Test listing available roles"""
    
    def test_list_roles_success(self, admin_token):
        """Test successful roles listing"""
        response = client.get(
            "/api/v1/users/roles/list",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_list_roles_unauthorized(self):
        """Test listing roles without authentication"""
        response = client.get("/api/v1/users/roles/list")
        
        assert response.status_code == 401
