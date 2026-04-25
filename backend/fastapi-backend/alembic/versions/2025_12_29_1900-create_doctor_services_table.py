"""create_doctor_services_table

Revision ID: create_doctor_services_001
Revises: create_services_001
Create Date: 2025-12-29 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_doctor_services_001'
down_revision = 'create_services_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure uuid-ossp extension exists (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create doctor_services table
    op.create_table(
        'doctor_services',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Doctor user ID'),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Service ID'),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Clinic ID'),
        sa.Column('slot_duration_minutes', sa.Integer(), nullable=False, comment='Duration of appointment slot in minutes'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether assignment is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE', name='doctor_services_doctor_id_fkey'),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ondelete='CASCADE', name='doctor_services_service_id_fkey'),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE', name='doctor_services_clinic_id_fkey'),
        sa.UniqueConstraint('doctor_id', 'service_id', name='doctor_services_doctor_service_unique'),
        sa.CheckConstraint('slot_duration_minutes >= 5 AND slot_duration_minutes <= 360', name='doctor_services_slot_duration_check'),
    )
    
    # Create indexes for performance
    op.create_index('doctor_services_doctor_id_index', 'doctor_services', ['doctor_id'])
    op.create_index('doctor_services_service_id_index', 'doctor_services', ['service_id'])
    op.create_index('doctor_services_clinic_id_index', 'doctor_services', ['clinic_id'])
    op.create_index('doctor_services_doctor_clinic_index', 'doctor_services', ['doctor_id', 'clinic_id'])
    op.create_index('doctor_services_service_clinic_index', 'doctor_services', ['service_id', 'clinic_id'])
    op.create_index('doctor_services_is_active_index', 'doctor_services', ['is_active'])
    op.create_index('doctor_services_created_at_index', 'doctor_services', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('doctor_services_created_at_index', table_name='doctor_services')
    op.drop_index('doctor_services_is_active_index', table_name='doctor_services')
    op.drop_index('doctor_services_service_clinic_index', table_name='doctor_services')
    op.drop_index('doctor_services_doctor_clinic_index', table_name='doctor_services')
    op.drop_index('doctor_services_clinic_id_index', table_name='doctor_services')
    op.drop_index('doctor_services_service_id_index', table_name='doctor_services')
    op.drop_index('doctor_services_doctor_id_index', table_name='doctor_services')
    
    # Drop table
    op.drop_table('doctor_services')
