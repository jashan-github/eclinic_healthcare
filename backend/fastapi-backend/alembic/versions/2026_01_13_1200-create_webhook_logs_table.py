"""create webhook logs table

Revision ID: create_webhook_logs_001
Revises: create_admin_settings_001
Create Date: 2026-01-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_webhook_logs_001'
down_revision = 'create_soap_notes_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create webhook_logs table
    op.create_table(
        'webhook_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False, comment='Primary key (UUID)'),
        sa.Column('source', sa.String(50), nullable=False, server_default='sentoo', comment="Webhook source (e.g., 'sentoo', 'stripe', etc.)"),
        sa.Column('event_type', sa.String(100), nullable=True, comment="Event type (e.g., 'payment.succeeded', 'payment.failed')"),
        sa.Column('webhook_id', sa.String(255), nullable=True, comment='Webhook event ID from payment gateway'),
        sa.Column('raw_payload', postgresql.JSONB, nullable=True, comment='Raw webhook payload (JSONB format)'),
        sa.Column('headers', postgresql.JSONB, nullable=True, comment='HTTP headers received with webhook'),
        sa.Column('processing_status', sa.String(50), nullable=False, server_default='pending', comment='Processing status: pending, success, error, ignored'),
        sa.Column('error_message', sa.Text, nullable=True, comment='Error message if processing failed'),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Related payment ID (FK to appointment_payments.id)'),
        sa.Column('appointment_request_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Related appointment request ID (FK to appointment_requests.id)'),
        sa.Column('ip_address', sa.String(45), nullable=True, comment='IP address of webhook sender (IPv6 support)'),
        sa.Column('user_agent', sa.Text, nullable=True, comment='User agent string from webhook request'),
        sa.Column('response_status', sa.String(50), nullable=True, comment="HTTP response status sent back (e.g., '200', '400')"),
        sa.Column('response_body', postgresql.JSONB, nullable=True, comment='Response body sent back to webhook sender'),
        sa.Column('processing_time_ms', sa.String(20), nullable=True, comment='Processing time in milliseconds'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='When the webhook was received (UTC timestamp)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp (UTC)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft delete timestamp (UTC). NULL means not deleted.'),
    )
    
    # Create indexes
    op.create_index('webhook_logs_source_created_at_idx', 'webhook_logs', ['source', 'created_at'])
    op.create_index('webhook_logs_event_type_idx', 'webhook_logs', ['event_type'])
    op.create_index('webhook_logs_webhook_id_idx', 'webhook_logs', ['webhook_id'])
    op.create_index('webhook_logs_payment_id_idx', 'webhook_logs', ['payment_id'])
    op.create_index('webhook_logs_processing_status_idx', 'webhook_logs', ['processing_status'])
    op.create_index('webhook_logs_created_at_idx', 'webhook_logs', ['created_at'])
    op.create_index('webhook_logs_id_idx', 'webhook_logs', ['id'])
    
    # Add foreign key constraints (optional, for referential integrity)
    # Note: These are commented out to allow logging even if related records are deleted
    # op.create_foreign_key('webhook_logs_payment_id_fkey', 'webhook_logs', 'appointment_payments', ['payment_id'], ['id'], ondelete='SET NULL')
    # op.create_foreign_key('webhook_logs_appointment_request_id_fkey', 'webhook_logs', 'appointment_requests', ['appointment_request_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('webhook_logs_created_at_idx', table_name='webhook_logs')
    op.drop_index('webhook_logs_processing_status_idx', table_name='webhook_logs')
    op.drop_index('webhook_logs_payment_id_idx', table_name='webhook_logs')
    op.drop_index('webhook_logs_webhook_id_idx', table_name='webhook_logs')
    op.drop_index('webhook_logs_event_type_idx', table_name='webhook_logs')
    op.drop_index('webhook_logs_source_created_at_idx', table_name='webhook_logs')
    op.drop_index('webhook_logs_id_idx', table_name='webhook_logs')
    
    # Drop table
    op.drop_table('webhook_logs')
