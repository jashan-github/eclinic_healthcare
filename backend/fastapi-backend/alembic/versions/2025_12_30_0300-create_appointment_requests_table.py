"""create_appointment_requests_table

Create appointment_requests table for appointment request → approval → payment flow.
Separate from appointments table to support pending/accepted/rejected states.

Revision ID: create_appointment_requests_001
Revises: add_appointment_snapshot_fields_001
Create Date: 2025-12-30 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_appointment_requests_001'
down_revision = 'add_appointment_snapshot_fields_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create appointment_requests table.
    
    Supports flow:
    1. Patient creates request (status: PENDING)
    2. Doctor accepts/rejects (status: ACCEPTED/REJECTED)
    3. Patient pays (converts to confirmed appointment)
    """
    # Check if table already exists (idempotent)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if inspector.has_table('appointment_requests'):
        # Table already exists, skip creation
        return
    
    op.create_table(
        'appointment_requests',
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
        # Request details
        sa.Column(
            'preferred_date',
            sa.Date(),
            nullable=False,
            index=True,
            comment='Preferred appointment date'
        ),
        sa.Column(
            'preferred_time',
            sa.Time(),
            nullable=False,
            comment='Preferred appointment time'
        ),
        sa.Column(
            'consultation_mode',
            sa.String(20),
            nullable=False,
            server_default='IN_CLINIC',
            index=True,
            comment='Consultation mode: IN_CLINIC or TELECONSULTATION'
        ),
        sa.Column(
            'duration_minutes',
            sa.Integer(),
            nullable=False,
            comment='Slot duration in minutes'
        ),
        # Status
        sa.Column(
            'status',
            sa.String(50),
            nullable=False,
            server_default='PENDING',
            index=False,  # We'll create the index manually below
            comment='Request status: PENDING, ACCEPTED, REJECTED'
        ),
        # Reason/symptoms (HIPAA: stored but never logged)
        sa.Column(
            'reason',
            sa.Text(),
            nullable=True,
            comment='Patient reason/symptoms (HIPAA-protected, never logged)'
        ),
        # Rejection reason (optional)
        sa.Column(
            'rejection_reason',
            sa.String(500),
            nullable=True,
            comment='Doctor rejection reason (if rejected)'
        ),
        # Pricing (calculated at request time, locked after acceptance)
        sa.Column(
            'price_amount',
            sa.Numeric(10, 2),
            nullable=True,
            comment='Calculated price (locked after acceptance)'
        ),
        sa.Column(
            'currency',
            sa.String(3),
            nullable=False,
            server_default='INR',
            comment='Currency code (ISO 4217)'
        ),
        sa.Column(
            'pricing_source',
            sa.String(50),
            nullable=True,
            comment='Source of price: availability, doctor, or global'
        ),
        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
            comment='Request creation timestamp (UTC)'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment='Request update timestamp (UTC)'
        ),
        sa.Column(
            'deleted_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
            comment='Soft delete timestamp (UTC)'
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint('id', name='appointment_requests_pkey'),
        # Check constraints
        sa.CheckConstraint(
            "status IN ('PENDING', 'ACCEPTED', 'REJECTED')",
            name='appointment_requests_status_check'
        ),
        sa.CheckConstraint(
            "consultation_mode IN ('IN_CLINIC', 'TELECONSULTATION')",
            name='appointment_requests_consultation_mode_check'
        ),
        sa.CheckConstraint(
            'duration_minutes >= 5 AND duration_minutes <= 360',
            name='appointment_requests_duration_check'
        ),
        sa.CheckConstraint(
            'price_amount IS NULL OR price_amount > 0',
            name='appointment_requests_price_check'
        ),
        comment='Appointment requests (pending → accepted/rejected → payment → confirmed appointment)'
    )
    
    # Create indexes for performance
    op.create_index(
        'ix_appointment_requests_doctor_status',
        'appointment_requests',
        ['doctor_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_appointment_requests_patient_status',
        'appointment_requests',
        ['patient_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_appointment_requests_date_time',
        'appointment_requests',
        ['preferred_date', 'preferred_time'],
        unique=False
    )
    # Index for status is already created automatically by SQLAlchemy 
    # when index=True is set on the column definition above
    # No need to create it manually - removed to avoid duplicate


def downgrade() -> None:
    """
    Drop appointment_requests table and indexes.
    """
    # Drop composite indexes (IF EXISTS for safety)
    op.execute("DROP INDEX IF EXISTS ix_appointment_requests_date_time")
    op.execute("DROP INDEX IF EXISTS ix_appointment_requests_patient_status")
    op.execute("DROP INDEX IF EXISTS ix_appointment_requests_doctor_status")
    # Note: ix_appointment_requests_status will be dropped with the table
    
    # Drop table (this also drops column-level indexes)
    op.drop_table('appointment_requests')
