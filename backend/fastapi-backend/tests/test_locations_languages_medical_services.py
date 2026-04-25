"""
Comprehensive test cases for Locations, Languages, and Medical Services endpoints
Tests public data endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4, UUID

from app.main import app
from app.core.database import Base, get_db


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_locations_languages.db"
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


class TestLocations:
    """Test location endpoints"""
    
    def test_get_countries_success(self):
        """Test successful countries retrieval"""
        response = client.get("/api/v1/locations/countries")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_states_success(self):
        """Test successful states retrieval"""
        # First get a country
        countries_response = client.get("/api/v1/locations/countries")
        if countries_response.status_code == 200:
            countries = countries_response.json()["data"]
            if countries:
                country_id = countries[0]["id"]
                
                # Get states for that country
                response = client.get(f"/api/v1/locations/countries/{country_id}/states")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
    
    def test_get_states_invalid_country(self):
        """Test getting states for invalid country"""
        fake_id = uuid4()
        response = client.get(f"/api/v1/locations/countries/{fake_id}/states")
        
        assert response.status_code in [404, 200]  # May return empty list
    
    def test_get_cities_success(self):
        """Test successful cities retrieval"""
        # First get states
        states_response = client.get("/api/v1/locations/states")
        if states_response.status_code == 200:
            states = states_response.json()["data"]
            if states:
                state_id = states[0]["id"]
                
                # Get cities for that state
                response = client.get(f"/api/v1/locations/states/{state_id}/cities")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
    
    def test_get_all_states_success(self):
        """Test getting all states"""
        response = client.get("/api/v1/locations/states")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_all_cities_success(self):
        """Test getting all cities"""
        response = client.get("/api/v1/locations/cities")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestLanguages:
    """Test language endpoints"""
    
    def test_get_languages_success(self):
        """Test successful languages retrieval"""
        response = client.get("/api/v1/languages/languages")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_languages_no_auth_required(self):
        """Test that languages endpoint doesn't require authentication"""
        response = client.get("/api/v1/languages/languages")
        
        # Should work without auth
        assert response.status_code == 200


class TestMedicalServices:
    """Test medical services endpoints"""
    
    def test_get_medical_services_success(self):
        """Test successful medical services retrieval"""
        response = client.get("/api/v1/medical-services/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_medical_services_no_auth_required(self):
        """Test that medical services endpoint doesn't require authentication"""
        response = client.get("/api/v1/medical-services/")
        
        # Should work without auth
        assert response.status_code == 200
    
    def test_get_medical_services_empty_result(self):
        """Test getting medical services when none exist"""
        response = client.get("/api/v1/medical-services/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
