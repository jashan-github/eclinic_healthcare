"""add_consultation_mode_to_availability_pricing

Add consultation_mode column to doctor_service_availability_pricing table.
Update unique constraint to explicitly include consultation_mode for mode-aware pricing.

Revision ID: add_consultation_mode_pricing_001
Revises: add_consultation_mode_dsa_001
Create Date: 2025-12-30 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_consultation_mode_pricing_001'
down_revision = 'add_consultation_mode_dsa_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add consultation_mode column to doctor_service_availability_pricing table.
    Update unique constraint to include consultation_mode.
    """
    # Step 1: Add consultation_mode column with default value
    # Get consultation_mode from related doctor_service_availability records
    op.execute("""
        ALTER TABLE doctor_service_availability_pricing
        ADD COLUMN consultation_mode VARCHAR(20) NOT NULL DEFAULT 'IN_CLINIC'
    """)
    
    # Step 2: Populate consultation_mode from related doctor_service_availability
    op.execute("""
        UPDATE doctor_service_availability_pricing p
        SET consultation_mode = dsa.consultation_mode
        FROM doctor_service_availability dsa
        WHERE p.doctor_service_availability_id = dsa.id
    """)
    
    # Step 3: Add check constraint for consultation_mode
    op.create_check_constraint(
        'doctor_service_availability_pricing_consultation_mode_check',
        'doctor_service_availability_pricing',
        "consultation_mode IN ('IN_CLINIC', 'TELECONSULTATION')"
    )
    
    # Step 4: Drop old unique constraint
    op.drop_constraint(
        'doctor_service_availability_pricing_avail_unique',
        'doctor_service_availability_pricing',
        type_='unique'
    )
    
    # Step 5: Create new unique constraint including consultation_mode
    # Note: This is technically redundant since doctor_service_availability_id already includes mode,
    # but makes it explicit for future-proofing
    op.create_unique_constraint(
        'doctor_service_availability_pricing_avail_mode_unique',
        'doctor_service_availability_pricing',
        ['doctor_service_availability_id', 'consultation_mode']
    )
    
    # Step 6: Create index on consultation_mode for performance
    op.create_index(
        'ix_doctor_service_availability_pricing_consultation_mode',
        'doctor_service_availability_pricing',
        ['consultation_mode'],
        unique=False
    )


def downgrade() -> None:
    """
    Remove consultation_mode column and revert unique constraint.
    """
    # Step 1: Drop index
    op.drop_index(
        'ix_doctor_service_availability_pricing_consultation_mode',
        table_name='doctor_service_availability_pricing'
    )
    
    # Step 2: Drop new unique constraint
    op.drop_constraint(
        'doctor_service_availability_pricing_avail_mode_unique',
        'doctor_service_availability_pricing',
        type_='unique'
    )
    
    # Step 3: Restore old unique constraint
    op.create_unique_constraint(
        'doctor_service_availability_pricing_avail_unique',
        'doctor_service_availability_pricing',
        ['doctor_service_availability_id']
    )
    
    # Step 4: Drop check constraint
    op.drop_constraint(
        'doctor_service_availability_pricing_consultation_mode_check',
        'doctor_service_availability_pricing',
        type_='check'
    )
    
    # Step 5: Drop consultation_mode column
    op.drop_column('doctor_service_availability_pricing', 'consultation_mode')
