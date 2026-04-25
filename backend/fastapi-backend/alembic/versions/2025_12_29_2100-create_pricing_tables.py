"""create_pricing_tables

Create pricing tables for appointment booking:
- doctor_service_pricing: Doctor-service level pricing
- doctor_service_availability_pricing: Availability-specific pricing

Revision ID: create_pricing_tables_001
Revises: create_doctor_service_availability_001
Create Date: 2025-12-29 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_pricing_tables_001'
down_revision = 'create_doctor_service_availability_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create pricing tables for appointment booking.
    
    Tables:
    - doctor_service_pricing: Doctor-service level pricing
    - doctor_service_availability_pricing: Availability-specific pricing
    """
    
    # ============================================================================
    # TABLE 1: doctor_service_pricing
    # ============================================================================
    op.create_table(
        'doctor_service_pricing',
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
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            comment='Doctor user ID'
        ),
        sa.Column(
            'service_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('services.id', ondelete='CASCADE'),
            nullable=False,
            comment='Service ID'
        ),
        # Pricing fields
        sa.Column(
            'price_amount',
            sa.Numeric(10, 2),
            nullable=False,
            comment='Price amount (must be > 0)'
        ),
        sa.Column(
            'currency',
            sa.String(3),
            server_default='INR',
            nullable=False,
            comment='Currency code (ISO 4217, default: INR)'
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
        sa.PrimaryKeyConstraint('id', name='doctor_service_pricing_pkey'),
        # Unique constraint: one price per doctor-service combination
        sa.UniqueConstraint(
            'doctor_id',
            'service_id',
            name='doctor_service_pricing_doctor_service_unique'
        ),
        # Check constraint: price must be positive
        sa.CheckConstraint(
            'price_amount > 0',
            name='doctor_service_pricing_price_check'
        ),
        comment='Doctor-service level pricing for appointments'
    )
    
    # Create indexes for foreign keys
    op.create_index(
        'ix_doctor_service_pricing_doctor_id',
        'doctor_service_pricing',
        ['doctor_id'],
        unique=False
    )
    
    op.create_index(
        'ix_doctor_service_pricing_service_id',
        'doctor_service_pricing',
        ['service_id'],
        unique=False
    )
    
    # ============================================================================
    # TABLE 2: doctor_service_availability_pricing
    # ============================================================================
    op.create_table(
        'doctor_service_availability_pricing',
        # Primary key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
            comment='Primary key (UUID)'
        ),
        # Foreign key to doctor_service_availability
        sa.Column(
            'doctor_service_availability_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('doctor_service_availability.id', ondelete='CASCADE'),
            nullable=False,
            comment='Reference to doctor service availability assignment'
        ),
        # Pricing fields
        sa.Column(
            'price_amount',
            sa.Numeric(10, 2),
            nullable=False,
            comment='Price amount (must be > 0)'
        ),
        sa.Column(
            'currency',
            sa.String(3),
            server_default='INR',
            nullable=False,
            comment='Currency code (ISO 4217, default: INR)'
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
        sa.PrimaryKeyConstraint('id', name='doctor_service_availability_pricing_pkey'),
        # Unique constraint: one price per availability assignment
        sa.UniqueConstraint(
            'doctor_service_availability_id',
            name='doctor_service_availability_pricing_avail_unique'
        ),
        # Check constraint: price must be positive
        sa.CheckConstraint(
            'price_amount > 0',
            name='doctor_service_availability_pricing_price_check'
        ),
        comment='Availability-specific pricing for appointments'
    )
    
    # Create index for foreign key
    op.create_index(
        'ix_doctor_service_availability_pricing_avail_id',
        'doctor_service_availability_pricing',
        ['doctor_service_availability_id'],
        unique=False
    )


def downgrade() -> None:
    """
    Drop pricing tables and indexes.
    """
    # Drop indexes first
    op.drop_index(
        'ix_doctor_service_availability_pricing_avail_id',
        table_name='doctor_service_availability_pricing'
    )
    
    op.drop_index(
        'ix_doctor_service_pricing_service_id',
        table_name='doctor_service_pricing'
    )
    
    op.drop_index(
        'ix_doctor_service_pricing_doctor_id',
        table_name='doctor_service_pricing'
    )
    
    # Drop tables
    op.drop_table('doctor_service_availability_pricing')
    op.drop_table('doctor_service_pricing')
