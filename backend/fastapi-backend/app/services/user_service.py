"""
User management service
Business logic for user management operations
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from loguru import logger

from app.core.config import settings
from app.core.security import UserRole
from app.core.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    ValidationException
)
from app.core.logging import log_admin_action, log_phi_access
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.auth import Role
from app.models.profile import UserProfile, user_medical_services
from app.models.medical_service import MedicalService
from app.services.notification.dispatcher import get_notification_dispatcher
from app.utils.encryption import get_encryption_service


class UserService:
    """Service for user management operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def get_all_users(
        self,
        current_user_id: Union[str, UUID],
        current_user_role: str,
        current_user_clinic_id: Optional[Union[str, UUID]],
        page: int = 1,
        per_page: int = 20,
        role_filter: Optional[str] = None,
        is_active_filter: Optional[bool] = None,
        search: Optional[str] = None,
        clinic_id_filter: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get all users with pagination and filters
        
        Args:
            current_user_id: Current user ID
            current_user_role: Current user role
            current_user_clinic_id: Current user clinic ID
            page: Page number
            per_page: Items per page
            role_filter: Filter by role
            is_active_filter: Filter by active status
            search: Search by name or email
            clinic_id_filter: Filter by clinic ID
        
        Returns:
            Dictionary with users list and pagination info
        
        Raises:
            ForbiddenException: If user doesn't have permission
        """
        # Only admins can view user list
        if current_user_role not in ['super_admin', 'clinic_admin']:
            raise ForbiddenException("Only admins can view user list")
        
        # Build query
        query = self.db.query(User).filter(User.deleted_at.is_(None))
        
        # Clinic admins can only see users in their clinic
        if current_user_role == 'clinic_admin' and current_user_clinic_id:
            # Convert to UUID if string
            clinic_id_uuid = current_user_clinic_id
            if isinstance(current_user_clinic_id, str):
                try:
                    clinic_id_uuid = UUID(current_user_clinic_id)
                except ValueError:
                    pass
            query = query.filter(User.clinic_id == clinic_id_uuid)
        
        # Super admins can filter by clinic
        if current_user_role == 'super_admin' and clinic_id_filter is not None:
            # Convert to UUID if string
            filter_clinic_id = clinic_id_filter
            if isinstance(clinic_id_filter, str):
                try:
                    filter_clinic_id = UUID(clinic_id_filter)
                except ValueError:
                    pass
            query = query.filter(User.clinic_id == filter_clinic_id)
        
        # Apply filters
        if role_filter and role_filter.strip():
            r = role_filter.strip().lower()
            query = query.filter(func.lower(User.role) == r)
        
        if is_active_filter is not None:
            query = query.filter(User.is_active == is_active_filter)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.order_by(User.created_at.desc()).offset(offset).limit(per_page).all()
        
        # Convert to dict
        users_data = [self._user_to_dict(user) for user in users]
        
        # Log PHI access
        log_phi_access(
            user_id=current_user_id,
            resource_type="users",
            resource_id=0,  # List operation
            action="list"
        )
        
        return {
            "users": users_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    def get_user_by_id(
        self,
        user_id: Union[str, UUID],
        current_user_id: Union[str, UUID],
        current_user_role: str,
        current_user_clinic_id: Optional[Union[str, UUID]]
    ) -> Dict[str, Any]:
        """
        Get user by ID
        
        Args:
            user_id: User ID to retrieve
            current_user_id: Current user ID
            current_user_role: Current user role
            current_user_clinic_id: Current user clinic ID
        
        Returns:
            User dictionary
        
        Raises:
            NotFoundException: If user not found
            ForbiddenException: If user doesn't have permission
        """
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundException("User not found")
        
        # Check permissions
        # Users can view their own profile
        # Convert both to strings for comparison
        user_id_str = str(user_id) if isinstance(user_id, UUID) else user_id
        current_user_id_str = str(current_user_id) if isinstance(current_user_id, UUID) else current_user_id
        if user_id_str != current_user_id_str:
            # Admins can view any user
            if current_user_role not in ['super_admin', 'clinic_admin']:
                raise ForbiddenException("You don't have permission to view this user")
            
            # Clinic admins can only view users in their clinic
            if current_user_role == 'clinic_admin':
                if user.clinic_id != current_user_clinic_id:
                    raise ForbiddenException("You can only view users in your clinic")
        
        # Log PHI access
        log_phi_access(
            user_id=current_user_id,
            resource_type="user",
            resource_id=user_id,
            action="view"
        )
        
        return self._user_to_response_dict(user)
    
    def create_user(
        self,
        email: str,
        password: str,
        name: str,
        role: str,
        phone: Optional[str],
        clinic_id: Optional[Union[str, UUID]],
        assigned_doctor_id: Optional[Union[str, UUID]],
        is_active: bool,
        current_user_id: Union[str, UUID],
        current_user_role: str,
        current_user_clinic_id: Optional[Union[str, UUID]],
        education: Optional[str] = None,
        years_of_experience: Optional[int] = None,
        specializations: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Create new user (admin only).
        When role is doctor, education, years_of_experience and specializations are required
        (enforced by schema) and a UserProfile plus user_medical_services are created.
        
        Args:
            email: User email
            password: User password
            name: User name
            role: User role
            phone: Phone number
            clinic_id: Clinic ID
            assigned_doctor_id: Assigned doctor ID (required for staff role)
            is_active: Active status
            current_user_id: Current user ID
            current_user_role: Current user role
            current_user_clinic_id: Current user clinic ID
            education: Doctor education (required when role is doctor)
            years_of_experience: Doctor years of experience (required when role is doctor)
            specializations: List of medical service IDs (required when role is doctor)
        
        Returns:
            Created user dictionary
        
        Raises:
            ForbiddenException: If user doesn't have permission
            ConflictException: If email already exists
            ValidationException: If assigned_doctor_id or doctor fields validation fails
        """
        # Only admins can create users
        if current_user_role not in ['super_admin', 'clinic_admin']:
            raise ForbiddenException("Only admins can create users")
        
        # Clinic admins can only create users in their clinic
        if current_user_role == 'clinic_admin':
            if clinic_id and clinic_id != current_user_clinic_id:
                raise ForbiddenException("You can only create users in your clinic")
            clinic_id = current_user_clinic_id
        
        # Check if email already exists
        if self.user_repo.email_exists(email):
            raise ConflictException(
                message="Email already exists",
                errors={"email": ["This email is already registered"]}
            )
        
        # Validate role
        try:
            UserRole(role)
        except ValueError:
            raise ValidationException(
                message="Invalid role",
                errors={"role": [f"Invalid role: {role}"]}
            )
        
        # Validate assigned_doctor_id for staff role
        if role == 'staff':
            if not assigned_doctor_id:
                raise ValidationException(
                    message="Assigned doctor is required",
                    errors={"assigned_doctor_id": ["assigned_doctor_id is required when role is 'staff'"]}
                )
            
            # Verify that assigned_doctor_id is a valid doctor
            doctor = self.db.query(User).filter(
                User.id == assigned_doctor_id,
                User.role == 'doctor',
                User.deleted_at.is_(None)
            ).first()
            
            if not doctor:
                raise ValidationException(
                    message="Invalid assigned doctor",
                    errors={"assigned_doctor_id": ["The assigned doctor ID does not exist or is not a doctor"]}
                )
            
            # Verify clinic admins can only assign doctors from their clinic
            if current_user_role == 'clinic_admin':
                if doctor.clinic_id != current_user_clinic_id:
                    raise ForbiddenException("You can only assign doctors from your clinic")
        elif assigned_doctor_id:
            # assigned_doctor_id should only be set for staff role
            raise ValidationException(
                message="Invalid assignment",
                errors={"assigned_doctor_id": ["assigned_doctor_id can only be set when role is 'staff'"]}
            )
        
        # Create user (repository will automatically assign DEFAULT clinic if clinic_id is None)
        user = self.user_repo.create(
            email=email,
            password=password,
            name=name,
            role=role,
            phone=phone,
            clinic_id=clinic_id,
            assigned_doctor_id=assigned_doctor_id
        )
        
        # Set active status
        if not is_active:
            user.is_active = False
        
        # Assign role to user_roles junction table
        # Find the Role by name (handle 'admin' -> 'super_admin' mapping for backward compatibility)
        role_name = role
        if role == "admin":
            role_name = "super_admin"  # Map 'admin' to 'super_admin'
        
        role_obj = self.db.query(Role).filter(Role.name == role_name).first()
        if role_obj:
            # Add role to user's roles relationship
            user.roles.append(role_obj)
            logger.info(f"Assigned role '{role_name}' (id: {role_obj.id}) to user {user.email} in user_roles table")
        else:
            logger.error(f"Role '{role_name}' not found in roles table. User created but role not assigned in user_roles table.")
            # Try to create the role if it doesn't exist (shouldn't happen, but safety net)
            try:
                new_role = Role(name=role_name, guard_name="web")
                self.db.add(new_role)
                self.db.flush()
                user.roles.append(new_role)
                logger.info(f"Created and assigned role '{role_name}' to user {user.email}")
            except Exception as e:
                logger.error(f"Failed to create role '{role_name}': {str(e)}")
        
        self.db.commit()
        self.db.refresh(user)
        
        # When role is doctor, create UserProfile (education, years_of_experience) and specializations
        if role == "doctor" and (education is not None or years_of_experience is not None or (specializations and len(specializations) > 0)):
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
            if not profile:
                # Use first name from name for profile (e.g. "Dr. John Doe" -> "Dr. John Doe" or split)
                first_name = (name or "").strip() or None
                profile = UserProfile(
                    user_id=user.id,
                    first_name=first_name,
                    education=education,
                    years_of_experience=years_of_experience,
                )
                self.db.add(profile)
                self.db.flush()
            else:
                if education is not None:
                    profile.education = education
                if years_of_experience is not None:
                    profile.years_of_experience = years_of_experience
                self.db.add(profile)
            
            if specializations and len(specializations) > 0:
                seen = set()
                for service_id in specializations:
                    if service_id in seen:
                        continue
                    seen.add(service_id)
                    service = self.db.query(MedicalService).filter(
                        MedicalService.id == service_id,
                        MedicalService.status == True,
                    ).first()
                    if service:
                        self.db.execute(
                            user_medical_services.insert().values(
                                user_id=user.id,
                                medical_service_id=service_id,
                            )
                        )
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Doctor profile and specializations set for user {user.id}")
        
        # Log admin action (HIPAA FIX 2: Remove email from audit_metadata)
        log_admin_action(
            user_id=current_user_id,
            action="create_user",
            resource_type="user",
            resource_id=user.id,
            changes={
                "name": name,
                "role": role,
                "clinic_id": str(clinic_id) if clinic_id else None,
                "is_active": is_active
            }
        )
        
        logger.info(f"User created: {user.id} by admin: {current_user_id}")
        
        # Note: Email sending is now handled by FastAPI BackgroundTasks in the endpoint
        # This ensures proper async execution without blocking user creation
        
        return self._user_to_response_dict(user)
    
    def update_user(
        self,
        user_id: Union[str, UUID],
        email: Optional[str],
        name: Optional[str],
        phone: Optional[str],
        role: Optional[str],
        clinic_id: Optional[Union[str, UUID]],
        assigned_doctor_id: Optional[Union[str, UUID]],
        is_active: Optional[bool],
        current_user_id: Union[str, UUID],
        current_user_role: str,
        current_user_clinic_id: Optional[Union[str, UUID]],
        education: Optional[str] = None,
        years_of_experience: Optional[int] = None,
        specializations: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Update user (admin only).
        When the user is a doctor, education, years_of_experience and specializations
        can be updated (same as doctor profile).
        
        Args:
            user_id: User ID to update
            email: New email
            name: New name
            phone: New phone
            role: New role
            clinic_id: New clinic ID
            assigned_doctor_id: New assigned doctor ID
            is_active: New active status
            current_user_id: Current user ID
            current_user_role: Current user role
            current_user_clinic_id: Current user clinic ID
            education: Doctor education (optional)
            years_of_experience: Doctor years of experience (optional)
            specializations: List of medical service IDs; replaces existing when provided (optional)
        
        Returns:
            Updated user dictionary
        
        Raises:
            ForbiddenException: If user doesn't have permission
            NotFoundException: If user not found
            ValidationException: If assigned_doctor_id validation fails
        """
        # Only admins can update users
        if current_user_role not in ['super_admin', 'clinic_admin']:
            raise ForbiddenException("Only admins can update users")
        
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundException("User not found")
        
        # Determine the effective role (use new role if provided, otherwise current role)
        effective_role = role if role is not None else user.role
        
        # Validate assigned_doctor_id for staff role
        if effective_role == 'staff':
            # If assigned_doctor_id is being set/updated, validate it
            if assigned_doctor_id is not None:
                # Verify that assigned_doctor_id is a valid doctor
                doctor = self.db.query(User).filter(
                    User.id == assigned_doctor_id,
                    User.role == 'doctor',
                    User.deleted_at.is_(None)
                ).first()
                
                if not doctor:
                    raise ValidationException(
                        message="Invalid assigned doctor",
                        errors={"assigned_doctor_id": ["The assigned doctor ID does not exist or is not a doctor"]}
                    )
                
                # Verify clinic admins can only assign doctors from their clinic
                if current_user_role == 'clinic_admin':
                    if doctor.clinic_id != current_user_clinic_id:
                        raise ForbiddenException("You can only assign doctors from your clinic")
            elif role == 'staff' and user.role != 'staff':
                # Role is being changed to staff, but assigned_doctor_id not provided
                raise ValidationException(
                    message="Assigned doctor is required",
                    errors={"assigned_doctor_id": ["assigned_doctor_id is required when role is 'staff'"]}
                )
        elif assigned_doctor_id is not None:
            # assigned_doctor_id should only be set for staff role
            raise ValidationException(
                message="Invalid assignment",
                errors={"assigned_doctor_id": ["assigned_doctor_id can only be set when role is 'staff'"]}
            )
        
        # Clinic admins can only update users in their clinic
        if current_user_role == 'clinic_admin':
            user_clinic_id_str = str(user.clinic_id) if user.clinic_id else None
            current_clinic_id_str = str(current_user_clinic_id) if current_user_clinic_id and isinstance(current_user_clinic_id, UUID) else current_user_clinic_id
            if user_clinic_id_str != current_clinic_id_str:
                raise ForbiddenException("You can only update users in your clinic")
        
        # Track changes for audit log
        changes = {}
        
        # Update fields
        if email is not None and email != user.email:
            # Check if new email already exists
            if self.user_repo.email_exists(email, exclude_user_id=user_id):
                raise ConflictException(
                    message="Email already exists",
                    errors={"email": ["This email is already registered"]}
                )
            changes["email"] = {"from": user.email, "to": email}
            user.email = email
        
        if name is not None and name != user.name:
            changes["name"] = {"from": user.name, "to": name}
            user.name = name
        
        if phone is not None and phone != user.phone:
            changes["phone"] = {"from": user.phone, "to": phone}
            user.phone = phone
        
        if role is not None and role != user.role:
            # Validate role
            try:
                UserRole(role)
            except ValueError:
                raise ValidationException(
                    message="Invalid role",
                    errors={"role": [f"Invalid role: {role}"]}
                )
            changes["role"] = {"from": user.role, "to": role}
            user.role = role
        
        if assigned_doctor_id is not None:
            # Convert assigned_doctor_id to UUID if it's a string
            assigned_doctor_id_uuid = assigned_doctor_id
            if isinstance(assigned_doctor_id, str):
                try:
                    assigned_doctor_id_uuid = UUID(assigned_doctor_id)
                except ValueError:
                    raise ValidationException("Invalid assigned_doctor_id format")
            elif not isinstance(assigned_doctor_id, UUID):
                assigned_doctor_id_uuid = UUID(str(assigned_doctor_id))
            
            user_assigned_doctor_id_str = str(user.assigned_doctor_id) if user.assigned_doctor_id else None
            assigned_doctor_id_str = str(assigned_doctor_id_uuid)
            
            if user_assigned_doctor_id_str != assigned_doctor_id_str:
                changes["assigned_doctor_id"] = {"from": user_assigned_doctor_id_str, "to": assigned_doctor_id_str}
                user.assigned_doctor_id = assigned_doctor_id_uuid
        elif effective_role != 'staff' and user.assigned_doctor_id is not None:
            # Clear assigned_doctor_id if role is being changed away from staff
            changes["assigned_doctor_id"] = {"from": str(user.assigned_doctor_id), "to": None}
            user.assigned_doctor_id = None
        
        if clinic_id is not None:
            # Convert clinic_id to UUID if it's a string
            clinic_id_uuid = clinic_id
            if isinstance(clinic_id, str):
                try:
                    clinic_id_uuid = UUID(clinic_id)
                except ValueError:
                    raise ValidationException("Invalid clinic_id format")
            elif not isinstance(clinic_id, UUID):
                clinic_id_uuid = UUID(str(clinic_id))
            
            user_clinic_id_str = str(user.clinic_id) if user.clinic_id else None
            clinic_id_str = str(clinic_id_uuid)
            
            if user_clinic_id_str != clinic_id_str:
                # Only super admin can change clinic
                if current_user_role != 'super_admin':
                    raise ForbiddenException("Only super admin can change user clinic")
                changes["clinic_id"] = {"from": user.clinic_id, "to": clinic_id_uuid}
                user.clinic_id = clinic_id_uuid
        
        if is_active is not None and is_active != user.is_active:
            changes["is_active"] = {"from": user.is_active, "to": is_active}
            user.is_active = is_active
        
        if changes:
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            
            # Log admin action
            log_admin_action(
                user_id=current_user_id,
                action="update_user",
                resource_type="user",
                resource_id=user_id,
                changes=changes
            )
        
        # When user is a doctor, update profile (education, years_of_experience) and/or specializations if provided
        if effective_role == "doctor" and (
            education is not None or years_of_experience is not None or specializations is not None
        ):
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
            if not profile:
                profile = UserProfile(
                    user_id=user.id,
                    first_name=(user.name or "").strip() or None,
                    education=education,
                    years_of_experience=years_of_experience,
                )
                self.db.add(profile)
                self.db.flush()
            else:
                if education is not None:
                    profile.education = education
                if years_of_experience is not None:
                    profile.years_of_experience = years_of_experience
                self.db.add(profile)
            
            if specializations is not None:
                self.db.execute(
                    user_medical_services.delete().where(user_medical_services.c.user_id == user.id)
                )
                seen = set()
                for service_id in specializations:
                    if service_id in seen:
                        continue
                    seen.add(service_id)
                    service = self.db.query(MedicalService).filter(
                        MedicalService.id == service_id,
                        MedicalService.status == True,
                    ).first()
                    if service:
                        self.db.execute(
                            user_medical_services.insert().values(
                                user_id=user.id,
                                medical_service_id=service_id,
                            )
                        )
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Doctor profile/specializations updated for user {user.id}")
            
            logger.info(f"User updated: {user_id} by admin: {current_user_id}")
        
        return self._user_to_response_dict(user)
    
    def delete_user(
        self,
        user_id: Union[str, UUID],
        current_user_id: Union[str, UUID],
        current_user_role: str,
        current_user_clinic_id: Optional[Union[str, UUID]]
    ):
        """
        Soft delete user (admin only)
        
        Args:
            user_id: User ID to delete
            current_user_id: Current user ID
            current_user_role: Current user role
            current_user_clinic_id: Current user clinic ID
        
        Raises:
            ForbiddenException: If user doesn't have permission
            NotFoundException: If user not found
            ValidationException: If trying to delete self
        """
        # Only admins can delete users
        if current_user_role not in ['super_admin', 'clinic_admin']:
            raise ForbiddenException("Only admins can delete users")
        
        # Cannot delete self
        user_id_str = str(user_id) if isinstance(user_id, UUID) else user_id
        current_user_id_str = str(current_user_id) if isinstance(current_user_id, UUID) else current_user_id
        if user_id_str == current_user_id_str:
            raise ValidationException(
                message="Cannot delete yourself",
                errors={"user": ["You cannot delete your own account"]}
            )
        
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundException("User not found")
        
        # Clinic admins can only delete users in their clinic
        if current_user_role == 'clinic_admin':
            if user.clinic_id != current_user_clinic_id:
                raise ForbiddenException("You can only delete users in your clinic")
        
        # Soft delete
        self.user_repo.soft_delete(user)
        
        # Log admin action
        log_admin_action(
            user_id=current_user_id,
            action="delete_user",
            resource_type="user",
            resource_id=user_id,
            changes={"deleted_at": datetime.utcnow().isoformat()}
        )
        
        logger.info(f"User deleted: {user_id} by admin: {current_user_id}")
    
    def activate_deactivate_user(
        self,
        user_id: Union[str, UUID],
        is_active: bool,
        reason: Optional[str],
        current_user_id: Union[str, UUID],
        current_user_role: str,
        current_user_clinic_id: Optional[Union[str, UUID]],
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Activate or deactivate user (admin only)
        
        Args:
            user_id: User ID
            is_active: Active status
            reason: Reason for status change
            current_user_id: Current user ID
            current_user_role: Current user role
            current_user_clinic_id: Current user clinic ID
            ip_address: Client IP address
        
        Returns:
            Updated user dictionary
        
        Raises:
            ForbiddenException: If user doesn't have permission
            NotFoundException: If user not found
        """
        # Only admins can activate/deactivate users
        if current_user_role not in ['super_admin', 'clinic_admin']:
            raise ForbiddenException("Only admins can activate/deactivate users")
        
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundException("User not found")
        
        # Clinic admins can only manage users in their clinic
        if current_user_role == 'clinic_admin':
            user_clinic_id_str = str(user.clinic_id) if user.clinic_id else None
            current_clinic_id_str = str(current_user_clinic_id) if current_user_clinic_id and isinstance(current_user_clinic_id, UUID) else current_user_clinic_id
            if user_clinic_id_str != current_clinic_id_str:
                raise ForbiddenException("You can only manage users in your clinic")
        
        # Update status
        old_status = user.is_active
        user.is_active = is_active
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        # Log admin action with reason
        action = "activate_user" if is_active else "deactivate_user"
        log_admin_action(
            user_id=current_user_id,
            action=action,
            resource_type="user",
            resource_id=user_id,
            changes={
                "is_active": {"from": old_status, "to": is_active},
                "reason": reason,
                "ip_address": ip_address
            }
        )
        
        logger.info(f"User {action}: {user_id} by admin: {current_user_id}, reason: {reason}")
        
        return self._user_to_response_dict(user)
    
    def change_user_role(
        self,
        user_id: Union[str, UUID],
        new_role: str,
        reason: Optional[str],
        current_user_id: Union[str, UUID],
        current_user_role: str,
        current_user_clinic_id: Optional[Union[str, UUID]],
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Change user role (admin only)
        
        Args:
            user_id: User ID
            new_role: New role
            reason: Reason for role change
            current_user_id: Current user ID
            current_user_role: Current user role
            current_user_clinic_id: Current user clinic ID
            ip_address: Client IP address
        
        Returns:
            Updated user dictionary
        
        Raises:
            ForbiddenException: If user doesn't have permission
            NotFoundException: If user not found
            ValidationException: If invalid role
        """
        # Only admins can change roles
        if current_user_role not in ['super_admin', 'clinic_admin']:
            raise ForbiddenException("Only admins can change user roles")
        
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundException("User not found")
        
        # Clinic admins can only manage users in their clinic
        if current_user_role == 'clinic_admin':
            user_clinic_id_str = str(user.clinic_id) if user.clinic_id else None
            current_clinic_id_str = str(current_user_clinic_id) if current_user_clinic_id and isinstance(current_user_clinic_id, UUID) else current_user_clinic_id
            if user_clinic_id_str != current_clinic_id_str:
                raise ForbiddenException("You can only manage users in your clinic")
            
            # Clinic admins cannot create super admins
            if new_role == 'super_admin':
                raise ForbiddenException("Clinic admins cannot assign super admin role")
        
        # Validate role
        try:
            UserRole(new_role)
        except ValueError:
            raise ValidationException(
                message="Invalid role",
                errors={"role": [f"Invalid role: {new_role}"]}
            )
        
        # Update role
        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        # Log admin action with reason
        log_admin_action(
            user_id=current_user_id,
            action="change_user_role",
            resource_type="user",
            resource_id=user_id,
            changes={
                "role": {"from": old_role, "to": new_role},
                "reason": reason,
                "ip_address": ip_address
            }
        )
        
        logger.info(f"User role changed: {user_id} from {old_role} to {new_role} by admin: {current_user_id}, reason: {reason}")
        
        return self._user_to_response_dict(user)
    
    def get_user_statistics(
        self,
        current_user_role: str,
        current_user_clinic_id: Optional[Union[str, UUID]]
    ) -> Dict[str, Any]:
        """
        Get user statistics
        
        Args:
            current_user_role: Current user role
            current_user_clinic_id: Current user clinic ID
        
        Returns:
            Statistics dictionary
        
        Raises:
            ForbiddenException: If user doesn't have permission
        """
        # Only admins can view statistics
        if current_user_role not in ['super_admin', 'clinic_admin']:
            raise ForbiddenException("Only admins can view statistics")
        
        # Base query
        query = self.db.query(User).filter(User.deleted_at.is_(None))
        
        # Clinic admins can only see stats for their clinic
        if current_user_role == 'clinic_admin' and current_user_clinic_id:
            # Convert to UUID if string
            clinic_id_uuid = current_user_clinic_id
            if isinstance(current_user_clinic_id, str):
                try:
                    clinic_id_uuid = UUID(current_user_clinic_id)
                except ValueError:
                    pass
            query = query.filter(User.clinic_id == clinic_id_uuid)
        
        # Total users
        total_users = query.count()
        
        # Active users
        active_users = query.filter(User.is_active == True).count()
        
        # Inactive users
        inactive_users = total_users - active_users
        
        # By role
        by_role = {}
        roles = ['super_admin', 'clinic_admin', 'doctor', 'nurse', 'staff', 'receptionist', 'patient']
        
        for role in roles:
            count = query.filter(User.role == role).count()
            if count > 0:
                by_role[role] = count
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "by_role": by_role
        }
    
    async def _send_user_creation_email(self, user: User, password: str) -> None:
        """
        Send welcome email to newly created user with login credentials
        
        Args:
            user: Created user object
            password: Plain text password (only sent once in welcome email)
        """
        try:
            # Get notification dispatcher
            encryption_service = get_encryption_service()
            dispatcher = get_notification_dispatcher(self.db, encryption_service)
            
            # Check if email channel is enabled
            if not dispatcher.is_channel_enabled("email"):
                logger.warning(f"Email channel is disabled. Skipping welcome email to {user.email}")
                return
            
            # Prepare email content
            subject = f"Welcome to {settings.SMTP_FROM_NAME or 'eClinic'} - Your Account Details"
            
            # HTML email template
            message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Welcome to {settings.SMTP_FROM_NAME or 'eClinic'}!</h2>
                    
                    <p>Hello {user.name or 'User'},</p>
                    
                    <p>Your account has been created successfully. Please use the following credentials to log in and complete your profile:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Email:</strong> {user.email}</p>
                        <p style="margin: 5px 0;"><strong>Password:</strong> {password}</p>
                    </div>
                    
                    <p><strong>Important:</strong> Please log in and complete your profile. The following fields are required:</p>
                    <ul>
                        <li>Name (First Name, Last Name)</li>
                        <li>Gender</li>
                        <li>Date of Birth</li>
                    </ul>
                    
                    <p>For security reasons, we recommend changing your password after your first login.</p>
                    
                    <p style="margin-top: 30px;">Best regards,<br>{settings.SMTP_FROM_NAME or 'eClinic Team'}</p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            await dispatcher.send_email(
                email=user.email,
                message=message,
                subject=subject
            )
            
            logger.info(f"Welcome email sent successfully to {user.email}")
            
        except Exception as e:
            # Log error but don't raise - user creation should succeed even if email fails
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert user to dictionary (safe, no sensitive data)"""
        return {
            "id": str(user.id) if user.id else None,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "role": user.role,
            "clinic_id": str(user.clinic_id) if user.clinic_id else None,
            "assigned_doctor_id": str(user.assigned_doctor_id) if user.assigned_doctor_id else None,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "email_verified_at": user.email_verified_at.isoformat() if user.email_verified_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "avatar": user.avatar
        }

    def _enrich_user_dict_doctor_fields(self, user: User, data: Dict[str, Any]) -> None:
        """Add education, years_of_experience, and specializations to user dict when role is doctor. Modifies data in place."""
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if profile:
            data["education"] = profile.education
            data["years_of_experience"] = profile.years_of_experience
        else:
            data["education"] = None
            data["years_of_experience"] = None
        rows = self.db.execute(
            user_medical_services.select().where(user_medical_services.c.user_id == user.id)
        ).all()
        data["specializations"] = [str(r.medical_service_id) for r in rows] if rows else []

    def _user_to_response_dict(self, user: User) -> Dict[str, Any]:
        """Convert user to response dict; includes doctor fields (education, years_of_experience, specializations) when role is doctor."""
        data = self._user_to_dict(user)
        if user.role == "doctor":
            self._enrich_user_dict_doctor_fields(user, data)
        return data
