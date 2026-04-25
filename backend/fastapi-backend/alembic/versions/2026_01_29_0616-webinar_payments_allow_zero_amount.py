"""webinar_payments_allow_zero_amount

Allow amount >= 0 in webinar_payments for free webinar registrations (amount 0).

Revision ID: webinar_payments_amount_001
Revises: create_webinar_payments_001
Create Date: 2026-01-29 06:16:00.000000

"""
from alembic import op

revision = 'webinar_payments_amount_001'
down_revision = 'create_webinar_payments_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        'webinar_payments_amount_check',
        'webinar_payments',
        type_='check'
    )
    op.create_check_constraint(
        'webinar_payments_amount_check',
        'webinar_payments',
        'amount >= 0'
    )


def downgrade() -> None:
    op.drop_constraint(
        'webinar_payments_amount_check',
        'webinar_payments',
        type_='check'
    )
    op.create_check_constraint(
        'webinar_payments_amount_check',
        'webinar_payments',
        'amount > 0'
    )
