"""add_day_of_week_to_doctor_services

Revision ID: add_day_of_week_001
Revises: create_doctor_services_001
Create Date: 2025-12-29 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_day_of_week_001'
down_revision = 'create_doctor_services_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add day_of_week column
    # NULL = default duration for all days
    # 0 = Sunday, 1 = Monday, ..., 6 = Saturday
    op.add_column(
        'doctor_services',
        sa.Column(
            'day_of_week',
            sa.SmallInteger(),
            nullable=True,
            comment='Day of week (0=Sunday, 6=Saturday). NULL = default for all days'
        )
    )
    
    # Add check constraint for day_of_week values (0-6 or NULL)
    op.create_check_constraint(
        'doctor_services_day_of_week_check',
        'doctor_services',
        'day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6)'
    )
    
    # Drop existing unique constraint (doctor_id, service_id)
    op.drop_constraint('doctor_services_doctor_service_unique', 'doctor_services', type_='unique')
    
    # Add new unique constraint including day_of_week
    # This allows same doctor+service to have different durations per day
    op.create_unique_constraint(
        'doctor_services_doctor_service_day_unique',
        'doctor_services',
        ['doctor_id', 'service_id', 'day_of_week']
    )
    
    # Add composite index for lookups
    op.create_index(
        'doctor_services_doctor_service_day_index',
        'doctor_services',
        ['doctor_id', 'service_id', 'day_of_week']
    )


def downgrade() -> None:
    # Drop composite index
    op.drop_index('doctor_services_doctor_service_day_index', table_name='doctor_services')
    
    # Drop new unique constraint
    op.drop_constraint('doctor_services_doctor_service_day_unique', 'doctor_services', type_='unique')
    
    # Restore original unique constraint
    # Note: This may fail if there are duplicate (doctor_id, service_id) pairs
    # with different day_of_week values
    op.create_unique_constraint(
        'doctor_services_doctor_service_unique',
        'doctor_services',
        ['doctor_id', 'service_id']
    )
    
    # Drop check constraint
    op.drop_constraint('doctor_services_day_of_week_check', 'doctor_services', type_='check')
    
    # Drop day_of_week column
    op.drop_column('doctor_services', 'day_of_week')
