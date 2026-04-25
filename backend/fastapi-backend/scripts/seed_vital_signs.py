#!/usr/bin/env python3
"""
Vital Signs Seeder
Creates sample vital signs data for patients
Based on Laravel VitalSignsSeeder, adapted for new architecture
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random
import json
from uuid import UUID
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, Clinic
from app.models.patient_vital_signs import PatientVitalSigns
from app.models.vital_name import VitalName
from app.models.appointment import Appointment
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


def get_vital_name_cache(db: Session) -> dict:
    """Build a cache of vital names by display name"""
    vital_names = db.query(VitalName).filter(VitalName.deleted_at.is_(None)).all()
    cache = {}
    for vn in vital_names:
        cache[vn.name] = vn
    return cache


def get_clinic_ids(db: Session) -> list[UUID]:
    """Get all clinic IDs from clinics table"""
    clinics = db.query(Clinic).filter(Clinic.deleted_at.is_(None)).all()
    clinic_ids = [clinic.id for clinic in clinics]
    
    if not clinic_ids:
        logger.warning("No clinics found. Creating a default clinic...")
        # Create a default clinic if none exists
        default_clinic = Clinic(
            name="Default Clinic",
            code="DEFAULT",
            timezone="UTC",
            status="active"
        )
        db.add(default_clinic)
        db.commit()
        db.refresh(default_clinic)
        clinic_ids = [default_clinic.id]
    
    logger.info(f"Found {len(clinic_ids)} clinic(s)")
    return clinic_ids


def get_patient_ids(db: Session) -> list[UUID]:
    """Get all patient IDs from users table where role is patient"""
    patients = db.query(User).filter(
        User.role == "patient",
        User.deleted_at.is_(None)
    ).all()
    
    patient_ids = [patient.id for patient in patients]
    
    if not patient_ids:
        logger.warning("No patients found. Please seed users first.")
        return []
    
    logger.info(f"Found {len(patient_ids)} patient(s)")
    return patient_ids


def get_doctor_ids(db: Session, clinic_id: UUID) -> list[UUID]:
    """Get doctor IDs for a clinic"""
    doctors = db.query(User).filter(
        User.role == "doctor",
        User.clinic_id == clinic_id,
        User.deleted_at.is_(None)
    ).all()
    
    doctor_ids = [doctor.id for doctor in doctors]
    
    if not doctor_ids:
        logger.warning(f"No doctors found for clinic {clinic_id}. Will use None for doctor_id.")
        return []
    
    return doctor_ids


def get_appointment_id(
    db: Session,
    patient_id: UUID,
    doctor_id: UUID,
    clinic_id: UUID,
    date: datetime
) -> UUID | None:
    """Try to get an appointment ID for the patient and doctor on the given date"""
    appointment = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id == doctor_id,
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date >= date.replace(hour=0, minute=0, second=0),
        Appointment.appointment_date < date.replace(hour=23, minute=59, second=59),
        Appointment.deleted_at.is_(None)
    ).first()
    
    return appointment.id if appointment else None


def generate_vital_signs_variations() -> list[dict]:
    """Generate base vital signs variations for different patients"""
    return [
        # Patient 1 - Normal range
        {
            'weight_lbs': 185.5,
            'weight_kg': 84.1,
            'height_in': 72.0,
            'height_cm': 182.9,
            'bp_systolic': 118,
            'bp_diastolic': 76,
            'pulse': 72,
            'respiratory_rate': 16,
            'temperature_f': 98.6,
            'temperature_c': 37.0,
            'spo2': 98,
        },
        # Patient 2 - Slightly elevated BP
        {
            'weight_lbs': 175.8,
            'weight_kg': 79.8,
            'height_in': 70.0,
            'height_cm': 177.8,
            'bp_systolic': 130,
            'bp_diastolic': 85,
            'pulse': 78,
            'respiratory_rate': 18,
            'temperature_f': 98.4,
            'temperature_c': 36.9,
            'spo2': 97,
        },
        # Patient 3 - Lower weight
        {
            'weight_lbs': 150.2,
            'weight_kg': 68.1,
            'height_in': 65.0,
            'height_cm': 165.1,
            'bp_systolic': 110,
            'bp_diastolic': 70,
            'pulse': 68,
            'respiratory_rate': 14,
            'temperature_f': 98.2,
            'temperature_c': 36.8,
            'spo2': 99,
        },
        # Patient 4 - Higher values
        {
            'weight_lbs': 200.0,
            'weight_kg': 90.7,
            'height_in': 74.0,
            'height_cm': 188.0,
            'bp_systolic': 125,
            'bp_diastolic': 80,
            'pulse': 75,
            'respiratory_rate': 17,
            'temperature_f': 98.8,
            'temperature_c': 37.1,
            'spo2': 96,
        },
        # Patient 5 - Average
        {
            'weight_lbs': 165.0,
            'weight_kg': 74.8,
            'height_in': 68.0,
            'height_cm': 172.7,
            'bp_systolic': 120,
            'bp_diastolic': 75,
            'pulse': 70,
            'respiratory_rate': 16,
            'temperature_f': 98.6,
            'temperature_c': 37.0,
            'spo2': 98,
        },
        # Patient 6 - Varied
        {
            'weight_lbs': 190.5,
            'weight_kg': 86.4,
            'height_in': 71.0,
            'height_cm': 180.3,
            'bp_systolic': 115,
            'bp_diastolic': 72,
            'pulse': 73,
            'respiratory_rate': 15,
            'temperature_f': 98.5,
            'temperature_c': 36.9,
            'spo2': 97,
        },
    ]


def add_variations(base_vitals: dict, date_index: int) -> dict:
    """Add realistic variations to base vital signs based on date index"""
    vitals = base_vitals.copy()
    
    if date_index > 0:
        # Add some variation to make it realistic
        variation = {
            'weight_lbs': vitals['weight_lbs'] + (random.randint(-5, 5) * 0.1),
            'bp_systolic': vitals['bp_systolic'] + random.randint(-5, 5),
            'bp_diastolic': vitals['bp_diastolic'] + random.randint(-3, 3),
            'pulse': vitals['pulse'] + random.randint(-5, 5),
            'respiratory_rate': vitals['respiratory_rate'] + random.randint(-2, 2),
            'temperature_f': vitals['temperature_f'] + (random.randint(-5, 5) * 0.1),
            'spo2': vitals['spo2'] + random.randint(-1, 1),
        }
        
        # Ensure values stay within reasonable ranges
        vitals['weight_lbs'] = max(100, min(250, variation['weight_lbs']))
        vitals['weight_kg'] = round(vitals['weight_lbs'] / 2.20462, 2)
        vitals['bp_systolic'] = max(90, min(160, variation['bp_systolic']))
        vitals['bp_diastolic'] = max(60, min(100, variation['bp_diastolic']))
        vitals['pulse'] = max(60, min(100, variation['pulse']))
        vitals['respiratory_rate'] = max(12, min(20, variation['respiratory_rate']))
        vitals['temperature_f'] = max(97.0, min(99.5, variation['temperature_f']))
        vitals['temperature_c'] = round((vitals['temperature_f'] - 32) * 5/9, 1)
        vitals['spo2'] = max(95, min(100, variation['spo2']))
    
    # Add additional fields occasionally
    if random.randint(0, 1):
        vitals['rbs_serum'] = random.randint(80, 120)
    
    if random.randint(0, 1):
        # Calculate BMI
        height_m = vitals['height_in'] / 12
        vitals['bmi'] = round(vitals['weight_lbs'] / (height_m ** 2), 1)
    
    if random.randint(0, 2) == 0:
        vitals['head_circumference_in'] = round(random.uniform(20, 25), 1)
        vitals['head_circumference_cm'] = round(vitals['head_circumference_in'] * 2.54, 1)
    
    if random.randint(0, 2) == 0:
        vitals['waist_circumference_in'] = round(random.uniform(30, 40), 1)
        vitals['waist_circumference_cm'] = round(vitals['waist_circumference_in'] * 2.54, 1)
    
    if random.randint(0, 3) == 0:
        vitals['temp_location'] = random.choice(['Oral', 'Axillary', 'Rectal', 'Tympanic'])
    
    if random.randint(0, 4) == 0:
        vitals['other_notes'] = 'Patient appears healthy. No concerns noted.'
    
    return vitals


def generate_dates() -> list[datetime]:
    """Generate dates for vital signs (recent and historical)"""
    dates = []
    
    # Add recent dates (last 3 days)
    for i in range(3):
        dates.append(datetime.now(timezone.utc) - timedelta(days=i))
    
    # Add historical dates (matching screenshot pattern)
    historical_dates = [
        '2025-01-14',
        '2024-10-01',
        '2024-08-26',
        '2024-05-30',
        '2024-02-16',
        '2023-12-01',
        '2023-10-01',
    ]
    
    # Only add historical dates that are in the past
    for hist_date_str in historical_dates:
        hist_date = datetime.strptime(hist_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        if hist_date < datetime.now(timezone.utc):
            dates.append(hist_date)
    
    # Limit to 7 most recent dates
    dates = sorted(dates, reverse=True)[:7]
    
    return dates


def seed_vital_signs(db: Session) -> None:
    """Seed vital signs data for patients"""
    logger.info("Seeding vital signs data...")
    
    # Get vital name cache
    vital_name_cache = get_vital_name_cache(db)
    if not vital_name_cache:
        logger.error("No vital names found. Please run seed_vital_names.py first.")
        return
    
    # Get clinic IDs
    clinic_ids = get_clinic_ids(db)
    if not clinic_ids:
        logger.error("No clinics available. Cannot seed vital signs.")
        return
    
    # Get patient IDs
    patient_ids = get_patient_ids(db)
    if not patient_ids:
        logger.error("No patients available. Cannot seed vital signs.")
        return
    
    # Use first clinic for seeding
    clinic_id = clinic_ids[0]
    logger.info(f"Using clinic ID: {clinic_id}")
    
    # Get doctor IDs for the clinic
    doctor_ids = get_doctor_ids(db, clinic_id)
    doctor_id = doctor_ids[0] if doctor_ids else None
    
    # Generate dates
    dates = generate_dates()
    logger.info(f"Generating vital signs for {len(dates)} dates")
    
    # Generate vital signs variations
    vital_variations = generate_vital_signs_variations()
    
    # Limit patients to available variations
    patients_to_seed = min(len(patient_ids), len(vital_variations))
    patient_ids = patient_ids[:patients_to_seed]
    
    records_created = 0
    
    for patient_index, patient_id in enumerate(patient_ids):
        base_vitals = vital_variations[patient_index]
        
        for date_index, date in enumerate(dates):
            # Add variations to base vitals
            vitals = add_variations(base_vitals, date_index)
            
            # Extract notes
            notes = vitals.pop('other_notes', None)
            
            # Try to get appointment ID
            appointment_id = None
            if doctor_id:
                appointment_id = get_appointment_id(
                    db, patient_id, doctor_id, clinic_id, date
                )
            
            # Create record date
            record_date = date.replace(
                hour=random.randint(9, 17),
                minute=random.randint(0, 59),
                second=0
            )
            
            # Create individual records for each vital
            for key, value in vitals.items():
                # Skip if value is None
                if value is None:
                    continue
                
                # Map key to vital name
                vital_name_display = VITAL_KEY_TO_NAME_MAP.get(key)
                if not vital_name_display:
                    logger.debug(f"Skipping unknown vital key: {key}")
                    continue
                
                # Get vital name
                vital_name = vital_name_cache.get(vital_name_display)
                if not vital_name:
                    logger.warning(f"Vital name '{vital_name_display}' not found for key '{key}'. Skipping.")
                    continue
                
                # Check if record already exists
                existing_record = db.query(PatientVitalSigns).filter(
                    PatientVitalSigns.patient_id == patient_id,
                    PatientVitalSigns.vital_name_id == vital_name.id,
                    PatientVitalSigns.clinic_id == clinic_id,
                    PatientVitalSigns.record_date >= record_date.replace(hour=0, minute=0, second=0),
                    PatientVitalSigns.record_date < record_date.replace(hour=23, minute=59, second=59),
                    PatientVitalSigns.deleted_at.is_(None)
                ).first()
                
                if existing_record:
                    # Update existing record
                    if vital_name.data_type == "number":
                        existing_record.numeric_value = Decimal(str(value))
                        existing_record.text_value = None
                    else:
                        existing_record.text_value = str(value)
                        existing_record.numeric_value = None
                    existing_record.unit = vital_name.unit
                    existing_record.updated_at = datetime.now(timezone.utc)
                    logger.debug(f"Updated vital {vital_name_display} for patient {patient_id} on {date.date()}")
                else:
                    # Determine value storage
                    numeric_value = None
                    text_value = None
                    
                    if vital_name.data_type == "number":
                        numeric_value = Decimal(str(value))
                    else:
                        text_value = str(value)
                    
                    # Create new record
                    vital_record = PatientVitalSigns(
                        patient_id=patient_id,
                        clinic_id=clinic_id,
                        vital_name_id=vital_name.id,
                        doctor_id=doctor_id,
                        appointment_id=appointment_id,
                        record_date=record_date,
                        numeric_value=numeric_value,
                        text_value=text_value,
                        unit=vital_name.unit,
                        notes=notes if key == list(vitals.keys())[0] else None  # Only add notes to first record
                    )
                    
                    db.add(vital_record)
                    records_created += 1
                    logger.debug(f"Created vital {vital_name_display} for patient {patient_id} on {date.date()}")
    
    db.commit()
    logger.info(f"✓ Created/updated {records_created} vital signs records for {len(patient_ids)} patients")


def main():
    """Main seed function"""
    logger.info("=" * 60)
    logger.info("Seeding vital signs data...")
    logger.info("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        seed_vital_signs(db)
        
        logger.info("=" * 60)
        logger.info("✓ Vital signs seeded successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error seeding vital signs: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
