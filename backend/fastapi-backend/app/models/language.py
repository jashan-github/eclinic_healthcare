"""
Language model
Stores supported languages for the application
"""

from sqlalchemy import Column, String, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class Language(Base):
    """
    Language model
    Stores language information (name and code)
    """
    
    __tablename__ = "languages"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
        comment="Primary key (UUID)"
    )
    
    language_name = Column(
        String(255),
        nullable=True,
        comment="Language name (e.g., English, Spanish, French)"
    )
    
    language_code = Column(
        String(255),
        nullable=True,
        comment="Language code (e.g., en, es, fr)"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
        comment="Record creation timestamp (UTC)"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
        comment="Record last update timestamp (UTC)"
    )
    
    # Indexes
    __table_args__ = (
        Index('languages_language_code_index', 'language_code'),
        Index('languages_language_name_index', 'language_name'),
    )
    
    def __repr__(self):
        return f"<Language(id={self.id}, name='{self.language_name}', code='{self.language_code}')>"

