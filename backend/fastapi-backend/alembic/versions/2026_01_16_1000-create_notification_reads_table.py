"""create_notification_reads_table

Create notification_reads table for tracking which appointment notifications have been read by users.

Revision ID: create_notification_reads_001
Revises: add_assigned_doctor_id_001
Create Date: 2026-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_notification_reads_001'
down_revision = 'add_assigned_doctor_id_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create notification_reads table.
    
    Tracks:
    - Which appointment request notifications have been read by users
    - When notifications were marked as read
    - Supports both doctor and patient notifications
    """
    # Ensure uuid-ossp extension exists (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    op.create_table(
        'notification_reads',
        # Primary key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
            comment='Primary key (UUID)'
        ),
        # Foreign keys
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='User who read the notification'
        ),
        sa.Column(
            'appointment_request_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('appointment_requests.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='Appointment request ID (the notification)'
        ),
        # Timestamp
        sa.Column(
            'read_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
            comment='Timestamp when notification was marked as read (UTC)'
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint('id', name='notification_reads_pkey'),
        # Unique constraint: one read record per user per notification
        sa.UniqueConstraint(
            'user_id', 'appointment_request_id',
            name='notification_reads_user_request_unique'
        ),
        comment='Tracks which appointment notifications have been read by users'
    )
    
    # Create indexes for performance
    op.create_index(
        'notification_reads_user_id_index',
        'notification_reads',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'notification_reads_appointment_request_id_index',
        'notification_reads',
        ['appointment_request_id'],
        unique=False
    )
    op.create_index(
        'notification_reads_read_at_index',
        'notification_reads',
        ['read_at'],
        unique=False
    )


def downgrade() -> None:
    """
    Drop notification_reads table and indexes.
    """
    # Drop indexes first
    op.drop_index('notification_reads_read_at_index', table_name='notification_reads')
    op.drop_index('notification_reads_appointment_request_id_index', table_name='notification_reads')
    op.drop_index('notification_reads_user_id_index', table_name='notification_reads')
    
    # Drop table
    op.drop_table('notification_reads')
