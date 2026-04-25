"""create_notification_settings_table

Revision ID: create_notification_settings_001
Revises: create_audit_logs_001
Create Date: 2025-12-22 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_notification_settings_001'
down_revision = 'create_audit_logs_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure uuid-ossp extension exists (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create notification_settings table
    op.create_table(
        'notification_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('provider', sa.String(100), nullable=True),
        sa.Column('config_encrypted', postgresql.JSONB(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('channel', name='notification_settings_channel_unique'),
    )
    
    # Create indexes for performance
    op.create_index('notification_settings_channel_index', 'notification_settings', ['channel'])
    op.create_index('notification_settings_enabled_index', 'notification_settings', ['enabled'])
    op.create_index('notification_settings_provider_index', 'notification_settings', ['provider'])
    op.create_index('notification_settings_updated_by_index', 'notification_settings', ['updated_by'])
    op.create_index('notification_settings_created_at_index', 'notification_settings', ['created_at'])
    op.create_index('notification_settings_deleted_at_index', 'notification_settings', ['deleted_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('notification_settings_deleted_at_index', table_name='notification_settings')
    op.drop_index('notification_settings_created_at_index', table_name='notification_settings')
    op.drop_index('notification_settings_updated_by_index', table_name='notification_settings')
    op.drop_index('notification_settings_provider_index', table_name='notification_settings')
    op.drop_index('notification_settings_enabled_index', table_name='notification_settings')
    op.drop_index('notification_settings_channel_index', table_name='notification_settings')
    
    # Drop table
    op.drop_table('notification_settings')

