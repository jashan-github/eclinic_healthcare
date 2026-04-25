"""add_title_to_user_profiles

Revision ID: add_title_profile_001
Revises: add_role_metadata_001
Create Date: 2025-12-24 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_title_profile_001'
down_revision = 'add_role_metadata_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add title column to user_profiles table
    op.add_column('user_profiles', sa.Column('title', sa.String(10), nullable=True, comment='Title prefix (Dr, Mr, Mrs, Ms, etc.)'))


def downgrade() -> None:
    # Remove title column
    op.drop_column('user_profiles', 'title')

