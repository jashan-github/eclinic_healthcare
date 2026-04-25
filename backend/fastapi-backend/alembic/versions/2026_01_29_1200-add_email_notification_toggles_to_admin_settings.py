"""add_email_notification_toggles_to_admin_settings

Add admin toggles to enable/disable email notifications: password reset, new appointment request (to doctor), appointment accepted (to patient).

Revision ID: admin_email_notification_toggles_001
Revises: appointment_payments_commission_001
Create Date: 2026-01-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "admin_email_notification_toggles_001"
down_revision = "appointment_payments_commission_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "admin_settings",
        sa.Column(
            "email_notify_password_reset",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="If enabled, send password reset email when user requests reset",
        ),
    )
    op.add_column(
        "admin_settings",
        sa.Column(
            "email_notify_new_appointment_request",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="If enabled, send email to doctor when patient creates appointment request",
        ),
    )
    op.add_column(
        "admin_settings",
        sa.Column(
            "email_notify_appointment_accepted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="If enabled, send email to patient when doctor accepts appointment request",
        ),
    )


def downgrade() -> None:
    op.drop_column("admin_settings", "email_notify_appointment_accepted")
    op.drop_column("admin_settings", "email_notify_new_appointment_request")
    op.drop_column("admin_settings", "email_notify_password_reset")
