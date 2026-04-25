"""add_snapshot_fields_to_appointments

Add consultation_mode and duration_minutes snapshot fields to appointments table.
These fields store immutable snapshots at booking time.

Revision ID: add_appointment_snapshot_fields_001
Revises: add_consultation_mode_pricing_001
Create Date: 2025-12-30 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_appointment_snapshot_fields_001'
down_revision = 'add_consultation_mode_pricing_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add consultation_mode and duration_minutes snapshot fields to appointments table.
    """
    # Add consultation_mode column with default
    op.add_column(
        'appointments',
        sa.Column(
            'consultation_mode',
            sa.String(20),
            nullable=False,
            server_default='IN_CLINIC',
            comment='Consultation mode at booking time (snapshot, immutable). Used for visit type & billing.'
        )
    )
    
    # Add duration_minutes column (nullable first, then populate, then make NOT NULL)
    op.add_column(
        'appointments',
        sa.Column(
            'duration_minutes',
            sa.Integer(),
            nullable=True,
            comment='Slot duration in minutes at booking time (snapshot, immutable)'
        )
    )
    
    # Calculate duration from existing appointments (end_time - start_time)
    op.execute("""
        UPDATE appointments
        SET duration_minutes = EXTRACT(EPOCH FROM (end_time - start_time)) / 60
        WHERE duration_minutes IS NULL
    """)
    
    # Set default for any NULL values (shouldn't happen, but safety)
    op.execute("""
        UPDATE appointments
        SET duration_minutes = 30
        WHERE duration_minutes IS NULL
    """)
    
    # Make column NOT NULL
    op.alter_column(
        'appointments',
        'duration_minutes',
        nullable=False,
        server_default='30'
    )
    
    # Add check constraint for consultation_mode
    op.create_check_constraint(
        'appointments_consultation_mode_check',
        'appointments',
        "consultation_mode IN ('IN_CLINIC', 'TELECONSULTATION')"
    )
    
    # Add check constraint for duration_minutes
    op.create_check_constraint(
        'appointments_duration_check',
        'appointments',
        'duration_minutes >= 5 AND duration_minutes <= 360'
    )
    
    # Create index on consultation_mode for filtering
    op.create_index(
        'ix_appointments_consultation_mode',
        'appointments',
        ['consultation_mode'],
        unique=False
    )


def downgrade() -> None:
    """
    Remove consultation_mode and duration_minutes snapshot fields.
    """
    # Drop index
    op.drop_index(
        'ix_appointments_consultation_mode',
        table_name='appointments'
    )
    
    # Drop check constraints
    op.drop_constraint(
        'appointments_duration_check',
        'appointments',
        type_='check'
    )
    
    op.drop_constraint(
        'appointments_consultation_mode_check',
        'appointments',
        type_='check'
    )
    
    # Drop columns
    op.drop_column('appointments', 'duration_minutes')
    op.drop_column('appointments', 'consultation_mode')
