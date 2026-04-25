"""
Authentication endpoint tests
Tests for Laravel-compatible auth API
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import get_password_hash


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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
def test_user():
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        password=get_password_hash("password123"),
        name="Test User",
        role="doctor",
        clinic_id=1,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


class TestRegister:
    """Test user registration"""
    
    def test_register_success(self):
        """Test successful registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "password_confirmation": "password123",
                "name": "New User",
                "role": "patient"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Check Laravel format
        assert data["success"] is True
        assert data["message"] == "Registration successful"
        assert "data" in data
        assert "user" in data["data"]
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        
        # Check user data
        user = data["data"]["user"]
        assert user["email"] == "newuser@example.com"
        assert user["name"] == "New User"
        assert user["role"] == "patient"
    
    def test_register_duplicate_email(self, test_user):
        """Test registration with existing email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "password_confirmation": "password123",
                "name": "Duplicate User",
                "role": "patient"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        
        assert data["success"] is False
        assert "email" in data["errors"]
    
    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "password_confirmation": "different123",
                "name": "Test User",
                "role": "patient"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["success"] is False
        assert "errors" in data


class TestLogin:
    """Test user login"""
    
    def test_login_success(self, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check Laravel format
        assert data["success"] is True
        assert data["message"] == "Login successful"
        assert "data" in data
        assert "user" in data["data"]
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        
        # Check user data
        user = data["data"]["user"]
        assert user["email"] == test_user.email
        assert user["name"] == test_user.name
        assert user["role"] == test_user.role
    
    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["success"] is False
        assert "Invalid credentials" in data["message"]
    
    def test_login_invalid_password(self, test_user):
        """Test login with incorrect password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["success"] is False
        assert "Invalid credentials" in data["message"]


class TestProfile:
    """Test profile endpoints"""
    
    def test_get_profile_authenticated(self, test_user):
        """Test getting profile with authentication"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123"
            }
        )
        
        token = login_response.json()["data"]["access_token"]
        
        # Get profile
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Profile retrieved successfully"
        assert data["data"]["email"] == test_user.email
    
    def test_get_profile_unauthenticated(self):
        """Test getting profile without authentication"""
        response = client.get("/api/v1/auth/profile")
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["success"] is False
    
    def test_update_profile(self, test_user):
        """Test updating profile"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123"
            }
        )
        
        token = login_response.json()["data"]["access_token"]
        
        # Update profile
        response = client.put(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Updated Name",
                "phone": "+1234567890"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Profile updated successfully"
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["phone"] == "+1234567890"


class TestRefreshToken:
    """Test token refresh"""
    
    def test_refresh_token_success(self, test_user):
        """Test successful token refresh"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123"
            }
        )
        
        refresh_token = login_response.json()["data"]["refresh_token"]
        
        # Refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Token refreshed successfully"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
    
    def test_refresh_token_invalid(self):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["success"] is False


class TestLogout:
    """Test user logout"""
    
    def test_logout_success(self, test_user):
        """Test successful logout"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123"
            }
        )
        
        token = login_response.json()["data"]["access_token"]
        
        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Logged out successfully"


class TestChangePassword:
    """Test password change"""
    
    def test_change_password_success(self, test_user):
        """Test successful password change"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123"
            }
        )
        
        token = login_response.json()["data"]["access_token"]
        
        # Change password
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "password123",
                "new_password": "newpassword123",
                "new_password_confirmation": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Password changed successfully"
        
        # Verify new password works
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "newpassword123"
            }
        )
        
        assert login_response.status_code == 200
    
    def test_change_password_wrong_current(self, test_user):
        """Test password change with wrong current password"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123"
            }
        )
        
        token = login_response.json()["data"]["access_token"]
        
        # Change password with wrong current password
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123",
                "new_password_confirmation": "newpassword123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["success"] is False
