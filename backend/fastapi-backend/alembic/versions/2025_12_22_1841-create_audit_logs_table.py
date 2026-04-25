"""create_audit_logs_table

Revision ID: create_audit_logs_001
Revises: create_user_profile_001
Create Date: 2025-12-22 18:41:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_audit_logs_001'
down_revision = 'create_user_profile_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure uuid-ossp extension exists (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create audit_logs table (append-only, HIPAA-compliant)
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('audit_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for performance
    op.create_index('audit_logs_actor_user_id_created_at_idx', 'audit_logs', ['actor_user_id', 'created_at'])
    op.create_index('audit_logs_actor_user_id_index', 'audit_logs', ['actor_user_id'])
    op.create_index('audit_logs_action_index', 'audit_logs', ['action'])
    op.create_index('audit_logs_entity_type_index', 'audit_logs', ['entity_type'])
    op.create_index('audit_logs_entity_id_index', 'audit_logs', ['entity_id'])
    op.create_index('audit_logs_entity_type_entity_id_idx', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('audit_logs_created_at_index', 'audit_logs', ['created_at'])
    op.create_index('audit_logs_ip_address_index', 'audit_logs', ['ip_address'])
    
    # HIPAA Compliance: Prevent updates and deletes
    # Create a function to prevent updates
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_updates()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are append-only and cannot be updated';
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create a trigger to prevent updates
    op.execute("""
        CREATE TRIGGER prevent_audit_log_updates_trigger
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_updates();
    """)
    
    # Create a function to prevent deletes
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_deletes()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are append-only and cannot be deleted';
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create a trigger to prevent deletes
    op.execute("""
        CREATE TRIGGER prevent_audit_log_deletes_trigger
        BEFORE DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_deletes();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS prevent_audit_log_deletes_trigger ON audit_logs')
    op.execute('DROP TRIGGER IF EXISTS prevent_audit_log_updates_trigger ON audit_logs')
    
    # Drop functions
    op.execute('DROP FUNCTION IF EXISTS prevent_audit_log_deletes()')
    op.execute('DROP FUNCTION IF EXISTS prevent_audit_log_updates()')
    
    # Drop indexes
    op.drop_index('audit_logs_ip_address_index', table_name='audit_logs')
    op.drop_index('audit_logs_created_at_index', table_name='audit_logs')
    op.drop_index('audit_logs_entity_type_entity_id_idx', table_name='audit_logs')
    op.drop_index('audit_logs_entity_id_index', table_name='audit_logs')
    op.drop_index('audit_logs_entity_type_index', table_name='audit_logs')
    op.drop_index('audit_logs_action_index', table_name='audit_logs')
    op.drop_index('audit_logs_actor_user_id_index', table_name='audit_logs')
    op.drop_index('audit_logs_actor_user_id_created_at_idx', table_name='audit_logs')
    
    # Drop table
    op.drop_table('audit_logs')

