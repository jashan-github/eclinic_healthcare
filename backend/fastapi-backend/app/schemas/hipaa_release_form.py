"""
HIPAA Release Form schemas
Pydantic models for request/response – matches Pure Health BV form sections 1–10.
"""

from typing import Optional, Union
from uuid import UUID
from datetime import date
from pydantic import BaseModel, Field, field_validator


# --- Section 1 ---
class Section1Schema(BaseModel):
    last_name: Optional[str] = Field(None, description="Section 1: Last Name")
    first_name: Optional[str] = Field(None, description="Section 1: First Name")
    middle_name: Optional[str] = Field(None, description="Section 1: Middle Name")
    date_of_birth: Optional[date] = Field(None, description="Section 1: Date of Birth")
    reference_number: Optional[str] = Field(None, description="Section 1: Reference Number")
    address: Optional[str] = Field(None, description="Section 1: Address")
    country: Optional[str] = Field(None, description="Section 1: Country")


# --- Section 2 ---
class Section2Schema(BaseModel):
    name: Optional[str] = Field(None, description="Section 2: Name")
    address: Optional[str] = Field(None, description="Section 2: Address")
    country: Optional[str] = Field(None, description="Section 2: Country")


# --- Section 3 ---
class Section3Schema(BaseModel):
    name: Optional[str] = Field(None, description="Section 3: Name")
    relationship_to_patient: Optional[str] = Field(None, description="Section 3: Relationship to patient")
    phone_number: Optional[str] = Field(None, description="Section 3: Phone number")
    address: Optional[str] = Field(None, description="Section 3: Address")
    country: Optional[str] = Field(None, description="Section 3: Country")


# --- Section 4 ---
class Section4Schema(BaseModel):
    expiration_date: Optional[date] = Field(None, description="Section 4: Expiration date")
    expiration_event: Optional[str] = Field(None, description="Section 4: Expiration Event")


# --- Section 5 ---
class Section5Schema(BaseModel):
    medical_records: bool = Field(False, description="Section 5: Medical Records")
    dental_records: bool = Field(False, description="Section 5: Dental Records")
    other_non_specific: bool = Field(False, description="Section 5: Other Non-Specific")
    non_specific_records_details: Optional[str] = Field(None, description="Section 5: Non-Specific Records Details")


# --- Section 6 (each category: bool + date + signature) ---
class Section6CategorySchema(BaseModel):
    enabled: bool = False
    date: Optional[date] = None
    signature: Optional[str] = None


class Section6Schema(BaseModel):
    communicable_disease: Section6CategorySchema = Field(default_factory=Section6CategorySchema)
    reproductive_health: Section6CategorySchema = Field(default_factory=Section6CategorySchema)
    hiv_test_results: Section6CategorySchema = Field(default_factory=Section6CategorySchema)
    mental_health_records: Section6CategorySchema = Field(default_factory=Section6CategorySchema)
    substance_use_disorder: Section6CategorySchema = Field(default_factory=Section6CategorySchema)
    other: Section6CategorySchema = Field(default_factory=Section6CategorySchema)
    other_records_details: Optional[str] = None
    psychotherapy_notes: Section6CategorySchema = Field(default_factory=Section6CategorySchema)


# --- Section 7 ---
class Section7Schema(BaseModel):
    healthcare: bool = Field(False, description="Section 7: Healthcare")
    research: bool = Field(False, description="Section 7: Research")
    marketing: bool = Field(False, description="Section 7: Marketing")
    sale: bool = Field(False, description="Section 7: Sale")
    legal: bool = Field(False, description="Section 7: Legal")
    other: bool = Field(False, description="Section 7: Other")
    other_details: Optional[str] = Field(None, description="Section 7: Other Records Details")


# --- Section 9 ---
class Section9Schema(BaseModel):
    additional_information: Optional[str] = Field(None, description="Section 9: Additional Information")


# --- Section 10 ---
class Section10Schema(BaseModel):
    name_of_patient_client: Optional[str] = Field(None, description="Section 10: Name of Patient/Client")
    signature_date: Optional[date] = Field(None, description="Section 10: Signature Date")
    name_of_signatory_if_not_patient: Optional[str] = Field(None, description="Section 10: Name of signatory if not patient/client")
    authority_to_sign: Optional[str] = Field(None, description="Section 10: Authority to sign on behalf of patient/client")
    name_of_translator: Optional[str] = Field(None, description="Section 10: Name of translator")
    signature_of_translator: Optional[str] = Field(None, description="Section 10: Signature of translator")


