"""create admin settings table

Revision ID: create_admin_settings_001
Revises: create_video_sessions_001
Create Date: 2026-01-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_admin_settings_001'
down_revision = 'create_video_sessions_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create admin_settings table
    op.create_table(
        'admin_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('auto_approve_appointments', sa.Boolean(), nullable=False, server_default='FALSE'),
        sa.Column('allow_same_day_booking', sa.Boolean(), nullable=False, server_default='FALSE'),
        sa.Column('booking_window_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        comment='System-wide admin configuration settings'
    )
    
    # Create indexes
    op.create_index('ix_admin_settings_deleted_at', 'admin_settings', ['deleted_at'])
    
    # Insert default settings record
    op.execute("""
        INSERT INTO admin_settings (id, auto_approve_appointments, allow_same_day_booking, booking_window_days)
        VALUES (uuid_generate_v4(), FALSE, FALSE, 30)
    """)


def downgrade() -> None:
    op.drop_table('admin_settings')
