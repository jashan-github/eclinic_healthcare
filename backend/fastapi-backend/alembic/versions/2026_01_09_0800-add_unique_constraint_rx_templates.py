"""add unique constraint for doctor and clinic location

Revision ID: add_unique_constraint_rx_templates_001
Revises: create_rx_templates_001
Create Date: 2026-01-09 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_unique_constraint_rx_templates_001'
down_revision = 'create_rx_templates_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, handle duplicates: keep the most recent one, soft-delete others
    op.execute("""
        WITH duplicates AS (
            SELECT id, 
                   ROW_NUMBER() OVER (
                       PARTITION BY doctor_id, clinic_location_id 
                       ORDER BY created_at DESC, id DESC
                   ) as rn
            FROM rx_templates
            WHERE deleted_at IS NULL
        )
        UPDATE rx_templates
        SET deleted_at = NOW()
        WHERE id IN (
            SELECT id FROM duplicates WHERE rn > 1
        )
    """)
    
    # Create unique index: one template per doctor per location (excluding deleted)
    op.execute("""
        CREATE UNIQUE INDEX rx_templates_unique_doctor_location 
        ON rx_templates (doctor_id, clinic_location_id) 
        WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    op.drop_index('rx_templates_unique_doctor_location', table_name='rx_templates')
