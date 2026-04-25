"""create_doctor_service_availability_table

Links doctor availability slots to specific services with custom slot durations.
Allows different duration per availability window per service.

Revision ID: create_doctor_service_availability_001
Revises: add_day_of_week_001
Create Date: 2025-12-29 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_doctor_service_availability_001'
down_revision = 'add_day_of_week_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create doctor_service_availability table.
    
    Links doctor availability slots to specific services with custom slot durations.
    This allows a doctor to offer different services with different durations
    on specific availability windows.
    """
    op.create_table(
        'doctor_service_availability',
        # Primary key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
            comment='Primary key (UUID)'
        ),
        # Foreign key to doctor_availability
        sa.Column(
            'availability_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('doctor_availability.id', ondelete='CASCADE'),
            nullable=False,
            comment='Reference to doctor availability slot'
        ),
        # Foreign key to services
        sa.Column(
            'service_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('services.id', ondelete='CASCADE'),
            nullable=False,
            comment='Reference to service'
        ),
        # Slot duration for this availability-service combination
        sa.Column(
            'slot_duration_minutes',
            sa.Integer(),
            nullable=False,
            comment='Duration of appointment slot in minutes (5-360)'
        ),
        # Timestamp
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Record creation timestamp (UTC)'
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint('id', name='doctor_service_availability_pkey'),
        # Unique constraint: one service per availability slot
        sa.UniqueConstraint(
            'availability_id',
            'service_id',
            name='doctor_service_availability_avail_service_unique'
        ),
        # Check constraint: slot duration between 5 and 360 minutes
        sa.CheckConstraint(
            'slot_duration_minutes >= 5 AND slot_duration_minutes <= 360',
            name='doctor_service_availability_duration_check'
        ),
        comment='Links doctor availability slots to specific services with custom durations'
    )
    
    # Create indexes for foreign keys (performance)
    op.create_index(
        'ix_doctor_service_availability_availability_id',
        'doctor_service_availability',
        ['availability_id'],
        unique=False
    )
    
    op.create_index(
        'ix_doctor_service_availability_service_id',
        'doctor_service_availability',
        ['service_id'],
        unique=False
    )


def downgrade() -> None:
    """
    Drop doctor_service_availability table and indexes.
    """
    # Drop indexes first
    op.drop_index(
        'ix_doctor_service_availability_service_id',
        table_name='doctor_service_availability'
    )
    op.drop_index(
        'ix_doctor_service_availability_availability_id',
        table_name='doctor_service_availability'
    )
    
    # Drop table
    op.drop_table('doctor_service_availability')
