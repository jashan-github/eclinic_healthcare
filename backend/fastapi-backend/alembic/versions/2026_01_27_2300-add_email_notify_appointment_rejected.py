"""Add email_notify_appointment_rejected to admin_settings

Revision ID: add_email_notify_rejected
Revises: 2026_01_30_1000
Create Date: 2026-01-27 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_email_notify_rejected'
down_revision: Union[str, None] = 'waiver_payments_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email_notify_appointment_rejected column to admin_settings
    op.add_column(
        'admin_settings',
        sa.Column(
            'email_notify_appointment_rejected',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
            comment='If enabled, send email to patient when doctor rejects appointment request'
        )
    )


def downgrade() -> None:
    # Remove email_notify_appointment_rejected column
    op.drop_column('admin_settings', 'email_notify_appointment_rejected')
