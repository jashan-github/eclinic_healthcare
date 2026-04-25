"""backfill_users_clinic_id

Revision ID: backfill_users_clinic_id_001
Revises: seed_default_clinic_001
Create Date: 2025-12-23 12:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'backfill_users_clinic_id_001'
down_revision = 'seed_default_clinic_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill clinic_id for users where it is NULL
    # Uses efficient single UPDATE with subquery to fetch DEFAULT clinic ID
    # Safe for large tables - single statement, runs in transaction
    op.execute("""
        UPDATE users
        SET clinic_id = (
            SELECT id 
            FROM clinics 
            WHERE code = 'DEFAULT' 
            AND deleted_at IS NULL 
            LIMIT 1
        ),
        updated_at = NOW()
        WHERE clinic_id IS NULL
        AND deleted_at IS NULL
    """)


def downgrade() -> None:
    # Set clinic_id back to NULL for users that were backfilled
    # Only affects users with DEFAULT clinic
    op.execute("""
        UPDATE users
        SET clinic_id = NULL,
        updated_at = NOW()
        WHERE clinic_id = (
            SELECT id 
            FROM clinics 
            WHERE code = 'DEFAULT' 
            AND deleted_at IS NULL 
            LIMIT 1
        )
        AND deleted_at IS NULL
    """)

