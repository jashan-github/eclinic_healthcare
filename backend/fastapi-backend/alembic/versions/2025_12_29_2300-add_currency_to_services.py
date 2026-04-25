"""add_currency_to_services

Add currency column to services table for pricing support.
Existing rows will get default currency 'INR'.

Revision ID: add_currency_to_services_001
Revises: create_appointments_001
Create Date: 2025-12-29 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_currency_to_services_001'
down_revision = 'create_appointments_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add currency column to services table.
    
    - Adds currency VARCHAR(3) NOT NULL DEFAULT 'INR'
    - Existing rows automatically get 'INR' as default
    - Price column remains untouched
    """
    # Add currency column with default value
    # Existing rows will automatically get 'INR' due to server_default
    op.add_column(
        'services',
        sa.Column(
            'currency',
            sa.String(3),
            nullable=False,
            server_default='INR',
            comment='Currency code (ISO 4217, default: INR)'
        )
    )
    
    # Add check constraint to ensure currency is exactly 3 characters
    op.create_check_constraint(
        'services_currency_length_check',
        'services',
        "LENGTH(currency) = 3"
    )


def downgrade() -> None:
    """
    Remove currency column from services table.
    """
    # Drop check constraint first
    op.drop_constraint(
        'services_currency_length_check',
        'services',
        type_='check'
    )
    
    # Drop currency column
    op.drop_column('services', 'currency')