# --- Create payload: flat fields for API (matches DB columns) ---
class HipaaReleaseFormCreate(BaseModel):
    """Schema for creating a HIPAA release form – sections 1–10, flat fields."""

    # Section 1
    section1_last_name: Optional[str] = None
    section1_first_name: Optional[str] = None
    section1_middle_name: Optional[str] = None
    section1_date_of_birth: Optional[date] = None
    section1_reference_number: Optional[str] = None
    section1_address: Optional[str] = None
    section1_country: Optional[str] = None
    # Section 2
    section2_name: Optional[str] = None
    section2_address: Optional[str] = None
    section2_country: Optional[str] = None
    # Section 3
    section3_name: Optional[str] = None
    section3_relationship_to_patient: Optional[str] = None
    section3_phone_number: Optional[str] = None
    section3_address: Optional[str] = None
    section3_country: Optional[str] = None
    # Section 4
    section4_expiration_date: Optional[date] = None
    section4_expiration_event: Optional[str] = None
    # Section 5
    section5_medical_records: bool = False
    section5_dental_records: bool = False
    section5_other_non_specific: bool = False
    section5_non_specific_records_details: Optional[str] = None
    # Section 6
    section6_communicable_disease: bool = False
    section6_communicable_disease_date: Optional[date] = None
    section6_communicable_disease_signature: Optional[str] = None
    section6_reproductive_health: bool = False
    section6_reproductive_health_date: Optional[date] = None
    section6_reproductive_health_signature: Optional[str] = None
    section6_hiv_test_results: bool = False
    section6_hiv_test_results_date: Optional[date] = None
    section6_hiv_test_results_signature: Optional[str] = None
    section6_mental_health_records: bool = False
    section6_mental_health_records_date: Optional[date] = None
    section6_mental_health_records_signature: Optional[str] = None
    section6_substance_use_disorder: bool = False
    section6_substance_use_disorder_date: Optional[date] = None
    section6_substance_use_disorder_signature: Optional[str] = None
    section6_other: bool = False
    section6_other_date: Optional[date] = None
    section6_other_signature: Optional[str] = None
    section6_other_records_details: Optional[str] = None
    section6_psychotherapy_notes: bool = False
    section6_psychotherapy_notes_date: Optional[date] = None
    section6_psychotherapy_notes_signature: Optional[str] = None

    # Validators to convert empty strings to None for date fields
    @field_validator(
        "section1_date_of_birth",
        "section4_expiration_date",
        "section6_communicable_disease_date",
        "section6_reproductive_health_date",
        "section6_hiv_test_results_date",
        "section6_mental_health_records_date",
        "section6_substance_use_disorder_date",
        "section6_other_date",
        "section6_psychotherapy_notes_date",
        "section10_signature_date",
        mode="before",
    )
    @classmethod
    def convert_empty_date_to_none(cls, v: Union[str, date, None]) -> Optional[date]:
        """Convert empty strings to None for date fields."""
        if v == "" or v is None:
            return None
        return v
    # Section 7
    section7_healthcare: bool = False
    section7_research: bool = False
    section7_marketing: bool = False
    section7_sale: bool = False
    section7_legal: bool = False
    section7_other: bool = False
    section7_other_details: Optional[str] = None
    # Section 9
    section9_additional_information: Optional[str] = None
    # Section 10
    section10_name_of_patient_client: Optional[str] = None
    section10_signature_date: Optional[date] = None
    section10_name_of_signatory_if_not_patient: Optional[str] = None
    section10_authority_to_sign: Optional[str] = None
    section10_name_of_translator: Optional[str] = None
    section10_signature_of_translator: Optional[str] = None


