"""create_chat_tables

Revision ID: 20250101000001
Revises: 
Create Date: 2025-01-01 00:00:01.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250101000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chat_rooms table
    op.create_table(
        'chat_rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('active', 'closed', name='chatroomstatus'), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute("COMMENT ON TABLE chat_rooms IS 'Chat rooms between doctors and patients'")
    
    op.create_index('ix_chat_rooms_doctor_id', 'chat_rooms', ['doctor_id'])
    op.create_index('ix_chat_rooms_patient_id', 'chat_rooms', ['patient_id'])
    op.create_index('ix_chat_rooms_appointment_id', 'chat_rooms', ['appointment_id'])
    op.create_index('ix_chat_rooms_status', 'chat_rooms', ['status'])
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('chat_room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_type', sa.Enum('doctor', 'patient', 'system', name='sendertype'), nullable=False),
        sa.Column('message_type', sa.Enum('text', 'image', 'file', name='messagetype'), nullable=False, server_default='text'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chat_room_id'], ['chat_rooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute("COMMENT ON TABLE chat_messages IS 'Chat messages within chat rooms'")
    
    op.create_index('ix_chat_messages_chat_room_id', 'chat_messages', ['chat_room_id'])
    op.create_index('ix_chat_messages_sender_id', 'chat_messages', ['sender_id'])
    op.create_index('ix_chat_messages_sender_type', 'chat_messages', ['sender_type'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_chat_messages_created_at', table_name='chat_messages')
    op.drop_index('ix_chat_messages_sender_type', table_name='chat_messages')
    op.drop_index('ix_chat_messages_sender_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_chat_room_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    
    op.drop_index('ix_chat_rooms_status', table_name='chat_rooms')
    op.drop_index('ix_chat_rooms_appointment_id', table_name='chat_rooms')
    op.drop_index('ix_chat_rooms_patient_id', table_name='chat_rooms')
    op.drop_index('ix_chat_rooms_doctor_id', table_name='chat_rooms')
    op.drop_table('chat_rooms')
    
    op.execute('DROP TYPE IF EXISTS messagetype')
    op.execute('DROP TYPE IF EXISTS sendertype')
    op.execute('DROP TYPE IF EXISTS chatroomstatus')
