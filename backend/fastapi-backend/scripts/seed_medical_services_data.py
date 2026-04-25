"""
Seed medical services data
Inserts medical services into the medical_services table
Idempotent - can be run multiple times safely
"""

import sys
import os
from datetime import datetime
from uuid import UUID

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.medical_service import MedicalService
from loguru import logger


def seed_medical_services(db: Session) -> None:
    """
    Seed medical services data
    
    Args:
        db: Database session
    """
    logger.info("Starting medical services seeding...")
    
    # Medical services data
    medical_services_data = [
        {
            "id": UUID("9cdf3788-f630-47d5-8e11-a49d84409d21"),
            "parent": "0",
            "name": "Lungs",
            "image": "https://portal.orvo.app/storage/service_image/jinej5316w.png",
            "status": True,
        },
        {
            "id": UUID("9cdf3789-00dd-40fd-9932-3ed703e12a44"),
            "parent": "0",
            "name": "Heart",
            "image": "https://portal.orvo.app/storage/service_image/d3n1wobffg.png",
            "status": True,
        },
        {
            "id": UUID("9cdf3789-019b-4366-a8ca-e42f879ba156"),
            "parent": "0",
            "name": "Dental Care",
            "image": "https://portal.orvo.app/storage/service_image/63uqxpw7fy.svg",
            "status": True,
        },
        {
            "id": UUID("9cdf3789-01ce-446e-bee2-11b1e780ca05"),
            "parent": "0",
            "name": "Hair Care",
            "image": "https://portal.orvo.app/storage/service_image/llrm2z8yyx.svg",
            "status": True,
        },
        {
            "id": UUID("9cdf3789-020b-457d-805c-7cb991820a35"),
            "parent": "0",
            "name": "Brain & Nerves",
            "image": "https://portal.orvo.app/storage/service_image/2hqkpjrwvc.svg",
            "status": True,
        },
        {
            "id": UUID("9cdf3789-0236-4327-89aa-e9de6021a0e3"),
            "parent": "0",
            "name": "Bones & Joints",
            "image": "https://portal.orvo.app/storage/service_image/33b3fcdzlp.svg",
            "status": True,
        },
        {
            "id": UUID("9cdf3789-0262-4580-b07f-c9c8eadd926e"),
            "parent": "0",
            "name": "Homeopathy",
            "image": "https://portal.orvo.app/storage/service_image/5jo5jy80io.svg",
            "status": True,
        },
        {
            "id": UUID("9cdf3789-028f-438e-951f-041ccdefdafa"),
            "parent": "0",
            "name": "Ayurveda",
            "image": "https://portal.orvo.app/storage/service_image/mss3qwfrqd.svg",
            "status": True,
        },
    ]
    
    current_time = datetime.utcnow()
    created_count = 0
    updated_count = 0
    
    for service_data in medical_services_data:
        # Check if service already exists
        existing_service = db.query(MedicalService).filter(
            MedicalService.id == service_data["id"]
        ).first()
        
        if existing_service:
            # Update existing service
            existing_service.parent = service_data["parent"]
            existing_service.name = service_data["name"]
            existing_service.image = service_data["image"]
            existing_service.status = service_data["status"]
            existing_service.updated_at = current_time
            updated_count += 1
            logger.info(f"Updated medical service: {service_data['name']} (ID: {service_data['id']})")
        else:
            # Create new service
            new_service = MedicalService(
                id=service_data["id"],
                parent=service_data["parent"],
                name=service_data["name"],
                image=service_data["image"],
                status=service_data["status"],
                created_at=current_time,
                updated_at=current_time,
            )
            db.add(new_service)
            created_count += 1
            logger.info(f"Created medical service: {service_data['name']} (ID: {service_data['id']})")
    
    # Commit all changes
    try:
        db.commit()
        logger.info(f"Medical services seeding completed: {created_count} created, {updated_count} updated")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding medical services: {e}")
        raise


def main():
    """Main function to run the seeder"""
    db = SessionLocal()
    try:
        seed_medical_services(db)
        logger.info("Medical services seeding completed successfully!")
    except Exception as e:
        logger.error(f"Failed to seed medical services: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

