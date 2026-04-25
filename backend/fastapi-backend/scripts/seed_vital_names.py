#!/usr/bin/env python3
"""
Vital Names Seeder
Creates standard vital sign names that admins can manage
These names define which vital signs are available in the system
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.vital_name import VitalName
from loguru import logger


def seed_vital_names(db: Session) -> None:
    """Seed standard vital sign names"""
    logger.info("Seeding vital names...")
    
    # Standard vital signs that should be available
    vital_names_data = [
        {
            "name": "Weight (lbs)",
            "unit": "lbs",
            "display_order": "1",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Weight (kg)",
            "unit": "kg",
            "display_order": "2",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Height (in)",
            "unit": "in",
            "display_order": "3",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Height (cm)",
            "unit": "cm",
            "display_order": "4",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "BP Systolic",
            "unit": "mmHg",
            "display_order": "5",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "BP Diastolic",
            "unit": "mmHg",
            "display_order": "6",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Pulse",
            "unit": "per min",
            "display_order": "7",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Respiratory Rate",
            "unit": "per min",
            "display_order": "8",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Temperature (F)",
            "unit": "°F",
            "display_order": "9",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Temperature (C)",
            "unit": "°C",
            "display_order": "10",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "SpO2",
            "unit": "%",
            "display_order": "11",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "BMI",
            "unit": "",
            "display_order": "12",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "RBS (Serum)",
            "unit": "mg/dL",
            "display_order": "13",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Head Circumference (in)",
            "unit": "in",
            "display_order": "14",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Head Circumference (cm)",
            "unit": "cm",
            "display_order": "15",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Waist Circumference (in)",
            "unit": "in",
            "display_order": "16",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Waist Circumference (cm)",
            "unit": "cm",
            "display_order": "17",
            "is_active": True,
            "data_type": "number",
            "max_entries_per_day": "1"
        },
        {
            "name": "Temperature Location",
            "unit": "",
            "display_order": "18",
            "is_active": True,
            "data_type": "select",
            "options": '["Oral", "Axillary", "Rectal", "Tympanic"]',
            "max_entries_per_day": "1"
        },
    ]
    
    records_created = 0
    records_updated = 0
    
    for vital_data in vital_names_data:
        # Check if vital name already exists
        existing = db.query(VitalName).filter(
            VitalName.name == vital_data["name"],
            VitalName.deleted_at.is_(None)
        ).first()
        
        if existing:
            # Update existing record to ensure it matches the seed data
            existing.unit = vital_data["unit"]
            existing.display_order = vital_data["display_order"]
            existing.is_active = vital_data["is_active"]
            existing.data_type = vital_data["data_type"]
            existing.options = vital_data.get("options")
            existing.max_entries_per_day = vital_data["max_entries_per_day"]
            records_updated += 1
            logger.debug(f"Updated vital name: {vital_data['name']}")
        else:
            # Create new vital name
            vital_name = VitalName(**vital_data)
            db.add(vital_name)
            records_created += 1
            logger.debug(f"Created vital name: {vital_data['name']}")
    
    db.commit()
    logger.info(f"✓ Created {records_created} vital names, updated {records_updated} existing vital names")


def main():
    """Main seed function"""
    logger.info("=" * 60)
    logger.info("Seeding vital names...")
    logger.info("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        seed_vital_names(db)
        
        logger.info("=" * 60)
        logger.info("✓ Vital names seeded successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error seeding vital names: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

