"""
Base SQLAlchemy model with common fields and functionality

All models should inherit from this base class to ensure:
- UUID primary keys
- UTC timestamps (created_at, updated_at)
- Soft deletes (deleted_at)
- Consistent column naming (snake_case)
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

# Create declarative base
Base = declarative_base()


class BaseModel(Base):
    """
    Base model class for all database models
    
    Provides:
    - UUID primary key (id)
    - UTC timestamps (created_at, updated_at)
    - Soft delete support (deleted_at)
    
    All timestamps are stored in UTC timezone.
    Column names follow snake_case convention to match Laravel standards.
    """
    
    __abstract__ = True  # This is an abstract base class
    
    # UUID primary key (PostgreSQL UUID type)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
        comment="Primary key (UUID)"
    )
    
    # UTC timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Record creation timestamp (UTC)"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
        comment="Record last update timestamp (UTC)"
    )
    
    # Soft delete
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Soft delete timestamp (UTC). NULL means not deleted."
    )
    
    def __repr__(self) -> str:
        """Default string representation"""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted"""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Soft delete the record"""
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        """Restore a soft-deleted record"""
        self.deleted_at = None
    
    def to_dict(self, include_deleted: bool = False) -> dict:
        """
        Convert model to dictionary
        
        Args:
            include_deleted: Include deleted_at field in output
            
        Returns:
            Dictionary representation of model
        """
        data = {
            "id": str(self.id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_deleted:
            data["deleted_at"] = self.deleted_at.isoformat() if self.deleted_at else None
        
        return data

