"""add_in_channel_flags_to_video_sessions

Revision ID: add_in_channel_001
Revises: add_readiness_flags_001
Create Date: 2025-01-27 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_in_channel_001'
down_revision = 'add_readiness_flags_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if 'video_sessions' not in inspector.get_table_names():
        return
    columns = [c['name'] for c in inspector.get_columns('video_sessions')]
    if 'doctor_in_channel' not in columns:
        op.add_column(
            'video_sessions',
            sa.Column('doctor_in_channel', sa.Boolean(), nullable=False, server_default='false',
                     comment='Doctor is currently in Agora channel (set on join-success, clear on leave)'),
        )
    if 'patient_in_channel' not in columns:
        op.add_column(
            'video_sessions',
            sa.Column('patient_in_channel', sa.Boolean(), nullable=False, server_default='false',
                     comment='Patient is currently in Agora channel (set on join-success, clear on leave)'),
        )


def downgrade() -> None:
    op.drop_column('video_sessions', 'doctor_in_channel')
    op.drop_column('video_sessions', 'patient_in_channel')
