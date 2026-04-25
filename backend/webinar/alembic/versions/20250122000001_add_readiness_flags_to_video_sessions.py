"""add_readiness_flags_to_video_sessions

Revision ID: add_readiness_flags_001
Revises: create_webinars_001
Create Date: 2025-01-22 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_readiness_flags_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if video_sessions table exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    # Check if columns already exist
    columns_exist = False
    if 'video_sessions' in tables:
        columns = [col['name'] for col in inspector.get_columns('video_sessions')]
        columns_exist = all(col in columns for col in ['doctor_ready', 'patient_ready', 'doctor_confirmed_join', 'patient_confirmed_join'])
    
    if columns_exist:
        # Columns already exist, skip
        return
    
    if 'video_sessions' not in tables:
        # Create video_sessions table if it doesn't exist
        op.create_table(
            'video_sessions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
            sa.Column('session_id', postgresql.UUID(as_uuid=True), unique=True, nullable=False, index=True, comment='Unique session identifier (UUID)'),
            sa.Column('channel_name', sa.String(255), unique=True, nullable=False, index=True, comment='Agora channel name (secure hash, no PHI)'),
            sa.Column('session_type', sa.String(20), nullable=False, server_default='appointment', comment='Type of video session'),
            sa.Column('status', sa.String(20), nullable=False, server_default='scheduled', index=True, comment='Current state in state machine'),
            sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False, index=True, comment='Doctor/host user ID'),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True, index=True, comment='Patient/participant user ID (null for webinars)'),
            sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=True, index=True, comment='Associated appointment ID'),
            sa.Column('webinar_id', postgresql.UUID(as_uuid=True), nullable=True, index=True, comment='Associated webinar ID'),
            sa.Column('scheduled_start_time', sa.DateTime(timezone=True), nullable=True, index=True, comment='Scheduled start time (null for emergency calls)'),
            sa.Column('scheduled_end_time', sa.DateTime(timezone=True), nullable=True, comment='Scheduled end time'),
            sa.Column('doctor_joined_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when doctor successfully joined (billing starts here)'),
            sa.Column('patient_joined_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when patient successfully joined'),
            sa.Column('call_started_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when both parties in call'),
            sa.Column('call_ended_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when call ended'),
            sa.Column('patient_entered_waiting_room_at', sa.DateTime(timezone=True), nullable=True, comment='When patient entered waiting room'),
            sa.Column('waiting_room_duration_seconds', sa.Integer(), nullable=True, server_default='0', comment='Total time patient spent in waiting room (not billed)'),
            sa.Column('join_attempt_started_at', sa.DateTime(timezone=True), nullable=True, comment='When join attempt started (for 30s watchdog)'),
            sa.Column('join_watchdog_expires_at', sa.DateTime(timezone=True), nullable=True, comment='When join watchdog expires (30s after attempt start)'),
            sa.Column('billing_started_at', sa.DateTime(timezone=True), nullable=True, comment='When billing started (same as doctor_joined_at)'),
            sa.Column('billable_duration_seconds', sa.Integer(), nullable=True, server_default='0', comment='Total billable duration in seconds'),
            sa.Column('doctor_token', sa.Text(), nullable=True, comment='Agora token for doctor (encrypted, expires in 15-60 min)'),
            sa.Column('patient_token', sa.Text(), nullable=True, comment='Agora token for patient (encrypted, expires in 15-60 min)'),
            sa.Column('doctor_token_expires_at', sa.DateTime(timezone=True), nullable=True, comment='Doctor token expiration'),
            sa.Column('patient_token_expires_at', sa.DateTime(timezone=True), nullable=True, comment='Patient token expiration'),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0', comment='Number of retry attempts'),
            sa.Column('previous_session_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Previous session ID if this is a retry'),
            sa.Column('grace_period_seconds', sa.Integer(), nullable=True, server_default='300', comment='Grace period after end_time before expiry (default 5 min)'),
            sa.Column('recording_enabled', sa.Boolean(), nullable=False, server_default='false', comment='Whether recording is enabled (requires consent)'),
            sa.Column('recording_started_at', sa.DateTime(timezone=True), nullable=True, comment='When recording started'),
            sa.Column('recording_stopped_at', sa.DateTime(timezone=True), nullable=True, comment='When recording stopped'),
            sa.Column('recording_resource_id', sa.String(255), nullable=True, comment='Agora recording resource ID'),
            sa.Column('last_error', sa.Text(), nullable=True, comment='Last error message if join failed'),
            sa.Column('error_code', sa.String(50), nullable=True, comment='Error code for join failure'),
            sa.Column('metadata', postgresql.JSONB(), nullable=True, comment='Additional metadata (device info, network, etc.)'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        )
        
        # Add readiness flags
        op.add_column('video_sessions', 
            sa.Column('doctor_ready', sa.Boolean(), nullable=False, server_default='false', comment='Doctor has indicated readiness to join')
        )
        op.add_column('video_sessions', 
            sa.Column('patient_ready', sa.Boolean(), nullable=False, server_default='false', comment='Patient has indicated readiness to join')
        )
        op.add_column('video_sessions', 
            sa.Column('doctor_confirmed_join', sa.Boolean(), nullable=False, server_default='false', comment='Doctor has confirmed successful join via Agora')
        )
        op.add_column('video_sessions', 
            sa.Column('patient_confirmed_join', sa.Boolean(), nullable=False, server_default='false', comment='Patient has confirmed successful join via Agora')
        )
    else:
        # Table exists, just add the new columns
        op.add_column('video_sessions', 
            sa.Column('doctor_ready', sa.Boolean(), nullable=False, server_default='false', comment='Doctor has indicated readiness to join')
        )
        op.add_column('video_sessions', 
            sa.Column('patient_ready', sa.Boolean(), nullable=False, server_default='false', comment='Patient has indicated readiness to join')
        )
        op.add_column('video_sessions', 
            sa.Column('doctor_confirmed_join', sa.Boolean(), nullable=False, server_default='false', comment='Doctor has confirmed successful join via Agora')
        )
        op.add_column('video_sessions', 
            sa.Column('patient_confirmed_join', sa.Boolean(), nullable=False, server_default='false', comment='Patient has confirmed successful join via Agora')
        )


def downgrade() -> None:
    # Remove the columns
    op.drop_column('video_sessions', 'patient_confirmed_join')
    op.drop_column('video_sessions', 'doctor_confirmed_join')
    op.drop_column('video_sessions', 'patient_ready')
    op.drop_column('video_sessions', 'doctor_ready')
