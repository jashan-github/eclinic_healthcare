"""add_updated_at_to_doctor_time_off

Revision ID: add_updated_at_time_off_001
Revises: create_appointment_requests_001
Create Date: 2025-12-30 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_updated_at_time_off_001'
down_revision = 'create_appointment_payments_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if column already exists (idempotent)
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'doctor_time_off' 
        AND column_name = 'updated_at'
    """))
    
    if result.fetchone() is None:
        # Add updated_at column to doctor_time_off table
        op.add_column(
            'doctor_time_off',
            sa.Column(
                'updated_at',
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
                comment='Record last update timestamp (UTC)'
            )
        )
        
        # Create index for updated_at
        op.create_index(
            'doctor_time_off_updated_at_index',
            'doctor_time_off',
            ['updated_at']
        )


def downgrade() -> None:
    # Drop index
    op.drop_index('doctor_time_off_updated_at_index', table_name='doctor_time_off')
    
    # Drop column
    op.drop_column('doctor_time_off', 'updated_at')

