"""add_assigned_doctor_id_to_users

Revision ID: add_assigned_doctor_id_001
Revises: create_webhook_logs_001
Create Date: 2026-01-13 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_assigned_doctor_id_001'
down_revision = 'create_webhook_logs_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add assigned_doctor_id column to users table
    op.add_column(
        'users',
        sa.Column(
            'assigned_doctor_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Assigned doctor ID for staff role users (nullable)'
        )
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'users_assigned_doctor_id_fkey',
        'users',
        'users',
        ['assigned_doctor_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for better query performance
    op.create_index(
        'ix_users_assigned_doctor_id',
        'users',
        ['assigned_doctor_id']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_users_assigned_doctor_id', table_name='users')
    
    # Drop foreign key constraint
    op.drop_constraint('users_assigned_doctor_id_fkey', 'users', type_='foreignkey')
    
    # Drop column
    op.drop_column('users', 'assigned_doctor_id')
