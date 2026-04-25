"""add_waiver_to_appointment_and_webinar_payments

Add waiver_percent and amount_before_waiver for tracking; allow amount >= 0 for 100% waiver.

Revision ID: waiver_payments_001
Revises: waiver_settings_001
Create Date: 2026-01-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "waiver_payments_001"
down_revision = "waiver_settings_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # appointment_requests: store waiver % when payment is initialized (for display consistency)
    op.add_column(
        "appointment_requests",
        sa.Column(
            "waiver_percent",
            sa.Integer(),
            nullable=True,
            comment="Waiver percentage applied (0-100) when payment was initialized; for tracking",
        ),
    )

    # appointment_payments: waiver tracking and allow 0 amount
    op.add_column(
        "appointment_payments",
        sa.Column(
            "waiver_percent",
            sa.Integer(),
            nullable=True,
            comment="Waiver percentage applied (0-100) at payment creation",
        ),
    )
    op.add_column(
        "appointment_payments",
        sa.Column(
            "amount_before_waiver",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Original amount before waiver (request price_amount)",
        ),
    )
    op.drop_constraint("appointment_payments_amount_check", "appointment_payments", type_="check")
    op.create_check_constraint(
        "appointment_payments_amount_check",
        "appointment_payments",
        "amount >= 0",
    )

    # webinar_payments: waiver tracking (amount >= 0 already allowed)
    op.add_column(
        "webinar_payments",
        sa.Column(
            "waiver_percent",
            sa.Integer(),
            nullable=True,
            comment="Waiver percentage applied (0-100) at registration",
        ),
    )
    op.add_column(
        "webinar_payments",
        sa.Column(
            "amount_before_waiver",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Original price before waiver",
        ),
    )


def downgrade() -> None:
    op.drop_column("webinar_payments", "amount_before_waiver")
    op.drop_column("webinar_payments", "waiver_percent")
    op.drop_constraint("appointment_payments_amount_check", "appointment_payments", type_="check")
    op.create_check_constraint(
        "appointment_payments_amount_check",
        "appointment_payments",
        "amount > 0",
    )
    op.drop_column("appointment_payments", "amount_before_waiver")
    op.drop_column("appointment_payments", "waiver_percent")
    op.drop_column("appointment_requests", "waiver_percent")
