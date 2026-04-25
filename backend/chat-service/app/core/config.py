from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Chat Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ROOT_PATH: str = ""  # For reverse proxy support (e.g., "/backend/chat-service")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # Database - Use shared PostgreSQL from eclinic-backend
    DATABASE_URL: str = "postgresql+asyncpg://eclinic_user:eclinic_password@eclinic-postgres:5432/eclinic_db"
    
    # Redis - Use shared Redis from eclinic-backend
    REDIS_URL: str = "redis://eclinic-redis:6379/0"
    REDIS_PUBSUB_PREFIX: str = "chat_room:"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-min-32-characters-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Encryption
    ENCRYPTION_KEY: str = Field(
        default="",
        description="Fernet encryption key for chat messages (32 url-safe base64-encoded bytes). Generate using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    )
    
    # Auth Service (shared)
    AUTH_SERVICE_URL: str = "http://backend:8000"
    
    # Base URL for generating absolute URLs (e.g., for avatar images)
    BASE_URL: str = Field(default="https://portal.salutogenahealthcareltd.com/backend/api-fast/", description="Base URL for generating absolute URLs")
    
    # Security
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_MESSAGES_PER_MINUTE: int = 60
    RATE_LIMIT_MESSAGE_SIZE_BYTES: int = 10240  # 10KB
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS_PER_USER: int = 5
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
