"""add_role_metadata_fields

Revision ID: add_role_metadata_001
Revises: enforce_clinic_not_null_001
Create Date: 2025-12-24 09:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_role_metadata_001'
down_revision = 'enforce_clinic_not_null_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to roles table
    op.add_column('roles', sa.Column('display_name', sa.String(255), nullable=True, comment='Human-readable role name'))
    op.add_column('roles', sa.Column('description', sa.Text(), nullable=True, comment='Role description'))
    op.add_column('roles', sa.Column('permissions', postgresql.JSONB(), nullable=True, comment='List of permissions for this role'))
    
    # Create index on display_name for faster lookups
    op.create_index('roles_display_name_index', 'roles', ['display_name'])


def downgrade() -> None:
    # Remove index
    op.drop_index('roles_display_name_index', table_name='roles')
    
    # Remove columns
    op.drop_column('roles', 'permissions')
    op.drop_column('roles', 'description')
    op.drop_column('roles', 'display_name')