class HipaaReleaseFormUpdate(BaseModel):
    """All fields optional for partial updates."""

    section1_last_name: Optional[str] = None
    section1_first_name: Optional[str] = None
    section1_middle_name: Optional[str] = None
    section1_date_of_birth: Optional[date] = None
    section1_reference_number: Optional[str] = None
    section1_address: Optional[str] = None
    section1_country: Optional[str] = None
    section2_name: Optional[str] = None
    section2_address: Optional[str] = None
    section2_country: Optional[str] = None
    section3_name: Optional[str] = None
    section3_relationship_to_patient: Optional[str] = None
    section3_phone_number: Optional[str] = None
    section3_address: Optional[str] = None
    section3_country: Optional[str] = None
    section4_expiration_date: Optional[date] = None
    section4_expiration_event: Optional[str] = None
    section5_medical_records: Optional[bool] = None
    section5_dental_records: Optional[bool] = None
    section5_other_non_specific: Optional[bool] = None
    section5_non_specific_records_details: Optional[str] = None
    section6_communicable_disease: Optional[bool] = None
    section6_communicable_disease_date: Optional[date] = None
    section6_communicable_disease_signature: Optional[str] = None
    section6_reproductive_health: Optional[bool] = None
    section6_reproductive_health_date: Optional[date] = None
    section6_reproductive_health_signature: Optional[str] = None
    section6_hiv_test_results: Optional[bool] = None
    section6_hiv_test_results_date: Optional[date] = None
    section6_hiv_test_results_signature: Optional[str] = None
    section6_mental_health_records: Optional[bool] = None
    section6_mental_health_records_date: Optional[date] = None
    section6_mental_health_records_signature: Optional[str] = None
    section6_substance_use_disorder: Optional[bool] = None
    section6_substance_use_disorder_date: Optional[date] = None
    section6_substance_use_disorder_signature: Optional[str] = None
    section6_other: Optional[bool] = None
    section6_other_date: Optional[date] = None
    section6_other_signature: Optional[str] = None
    section6_other_records_details: Optional[str] = None
    section6_psychotherapy_notes: Optional[bool] = None
    section6_psychotherapy_notes_date: Optional[date] = None
    section6_psychotherapy_notes_signature: Optional[str] = None

    # Validators to convert empty strings to None for date fields
    @field_validator(
        "section1_date_of_birth",
        "section4_expiration_date",
        "section6_communicable_disease_date",
        "section6_reproductive_health_date",
        "section6_hiv_test_results_date",
        "section6_mental_health_records_date",
        "section6_substance_use_disorder_date",
        "section6_other_date",
        "section6_psychotherapy_notes_date",
        "section10_signature_date",
        mode="before",
    )
    @classmethod
    def convert_empty_date_to_none(cls, v: Union[str, date, None]) -> Optional[date]:
        """Convert empty strings to None for date fields."""
        if v == "" or v is None:
            return None
        return v
    section7_healthcare: Optional[bool] = None
    section7_research: Optional[bool] = None
    section7_marketing: Optional[bool] = None
    section7_sale: Optional[bool] = None
    section7_legal: Optional[bool] = None
    section7_other: Optional[bool] = None
    section7_other_details: Optional[str] = None
    section9_additional_information: Optional[str] = None
    section10_name_of_patient_client: Optional[str] = None
    section10_signature_date: Optional[date] = None
    section10_name_of_signatory_if_not_patient: Optional[str] = None
    section10_authority_to_sign: Optional[str] = None
    section10_name_of_translator: Optional[str] = None
    section10_signature_of_translator: Optional[str] = None


class HipaaReleaseFormResponse(BaseModel):
    """Response schema – flat section fields plus id/patient_id/timestamps."""

    id: UUID
    patient_id: UUID
    section1_last_name: Optional[str] = None
    section1_first_name: Optional[str] = None
    section1_middle_name: Optional[str] = None
    section1_date_of_birth: Optional[str] = None
    section1_reference_number: Optional[str] = None
    section1_address: Optional[str] = None
    section1_country: Optional[str] = None
    section2_name: Optional[str] = None
    section2_address: Optional[str] = None
    section2_country: Optional[str] = None
    section3_name: Optional[str] = None
    section3_relationship_to_patient: Optional[str] = None
    section3_phone_number: Optional[str] = None
    section3_address: Optional[str] = None
    section3_country: Optional[str] = None
    section4_expiration_date: Optional[str] = None
    section4_expiration_event: Optional[str] = None
    section5_medical_records: bool = False
    section5_dental_records: bool = False
    section5_other_non_specific: bool = False
    section5_non_specific_records_details: Optional[str] = None
    section6_communicable_disease: bool = False
    section6_communicable_disease_date: Optional[str] = None
    section6_communicable_disease_signature: Optional[str] = None
    section6_reproductive_health: bool = False
    section6_reproductive_health_date: Optional[str] = None
    section6_reproductive_health_signature: Optional[str] = None
    section6_hiv_test_results: bool = False
    section6_hiv_test_results_date: Optional[str] = None
    section6_hiv_test_results_signature: Optional[str] = None
    section6_mental_health_records: bool = False
    section6_mental_health_records_date: Optional[str] = None
    section6_mental_health_records_signature: Optional[str] = None
    section6_substance_use_disorder: bool = False
    section6_substance_use_disorder_date: Optional[str] = None
    section6_substance_use_disorder_signature: Optional[str] = None
    section6_other: bool = False
    section6_other_date: Optional[str] = None
    section6_other_signature: Optional[str] = None
    section6_other_records_details: Optional[str] = None
    section6_psychotherapy_notes: bool = False
    section6_psychotherapy_notes_date: Optional[str] = None
    section6_psychotherapy_notes_signature: Optional[str] = None
    section7_healthcare: bool = False
    section7_research: bool = False
    section7_marketing: bool = False
    section7_sale: bool = False
    section7_legal: bool = False
    section7_other: bool = False
    section7_other_details: Optional[str] = None
    section9_additional_information: Optional[str] = None
    section10_name_of_patient_client: Optional[str] = None
    section10_signature_date: Optional[str] = None
    section10_name_of_signatory_if_not_patient: Optional[str] = None
    section10_authority_to_sign: Optional[str] = None
    section10_name_of_translator: Optional[str] = None
    section10_signature_of_translator: Optional[str] = None
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None

    class Config:
        from_attributes = True


class HipaaReleaseFormListResponse(BaseModel):
    status: bool = True
    message: str = "HIPAA release forms retrieved successfully"
    data: dict

    class Config:
        from_attributes = True


class HipaaReleaseFormSingleResponse(BaseModel):
    status: bool = True
    message: str = ""
    data: dict

    class Config:
        from_attributes = True
