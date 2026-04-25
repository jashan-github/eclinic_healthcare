"""
Vital Frequency model
Stores frequency rules for vital sign recording
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import BaseModel


class VitalFrequency(BaseModel):
    """
    Vital Frequency model
    Defines how often vital signs should be recorded
    
    Priority order (highest to lowest):
    1. Patient-specific + Vital-specific
    2. Patient-specific + All vitals (vital_name_id = NULL)
    3. Clinic-specific + Vital-specific
    4. Clinic-specific + All vitals (vital_name_id = NULL)
    5. Global + Vital-specific (patient_id = NULL, clinic_id = NULL)
    6. Global + All vitals (all NULL)
    """
    
    __tablename__ = "vital_frequency"
    
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Patient user ID (NULL = applies to all patients or clinic/global default)"
    )
    vital_name_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vital_names.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Vital name ID (NULL = applies to all vital names)"
    )
    clinic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Clinic ID (NULL = global default)"
    )
    frequency_type = Column(
        String(50),
        nullable=True,
        default="daily",
        comment="Frequency type: 'daily', 'weekly', 'custom'"
    )
    max_entries_per_day = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Maximum number of entries allowed per day (e.g., 1, 2, 4, 6)"
    )
    times_per_day = Column(
        Integer,
        nullable=True,
        comment="Number of times per day (e.g., 2 = twice a day). Used for display/reminders."
    )
    preferred_times = Column(
        JSONB,
        nullable=True,
        comment="Preferred times of day for recording (e.g., ['09:00', '17:00']). Used for reminders."
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this frequency rule is active"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_vital_frequency_patient_vital', 'patient_id', 'vital_name_id'),
        Index('ix_vital_frequency_clinic_vital', 'clinic_id', 'vital_name_id'),
        Index('ix_vital_frequency_is_active', 'is_active'),
    )
    
    def __repr__(self):
        scope = []
        if self.patient_id:
            scope.append(f"patient={self.patient_id}")
        if self.vital_name_id:
            scope.append(f"vital={self.vital_name_id}")
        if self.clinic_id:
            scope.append(f"clinic={self.clinic_id}")
        if not scope:
            scope.append("global")
        return f"<VitalFrequency(id={self.id}, scope={', '.join(scope)}, max={self.max_entries_per_day}/day)>"

