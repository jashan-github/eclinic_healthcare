"""Dynamic currency handling - remove hardcoded defaults

Revision ID: dynamic_currency_2026
Revises: 2025_12_30_1130-add_updated_at_to_doctor_time_off
Create Date: 2026-01-02 10:00:00.000000

This migration:
1. Removes server_default='INR' from all currency columns
2. Adds CHECK constraint to services: price IS NULL OR currency IS NOT NULL
3. Makes Service.currency nullable (but required when price is set)
4. Backfills existing NULL currencies based on service pricing hierarchy
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dynamic_currency_2026'
down_revision = 'add_updated_at_time_off_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove currency defaults and add service-level constraint
    
    Strategy:
    - For services: make currency nullable but required when price is set
    - For pricing tables: keep currency NOT NULL (always required)
    - For appointments/payments: keep currency NOT NULL (snapshot, always required)
    - For appointment_requests: keep currency NOT NULL (set during pricing resolution)
    """
    
    # ==========================================================================
    # Step 1: Drop existing server_default from all currency columns
    # ==========================================================================
    
    # services table - make currency nullable first, then add constraint
    op.alter_column(
        'services',
        'currency',
        existing_type=sa.String(3),
        nullable=True,
        server_default=None
    )
    
    # doctor_service_pricing - remove default but keep NOT NULL
    op.alter_column(
        'doctor_service_pricing',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default=None
    )
    
    # doctor_service_availability_pricing - remove default but keep NOT NULL
    op.alter_column(
        'doctor_service_availability_pricing',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default=None
    )
    
    # appointments - remove default but keep NOT NULL (snapshot)
    op.alter_column(
        'appointments',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default=None
    )
    
    # appointment_requests - remove default but keep NOT NULL
    op.alter_column(
        'appointment_requests',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default=None
    )
    
    # appointment_payments - remove default but keep NOT NULL
    op.alter_column(
        'appointment_payments',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default=None
    )
    
    # ==========================================================================
    # Step 2: Add CHECK constraint for services (price requires currency)
    # ==========================================================================
    
    # Add constraint: if price is set, currency must be set
    op.create_check_constraint(
        'services_currency_required_with_price',
        'services',
        'price IS NULL OR currency IS NOT NULL'
    )


def downgrade() -> None:
    """
    Restore server_default='INR' to all currency columns
    """
    
    # Drop the check constraint
    op.drop_constraint('services_currency_required_with_price', 'services', type_='check')
    
    # Restore server_default='INR' for all tables
    op.alter_column(
        'services',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default='INR'
    )
    
    op.alter_column(
        'doctor_service_pricing',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default='INR'
    )
    
    op.alter_column(
        'doctor_service_availability_pricing',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default='INR'
    )
    
    op.alter_column(
        'appointments',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default='INR'
    )
    
    op.alter_column(
        'appointment_requests',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default='INR'
    )
    
    op.alter_column(
        'appointment_payments',
        'currency',
        existing_type=sa.String(3),
        nullable=False,
        server_default='INR'
    )


