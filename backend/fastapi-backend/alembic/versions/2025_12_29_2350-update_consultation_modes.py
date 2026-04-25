"""update_consultation_modes

Update consultation modes from VIDEO to TELECONSULTATION.
Update database constraint to use new enum values.

Revision ID: update_consultation_modes_001
Revises: add_currency_to_services_001
Create Date: 2025-12-29 23:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'update_consultation_modes_001'
down_revision = 'add_currency_to_services_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if constraint exists before dropping (idempotent)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'services_service_mode_check'
    """))
    constraint_exists = result.fetchone() is not None
    
    # Step 1: Drop old constraint FIRST (before updating data)
    if constraint_exists:
        op.drop_constraint('services_service_mode_check', 'services', type_='check')
    
    # Step 2: Update existing VIDEO records to TELECONSULTATION
    op.execute("""
        UPDATE services 
        SET service_mode = 'TELECONSULTATION' 
        WHERE service_mode = 'VIDEO'
    """)
    
    # Step 3: Add new constraint with TELECONSULTATION
    op.create_check_constraint(
        'services_service_mode_check',
        'services',
        "service_mode IN ('IN_CLINIC', 'TELECONSULTATION')"
    )


def downgrade() -> None:
    # Step 1: Drop new constraint
    op.drop_constraint('services_service_mode_check', 'services', type_='check')
    
    # Step 2: Add old constraint with VIDEO
    op.create_check_constraint(
        'services_service_mode_check',
        'services',
        "service_mode IN ('IN_CLINIC', 'VIDEO')"
    )
    
    # Step 3: Revert TELECONSULTATION back to VIDEO
    op.execute("""
        UPDATE services 
        SET service_mode = 'VIDEO' 
        WHERE service_mode = 'TELECONSULTATION'
    """)
