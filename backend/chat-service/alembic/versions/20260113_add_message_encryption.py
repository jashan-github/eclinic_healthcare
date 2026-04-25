"""add message encryption support

Revision ID: add_message_encryption_001
Revises: 202601091049
Create Date: 2026-01-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_message_encryption_001'
down_revision = '202601091049'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_encrypted flag to chat_messages table
    op.add_column('chat_messages', 
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='true')
    )
    
    # Add comments to columns
    op.execute("COMMENT ON COLUMN chat_messages.message IS 'Encrypted message content (Fernet encryption)'")
    op.execute("COMMENT ON COLUMN chat_messages.is_encrypted IS 'Flag indicating if message is encrypted (true for new messages, false for legacy unencrypted messages)'")
    
    # Create index on is_encrypted for efficient queries
    op.create_index('ix_chat_messages_is_encrypted', 'chat_messages', ['is_encrypted'])


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_chat_messages_is_encrypted', table_name='chat_messages')
    
    # Remove comments
    op.execute("COMMENT ON COLUMN chat_messages.message IS NULL")
    
    # Drop column
    op.drop_column('chat_messages', 'is_encrypted')
