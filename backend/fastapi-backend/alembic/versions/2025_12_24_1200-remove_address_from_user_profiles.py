"""remove_address_from_user_profiles

Revision ID: remove_addr_profile
Revises: add_title_profile_001
Create Date: 2025-12-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_addr_profile'
down_revision = 'add_title_profile_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove address fields from user_profiles table.
    Address fields are now stored in contact_details table following best practices:
    - user_profiles: Personal/demographic information (WHO the person is)
    - contact_details: Contact information (HOW to reach the person)
    """
    # Remove address columns from user_profiles
    op.drop_column('user_profiles', 'address_line_1')
    op.drop_column('user_profiles', 'address_line_2')
    op.drop_column('user_profiles', 'city')
    op.drop_column('user_profiles', 'state')
    op.drop_column('user_profiles', 'postal_code')
    op.drop_column('user_profiles', 'country')


def downgrade() -> None:
    """
    Restore address fields to user_profiles table (for rollback)
    """
    op.add_column('user_profiles', sa.Column('address_line_1', sa.String(length=255), nullable=True))
    op.add_column('user_profiles', sa.Column('address_line_2', sa.String(length=255), nullable=True))
    op.add_column('user_profiles', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('user_profiles', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('user_profiles', sa.Column('postal_code', sa.String(length=20), nullable=True))
    op.add_column('user_profiles', sa.Column('country', sa.String(length=100), nullable=True))

