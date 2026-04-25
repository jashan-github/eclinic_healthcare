"""add_consultation_mode_to_doctor_service_availability

Add consultation_mode column to doctor_service_availability table.
Update unique constraint to include consultation_mode.

Revision ID: add_consultation_mode_dsa_001
Revises: update_consultation_modes_001
Create Date: 2025-12-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_consultation_mode_dsa_001'
down_revision = 'update_consultation_modes_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add consultation_mode column to doctor_service_availability table.
    Update unique constraint to include consultation_mode.
    """
    # Step 1: Add consultation_mode column with default value
    op.add_column(
        'doctor_service_availability',
        sa.Column(
            'consultation_mode',
            sa.String(20),
            nullable=False,
            server_default='IN_CLINIC',
            comment='Consultation mode: IN_CLINIC or TELECONSULTATION'
        )
    )
    
    # Step 2: Add check constraint for consultation_mode
    op.create_check_constraint(
        'doctor_service_availability_consultation_mode_check',
        'doctor_service_availability',
        "consultation_mode IN ('IN_CLINIC', 'TELECONSULTATION')"
    )
    
    # Step 3: Drop old unique constraint
    op.drop_constraint(
        'doctor_service_availability_avail_service_unique',
        'doctor_service_availability',
        type_='unique'
    )
    
    # Step 4: Create new unique constraint including consultation_mode
    op.create_unique_constraint(
        'doctor_service_availability_avail_service_mode_unique',
        'doctor_service_availability',
        ['availability_id', 'service_id', 'consultation_mode']
    )


def downgrade() -> None:
    """
    Remove consultation_mode column and revert unique constraint.
    """
    # Step 1: Drop new unique constraint
    op.drop_constraint(
        'doctor_service_availability_avail_service_mode_unique',
        'doctor_service_availability',
        type_='unique'
    )
    
    # Step 2: Restore old unique constraint
    op.create_unique_constraint(
        'doctor_service_availability_avail_service_unique',
        'doctor_service_availability',
        ['availability_id', 'service_id']
    )
    
    # Step 3: Drop check constraint
    op.drop_constraint(
        'doctor_service_availability_consultation_mode_check',
        'doctor_service_availability',
        type_='check'
    )
    
    # Step 4: Drop consultation_mode column
    op.drop_column('doctor_service_availability', 'consultation_mode')
