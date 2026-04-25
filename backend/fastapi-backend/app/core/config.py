"""
Configuration management using Pydantic Settings
Supports environment-based configuration with validation
"""

from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "eClinic Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False
    ROOT_PATH: str = ""  # Set to proxy path like "/backend/api-fast" if behind reverse proxy
    BASE_URL: str = Field(default="https://portal.salutogenahealthcareltd.com/backend/api-fast/", description="Base URL for generating absolute URLs (e.g., for file uploads)")
    FRONTEND_URL: str = Field(default="https://portal.salutogenahealthcareltd.com", description="Frontend URL for redirects")
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ENCRYPTION_KEY: str = Field(
        default="",
        description="Fernet encryption key for sensitive data (32 url-safe base64-encoded bytes)"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    # Default includes localhost for development
    # For production, set CORS_ORIGINS in .env with your frontend domain(s)
    # Example: CORS_ORIGINS=https://portal.salutogenahealthcareltd.com,https://yourdomain.com,http://localhost:3000
    # IMPORTANT: Include both HTTP and HTTPS versions if you use both
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080,https://portal.salutogenahealthcareltd.com,http://portal.salutogenahealthcareltd.com"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/eclinic",
        description="PostgreSQL connection string"
    )
    DB_ECHO: bool = False  # SQLAlchemy echo SQL statements
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    
    # Redis (for caching, sessions, rate limiting)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True
    REDIS_PUBSUB_PREFIX: str = "video_session:"  # Prefix for video session pub/sub channels
    
    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"
    LOG_FILE_PATH: Optional[str] = None
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "30 days"
    
    # PHI Protection (fields to redact in logs)
    PHI_FIELDS: str = "ssn,social_security_number,date_of_birth,dob,medical_record_number,mrn,phone,email,address,password,credit_card,bank_account"
    
    @property
    def phi_fields_list(self) -> list[str]:
        """Get PHI fields as a list"""
        if isinstance(self.PHI_FIELDS, str):
            return [field.strip().lower() for field in self.PHI_FIELDS.split(",")]
        return self.PHI_FIELDS
    
    # Multi-clinic support (for future)
    MULTI_CLINIC_ENABLED: bool = False
    DEFAULT_CLINIC_ID: Optional[str] = None  # UUID string of default clinic (queried by code "DEFAULT" if not set)
    
    # Notifications
    SMS_ENABLED: bool = False
    EMAIL_ENABLED: bool = False
    WHATSAPP_ENABLED: bool = False
    
    # Email (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = "eClinic"
    SMTP_TLS: bool = True
    
    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: Optional[str] = None
    SENDGRID_FROM_NAME: Optional[str] = "eClinic"
    
    # SMS (Twilio example)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # WhatsApp (Twilio)
    WHATSAPP_API_KEY: Optional[str] = None
    WHATSAPP_PHONE_NUMBER: Optional[str] = None
    TWILIO_WHATSAPP_FROM: Optional[str] = Field(default=None, description="Twilio WhatsApp sender (E.164, e.g. +14155238886 for sandbox)")

    # Firebase Cloud Messaging (FCM) for push notifications
    FCM_ENABLED: bool = False
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(
        default=None,
        description="Path to Firebase service account JSON file (e.g. /secrets/firebase-key.json)",
    )
    FIREBASE_CREDENTIALS_JSON: Optional[str] = Field(
        default=None,
        description="Firebase service account JSON as string (alternative to path). Prefer path in production.",
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Audit Logging
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # 7 years for HIPAA compliance
    
    # File Uploads
    UPLOAD_DIR: str = "uploads"
    AVATAR_UPLOAD_DIR: str = "uploads/avatars"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_EXTENSIONS: list[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    
    # Payment Gateway - Sentoo
    SENTOO_MERCHANT_ID: str = Field(default="", description="Sentoo Merchant ID")
    SENTOO_MERCHANT_SECRET: str = Field(default="", description="Sentoo Merchant Secret")
    SENTOO_API_URL: str = Field(default="https://api.sandbox.sentoo.io/v1", description="Sentoo API base URL")
    SENTOO_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Sentoo webhook verification secret")
    PAYMENT_GATEWAY: str = Field(default="sentoo", description="Payment gateway to use (sentoo)")
    
    # Agora Video SDK
    AGORA_APP_ID: str = Field(default="", description="Agora App ID for video calls")
    AGORA_APP_CERTIFICATE: str = Field(default="", description="Agora App Certificate for token generation")
    AGORA_TOKEN_EXPIRY_MINUTES: int = Field(default=60, description="Agora token expiry in minutes (15-60)")
    
    # Video Call Settings
    VIDEO_DOCTOR_EARLY_JOIN_MINUTES: int = Field(default=5, description="Minutes before scheduled time doctor can join")
    VIDEO_JOIN_WATCHDOG_SECONDS: int = Field(default=30, description="Join attempt timeout in seconds")
    VIDEO_GRACE_PERIOD_SECONDS: int = Field(default=300, description="Grace period after call end before expiry (5 min)")
    
    # Webinar Service (for video sessions)
    WEBINAR_SERVICE_URL: str = Field(default="http://webinar-service:8002", description="Webinar service URL for creating video sessions")
    
    # Timezone
    TIMEZONE: str = Field(default="UTC", description="Application timezone (e.g., 'IST', 'EST', 'UTC', 'America/New_York', 'Asia/Kolkata')")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"
    
    def get_timezone(self):
        """
        Get pytz timezone object from TIMEZONE setting.
        Supports common abbreviations (IST, EST, UTC) and full timezone names.
        """
        import pytz
        
        timezone_str = self.TIMEZONE.strip().upper()
        
        # Map common abbreviations to pytz timezone names
        timezone_map = {
            "IST": "Asia/Kolkata",
            "EST": "America/New_York",
            "EDT": "America/New_York",  # EDT is same timezone as EST
            "PST": "America/Los_Angeles",
            "PDT": "America/Los_Angeles",  # PDT is same timezone as PST
            "CST": "America/Chicago",
            "CDT": "America/Chicago",  # CDT is same timezone as CST
            "MST": "America/Denver",
            "MDT": "America/Denver",  # MDT is same timezone as MST
            "UTC": "UTC",
            "GMT": "UTC",
        }
        
        # Check if it's a known abbreviation
        if timezone_str in timezone_map:
            timezone_name = timezone_map[timezone_str]
        else:
            # Assume it's already a valid pytz timezone name (e.g., "America/New_York", "Asia/Kolkata")
            timezone_name = self.TIMEZONE.strip()
        
        try:
            return pytz.timezone(timezone_name)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fallback to UTC if timezone is invalid
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid timezone '{self.TIMEZONE}', falling back to UTC")
            return pytz.UTC


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency injection for settings"""
    return settings
