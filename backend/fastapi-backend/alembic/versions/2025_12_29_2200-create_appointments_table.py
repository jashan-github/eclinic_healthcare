"""create_appointments_table

Create appointments table with pricing snapshot at booking time.
Pricing is stored as a snapshot and never changes after booking.

Revision ID: create_appointments_001
Revises: create_pricing_tables_001
Create Date: 2025-12-29 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_appointments_001'
down_revision = 'create_pricing_tables_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create appointments table with pricing snapshot.
    
    Pricing snapshot fields:
    - price_amount: Price at booking time (never changes)
    - currency: Currency at booking time
    - pricing_source: Source of price (availability | doctor | global)
    """
    # Check if table already exists (idempotent)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if inspector.has_table('appointments'):
        # Table already exists, skip creation
        return
    
    op.create_table(
        'appointments',
        # Primary key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
            comment='Primary key (UUID)'
        ),
        # Foreign keys
        sa.Column(
            'doctor_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='RESTRICT'),
            nullable=False,
            index=True,
            comment='Doctor user ID'
        ),
        sa.Column(
            'patient_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='RESTRICT'),
            nullable=False,
            index=True,
            comment='Patient user ID'
        ),
        sa.Column(
            'service_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('services.id', ondelete='RESTRICT'),
            nullable=False,
            index=True,
            comment='Service ID'
        ),
        sa.Column(
            'clinic_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('clinics.id', ondelete='RESTRICT'),
            nullable=False,
            index=True,
            comment='Clinic ID'
        ),
        sa.Column(
            'doctor_service_availability_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('doctor_service_availability.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
            comment='Doctor service availability assignment ID (if applicable)'
        ),
        # Appointment details
        sa.Column(
            'appointment_date',
            sa.Date(),
            nullable=False,
            index=True,
            comment='Appointment date'
        ),
        sa.Column(
            'start_time',
            sa.Time(),
            nullable=False,
            comment='Appointment start time'
        ),
        sa.Column(
            'end_time',
            sa.Time(),
            nullable=False,
            comment='Appointment end time'
        ),
        sa.Column(
            'status',
            sa.String(50),
            nullable=False,
            server_default='SCHEDULED',
            index=False,  # We'll create the index manually below
            comment='Appointment status: SCHEDULED, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW'
        ),
        # Pricing snapshot (immutable after booking)
        sa.Column(
            'price_amount',
            sa.Numeric(10, 2),
            nullable=False,
            comment='Price at booking time (snapshot, never changes)'
        ),
        sa.Column(
            'currency',
            sa.String(3),
            nullable=False,
            server_default='INR',
            comment='Currency at booking time (snapshot)'
        ),
        sa.Column(
            'pricing_source',
            sa.String(50),
            nullable=False,
            comment='Source of price: availability, doctor, or global'
        ),
        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
            comment='Record creation timestamp (UTC)'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment='Record update timestamp (UTC)'
        ),
        sa.Column(
            'deleted_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
            comment='Soft delete timestamp (UTC)'
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint('id', name='appointments_pkey'),
        # Check constraints
        sa.CheckConstraint(
            "status IN ('SCHEDULED', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'NO_SHOW')",
            name='appointments_status_check'
        ),
        sa.CheckConstraint(
            'price_amount > 0',
            name='appointments_price_check'
        ),
        sa.CheckConstraint(
            "pricing_source IN ('availability', 'doctor', 'global')",
            name='appointments_pricing_source_check'
        ),
        sa.CheckConstraint(
            'end_time > start_time',
            name='appointments_time_check'
        ),
        comment='Appointments with immutable pricing snapshot'
    )
    
    # Create indexes for performance
    op.create_index(
        'ix_appointments_doctor_date',
        'appointments',
        ['doctor_id', 'appointment_date'],
        unique=False
    )
    op.create_index(
        'ix_appointments_patient_date',
        'appointments',
        ['patient_id', 'appointment_date'],
        unique=False
    )
    op.create_index(
        'ix_appointments_clinic_date',
        'appointments',
        ['clinic_id', 'appointment_date'],
        unique=False
    )
    # Index for status is already created automatically by SQLAlchemy 
    # when index=True is set on the column definition above
    # No need to create it manually


def downgrade() -> None:
    """
    Drop appointments table and indexes.
    """
    # Drop composite indexes first (IF EXISTS for safety)
    op.execute("DROP INDEX IF EXISTS ix_appointments_clinic_date")
    op.execute("DROP INDEX IF EXISTS ix_appointments_patient_date")
    op.execute("DROP INDEX IF EXISTS ix_appointments_doctor_date")
    # Note: ix_appointments_status will be dropped with the table
    
    # Drop table (this also drops column-level indexes)
    op.drop_table('appointments')
