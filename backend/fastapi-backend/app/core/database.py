"""
Database configuration and session management
SQLAlchemy setup for PostgreSQL
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings
from app.models.base import Base
from loguru import logger

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DB_ECHO,  # Log SQL statements
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency
    
    Usage:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database
    Create all tables
    
    Note: In production, use Alembic migrations instead of this function.
    This is only for development/testing purposes.
    """
    try:
        # Import all models here to ensure they're registered with Base
        from app.models import user  # noqa: F401
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully")
    
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working
    
    Returns:
        True if connection is successful
    """
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse DATABASE_URL
        url = urlparse(settings.DATABASE_URL)
        
        # Create a simple connection without pooling
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port or 5432,
            user=url.username,
            password=url.password,
            database=url.path[1:],  # Remove leading /
            connect_timeout=10  # 10 second timeout
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False
