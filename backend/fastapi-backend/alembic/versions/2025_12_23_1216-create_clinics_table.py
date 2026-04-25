"""create_clinics_table

Revision ID: create_clinics_001
Revises: create_notification_settings_001
Create Date: 2025-12-23 12:16:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_clinics_001'
down_revision = 'create_notification_settings_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure uuid-ossp extension exists (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create clinics table
    op.create_table(
        'clinics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(255), nullable=False),
        sa.Column('timezone', sa.String(255), nullable=False, server_default='UTC'),
        sa.Column('country', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('code', name='clinics_code_unique'),
    )
    
    # Create indexes for performance
    # Note: code unique index is created by UniqueConstraint above
    op.create_index('clinics_status_index', 'clinics', ['status'])
    op.create_index('clinics_created_at_index', 'clinics', ['created_at'])
    op.create_index('clinics_deleted_at_index', 'clinics', ['deleted_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('clinics_deleted_at_index', table_name='clinics')
    op.drop_index('clinics_created_at_index', table_name='clinics')
    op.drop_index('clinics_status_index', table_name='clinics')
    # Note: clinics_code_unique constraint/index is dropped automatically with table
    
    # Drop table
    op.drop_table('clinics')

