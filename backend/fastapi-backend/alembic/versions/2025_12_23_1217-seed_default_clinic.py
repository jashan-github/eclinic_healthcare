"""seed_default_clinic

Revision ID: seed_default_clinic_001
Revises: create_clinics_001
Create Date: 2025-12-23 12:24:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'seed_default_clinic_001'
down_revision = 'create_clinics_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure uuid-ossp extension exists (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Insert default clinic only if no clinic exists
    # This is idempotent - safe to run multiple times
    op.execute("""
        INSERT INTO clinics (id, name, code, timezone, status, created_at, updated_at)
        SELECT 
            uuid_generate_v4(),
            'Default Clinic',
            'DEFAULT',
            'UTC',
            'active',
            NOW(),
            NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM clinics WHERE deleted_at IS NULL
        )
    """)


def downgrade() -> None:
    # Remove default clinic (only if code is 'DEFAULT')
    # This is safe - only removes the default clinic we created
    op.execute("""
        UPDATE clinics 
        SET deleted_at = NOW()
        WHERE code = 'DEFAULT' AND deleted_at IS NULL
    """)

