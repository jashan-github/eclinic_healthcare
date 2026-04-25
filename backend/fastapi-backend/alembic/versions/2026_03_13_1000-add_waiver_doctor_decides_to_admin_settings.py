"""add_waiver_doctor_decides_to_admin_settings

When waiver_doctor_decides is True and waiver_enabled, doctor sets waiver (0,25,50,75,100%) at accept; admin waiver_percent ignored.

Revision ID: waiver_doctor_decides_001
Revises: add_email_notify_rejected
Create Date: 2026-03-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "waiver_doctor_decides_001"
down_revision = "add_email_notify_rejected"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "admin_settings",
        sa.Column(
            "waiver_doctor_decides",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="If True (and waiver_enabled), doctor sets waiver at accept (0,25,50,75,100%); admin waiver_percent ignored",
        ),
    )


def downgrade() -> None:
    op.drop_column("admin_settings", "waiver_doctor_decides")
