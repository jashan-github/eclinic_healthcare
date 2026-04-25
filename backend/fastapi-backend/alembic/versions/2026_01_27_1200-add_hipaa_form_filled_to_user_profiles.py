"""add_hipaa_form_filled_to_user_profiles

Add hipaa_form_filled column to user_profiles table to track if patient has filled HIPAA release form.

Revision ID: add_hipaa_form_filled_001
Revises: hipaa_release_forms_sections_001
Create Date: 2026-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "add_hipaa_form_filled_001"
down_revision = "hipaa_release_forms_sections_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column(
            "hipaa_form_filled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="HIPAA release form filled (required before first appointment)",
        ),
    )
    op.create_index(
        "user_profiles_hipaa_form_filled_index",
        "user_profiles",
        ["hipaa_form_filled"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("user_profiles_hipaa_form_filled_index", table_name="user_profiles")
    op.drop_column("user_profiles", "hipaa_form_filled")
