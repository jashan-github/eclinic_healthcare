"""add_users_clinic_fk

Revision ID: add_users_clinic_fk_001
Revises: backfill_users_clinic_id_001
Create Date: 2025-12-23 12:43:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_users_clinic_fk_001'
down_revision = 'backfill_users_clinic_id_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure no NULL clinic_id exists before adding FK
    # Backfill any remaining NULL values with DEFAULT clinic
    # This is a safety check in case some users were created between migrations
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
    
    # Check if foreign key already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing foreign keys for users table
    fks = inspector.get_foreign_keys('users')
    fk_exists = any(
        fk['name'] == 'fk_users_clinic_id_clinics' or 
        (fk['constrained_columns'] == ['clinic_id'] and fk['referred_table'] == 'clinics')
        for fk in fks
    )
    
    # Add foreign key constraint if it doesn't exist
    if not fk_exists:
        op.create_foreign_key(
            'fk_users_clinic_id_clinics',
            'users', 'clinics',
            ['clinic_id'], ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_users_clinic_id_clinics', 'users', type_='foreignkey')

