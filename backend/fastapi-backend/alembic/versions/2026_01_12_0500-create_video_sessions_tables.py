"""create video sessions and audit log tables

Revision ID: create_video_sessions_001
Revises: add_unique_constraint_rx_templates_001
Create Date: 2026-01-12 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_video_sessions_001'
down_revision = 'add_unique_constraint_rx_templates_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create video_sessions table
    op.create_table(
        'video_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('channel_name', sa.String(255), nullable=False, unique=True),
        sa.Column('session_type', sa.String(50), nullable=False, server_default='appointment'),
        sa.Column('status', sa.String(50), nullable=False, server_default='scheduled'),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('webinar_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scheduled_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('doctor_joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('call_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('call_ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_entered_waiting_room_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('waiting_room_duration_seconds', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('join_attempt_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('join_watchdog_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billable_duration_seconds', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('doctor_token', sa.Text(), nullable=True),
        sa.Column('patient_token', sa.Text(), nullable=True),
        sa.Column('doctor_token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('previous_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('grace_period_seconds', sa.Integer(), nullable=True, server_default='300'),
        sa.Column('recording_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('recording_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recording_stopped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recording_resource_id', sa.String(255), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['webinar_id'], ['webinars.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='HIPAA-compliant video call and webinar sessions'
    )
    
    # Create indexes
    op.create_index('ix_video_sessions_session_id', 'video_sessions', ['session_id'], unique=True)
    op.create_index('ix_video_sessions_channel_name', 'video_sessions', ['channel_name'], unique=True)
    op.create_index('ix_video_sessions_status', 'video_sessions', ['status'])
    op.create_index('ix_video_sessions_doctor_id', 'video_sessions', ['doctor_id'])
    op.create_index('ix_video_sessions_patient_id', 'video_sessions', ['patient_id'])
    op.create_index('ix_video_sessions_appointment_id', 'video_sessions', ['appointment_id'])
    op.create_index('ix_video_sessions_webinar_id', 'video_sessions', ['webinar_id'])
    op.create_index('ix_video_sessions_scheduled_start_time', 'video_sessions', ['scheduled_start_time'])
    op.create_index('ix_video_sessions_created_at', 'video_sessions', ['created_at'])
    
    # Create video_session_audit_logs table
    op.create_table(
        'video_session_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_role', sa.String(50), nullable=True),
        sa.Column('previous_status', sa.String(50), nullable=True),
        sa.Column('new_status', sa.String(50), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        comment='HIPAA-compliant audit log for video sessions'
    )
    
    # Create indexes for audit logs
    op.create_index('ix_video_session_audit_logs_session_id', 'video_session_audit_logs', ['session_id'])
    op.create_index('ix_video_session_audit_logs_event_type', 'video_session_audit_logs', ['event_type'])
    op.create_index('ix_video_session_audit_logs_user_id', 'video_session_audit_logs', ['user_id'])
    op.create_index('ix_video_session_audit_logs_event_timestamp', 'video_session_audit_logs', ['event_timestamp'])


def downgrade() -> None:
    op.drop_index('ix_video_session_audit_logs_event_timestamp', table_name='video_session_audit_logs')
    op.drop_index('ix_video_session_audit_logs_user_id', table_name='video_session_audit_logs')
    op.drop_index('ix_video_session_audit_logs_event_type', table_name='video_session_audit_logs')
    op.drop_index('ix_video_session_audit_logs_session_id', table_name='video_session_audit_logs')
    op.drop_table('video_session_audit_logs')
    
    op.drop_index('ix_video_sessions_created_at', table_name='video_sessions')
    op.drop_index('ix_video_sessions_scheduled_start_time', table_name='video_sessions')
    op.drop_index('ix_video_sessions_webinar_id', table_name='video_sessions')
    op.drop_index('ix_video_sessions_appointment_id', table_name='video_sessions')
    op.drop_index('ix_video_sessions_patient_id', table_name='video_sessions')
    op.drop_index('ix_video_sessions_doctor_id', table_name='video_sessions')
    op.drop_index('ix_video_sessions_status', table_name='video_sessions')
    op.drop_index('ix_video_sessions_channel_name', table_name='video_sessions')
    op.drop_index('ix_video_sessions_session_id', table_name='video_sessions')
    op.drop_table('video_sessions')
