#!/usr/bin/env python3
"""
Data Migration Script: Convert JSONB vital_data to individual records

This script migrates existing patient_vital_signs records from JSONB format
to the new structure with individual records per vital.

Before: 1 record with vital_data = {"weight_lbs": 185.5, "bp_systolic": 118}
After:  2 records:
  - Record 1: vital_name_id=weight, numeric_value=185.5
  - Record 2: vital_name_id=bp-systolic, numeric_value=118
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.patient_vital_signs import PatientVitalSigns
from app.models.vital_name import VitalName
from loguru import logger


# Mapping from vital_data keys to vital_names.name
VITAL_KEY_TO_NAME_MAP = {
    'weight_lbs': 'Weight (lbs)',
    'weight_kg': 'Weight (kg)',
    'height_in': 'Height (in)',
    'height_cm': 'Height (cm)',
    'bp_systolic': 'BP Systolic',
    'bp_diastolic': 'BP Diastolic',
    'pulse': 'Pulse',
    'respiratory_rate': 'Respiratory Rate',
    'temperature_f': 'Temperature (F)',
    'temperature_c': 'Temperature (C)',
    'spo2': 'SpO2',
    'bmi': 'BMI',
    'rbs_serum': 'RBS (Serum)',
    'head_circumference_in': 'Head Circumference (in)',
    'head_circumference_cm': 'Head Circumference (cm)',
    'waist_circumference_in': 'Waist Circumference (in)',
    'waist_circumference_cm': 'Waist Circumference (cm)',
    'temp_location': 'Temperature Location',
}


def get_vital_name_by_name(db: Session, name: str) -> VitalName | None:
    """Get vital name by display name"""
    return db.query(VitalName).filter(
        VitalName.name == name,
        VitalName.deleted_at.is_(None)
    ).first()


def migrate_vital_data(db: Session) -> None:
    """Migrate existing JSONB vital_data to individual records"""
    logger.info("Starting vital data migration...")
    
    # Get all records that still have vital_data (not yet migrated)
    old_records = db.query(PatientVitalSigns).filter(
        PatientVitalSigns.vital_data.isnot(None),
        PatientVitalSigns.deleted_at.is_(None)
    ).all()
    
    logger.info(f"Found {len(old_records)} records with JSONB vital_data to migrate")
    
    if not old_records:
        logger.info("No records to migrate. Migration complete.")
        return
    
    # Build vital name cache
    vital_name_cache = {}
    for vital_name in db.query(VitalName).filter(VitalName.deleted_at.is_(None)).all():
        vital_name_cache[vital_name.name] = vital_name
    
    records_created = 0
    records_skipped = 0
    records_updated = 0
    
    for old_record in old_records:
        try:
            # Parse JSONB vital_data
            if isinstance(old_record.vital_data, str):
                vital_data = json.loads(old_record.vital_data)
            else:
                vital_data = old_record.vital_data
            
            if not isinstance(vital_data, dict):
                logger.warning(f"Record {old_record.id} has invalid vital_data format. Skipping.")
                records_skipped += 1
                continue
            
            # Check if already migrated (has vital_name_id)
            if old_record.vital_name_id is not None:
                logger.debug(f"Record {old_record.id} already migrated. Skipping.")
                records_skipped += 1
                continue
            
            # Create new records for each vital in vital_data
            created_count = 0
            for key, value in vital_data.items():
                # Skip non-vital keys
                if key in ['other_notes', 'notes']:
                    # These should go to notes field, not as separate vitals
                    if key == 'other_notes' and not old_record.notes:
                        old_record.notes = str(value)
                    continue
                
                # Map key to vital name
                vital_name_display = VITAL_KEY_TO_NAME_MAP.get(key)
                if not vital_name_display:
                    logger.warning(f"Unknown vital key '{key}' in record {old_record.id}. Skipping.")
                    continue
                
                # Get vital name
                vital_name = vital_name_cache.get(vital_name_display)
                if not vital_name:
                    logger.warning(f"Vital name '{vital_name_display}' not found for key '{key}'. Skipping.")
                    continue
                
                # Determine value storage
                numeric_value = None
                text_value = None
                
                if vital_name.data_type == "number":
                    try:
                        numeric_value = float(value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid numeric value '{value}' for {vital_name_display}. Skipping.")
                        continue
                else:
                    text_value = str(value) if value is not None else None
                
                # Check if record already exists (avoid duplicates)
                existing = db.query(PatientVitalSigns).filter(
                    PatientVitalSigns.patient_id == old_record.patient_id,
                    PatientVitalSigns.vital_name_id == vital_name.id,
                    PatientVitalSigns.record_date == old_record.record_date,
                    PatientVitalSigns.deleted_at.is_(None)
                ).first()
                
                if existing:
                    # Update existing record
                    existing.numeric_value = numeric_value
                    existing.text_value = text_value
                    existing.unit = vital_name.unit
                    if old_record.doctor_id:
                        existing.doctor_id = old_record.doctor_id
                    if old_record.appointment_id:
                        existing.appointment_id = old_record.appointment_id
                    records_updated += 1
                    logger.debug(f"Updated existing record for {vital_name_display}")
                else:
                    # Create new record
                    new_record = PatientVitalSigns(
                        patient_id=old_record.patient_id,
                        clinic_id=old_record.clinic_id,
                        vital_name_id=vital_name.id,
                        doctor_id=old_record.doctor_id,
                        appointment_id=old_record.appointment_id,
                        record_date=old_record.record_date,
                        numeric_value=numeric_value,
                        text_value=text_value,
                        unit=vital_name.unit,
                        notes=old_record.notes,
                        created_at=old_record.created_at,
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.add(new_record)
                    created_count += 1
                    records_created += 1
                    logger.debug(f"Created new record for {vital_name_display}")
            
            # Mark old record as migrated (clear vital_data)
            if created_count > 0 or records_updated > 0:
                old_record.vital_data = None  # Clear JSONB data
                old_record.updated_at = datetime.now(timezone.utc)
                logger.debug(f"Marked record {old_record.id} as migrated")
            
        except Exception as e:
            logger.error(f"Error migrating record {old_record.id}: {e}")
            db.rollback()
            continue
    
    # Commit all changes
    try:
        db.commit()
        logger.info(f"✓ Migration complete!")
        logger.info(f"  - Created: {records_created} new records")
        logger.info(f"  - Updated: {records_updated} existing records")
        logger.info(f"  - Skipped: {records_skipped} records")
    except Exception as e:
        logger.error(f"Error committing migration: {e}")
        db.rollback()
        raise


def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("Vital Data Migration Script")
    logger.info("Converting JSONB vital_data to individual records")
    logger.info("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        migrate_vital_data(db)
        
        logger.info("=" * 60)
        logger.info("✓ Migration completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

