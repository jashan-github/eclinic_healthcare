"""create_doctor_availability_tables

Revision ID: create_doctor_availability_001
Revises: update_location_to_uuids
Create Date: 2025-12-29 11:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_doctor_availability_001'
down_revision = 'update_location_to_uuids'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure uuid-ossp extension exists (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create doctor_availability table
    op.create_table(
        'doctor_availability',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False, comment='0=Monday, 1=Tuesday, ..., 6=Sunday'),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE', name='doctor_availability_doctor_id_fkey'),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE', name='doctor_availability_clinic_id_fkey'),
        sa.CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='doctor_availability_day_of_week_check'),
        sa.CheckConstraint('end_time > start_time', name='doctor_availability_time_check'),
    )
    
    # Create doctor_time_off table
    op.create_table(
        'doctor_time_off',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE', name='doctor_time_off_doctor_id_fkey'),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE', name='doctor_time_off_clinic_id_fkey'),
        sa.CheckConstraint('end_datetime > start_datetime', name='doctor_time_off_datetime_check'),
    )
    
    # Create indexes for performance
    # doctor_availability indexes
    op.create_index('doctor_availability_doctor_id_index', 'doctor_availability', ['doctor_id'])
    op.create_index('doctor_availability_clinic_id_index', 'doctor_availability', ['clinic_id'])
    op.create_index('doctor_availability_doctor_clinic_index', 'doctor_availability', ['doctor_id', 'clinic_id'])
    op.create_index('doctor_availability_day_index', 'doctor_availability', ['day_of_week'])
    op.create_index('doctor_availability_active_index', 'doctor_availability', ['is_active'])
    op.create_index('doctor_availability_deleted_at_index', 'doctor_availability', ['deleted_at'])
    op.create_index('doctor_availability_created_at_index', 'doctor_availability', ['created_at'])
    
    # doctor_time_off indexes
    op.create_index('doctor_time_off_doctor_id_index', 'doctor_time_off', ['doctor_id'])
    op.create_index('doctor_time_off_clinic_id_index', 'doctor_time_off', ['clinic_id'])
    op.create_index('doctor_time_off_doctor_clinic_index', 'doctor_time_off', ['doctor_id', 'clinic_id'])
    op.create_index('doctor_time_off_start_datetime_index', 'doctor_time_off', ['start_datetime'])
    op.create_index('doctor_time_off_end_datetime_index', 'doctor_time_off', ['end_datetime'])
    op.create_index('doctor_time_off_deleted_at_index', 'doctor_time_off', ['deleted_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('doctor_time_off_deleted_at_index', table_name='doctor_time_off')
    op.drop_index('doctor_time_off_end_datetime_index', table_name='doctor_time_off')
    op.drop_index('doctor_time_off_start_datetime_index', table_name='doctor_time_off')
    op.drop_index('doctor_time_off_doctor_clinic_index', table_name='doctor_time_off')
    op.drop_index('doctor_time_off_clinic_id_index', table_name='doctor_time_off')
    op.drop_index('doctor_time_off_doctor_id_index', table_name='doctor_time_off')
    
    op.drop_index('doctor_availability_created_at_index', table_name='doctor_availability')
    op.drop_index('doctor_availability_deleted_at_index', table_name='doctor_availability')
    op.drop_index('doctor_availability_active_index', table_name='doctor_availability')
    op.drop_index('doctor_availability_day_index', table_name='doctor_availability')
    op.drop_index('doctor_availability_doctor_clinic_index', table_name='doctor_availability')
    op.drop_index('doctor_availability_clinic_id_index', table_name='doctor_availability')
    op.drop_index('doctor_availability_doctor_id_index', table_name='doctor_availability')
    
    # Drop tables
    op.drop_table('doctor_time_off')
    op.drop_table('doctor_availability')
