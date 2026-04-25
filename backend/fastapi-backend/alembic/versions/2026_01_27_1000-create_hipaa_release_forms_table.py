"""create_hipaa_release_forms_table

Create hipaa_release_forms table for storing HIPAA authorization/release form details.

Revision ID: create_hipaa_release_forms_001
Revises: create_notification_reads_001
Create Date: 2026-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "create_hipaa_release_forms_001"
down_revision = "create_notification_reads_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
        sa.Column(
            "individual_name",
            sa.String(255),
            nullable=False,
            comment="Full name of individual authorizing release",
        ),
        sa.Column("date_of_birth", sa.Date(), nullable=True, comment="Date of birth"),
        sa.Column("address", sa.Text(), nullable=True, comment="Address"),
        sa.Column("phone", sa.String(50), nullable=True, comment="Phone number"),
        sa.Column("email", sa.String(255), nullable=True, comment="Email address"),
        sa.Column(
            "authorization_purpose",
            sa.Text(),
            nullable=True,
            comment="Purpose of the disclosure",
        ),
        sa.Column(
            "covered_entity",
            sa.String(500),
            nullable=True,
            comment="Name of covered entity (e.g. Pure Health BV)",
        ),
        sa.Column(
            "recipient_name",
            sa.String(500),
            nullable=True,
            comment="Name of recipient of PHI",
        ),
        sa.Column(
            "recipient_address",
            sa.Text(),
            nullable=True,
            comment="Recipient address",
        ),
        sa.Column(
            "include_medical",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="Include medical records",
        ),
        sa.Column(
            "include_mental_health",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="Include mental health records",
        ),
        sa.Column(
            "include_substance_abuse",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="Include substance abuse records",
        ),
        sa.Column(
            "expiration_date",
            sa.Date(),
            nullable=True,
            comment="Expiration date; NULL = no expiration",
        ),
        sa.Column(
            "right_to_revoke_noted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="Patient informed of right to revoke",
        ),
        sa.Column(
            "signature_name",
            sa.String(255),
            nullable=True,
            comment="Name as signed",
        ),
        sa.Column("signature_date", sa.Date(), nullable=True, comment="Date signed"),
        sa.Column(
            "relationship_to_patient",
            sa.String(100),
            nullable=True,
            comment="Relationship if signing for patient",
        ),
        sa.Column(
            "witnessed_by",
            sa.String(255),
            nullable=True,
            comment="Witness name if applicable",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        comment="HIPAA authorization for release of protected health information",
    )

    op.create_index(
        "hipaa_release_forms_patient_id_index",
        "hipaa_release_forms",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "hipaa_release_forms_signature_date_index",
        "hipaa_release_forms",
        ["signature_date"],
        unique=False,
    )
    op.create_index(
        "hipaa_release_forms_created_at_index",
        "hipaa_release_forms",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "hipaa_release_forms_deleted_at_index",
        "hipaa_release_forms",
        ["deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("hipaa_release_forms_deleted_at_index", table_name="hipaa_release_forms")
    op.drop_index("hipaa_release_forms_created_at_index", table_name="hipaa_release_forms")
    op.drop_index("hipaa_release_forms_signature_date_index", table_name="hipaa_release_forms")
    op.drop_index("hipaa_release_forms_patient_id_index", table_name="hipaa_release_forms")
    op.drop_table("hipaa_release_forms")
