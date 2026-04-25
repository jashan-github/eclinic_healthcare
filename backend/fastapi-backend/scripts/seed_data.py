#!/usr/bin/env python3
"""
Seed data script for local testing
Creates initial roles, admin user, and notification settings
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash, UserRole
from app.models.auth import Role
from app.models.user import User, Clinic
from app.models.notification import NotificationSetting
from app.models.auth import user_roles
from loguru import logger


def seed_roles(db: Session) -> dict[str, Role]:
    """Create default roles with metadata"""
    logger.info("Creating roles...")
    
    # Role metadata: display_name, description, permissions
    roles_metadata = {
        UserRole.SUPER_ADMIN.value: {
            "display_name": "Super Administrator",
            "description": "Full system access across all clinics",
            "permissions": ["all"]
        },
        UserRole.CLINIC_ADMIN.value: {
            "display_name": "Clinic Administrator",
            "description": "Full access within assigned clinic",
            "permissions": ["manage_users", "manage_clinic_settings", "view_all_reports"]
        },
        UserRole.DOCTOR.value: {
            "display_name": "Doctor",
            "description": "Medical professional with full patient care access",
            "permissions": ["view_patients", "create_prescriptions", "view_appointments", "create_medical_records"]
        },
        UserRole.NURSE.value: {
            "display_name": "Nurse",
            "description": "Healthcare professional with patient care support access",
            "permissions": ["view_patients", "view_prescriptions", "update_vital_signs", "view_appointments"]
        },
        UserRole.STAFF.value: {
            "display_name": "Staff",
            "description": "General staff member with patient care support access",
            "permissions": ["view_patients", "view_prescriptions", "update_vital_signs", "view_appointments"]
        },
        UserRole.RECEPTIONIST.value: {
            "display_name": "Receptionist",
            "description": "Front desk staff with scheduling and check-in access",
            "permissions": ["create_appointments", "view_appointments", "check_in_patients", "view_basic_patient_info"]
        },
        UserRole.PATIENT.value: {
            "display_name": "Patient",
            "description": "Patient with access to personal records only",
            "permissions": ["view_own_records", "view_own_appointments", "view_own_prescriptions"]
        },
        "admin": {  # Backward compatibility
            "display_name": "Administrator",
            "description": "System administrator with full access",
            "permissions": ["all"]
        }
    }
    
    roles_data = [
        {"name": UserRole.SUPER_ADMIN.value, "guard_name": "web"},
        {"name": UserRole.CLINIC_ADMIN.value, "guard_name": "web"},
        {"name": UserRole.DOCTOR.value, "guard_name": "web"},
        {"name": UserRole.NURSE.value, "guard_name": "web"},
        {"name": UserRole.STAFF.value, "guard_name": "web"},
        {"name": UserRole.RECEPTIONIST.value, "guard_name": "web"},
        {"name": UserRole.PATIENT.value, "guard_name": "web"},
        # Backward compatibility: 'admin' maps to 'super_admin'
        {"name": "admin", "guard_name": "web"},
    ]
    
    roles = {}
    for role_data in roles_data:
        role_name = role_data["name"]
        metadata = roles_metadata.get(role_name, {})
        
        # Check if role already exists
        existing_role = db.query(Role).filter(
            Role.name == role_name,
            Role.deleted_at.is_(None)
        ).first()
        
        if existing_role:
            logger.info(f"Role '{role_name}' already exists, updating metadata...")
            # Update metadata if not set
            if not existing_role.display_name and metadata.get("display_name"):
                existing_role.display_name = metadata["display_name"]
            if not existing_role.description and metadata.get("description"):
                existing_role.description = metadata["description"]
            if not existing_role.permissions and metadata.get("permissions"):
                existing_role.permissions = metadata["permissions"]
            db.flush()
            roles[role_name] = existing_role
        else:
            role = Role(
                name=role_name,
                guard_name=role_data["guard_name"],
                display_name=metadata.get("display_name"),
                description=metadata.get("description"),
                permissions=metadata.get("permissions")
            )
            db.add(role)
            db.flush()  # Get the ID without committing
            roles[role_name] = role
            logger.info(f"✓ Created role: {role_name}")
    
    db.commit()
    return roles


def seed_admin_user(db: Session, admin_role: Role) -> User:
    """Create admin user"""
    logger.info("Creating admin user...")
    
    # Get admin credentials from environment or use defaults
    admin_email = os.getenv("ADMIN_EMAIL", "admin@yopmail.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "password")
    admin_name = os.getenv("ADMIN_NAME", "System Administrator")
    
    # Get default clinic (required for clinic_id NOT NULL constraint)
    default_clinic = db.query(Clinic).filter(
        Clinic.code == "DEFAULT",
        Clinic.deleted_at.is_(None)
    ).first()
    
    if not default_clinic:
        raise Exception("Default clinic not found. Please run migrations first to create the DEFAULT clinic.")
    
    # Check if admin user already exists
    existing_user = db.query(User).filter(
        User.email == admin_email.lower(),
        User.deleted_at.is_(None)
    ).first()
    
    if existing_user:
        logger.info(f"Admin user '{admin_email}' already exists, skipping...")
        # Ensure admin has admin role
        if admin_role not in existing_user.roles:
            existing_user.roles.append(admin_role)
        # Ensure admin has clinic_id (in case it was NULL)
        if not existing_user.clinic_id:
            existing_user.clinic_id = default_clinic.id
        db.commit()
        return existing_user
    
    # Create admin user
    admin_user = User(
        email=admin_email.lower(),
        password=get_password_hash(admin_password),
        name=admin_name,
        role="super_admin",  # Laravel-style role field
        clinic_id=default_clinic.id,  # Required: clinic_id is NOT NULL
        is_active=True,
        is_verified=True,
        email_verified_at=None,  # Can be set if needed
    )
    
    db.add(admin_user)
    db.flush()  # Get the ID without committing
    
    # Assign admin role
    admin_user.roles.append(admin_role)
    
    db.commit()
    db.refresh(admin_user)
    
    logger.info(f"✓ Created admin user: {admin_email}")
    logger.info(f"  Email: {admin_email}")
    logger.info(f"  Password: {admin_password} (from ADMIN_PASSWORD env var or default)")
    logger.info(f"  Role: super_admin")
    
    return admin_user


def encrypt_config_for_seed(config_dict: dict) -> dict:
    """
    Encrypt configuration for seed data
    For local testing, we'll store a placeholder structure
    In production, use proper encryption
    """
    # For seed data, we'll store a structure that indicates it needs encryption
    # In real usage, this should be encrypted before storage
    return {
        "encrypted": False,  # Flag to indicate this is seed data
        "placeholder": True,
        "note": "Replace with encrypted config in production",
        "data": config_dict  # Store unencrypted for local testing only
    }


def seed_notification_settings(db: Session, admin_user: User) -> None:
    """Create default notification settings"""
    logger.info("Creating notification settings...")
    
    # Default notification settings (enabled by default for local testing)
    settings_data = [
        {
            "channel": "email",
            "enabled": True,
            "provider": "smtp",
            "config": {
                "host": "smtp.mailtrap.io",
                "port": 2525,
                "username": "your_username",
                "password": "your_password",
                "from_email": "noreply@eclinic.local",
                "from_name": "eClinic"
            }
        },
        {
            "channel": "sms",
            "enabled": True,
            "provider": "twilio",
            "config": {
                "account_sid": "your_account_sid",
                "auth_token": "your_auth_token",
                "from_number": "+1234567890"
            }
        },
        {
            "channel": "whatsapp",
            "enabled": True,
            "provider": "twilio_whatsapp",
            "config": {
                "account_sid": "your_account_sid",
                "auth_token": "your_auth_token",
                "from_number": "whatsapp:+1234567890"
            }
        },
    ]
    
    for setting_data in settings_data:
        # Check if setting already exists
        existing_setting = db.query(NotificationSetting).filter(
            NotificationSetting.channel == setting_data["channel"],
            NotificationSetting.deleted_at.is_(None)
        ).first()
        
        if existing_setting:
            logger.info(f"Notification setting for '{setting_data['channel']}' already exists, skipping...")
            continue
        
        # Encrypt config (for seed data, we'll use placeholder encryption)
        encrypted_config = encrypt_config_for_seed(setting_data["config"])
        
        setting = NotificationSetting(
            channel=setting_data["channel"],
            enabled=setting_data["enabled"],
            provider=setting_data["provider"],
            config_encrypted=encrypted_config,
            updated_by=admin_user.id
        )
        
        db.add(setting)
        logger.info(f"✓ Created notification setting: {setting_data['channel']} ({setting_data['provider']})")
    
    db.commit()


def main():
    """Main seed function"""
    logger.info("=" * 60)
    logger.info("Seeding database with initial data...")
    logger.info("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Create roles
        roles = seed_roles(db)
        
        # Create admin user
        admin_user = seed_admin_user(db, roles["admin"])
        
        # Create notification settings
        seed_notification_settings(db, admin_user)
        
        logger.info("=" * 60)
        logger.info("✓ Seed data created successfully!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Admin Credentials:")
        logger.info(f"  Email: {os.getenv('ADMIN_EMAIL', 'admin@yopmail.com')}")
        logger.info(f"  Password: {os.getenv('ADMIN_PASSWORD', 'password')}")
        logger.info("")
        logger.info("Note: Change admin password after first login!")
        logger.info("      Set ADMIN_PASSWORD environment variable to customize.")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

