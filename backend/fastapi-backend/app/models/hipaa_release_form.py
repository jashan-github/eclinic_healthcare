"""
HIPAA Release Form model
Stores patient authorization for release of protected health information (PHI)
Matches Pure Health BV HIPAA release form sections 1–10.
"""

from sqlalchemy import Column, String, Text, Boolean, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class HipaaReleaseForm(BaseModel):
    """
    HIPAA Release Form model
    Section-based fields matching the Pure Health BV HIPAA release form.
    """

    __tablename__ = "hipaa_release_forms"

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient user ID",
    )

    # Section 1
    section1_last_name = Column(String(255), nullable=True, comment="Section 1: Last Name")
    section1_first_name = Column(String(255), nullable=True, comment="Section 1: First Name")
    section1_middle_name = Column(String(255), nullable=True, comment="Section 1: Middle Name")
    section1_date_of_birth = Column(Date, nullable=True, comment="Section 1: Date of Birth")
    section1_reference_number = Column(String(255), nullable=True, comment="Section 1: Reference Number")
    section1_address = Column(Text, nullable=True, comment="Section 1: Address")
    section1_country = Column(String(255), nullable=True, comment="Section 1: Country")

    # Section 2
    section2_name = Column(String(500), nullable=True, comment="Section 2: Name")
    section2_address = Column(Text, nullable=True, comment="Section 2: Address")
    section2_country = Column(String(255), nullable=True, comment="Section 2: Country")

    # Section 3
    section3_name = Column(String(500), nullable=True, comment="Section 3: Name")
    section3_relationship_to_patient = Column(String(255), nullable=True, comment="Section 3: Relationship to patient")
    section3_phone_number = Column(String(50), nullable=True, comment="Section 3: Phone number")
    section3_address = Column(Text, nullable=True, comment="Section 3: Address")
    section3_country = Column(String(255), nullable=True, comment="Section 3: Country")

    # Section 4
    section4_expiration_date = Column(Date, nullable=True, comment="Section 4: Expiration date")
    section4_expiration_event = Column(String(500), nullable=True, comment="Section 4: Expiration Event")

    # Section 5
    section5_medical_records = Column(Boolean, nullable=False, default=False, comment="Section 5: Medical Records")
    section5_dental_records = Column(Boolean, nullable=False, default=False, comment="Section 5: Dental Records")
    section5_other_non_specific = Column(Boolean, nullable=False, default=False, comment="Section 5: Other Non-Specific")
    section5_non_specific_records_details = Column(Text, nullable=True, comment="Section 5: Non-Specific Records Details")

    # Section 6 – each category: bool + date + signature
    section6_communicable_disease = Column(Boolean, nullable=False, default=False, comment="Section 6: Communicable Disease")
    section6_communicable_disease_date = Column(Date, nullable=True)
    section6_communicable_disease_signature = Column(String(500), nullable=True)
    section6_reproductive_health = Column(Boolean, nullable=False, default=False, comment="Section 6: Reproductive Health")
    section6_reproductive_health_date = Column(Date, nullable=True)
    section6_reproductive_health_signature = Column(String(500), nullable=True)
    section6_hiv_test_results = Column(Boolean, nullable=False, default=False, comment="Section 6: HIV Test Results")
    section6_hiv_test_results_date = Column(Date, nullable=True)
    section6_hiv_test_results_signature = Column(String(500), nullable=True)
    section6_mental_health_records = Column(Boolean, nullable=False, default=False, comment="Section 6: Mental Health Records")
    section6_mental_health_records_date = Column(Date, nullable=True)
    section6_mental_health_records_signature = Column(String(500), nullable=True)
    section6_substance_use_disorder = Column(Boolean, nullable=False, default=False, comment="Section 6: Substance Use Disorder")
    section6_substance_use_disorder_date = Column(Date, nullable=True)
    section6_substance_use_disorder_signature = Column(String(500), nullable=True)
    section6_other = Column(Boolean, nullable=False, default=False, comment="Section 6: Other")
    section6_other_date = Column(Date, nullable=True)
    section6_other_signature = Column(String(500), nullable=True)
    section6_other_records_details = Column(Text, nullable=True, comment="Section 6: Other Records Details")
    section6_psychotherapy_notes = Column(Boolean, nullable=False, default=False, comment="Section 6: Psychotherapy Notes")
    section6_psychotherapy_notes_date = Column(Date, nullable=True)
    section6_psychotherapy_notes_signature = Column(String(500), nullable=True)

    # Section 7
    section7_healthcare = Column(Boolean, nullable=False, default=False, comment="Section 7: Healthcare")
    section7_research = Column(Boolean, nullable=False, default=False, comment="Section 7: Research")
    section7_marketing = Column(Boolean, nullable=False, default=False, comment="Section 7: Marketing")
    section7_sale = Column(Boolean, nullable=False, default=False, comment="Section 7: Sale")
    section7_legal = Column(Boolean, nullable=False, default=False, comment="Section 7: Legal")
    section7_other = Column(Boolean, nullable=False, default=False, comment="Section 7: Other")
    section7_other_details = Column(Text, nullable=True, comment="Section 7: Other Records Details")

    # Section 9
    section9_additional_information = Column(Text, nullable=True, comment="Section 9: Additional Information")

    # Section 10
    section10_name_of_patient_client = Column(String(500), nullable=True, comment="Section 10: Name of Patient/Client")
    section10_signature_date = Column(Date, nullable=True, comment="Section 10: Signature Date")
    section10_name_of_signatory_if_not_patient = Column(String(500), nullable=True, comment="Section 10: Name of signatory if not patient/client")
    section10_authority_to_sign = Column(String(500), nullable=True, comment="Section 10: Authority to sign on behalf of patient/client")
    section10_name_of_translator = Column(String(500), nullable=True, comment="Section 10: Name of translator")
    section10_signature_of_translator = Column(String(500), nullable=True, comment="Section 10: Signature of translator")

    patient = relationship("User", foreign_keys=[patient_id], lazy="select")

    __table_args__ = (
        Index("hipaa_release_forms_patient_id_index", "patient_id"),
        Index("hipaa_release_forms_s10_signature_date_index", "section10_signature_date"),
        Index("hipaa_release_forms_created_at_index", "created_at"),
        Index("hipaa_release_forms_deleted_at_index", "deleted_at"),
    )

    def __repr__(self):
        return f"<HipaaReleaseForm(id={self.id}, patient_id={self.patient_id}, s1='{self.section1_last_name},{self.section1_first_name}')>"
