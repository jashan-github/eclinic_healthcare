"""add_waiver_settings_to_admin_settings

Add waiver settings: enable/disable and single waiver percentage (0-100%).

Revision ID: waiver_settings_001
Revises: admin_email_notification_toggles_001
Create Date: 2026-01-29 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "waiver_settings_001"
down_revision = "admin_email_notification_toggles_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "admin_settings",
        sa.Column(
            "waiver_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="If enabled, waiver feature is available; admin sets allowed percentage (0-100%)",
        ),
    )
    op.add_column(
        "admin_settings",
        sa.Column(
            "waiver_percent",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="Allowed waiver percentage (0-100)",
        ),
    )
    op.create_check_constraint(
        "admin_settings_waiver_percent_range",
        "admin_settings",
        "waiver_percent >= 0 AND waiver_percent <= 100",
    )


def downgrade() -> None:
    op.drop_constraint("admin_settings_waiver_percent_range", "admin_settings", type_="check")
    op.drop_column("admin_settings", "waiver_percent")
    op.drop_column("admin_settings", "waiver_enabled")
