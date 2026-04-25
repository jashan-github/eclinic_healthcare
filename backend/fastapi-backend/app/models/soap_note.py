"""
SOAP Notes Model
Stores SOAP (Subjective, Objective, Assessment, Plan) notes for patient appointments
"""

from sqlalchemy import Column, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class SoapNote(BaseModel):
    """
    SOAP Notes model
    Stores SOAP notes for patient appointments
    
    SOAP stands for:
    - Subjective: Patient's symptoms, feelings, concerns
    - Objective: Observable findings, measurements, test results
    - Assessment: Diagnosis, evaluation, clinical impression
    - Plan: Treatment plan, medications, follow-up actions
    """
    
    __tablename__ = "soap_notes"
    
    # Foreign keys
    appointment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Appointment ID (one SOAP note per appointment)"
    )
    
    doctor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Doctor user ID who created the SOAP note"
    )
    
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Patient user ID"
    )
    
    # SOAP sections
    subjective = Column(
        Text,
        nullable=True,
        comment="Subjective: Patient's symptoms, feelings, concerns"
    )
    
    objective = Column(
        Text,
        nullable=True,
        comment="Objective: Observable findings, measurements, test results"
    )
    
    assessment = Column(
        Text,
        nullable=True,
        comment="Assessment: Diagnosis, evaluation, clinical impression"
    )
    
    plan = Column(
        Text,
        nullable=True,
        comment="Plan: Treatment plan, medications, follow-up actions"
    )
    
    # Relationships
    appointment = relationship(
        "Appointment",
        foreign_keys=[appointment_id],
        lazy="joined",
        backref="soap_note"
    )
    
    doctor = relationship(
        "User",
        foreign_keys=[doctor_id],
        lazy="select"
    )
    
    patient = relationship(
        "User",
        foreign_keys=[patient_id],
        lazy="select"
    )
    
    # Indexes
    __table_args__ = (
        Index('soap_notes_appointment_id_index', 'appointment_id'),
        Index('soap_notes_doctor_id_index', 'doctor_id'),
        Index('soap_notes_patient_id_index', 'patient_id'),
        Index('soap_notes_created_at_index', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SoapNote(id={self.id}, appointment_id={self.appointment_id})>"
