"""enforce_users_clinic_not_null

Revision ID: enforce_clinic_not_null_001
Revises: add_users_clinic_fk_001
Create Date: 2025-12-23 12:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enforce_clinic_not_null_001'
down_revision = 'add_users_clinic_fk_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Verify no users.clinic_id IS NULL
    # This will raise an exception if NULL values exist, failing the migration
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT COUNT(*) as null_count
        FROM users
        WHERE clinic_id IS NULL
        AND deleted_at IS NULL
    """))
    
    row = result.fetchone()
    null_count = row[0] if row else 0
    
    if null_count > 0:
        raise Exception(
            f"Migration failed: Found {null_count} user(s) with NULL clinic_id. "
            "All users must have a clinic_id before making this column NOT NULL. "
            "Please backfill clinic_id values first."
        )
    
    # Step 2: Alter users.clinic_id → NOT NULL
    # Only executed if no NULL values exist
    op.alter_column(
        'users',
        'clinic_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
        existing_nullable=True
    )


def downgrade() -> None:
    # Revert clinic_id back to nullable
    op.alter_column(
        'users',
        'clinic_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
        existing_nullable=False
    )

