"""reorder_title_column

Revision ID: reorder_title_col
Revises: remove_addr_profile
Create Date: 2025-12-24 18:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'reorder_title_col'
down_revision = 'remove_addr_profile'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Reorder title column to be right after user_id in user_profiles table.
    
    Note: PostgreSQL doesn't support direct column reordering, so we:
    1. Create a new table with correct column order
    2. Copy data
    3. Drop old table
    4. Rename new table
    """
    # Get current table structure
    conn = op.get_bind()
    
    # Create new table with title right after user_id
    op.execute("""
        CREATE TABLE user_profiles_new (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(10),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            middle_name VARCHAR(255),
            date_of_birth DATE,
            gender VARCHAR(20),
            bio TEXT,
            avatar VARCHAR(255),
            occupation VARCHAR(255),
            company VARCHAR(255),
            website VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Copy data from old table to new table
    op.execute("""
        INSERT INTO user_profiles_new (
            id, user_id, title, first_name, last_name, middle_name,
            date_of_birth, gender, bio, avatar, occupation, company, website,
            created_at, updated_at, deleted_at
        )
        SELECT 
            id, user_id, title, first_name, last_name, middle_name,
            date_of_birth, gender, bio, avatar, occupation, company, website,
            created_at, updated_at, deleted_at
        FROM user_profiles
    """)
    
    # Drop old table
    op.execute("DROP TABLE user_profiles CASCADE")
    
    # Rename new table
    op.execute("ALTER TABLE user_profiles_new RENAME TO user_profiles")
    
    # Recreate indexes
    op.create_index('user_profiles_user_id_index', 'user_profiles', ['user_id'])
    op.create_index('ix_user_profiles_id', 'user_profiles', ['id'])
    op.create_index('ix_user_profiles_created_at', 'user_profiles', ['created_at'])
    op.create_index('ix_user_profiles_updated_at', 'user_profiles', ['updated_at'])
    op.create_index('ix_user_profiles_deleted_at', 'user_profiles', ['deleted_at'])


def downgrade() -> None:
    """
    Revert title column order (move it back to original position after personal info fields)
    """
    # Similar process in reverse - recreate table with title in original position
    conn = op.get_bind()
    
    op.execute("""
        CREATE TABLE user_profiles_old (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            middle_name VARCHAR(255),
            date_of_birth DATE,
            gender VARCHAR(20),
            bio TEXT,
            avatar VARCHAR(255),
            title VARCHAR(10),
            occupation VARCHAR(255),
            company VARCHAR(255),
            website VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    op.execute("""
        INSERT INTO user_profiles_old (
            id, user_id, first_name, last_name, middle_name,
            date_of_birth, gender, bio, avatar, title, occupation, company, website,
            created_at, updated_at, deleted_at
        )
        SELECT 
            id, user_id, first_name, last_name, middle_name,
            date_of_birth, gender, bio, avatar, title, occupation, company, website,
            created_at, updated_at, deleted_at
        FROM user_profiles
    """)
    
    op.execute("DROP TABLE user_profiles CASCADE")
    op.execute("ALTER TABLE user_profiles_old RENAME TO user_profiles")
    
    # Recreate indexes
    op.create_index('user_profiles_user_id_index', 'user_profiles', ['user_id'])
    op.create_index('ix_user_profiles_id', 'user_profiles', ['id'])
    op.create_index('ix_user_profiles_created_at', 'user_profiles', ['created_at'])
    op.create_index('ix_user_profiles_updated_at', 'user_profiles', ['updated_at'])
    op.create_index('ix_user_profiles_deleted_at', 'user_profiles', ['deleted_at'])

