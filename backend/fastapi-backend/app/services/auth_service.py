"""
Authentication service
Business logic for authentication operations
"""

from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta, date
from uuid import UUID
import uuid

from sqlalchemy.orm import Session, joinedload
from loguru import logger

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    UserRole
)
from app.core.redis import redis_client
from app.core.exceptions import (
    UnauthorizedException,
    ValidationException,
    ConflictException,
    NotFoundException
)
from app.core.logging import log_phi_access, log_admin_action
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.profile import UserProfile, ContactDetail
from app.models.location import Country
from app.models.auth import Role
from app.services.login_attempt_service import LoginAttemptService
from app.services.audit_service import AuditService
from app.utils.phone import format_phone_number


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.login_attempt_service = LoginAttemptService(db)
        self.audit_service = AuditService(db)
        self.audit_service = AuditService(db)
    
    def login(
        self,
        email: str,
        password: str,
        role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate user and generate tokens
        
        Args:
            email: User email
            password: User password
            role: (Optional) Expected user role. If provided, validates that the user's role matches.
            ip_address: Client IP address
            user_agent: Client user agent string
        
        Returns:
            Dictionary with user data and tokens
        
        Raises:
            UnauthorizedException: If credentials are invalid or role doesn't match
        """
        # Get user by email with profile eagerly loaded
        user = self.db.query(User).options(joinedload(User.profile)).filter(
            User.email == email.lower(),
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            # Log failed login attempt (non-existent email)
            self.login_attempt_service.log_login_attempt(
                email=email,
                success=False,
                user_id=None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise UnauthorizedException(
                message="Invalid credentials",
                errors={"email": ["Invalid email or password"]}
            )
        
        # Verify password
        if not self.user_repo.verify_password(user, password):
            # Log failed login attempt (wrong password)
            self.login_attempt_service.log_login_attempt(
                email=email,
                success=False,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            logger.warning(f"Failed login attempt for user: {user.id}")
            raise UnauthorizedException(
                message="Invalid credentials",
                errors={"password": ["Invalid email or password"]}
            )
        
        # Check if user is active
        if not user.is_active:
            # Log failed login attempt (inactive account)
            self.login_attempt_service.log_login_attempt(
                email=email,
                success=False,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            logger.warning(f"Login attempt by inactive user: {user.id}")
            raise UnauthorizedException(
                message="Account is inactive",
                errors={"account": ["Your account has been deactivated"]}
            )
        
        # Validate role if provided in request
        if role is not None:
            user_role_lower = user.role.lower() if user.role else None
            requested_role_lower = role.lower()
            
            if user_role_lower != requested_role_lower:
                # Log failed login attempt (role mismatch)
                self.login_attempt_service.log_login_attempt(
                    email=email,
                    success=False,
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                logger.warning(f"Login attempt with role mismatch for user: {user.id} (expected: {requested_role_lower}, actual: {user_role_lower})")
                raise UnauthorizedException(
                    message="Invalid credentials",
                    errors={"role": [f"Invalid credentials for role: {role}"]}
                )
        
        # Update last login
        self.user_repo.update_last_login(user, ip_address)
        
        # Generate tokens
        access_token = self._generate_access_token(user)
        refresh_token = self._generate_refresh_token(user)
        
        # Log successful login attempt
        self.login_attempt_service.log_login_attempt(
            email=email,
            success=True,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Create audit log for successful login
        self.audit_service.create_audit_log(
            actor_user_id=user.id,
            action="login",
            entity_type="user",
            entity_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log successful login
        logger.info(f"User logged in: {str(user.id) if user.id else 'unknown'} ({user.email})")
        
        # Return user data and tokens (Laravel compatible format)
        try:
            user_dict = self._user_to_dict(user)
        except AttributeError as e:
            logger.error(f"Error converting user to dict: {e}")
            logger.error(f"User object: {user}")
            logger.error(f"User attributes: {dir(user)}")
            raise
        
        return {
            "user": user_dict,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
        }
    
    def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        gender: str,
        title: Optional[str] = None,
        middle_name: Optional[str] = None,
        country_id: Optional[UUID] = None,
        mobile_number: Optional[str] = None,
        clinic_id: Optional[Union[str, UUID]] = None
    ) -> Dict[str, Any]:
        """
        Register new patient user
        
        Args:
            email: User email
            password: User password
            first_name: First name
            last_name: Last name
            date_of_birth: Date of birth
            gender: Gender (male, female, other)
            title: Title (optional)
            middle_name: Middle name (optional)
            country_id: Country ID for phone code (optional)
            mobile_number: Mobile number without country code (optional)
            clinic_id: Clinic ID (optional, defaults to DEFAULT clinic)
        
        Returns:
            Dictionary with user data and tokens
        
        Raises:
            ConflictException: If email already exists
            ValidationException: If validation fails
            NotFoundException: If country not found
        """
        # Registration is only for patients
        role = "patient"
        
        # Check if email already exists
        if self.user_repo.email_exists(email):
            raise ConflictException(
                message="Email already registered",
                errors={"email": ["This email is already registered"]}
            )
        
        # Construct full name from name parts
        name_parts = []
        if first_name:
            name_parts.append(first_name)
        if middle_name:
            name_parts.append(middle_name)
        if last_name:
            name_parts.append(last_name)
        name = ' '.join(name_parts) if name_parts else first_name
        
        # Handle phone number with country code
        phone = None
        if mobile_number and country_id:
            # Get country to get phone code
            country = self.db.query(Country).filter(
                Country.id == country_id,
                Country.deleted_at.is_(None)
            ).first()
            
            if not country:
                raise NotFoundException(
                    message="Country not found",
                    errors={"country_id": ["Country does not exist"]}
                )
            
            # Construct phone number with country code in format: +1 (721) 544-2275
            phone_code = str(country.phonecode)
            # Remove any formatting (dashes, spaces, parentheses, plus signs)
            mobile_clean = mobile_number.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "").lstrip('+')
            
            # Validate: Should be 10 digits for NANP format (US/Canada/Sint Maarten)
            if len(mobile_clean) != 10:
                raise ValidationException(
                    message="Invalid phone number format",
                    errors={"mobile_number": [f"Phone number must be exactly 10 digits. Received {len(mobile_clean)} digits."]}
                )
            
            # Format: +1 (721) 544-2275
            phone = format_phone_number(phone_code, mobile_clean)
        
        # Create user (repository will automatically assign DEFAULT clinic if clinic_id is None)
        user = self.user_repo.create(
            email=email,
            password=password,
            name=name,
            role=role,
            phone=phone,
            clinic_id=clinic_id
        )
        
        # Assign patient role to user_roles junction table
        role_obj = self.db.query(Role).filter(Role.name == role).first()
        if role_obj:
            user.roles.append(role_obj)
            logger.info(f"Assigned role '{role}' (id: {role_obj.id}) to user {user.email} in user_roles table")
        else:
            logger.error(f"Role '{role}' not found in roles table. User created but role not assigned.")
        
        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            title=title,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender
        )
        self.db.add(profile)
        
        # Create primary contact detail
        primary_contact = ContactDetail(
            user_id=user.id,
            contact_type="primary",
            is_primary=True,
            email=user.email,
            phone=user.phone,
            country_id=country_id if country_id else None
        )
        self.db.add(primary_contact)
        
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(profile)
        
        # Generate tokens
        access_token = self._generate_access_token(user)
        refresh_token = self._generate_refresh_token(user)
        
        # Log registration
        logger.info(f"New patient registered: {user.id} ({user.email})")
        
        # Return user data and tokens (Laravel compatible format)
        return {
            "user": self._user_to_dict(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
            ip_address: IP address for audit logging (optional)
            user_agent: User agent for audit logging (optional)
        
        Returns:
            Dictionary with new tokens
        
        Raises:
            UnauthorizedException: If refresh token is invalid
        """
        try:
            # Decode refresh token
            payload = decode_token(refresh_token)
            verify_token_type(payload, "refresh")
            
            # Check if token is blacklisted
            token_jti = payload.get("jti")
            if token_jti and redis_client.is_token_blacklisted(token_jti):
                raise UnauthorizedException("Token has been revoked")
            
            # Get user
            user_id = payload.get("user_id")
            user = self.user_repo.get_by_id(user_id)
            
            if not user:
                raise UnauthorizedException("User not found")
            
            if not user.is_active:
                raise UnauthorizedException("Account is inactive")
            
            # Generate new tokens
            new_access_token = self._generate_access_token(user)
            new_refresh_token = self._generate_refresh_token(user)
            
            # Blacklist old refresh token
            if token_jti:
                ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
                redis_client.blacklist_token(token_jti, ttl)
            
            logger.info(f"Tokens refreshed for user: {user.id}")
            
            # HIPAA FIX 3: Add audit log for token refresh
            self.audit_service.create_audit_log(
                actor_user_id=user.id,
                action="TOKEN_REFRESH",
                entity_type="user",
                entity_id=user.id,
                audit_metadata=None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        
        except Exception as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise UnauthorizedException("Invalid refresh token")
    
    def logout(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        user_id: Optional[Union[str, UUID]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Logout user by blacklisting tokens
        
        Args:
            access_token: Access token to blacklist
            refresh_token: Optional refresh token to blacklist
            user_id: User ID for audit logging (optional, extracted from token if not provided)
            ip_address: IP address for audit logging (optional)
            user_agent: User agent for audit logging (optional)
        """
        try:
            # Blacklist access token
            payload = decode_token(access_token)
            access_jti = payload.get("jti")
            
            # Extract user_id from token if not provided
            if not user_id:
                user_id = payload.get("user_id")
            
            if access_jti:
                ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                redis_client.blacklist_token(access_jti, ttl)
            
            # Blacklist refresh token if provided
            if refresh_token:
                refresh_payload = decode_token(refresh_token)
                refresh_jti = refresh_payload.get("jti")
                
                if refresh_jti:
                    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
                    redis_client.blacklist_token(refresh_jti, ttl)
            
            # HIPAA FIX 3: Add audit log for logout
            if user_id:
                self.audit_service.create_audit_log(
                    actor_user_id=user_id,
                    action="LOGOUT",
                    entity_type="user",
                    entity_id=user_id,
                    audit_metadata=None,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            user_id = payload.get("user_id")
            logger.info(f"User logged out: {user_id}")
        
        except Exception as e:
            logger.warning(f"Logout error: {str(e)}")
            # Don't fail logout even if token is invalid
    
    def get_profile(self, user_id: Union[str, UUID]) -> Dict[str, Any]:
        """
        Get user profile
        
        Args:
            user_id: User ID
        
        Returns:
            User profile dictionary
        
        Raises:
            NotFoundException: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundException("User not found")
        
        # Log PHI access
        log_phi_access(
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            action="view_profile"
        )
        
        return self._user_to_dict(user)
    
    def update_profile(
        self,
        user_id: Union[str, UUID],
        name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user profile
        
        Args:
            user_id: User ID
            name: New name
            phone: New phone
        
        Returns:
            Updated user profile
        
        Raises:
            NotFoundException: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundException("User not found")
        
        # Update fields
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if phone is not None:
            update_data["phone"] = phone
        
        if update_data:
            user = self.user_repo.update(user, **update_data)
            logger.info(f"Profile updated for user: {user_id}")
        
        # Log PHI access
        log_phi_access(
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            action="update_profile"
        )
        
        return self._user_to_dict(user)
    
    def change_password(
        self,
        user_id: Union[str, UUID],
        current_password: str,
        new_password: str
    ):
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
        
        Raises:
            NotFoundException: If user not found
            UnauthorizedException: If current password is incorrect
        """
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundException("User not found")
        
        # Verify current password
        if not self.user_repo.verify_password(user, current_password):
            raise UnauthorizedException(
                message="Current password is incorrect",
                errors={"current_password": ["Current password is incorrect"]}
            )
        
        # Update password
        self.user_repo.update_password(user, new_password)
        
        logger.info(f"Password changed for user: {user_id}")
        
        # Log admin action (password change is security-sensitive)
        log_admin_action(
            user_id=user_id,
            action="change_password",
            resource_type="user",
            resource_id=user_id
        )
    
    def _generate_access_token(self, user: User) -> str:
        """Generate access token for user"""
        token_data = {
            "user_id": str(user.id) if user.id else None,  # Convert UUID to string
            "email": user.email,
            "role": user.role,
            "clinic_id": str(user.clinic_id) if user.clinic_id else None,  # Convert UUID to string
            "jti": str(uuid.uuid4())  # JWT ID for blacklisting
        }
        
        return create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
    
    def _generate_refresh_token(self, user: User) -> str:
        """Generate refresh token for user"""
        token_data = {
            "user_id": str(user.id) if user.id else None,  # Convert UUID to string
            "email": user.email,
            "role": user.role,
            "clinic_id": str(user.clinic_id) if user.clinic_id else None,  # Convert UUID to string
            "jti": str(uuid.uuid4())  # JWT ID for blacklisting
        }
        
        return create_refresh_token(
            data=token_data,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
    
    def _is_profile_complete(self, user: User) -> bool:
        """
        Check if user profile is complete
        
        Profile is considered complete if:
        - User role is 'staff' (always complete)
        - OR: first_name is not null/empty AND gender is not null/empty AND date_of_birth is not null
        
        Args:
            user: User object (with profile relationship loaded via joinedload)
            
        Returns:
            True if profile is complete, False otherwise
        """
        try:
            # Staff users always have complete profiles
            if user.role == 'staff':
                return True
            
            # Access profile via relationship (should be loaded via joinedload in login method)
            profile = user.profile
            
            # If no profile exists, return False
            if profile is None:
                return False
            
            # Check required fields
            first_name = getattr(profile, 'first_name', None)
            gender = getattr(profile, 'gender', None)
            date_of_birth = getattr(profile, 'date_of_birth', None)
            
            # Profile is complete if all three fields are present and not empty
            is_complete = (
                first_name is not None and str(first_name).strip() != "" and
                gender is not None and str(gender).strip() != "" and
                date_of_birth is not None
            )
            
            return is_complete
        except Exception as e:
            logger.warning(f"Error checking profile completion for user {user.id}: {e}")
            return False
    
    def _get_avatar_url(self, avatar_path: Optional[str]) -> Optional[str]:
        """
        Generate full URL for avatar image
        
        Args:
            avatar_path: Relative path to avatar (e.g., "uploads/avatars/user_id.jpg")
        
        Returns:
            Full URL (e.g., "http://localhost:8000/uploads/avatars/user_id.jpg") or None
        """
        if not avatar_path:
            return None
        
        # Remove leading slash if present
        avatar_path = avatar_path.lstrip('/')
        
        # Construct full URL
        base_url = settings.BASE_URL.rstrip('/')
        return f"{base_url}/{avatar_path}"
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert user to dictionary (safe, no sensitive data)"""
        # Safely access all attributes with fallbacks
        try:
            # Check if profile is complete
            is_profile_complete = self._is_profile_complete(user)
            
            # Get HIPAA form status from profile
            hipaa_form_filled = False
            if hasattr(user, 'profile') and user.profile:
                hipaa_form_filled = getattr(user.profile, 'hipaa_form_filled', False)
            else:
                # Query profile if not loaded via relationship
                profile = self.db.query(UserProfile).filter(
                    UserProfile.user_id == user.id,
                    UserProfile.deleted_at.is_(None)
                ).first()
                if profile:
                    hipaa_form_filled = getattr(profile, 'hipaa_form_filled', False)
            
            return {
                "id": str(user.id) if hasattr(user, 'id') and user.id else None,
                "email": getattr(user, 'email', None),
                "name": getattr(user, 'name', None),
                "phone": getattr(user, 'phone', None),
                "role": getattr(user, 'role', None),
                "clinic_id": str(user.clinic_id) if hasattr(user, 'clinic_id') and user.clinic_id else None,
                "is_active": getattr(user, 'is_active', True),
                "is_verified": getattr(user, 'is_verified', False),
                "email_verified_at": user.email_verified_at.isoformat() if hasattr(user, 'email_verified_at') and user.email_verified_at else None,
                "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None,
                "last_login_at": user.last_login_at.isoformat() if hasattr(user, 'last_login_at') and user.last_login_at else None,
                "avatar": self._get_avatar_url(getattr(user, 'avatar', None)),
                "is_profile_complete": is_profile_complete,
                "hipaa_form_filled": hipaa_form_filled
            }
        except AttributeError as e:
            logger.error(f"AttributeError in _user_to_dict: {e}")
            logger.error(f"User type: {type(user)}")
            logger.error(f"User has id: {hasattr(user, 'id')}")
            logger.error(f"User dir: {[attr for attr in dir(user) if not attr.startswith('_')]}")
            raise
