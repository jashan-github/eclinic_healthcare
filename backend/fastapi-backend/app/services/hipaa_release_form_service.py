"""
HIPAA Release Form Service
Business logic for HIPAA authorization form (Pure Health BV sections 1–10).
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.hipaa_release_form import HipaaReleaseForm
from app.models.user import User
from app.models.profile import UserProfile
from app.core.exceptions import NotFoundException
from app.schemas.hipaa_release_form import HipaaReleaseFormCreate
from loguru import logger


def _date_str(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def _dt_str(dt) -> Optional[str]:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


class HipaaReleaseFormService:
    """Service for managing HIPAA release forms (sections 1–10)."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, patient_id: UUID, payload: HipaaReleaseFormCreate) -> HipaaReleaseForm:
        """
        Create a HIPAA release form for a patient.
        """
        patient = (
            self.db.query(User)
            .filter(and_(User.id == patient_id, User.deleted_at.is_(None)))
            .first()
        )
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient with this ID does not exist"]},
            )

        form = HipaaReleaseForm(
            patient_id=patient_id,
            **payload.model_dump(),
        )
        self.db.add(form)
        
        # Mark patient profile as having filled HIPAA form
        profile = (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == patient_id)
            .first()
        )
        if profile:
            profile.hipaa_form_filled = True
            logger.info(f"Marked HIPAA form as filled for patient {patient_id}")
        else:
            # Create profile if it doesn't exist (shouldn't happen, but handle gracefully)
            logger.warning(f"UserProfile not found for patient {patient_id}, creating one")
            profile = UserProfile(user_id=patient_id, hipaa_form_filled=True)
            self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(form)
        logger.info(f"Created HIPAA release form for patient {patient_id} (id: {form.id})")
        return form

    def get_by_id(self, form_id: UUID, patient_id: UUID) -> HipaaReleaseForm:
        """Get a HIPAA release form by ID (scoped to patient)."""
        form = (
            self.db.query(HipaaReleaseForm)
            .filter(
                and_(
                    HipaaReleaseForm.id == form_id,
                    HipaaReleaseForm.patient_id == patient_id,
                    HipaaReleaseForm.deleted_at.is_(None),
                )
            )
            .first()
        )
        if not form:
            raise NotFoundException(
                message="HIPAA release form not found",
                errors={"id": ["Form with this ID does not exist or you do not have access"]},
            )
        return form

    def get_by_patient_id(
        self,
        patient_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[HipaaReleaseForm]:
        """Get all HIPAA release forms for a patient."""
        query = (
            self.db.query(HipaaReleaseForm)
            .filter(
                and_(
                    HipaaReleaseForm.patient_id == patient_id,
                    HipaaReleaseForm.deleted_at.is_(None),
                )
            )
            .order_by(
                HipaaReleaseForm.section10_signature_date.desc().nullslast(),
                HipaaReleaseForm.created_at.desc(),
            )
        )
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def format_form_response(self, form: HipaaReleaseForm) -> dict:
        """Format a HipaaReleaseForm for API response (all section fields)."""
        return {
            "id": str(form.id),
            "patient_id": str(form.patient_id),
            # Section 1
            "section1_last_name": form.section1_last_name,
            "section1_first_name": form.section1_first_name,
            "section1_middle_name": form.section1_middle_name,
            "section1_date_of_birth": _date_str(form.section1_date_of_birth),
            "section1_reference_number": form.section1_reference_number,
            "section1_address": form.section1_address,
            "section1_country": form.section1_country,
            # Section 2
            "section2_name": form.section2_name,
            "section2_address": form.section2_address,
            "section2_country": form.section2_country,
            # Section 3
            "section3_name": form.section3_name,
            "section3_relationship_to_patient": form.section3_relationship_to_patient,
            "section3_phone_number": form.section3_phone_number,
            "section3_address": form.section3_address,
            "section3_country": form.section3_country,
            # Section 4
            "section4_expiration_date": _date_str(form.section4_expiration_date),
            "section4_expiration_event": form.section4_expiration_event,
            # Section 5
            "section5_medical_records": form.section5_medical_records,
            "section5_dental_records": form.section5_dental_records,
            "section5_other_non_specific": form.section5_other_non_specific,
            "section5_non_specific_records_details": form.section5_non_specific_records_details,
            # Section 6
            "section6_communicable_disease": form.section6_communicable_disease,
            "section6_communicable_disease_date": _date_str(form.section6_communicable_disease_date),
            "section6_communicable_disease_signature": form.section6_communicable_disease_signature,
            "section6_reproductive_health": form.section6_reproductive_health,
            "section6_reproductive_health_date": _date_str(form.section6_reproductive_health_date),
            "section6_reproductive_health_signature": form.section6_reproductive_health_signature,
            "section6_hiv_test_results": form.section6_hiv_test_results,
            "section6_hiv_test_results_date": _date_str(form.section6_hiv_test_results_date),
            "section6_hiv_test_results_signature": form.section6_hiv_test_results_signature,
            "section6_mental_health_records": form.section6_mental_health_records,
            "section6_mental_health_records_date": _date_str(form.section6_mental_health_records_date),
            "section6_mental_health_records_signature": form.section6_mental_health_records_signature,
            "section6_substance_use_disorder": form.section6_substance_use_disorder,
            "section6_substance_use_disorder_date": _date_str(form.section6_substance_use_disorder_date),
            "section6_substance_use_disorder_signature": form.section6_substance_use_disorder_signature,
            "section6_other": form.section6_other,
            "section6_other_date": _date_str(form.section6_other_date),
            "section6_other_signature": form.section6_other_signature,
            "section6_other_records_details": form.section6_other_records_details,
            "section6_psychotherapy_notes": form.section6_psychotherapy_notes,
            "section6_psychotherapy_notes_date": _date_str(form.section6_psychotherapy_notes_date),
            "section6_psychotherapy_notes_signature": form.section6_psychotherapy_notes_signature,
            # Section 7
            "section7_healthcare": form.section7_healthcare,
            "section7_research": form.section7_research,
            "section7_marketing": form.section7_marketing,
            "section7_sale": form.section7_sale,
            "section7_legal": form.section7_legal,
            "section7_other": form.section7_other,
            "section7_other_details": form.section7_other_details,
            # Section 9
            "section9_additional_information": form.section9_additional_information,
            # Section 10
            "section10_name_of_patient_client": form.section10_name_of_patient_client,
            "section10_signature_date": _date_str(form.section10_signature_date),
            "section10_name_of_signatory_if_not_patient": form.section10_name_of_signatory_if_not_patient,
            "section10_authority_to_sign": form.section10_authority_to_sign,
            "section10_name_of_translator": form.section10_name_of_translator,
            "section10_signature_of_translator": form.section10_signature_of_translator,
            # Base
            "created_at": _dt_str(form.created_at),
            "updated_at": _dt_str(form.updated_at),
            "deleted_at": _dt_str(form.deleted_at),
        }
