from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env that aren't defined in Settings
    )
    # Application
    APP_NAME: str = "Webinar Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ROOT_PATH: str = ""  # For reverse proxy support (e.g., "/backend/webinar-service")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # Database - Use shared PostgreSQL from eclinic-backend
    DATABASE_URL: str = "postgresql+asyncpg://eclinic_user:eclinic_password@eclinic-postgres:5432/eclinic_db"
    
    # Redis - Use shared Redis from eclinic-backend
    REDIS_URL: str = "redis://eclinic-redis:6379/0"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-min-32-characters-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Encryption
    ENCRYPTION_KEY: str = Field(
        default="",
        description="Fernet encryption key for Agora tokens (32 url-safe base64-encoded bytes). Generate using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    )
    
    # Agora Video SDK Configuration
    AGORA_APP_ID: str = Field(default="", description="Agora App ID for video calls/webinars")
    AGORA_APP_CERTIFICATE: str = Field(default="", description="Agora App Certificate for token generation")
    AGORA_TOKEN_EXPIRY_MINUTES: int = Field(default=60, description="Agora token expiry in minutes (15-60)")
    AGORA_TOKEN_LOG_FILE: str = Field(default="logs/agora_tokens.log", description="Path to file for Agora token debug logging")
    
    # Auth Service (shared) - Use container name from Docker network
    AUTH_SERVICE_URL: str = "http://eclinic-backend:8000"
    
    # Base URL for generating absolute URLs
    BASE_URL: str = Field(
        default="https://portal.salutogenahealthcareltd.com/backend/api-fast/",
        description="Base URL for generating absolute URLs"
    )
    
    # Security
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS into a list."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if self.CORS_ORIGINS == ["*"]:
            return ["*"]
        return self.CORS_ORIGINS.split(",") if isinstance(self.CORS_ORIGINS, str) else ["*"]


settings = Settings()
