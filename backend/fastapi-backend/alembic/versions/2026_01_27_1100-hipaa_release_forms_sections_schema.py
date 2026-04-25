"""hipaa_release_forms_sections_schema

Replace hipaa_release_forms table with section-based schema matching Pure Health BV HIPAA form.

Revision ID: hipaa_release_forms_sections_001
Revises: create_hipaa_release_forms_001
Create Date: 2026-01-27 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "hipaa_release_forms_sections_001"
down_revision = "create_hipaa_release_forms_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("hipaa_release_forms")

    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.create_table(
        "hipaa_release_forms",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="Patient user ID",
        ),
        # Section 1
        sa.Column("section1_last_name", sa.String(255), nullable=True, comment="Section 1: Last Name"),
        sa.Column("section1_first_name", sa.String(255), nullable=True, comment="Section 1: First Name"),
        sa.Column("section1_middle_name", sa.String(255), nullable=True, comment="Section 1: Middle Name"),
        sa.Column("section1_date_of_birth", sa.Date(), nullable=True, comment="Section 1: Date of Birth"),
        sa.Column("section1_reference_number", sa.String(255), nullable=True, comment="Section 1: Reference Number"),
        sa.Column("section1_address", sa.Text(), nullable=True, comment="Section 1: Address"),
        sa.Column("section1_country", sa.String(255), nullable=True, comment="Section 1: Country"),
        # Section 2
        sa.Column("section2_name", sa.String(500), nullable=True, comment="Section 2: Name"),
        sa.Column("section2_address", sa.Text(), nullable=True, comment="Section 2: Address"),
        sa.Column("section2_country", sa.String(255), nullable=True, comment="Section 2: Country"),
        # Section 3
        sa.Column("section3_name", sa.String(500), nullable=True, comment="Section 3: Name"),
        sa.Column("section3_relationship_to_patient", sa.String(255), nullable=True, comment="Section 3: Relationship to patient"),
        sa.Column("section3_phone_number", sa.String(50), nullable=True, comment="Section 3: Phone number"),
        sa.Column("section3_address", sa.Text(), nullable=True, comment="Section 3: Address"),
        sa.Column("section3_country", sa.String(255), nullable=True, comment="Section 3: Country"),
        # Section 4
        sa.Column("section4_expiration_date", sa.Date(), nullable=True, comment="Section 4: Expiration date"),
        sa.Column("section4_expiration_event", sa.String(500), nullable=True, comment="Section 4: Expiration Event"),
        # Section 5
        sa.Column("section5_medical_records", sa.Boolean(), nullable=False, server_default=sa.false(), comment="Section 5: Medical Records"),
        sa.Column("section5_dental_records", sa.Boolean(), nullable=False, server_default=sa.false(), comment="Section 5: Dental Records"),
        sa.Column("section5_other_non_specific", sa.Boolean(), nullable=False, server_default=sa.false(), comment="Section 5: Other Non-Specific"),
        sa.Column("section5_non_specific_records_details", sa.Text(), nullable=True, comment="Section 5: Non-Specific Records Details"),
        # Section 6
        sa.Column("section6_communicable_disease", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section6_communicable_disease_date", sa.Date(), nullable=True),
        sa.Column("section6_communicable_disease_signature", sa.String(500), nullable=True),
        sa.Column("section6_reproductive_health", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section6_reproductive_health_date", sa.Date(), nullable=True),
        sa.Column("section6_reproductive_health_signature", sa.String(500), nullable=True),
        sa.Column("section6_hiv_test_results", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section6_hiv_test_results_date", sa.Date(), nullable=True),
        sa.Column("section6_hiv_test_results_signature", sa.String(500), nullable=True),
        sa.Column("section6_mental_health_records", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section6_mental_health_records_date", sa.Date(), nullable=True),
        sa.Column("section6_mental_health_records_signature", sa.String(500), nullable=True),
        sa.Column("section6_substance_use_disorder", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section6_substance_use_disorder_date", sa.Date(), nullable=True),
        sa.Column("section6_substance_use_disorder_signature", sa.String(500), nullable=True),
        sa.Column("section6_other", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section6_other_date", sa.Date(), nullable=True),
        sa.Column("section6_other_signature", sa.String(500), nullable=True),
        sa.Column("section6_other_records_details", sa.Text(), nullable=True),
        sa.Column("section6_psychotherapy_notes", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section6_psychotherapy_notes_date", sa.Date(), nullable=True),
        sa.Column("section6_psychotherapy_notes_signature", sa.String(500), nullable=True),
        # Section 7
        sa.Column("section7_healthcare", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section7_research", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section7_marketing", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section7_sale", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section7_legal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section7_other", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section7_other_details", sa.Text(), nullable=True),
        # Section 9
        sa.Column("section9_additional_information", sa.Text(), nullable=True),
        # Section 10
        sa.Column("section10_name_of_patient_client", sa.String(500), nullable=True),
        sa.Column("section10_signature_date", sa.Date(), nullable=True),
        sa.Column("section10_name_of_signatory_if_not_patient", sa.String(500), nullable=True),
        sa.Column("section10_authority_to_sign", sa.String(500), nullable=True),
        sa.Column("section10_name_of_translator", sa.String(500), nullable=True),
        sa.Column("section10_signature_of_translator", sa.String(500), nullable=True),
        # Base
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        comment="HIPAA release form (Pure Health BV) sections 1–10",
    )
    op.create_index("hipaa_release_forms_patient_id_index", "hipaa_release_forms", ["patient_id"], unique=False)
    op.create_index("hipaa_release_forms_s10_signature_date_index", "hipaa_release_forms", ["section10_signature_date"], unique=False)
    op.create_index("hipaa_release_forms_created_at_index", "hipaa_release_forms", ["created_at"], unique=False)
    op.create_index("hipaa_release_forms_deleted_at_index", "hipaa_release_forms", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("hipaa_release_forms_deleted_at_index", table_name="hipaa_release_forms")
    op.drop_index("hipaa_release_forms_created_at_index", table_name="hipaa_release_forms")
    op.drop_index("hipaa_release_forms_s10_signature_date_index", table_name="hipaa_release_forms")
    op.drop_index("hipaa_release_forms_patient_id_index", table_name="hipaa_release_forms")
    op.drop_table("hipaa_release_forms")
    # Recreate original table from create_hipaa_release_forms_001
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.create_table(
        "hipaa_release_forms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("individual_name", sa.String(255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("authorization_purpose", sa.Text(), nullable=True),
        sa.Column("covered_entity", sa.String(500), nullable=True),
        sa.Column("recipient_name", sa.String(500), nullable=True),
        sa.Column("recipient_address", sa.Text(), nullable=True),
        sa.Column("include_medical", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("include_mental_health", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("include_substance_abuse", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("right_to_revoke_noted", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("signature_name", sa.String(255), nullable=True),
        sa.Column("signature_date", sa.Date(), nullable=True),
        sa.Column("relationship_to_patient", sa.String(100), nullable=True),
        sa.Column("witnessed_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("hipaa_release_forms_patient_id_index", "hipaa_release_forms", ["patient_id"], unique=False)
    op.create_index("hipaa_release_forms_signature_date_index", "hipaa_release_forms", ["signature_date"], unique=False)
    op.create_index("hipaa_release_forms_created_at_index", "hipaa_release_forms", ["created_at"], unique=False)
    op.create_index("hipaa_release_forms_deleted_at_index", "hipaa_release_forms", ["deleted_at"], unique=False)
