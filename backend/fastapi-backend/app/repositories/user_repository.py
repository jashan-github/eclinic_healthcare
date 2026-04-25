"""
User repository
Data access layer for user operations
"""

from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.core.security import get_password_hash, verify_password


class UserRepository:
    """Repository for user database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: Union[str, UUID]) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            user_id: User ID (UUID string or UUID object)
        
        Returns:
            User object or None
        """
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return None
        
        return self.db.query(User).filter(
            and_(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        ).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            email: User email
        
        Returns:
            User object or None
        """
        return self.db.query(User).filter(
            and_(
                User.email == email.lower(),
                User.deleted_at.is_(None)
            )
        ).first()
    
    def get_by_email_with_deleted(self, email: str) -> Optional[User]:
        """
        Get user by email including soft-deleted users
        
        Args:
            email: User email
        
        Returns:
            User object or None
        """
        return self.db.query(User).filter(
            User.email == email.lower()
        ).first()
    
    def create(
        self,
        email: str,
        password: str,
        name: str,
        role: str = "patient",
        phone: Optional[str] = None,
        clinic_id: Optional[Union[str, UUID]] = None,
        assigned_doctor_id: Optional[Union[str, UUID]] = None
    ) -> User:
        """
        Create new user
        
        Args:
            email: User email
            password: Plain password (will be hashed)
            name: User name
            role: User role
            phone: Phone number
            clinic_id: Clinic ID
            assigned_doctor_id: Assigned doctor ID (for staff role)
        
        Returns:
            Created user object
        """
        hashed_password = get_password_hash(password)
        
        # Convert clinic_id to UUID if it's a string
        clinic_id_uuid = None
        if clinic_id:
            if isinstance(clinic_id, str):
                try:
                    clinic_id_uuid = UUID(clinic_id)
                except ValueError:
                    clinic_id_uuid = None
            elif isinstance(clinic_id, UUID):
                clinic_id_uuid = clinic_id
        
        # If clinic_id is still None, get the DEFAULT clinic
        if not clinic_id_uuid:
            from app.models.user import Clinic
            default_clinic = self.db.query(Clinic).filter(
                Clinic.code == "DEFAULT",
                Clinic.deleted_at.is_(None)
            ).first()
            if default_clinic:
                clinic_id_uuid = default_clinic.id
            else:
                raise ValueError("DEFAULT clinic not found. Please run migrations and seed data first.")
        
        # Convert assigned_doctor_id to UUID if it's a string
        assigned_doctor_id_uuid = None
        if assigned_doctor_id:
            if isinstance(assigned_doctor_id, str):
                try:
                    assigned_doctor_id_uuid = UUID(assigned_doctor_id)
                except ValueError:
                    assigned_doctor_id_uuid = None
            elif isinstance(assigned_doctor_id, UUID):
                assigned_doctor_id_uuid = assigned_doctor_id
        
        user = User(
            email=email.lower(),
            password=hashed_password,
            name=name,
            role=role,
            phone=phone,
            clinic_id=clinic_id_uuid,
            assigned_doctor_id=assigned_doctor_id_uuid,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update(self, user: User, **kwargs) -> User:
        """
        Update user fields
        
        Args:
            user: User object
            **kwargs: Fields to update
        
        Returns:
            Updated user object
        """
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_password(self, user: User, new_password: str) -> User:
        """
        Update user password
        
        Args:
            user: User object
            new_password: New plain password (will be hashed)
        
        Returns:
            Updated user object
        """
        user.password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def verify_password(self, user: User, password: str) -> bool:
        """
        Verify user password
        
        Args:
            user: User object
            password: Plain password to verify
        
        Returns:
            True if password is correct
        """
        return verify_password(password, user.password)
    
    def update_last_login(self, user: User, ip_address: Optional[str] = None) -> User:
        """
        Update last login timestamp and IP
        
        Args:
            user: User object
            ip_address: Client IP address
        
        Returns:
            Updated user object
        """
        user.last_login_at = datetime.utcnow()
        if ip_address:
            user.last_login_ip = ip_address
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def soft_delete(self, user: User) -> User:
        """
        Soft delete user
        
        Modifies the email to free it up for reuse (appends deletion timestamp).
        Original email can be recovered from the modified email if needed.
        
        Args:
            user: User object
        
        Returns:
            Deleted user object
        """
        deleted_at = datetime.utcnow()
        user.deleted_at = deleted_at
        user.is_active = False
        
        # Modify email to free up the original email for reuse
        # Format: deleted_<timestamp>_<original_email>
        # This preserves the original email for reference while freeing the unique constraint
        timestamp = int(deleted_at.timestamp())
        user.email = f"deleted_{timestamp}_{user.email}"
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def restore(self, user: User) -> User:
        """
        Restore soft-deleted user
        
        Restores the original email if it was modified during soft delete.
        Checks if the original email is available before restoring.
        
        Args:
            user: User object
        
        Returns:
            Restored user object
            
        Raises:
            ConflictException: If original email is already taken by another user
        """
        from app.core.exceptions import ConflictException
        
        # Restore original email if it was modified during soft delete
        # Format: deleted_<timestamp>_<original_email>
        if user.email.startswith("deleted_"):
            parts = user.email.split("_", 2)  # Split into ['deleted', 'timestamp', 'original_email']
            if len(parts) == 3:
                original_email = parts[2]
                
                # Check if original email is available (not taken by another active user)
                existing = self.db.query(User).filter(
                    and_(
                        User.email == original_email,
                        User.deleted_at.is_(None),
                        User.id != user.id
                    )
                ).first()
                
                if existing:
                    raise ConflictException(
                        message="Cannot restore user",
                        errors={"email": ["Original email is already taken by another user"]}
                    )
                
                user.email = original_email
        
        user.deleted_at = None
        user.is_active = True
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_all_by_clinic(self, clinic_id: Union[str, UUID], include_inactive: bool = False) -> List[User]:
        """
        Get all users in a clinic
        
        Args:
            clinic_id: Clinic ID
            include_inactive: Include inactive users
        
        Returns:
            List of users
        """
        # Convert clinic_id to UUID if it's a string
        clinic_id_uuid = clinic_id
        if isinstance(clinic_id, str):
            try:
                clinic_id_uuid = UUID(clinic_id)
            except ValueError:
                return []
        elif not isinstance(clinic_id, UUID):
            return []
        
        query = self.db.query(User).filter(
            and_(
                User.clinic_id == clinic_id_uuid,
                User.deleted_at.is_(None)
            )
        )
        
        if not include_inactive:
            query = query.filter(User.is_active == True)
        
        return query.all()
    
    def get_by_role(self, role: str, clinic_id: Optional[Union[str, UUID]] = None) -> List[User]:
        """
        Get users by role
        
        Args:
            role: User role
            clinic_id: Optional clinic ID filter
        
        Returns:
            List of users
        """
        query = self.db.query(User).filter(
            and_(
                User.role == role,
                User.deleted_at.is_(None),
                User.is_active == True
            )
        )
        
        if clinic_id:
            # Convert clinic_id to UUID if it's a string
            clinic_id_uuid = clinic_id
            if isinstance(clinic_id, str):
                try:
                    clinic_id_uuid = UUID(clinic_id)
                except ValueError:
                    return []
            elif not isinstance(clinic_id, UUID):
                return []
            query = query.filter(User.clinic_id == clinic_id_uuid)
        
        return query.all()
    
    def email_exists(self, email: str, exclude_user_id: Optional[Union[str, UUID]] = None) -> bool:
        """
        Check if email already exists
        
        Args:
            email: Email to check
            exclude_user_id: Exclude this user ID from check (for updates)
        
        Returns:
            True if email exists
        """
        query = self.db.query(User).filter(
            and_(
                User.email == email.lower(),
                User.deleted_at.is_(None)
            )
        )
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is not None
    
    def set_verification_token(self, user: User, token: str) -> User:
        """
        Set email verification token
        
        Args:
            user: User object
            token: Verification token
        
        Returns:
            Updated user object
        """
        user.verification_token = token
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def verify_email(self, user: User) -> User:
        """
        Mark email as verified
        
        Args:
            user: User object
        
        Returns:
            Updated user object
        """
        user.is_verified = True
        user.email_verified_at = datetime.utcnow()
        user.verification_token = None
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def set_reset_token(self, user: User, token: str, expires_at: datetime) -> User:
        """
        Set password reset token
        
        Args:
            user: User object
            token: Reset token
            expires_at: Token expiration time
        
        Returns:
            Updated user object
        """
        user.reset_token = token
        user.reset_token_expires_at = expires_at
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def clear_reset_token(self, user: User) -> User:
        """
        Clear password reset token
        
        Args:
            user: User object
        
        Returns:
            Updated user object
        """
        user.reset_token = None
        user.reset_token_expires_at = None
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
