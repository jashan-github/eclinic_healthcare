"""
Patient Vital Signs model
Stores patient vital sign readings
One record per vital reading (not per date)
"""

from sqlalchemy import Column, DateTime, Text, String, ForeignKey, Index, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class PatientVitalSigns(BaseModel):
    """
    Patient Vital Signs model
    Stores individual vital sign readings for patients
    
    Each record represents ONE vital reading at ONE point in time.
    Multiple vitals recorded together will create multiple records.
    """
    
    __tablename__ = "patient_vital_signs"
    
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient user ID"
    )
    vital_name_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vital_names.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Vital name ID (FK to vital_names table)"
    )
    clinic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Clinic ID"
    )
    doctor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Doctor user ID who recorded the vital signs (NULL = patient recorded it)"
    )
    appointment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Associated appointment ID (if recorded during appointment)"
    )
    record_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Date and time when this vital sign was recorded"
    )
    numeric_value = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Numeric value for vital signs with data_type='number' (e.g., 185.5, 118, 72)"
    )
    text_value = Column(
        Text,
        nullable=True,
        comment="Text value for vital signs with data_type='text' or 'select'"
    )
    unit = Column(
        String(50),
        nullable=True,
        comment="Unit of measurement stored at time of recording (for historical accuracy)"
    )
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes about this specific vital reading"
    )
    share_with_doctor = Column(
        Boolean,
        nullable=False,
        server_default='false',
        index=True,
        comment="Patient consent to share this vital sign with doctor for medical evaluation and care"
    )
    
    # Legacy column (will be removed after migration)
    vital_data = Column(
        Text,
        nullable=True,
        comment="DEPRECATED: Legacy JSONB data. Will be removed after migration."
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_patient_vital_signs_patient_vital_date', 'patient_id', 'vital_name_id', 'record_date'),
        Index('ix_patient_vital_signs_patient_date', 'patient_id', 'record_date'),
        Index('ix_patient_vital_signs_clinic_date', 'clinic_id', 'record_date'),
        Index('ix_patient_vital_signs_vital_name', 'vital_name_id'),
        Index('ix_patient_vital_signs_appointment', 'appointment_id'),
        Index('ix_patient_vital_signs_patient_consent', 'patient_id', 'share_with_doctor'),
    )
    
    def __repr__(self):
        value = self.numeric_value if self.numeric_value is not None else self.text_value
        return f"<PatientVitalSigns(id={self.id}, patient_id={self.patient_id}, vital_name_id={self.vital_name_id}, value={value}, date={self.record_date})>"

