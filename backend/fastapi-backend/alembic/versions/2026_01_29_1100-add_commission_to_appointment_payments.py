"""add_commission_to_appointment_payments

Add commission_rate and commission_earned to appointment_payments.
Commission is stored when payment is marked COMPLETED (only upcoming: rate changes do not affect past payments).

Revision ID: appointment_payments_commission_001
Revises: service_commissions_001
Create Date: 2026-01-29 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "appointment_payments_commission_001"
down_revision = "service_commissions_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "appointment_payments",
        sa.Column(
            "commission_rate",
            sa.Numeric(5, 2),
            nullable=True,
            comment="Commission rate (1-100) at time of payment completion; used for reporting only.",
        ),
    )
    op.add_column(
        "appointment_payments",
        sa.Column(
            "commission_earned",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Commission amount earned at time of payment completion; used for reporting only.",
        ),
    )


def downgrade() -> None:
    op.drop_column("appointment_payments", "commission_earned")
    op.drop_column("appointment_payments", "commission_rate")
