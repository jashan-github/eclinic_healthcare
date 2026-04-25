"""
User model for authentication and authorization
SQLAlchemy ORM model
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.auth import user_roles


class User(BaseModel):
    """
    User model
    Stores user authentication and profile information
    """
    
    __tablename__ = "users"
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # Hashed password
    remember_token = Column(String(100), nullable=True, index=True)  # Laravel standard
    
    # Profile fields
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Role-based access control
    role = Column(
        String(50),
        nullable=False,
        default="patient",
        index=True,
        comment="User role: super_admin, clinic_admin, doctor, nurse, staff, receptionist, patient"
    )
    
    # Multi-clinic support
    # Note: When Clinic model is migrated to UUID, this should be changed to UUID
    clinic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Clinic ID for multi-clinic support (UUID)"
    )
    
    # Staff-doctor assignment (for staff role users)
    assigned_doctor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Assigned doctor ID for staff role users (nullable)"
    )
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional fields
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 support
    
    # Password reset
    reset_token = Column(String(255), nullable=True, unique=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    verification_token = Column(String(255), nullable=True, unique=True)
    
    # Profile picture
    avatar = Column(String(255), nullable=True)
    
    # Additional metadata (JSON)
    user_metadata = Column(Text, nullable=True, comment="JSON metadata for extensibility")
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False, lazy="select")
    # clinic = relationship("Clinic", back_populates="users")
    # appointments = relationship("Appointment", back_populates="user")
    # prescriptions = relationship("Prescription", back_populates="user")
    languages = relationship("Language", secondary="user_languages", lazy="select")
    medical_services = relationship("MedicalService", secondary="user_medical_services", lazy="select")
    assigned_doctor = relationship("User", foreign_keys=[assigned_doctor_id], remote_side="User.id", lazy="select")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    def to_dict(self, include_sensitive: bool = False, include_deleted: bool = False):
        """
        Convert user to dictionary
        
        Args:
            include_sensitive: Include sensitive fields (password, tokens)
            include_deleted: Include deleted_at field
        
        Returns:
            Dictionary representation of user
        """
        # Get base fields from BaseModel
        data = super().to_dict(include_deleted=include_deleted)
        
        # Add user-specific fields
        data.update({
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "role": self.role,
            "clinic_id": str(self.clinic_id) if self.clinic_id else None,
            "assigned_doctor_id": str(self.assigned_doctor_id) if self.assigned_doctor_id else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "email_verified_at": self.email_verified_at.isoformat() if self.email_verified_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "avatar": self.avatar,
        })
        
        if include_sensitive:
            data.update({
                "password": self.password,
                "reset_token": self.reset_token,
                "verification_token": self.verification_token,
            })
        
        return data
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role in ["super_admin", "clinic_admin"]
    
    @property
    def is_staff(self) -> bool:
        """Check if user is staff (doctor, nurse, staff, receptionist)"""
        return self.role in ["doctor", "nurse", "staff", "receptionist", "clinic_admin", "super_admin"]


class Clinic(BaseModel):
    """
    Clinic model for multi-clinic support
    """
    
    __tablename__ = "clinics"
    
    name = Column(String(255), nullable=False)
    code = Column(String(255), unique=True, nullable=False, index=True)
    timezone = Column(String(255), nullable=False, default="UTC")
    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to countries table"
    )
    status = Column(String(50), nullable=False, default="active", index=True)
    clinic_metadata = Column(JSONB, nullable=True, name="metadata")
    
    # Relationships
    country_rel = relationship("Country", foreign_keys=[country_id], lazy="select")
    # users = relationship("User", back_populates="clinic")
    
    def __repr__(self):
        return f"<Clinic(id={self.id}, name='{self.name}', code='{self.code}')>"
