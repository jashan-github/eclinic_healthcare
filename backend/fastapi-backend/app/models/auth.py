"""
Authentication and authorization models
Matches Laravel auth table structures exactly
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Index, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, Base


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('created_at', DateTime(timezone=True), nullable=True),
    Column('updated_at', DateTime(timezone=True), nullable=True),
    UniqueConstraint('user_id', 'role_id', name='user_roles_user_id_role_id_unique'),
    Index('user_roles_user_id_index', 'user_id'),
    Index('user_roles_role_id_index', 'role_id'),
)


class Role(BaseModel):
    """
    Role model
    Matches Laravel Spatie roles table structure with additional metadata
    """
    
    __tablename__ = "roles"
    
    name = Column(String(255), nullable=False, unique=True, index=True)
    guard_name = Column(String(255), nullable=False, default='web', index=True)
    display_name = Column(String(255), nullable=True, comment="Human-readable role name")
    description = Column(Text, nullable=True, comment="Role description")
    permissions = Column(JSONB, nullable=True, comment="List of permissions for this role")
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', guard_name='{self.guard_name}')>"


class PasswordReset(Base):
    """
    Password reset tokens model
    Matches Laravel password_resets table structure exactly
    Uses composite primary key (email, token) as SQLAlchemy requires a primary key
    """
    
    __tablename__ = "password_resets"
    
    email = Column(String(255), nullable=False, primary_key=True, index=True)
    token = Column(String(255), nullable=False, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('password_resets_email_index', 'email'),
        Index('password_resets_token_index', 'token'),
    )
    
    def __repr__(self):
        return f"<PasswordReset(email='{self.email}', created_at='{self.created_at}')>"


class LoginAttempt(BaseModel):
    """
    Login attempts tracking model
    Tracks all login attempts (successful and failed)
    """
    
    __tablename__ = "login_attempts"
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<LoginAttempt(id={self.id}, email='{self.email}', success={self.success})>"


class UserSession(Base):
    """
    User sessions model
    Matches Laravel sessions table structure
    """
    
    __tablename__ = "user_sessions"
    
    id = Column(String(255), primary_key=True, nullable=False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    payload = Column(Text, nullable=False)
    last_activity = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    # Indexes
    __table_args__ = (
        Index('user_sessions_user_id_index', 'user_id'),
        Index('user_sessions_last_activity_index', 'last_activity'),
    )
    
    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id={self.user_id}, last_activity={self.last_activity})>"

