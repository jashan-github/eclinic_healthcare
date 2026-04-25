"""create_services_table

Revision ID: create_services_001
Revises: merge_heads_001
Create Date: 2025-12-29 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_services_001'
down_revision = 'merge_heads_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure uuid-ossp extension exists (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create services table
    op.create_table(
        'services',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Clinic ID for multi-clinic support'),
        sa.Column('name', sa.String(255), nullable=False, comment='Service name'),
        sa.Column('nickname', sa.String(255), nullable=True, comment='Service nickname (optional)'),
        sa.Column('service_mode', sa.String(50), nullable=False, comment='Service mode: IN_CLINIC or VIDEO'),
        sa.Column('appointment_type', sa.String(50), nullable=False, comment='Appointment type: REGULAR or FOLLOW_UP'),
        sa.Column('is_bookable', sa.Boolean(), nullable=False, server_default='true', comment='Whether service is available for booking'),
        sa.Column('advance_booking_days', sa.Integer(), nullable=False, server_default='30', comment='Number of days in advance bookings can be made'),
        sa.Column('minimum_notice_minutes', sa.Integer(), nullable=False, server_default='60', comment='Minimum notice required in minutes'),
        sa.Column('payment_type', sa.String(50), nullable=False, comment='Payment type: PREPAID or POSTPAID'),
        sa.Column('price', sa.Numeric(10, 2), nullable=True, comment='Service price (nullable)'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False, comment='Admin user ID who created the service'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE', name='services_clinic_id_fkey'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT', name='services_created_by_fkey'),
        sa.CheckConstraint("service_mode IN ('IN_CLINIC', 'VIDEO')", name='services_service_mode_check'),
        sa.CheckConstraint("appointment_type IN ('REGULAR', 'FOLLOW_UP')", name='services_appointment_type_check'),
        sa.CheckConstraint("payment_type IN ('PREPAID', 'POSTPAID')", name='services_payment_type_check'),
        sa.CheckConstraint('advance_booking_days >= 0', name='services_advance_booking_days_check'),
        sa.CheckConstraint('minimum_notice_minutes >= 0', name='services_minimum_notice_minutes_check'),
        sa.CheckConstraint('price IS NULL OR price >= 0', name='services_price_check'),
    )
    
    # Create indexes for performance
    op.create_index('services_clinic_id_index', 'services', ['clinic_id'])
    op.create_index('services_created_by_index', 'services', ['created_by'])
    op.create_index('services_service_mode_index', 'services', ['service_mode'])
    op.create_index('services_appointment_type_index', 'services', ['appointment_type'])
    op.create_index('services_is_bookable_index', 'services', ['is_bookable'])
    op.create_index('services_payment_type_index', 'services', ['payment_type'])
    op.create_index('services_clinic_bookable_index', 'services', ['clinic_id', 'is_bookable'])
    op.create_index('services_deleted_at_index', 'services', ['deleted_at'])
    op.create_index('services_created_at_index', 'services', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('services_created_at_index', table_name='services')
    op.drop_index('services_deleted_at_index', table_name='services')
    op.drop_index('services_clinic_bookable_index', table_name='services')
    op.drop_index('services_payment_type_index', table_name='services')
    op.drop_index('services_is_bookable_index', table_name='services')
    op.drop_index('services_appointment_type_index', table_name='services')
    op.drop_index('services_service_mode_index', table_name='services')
    op.drop_index('services_created_by_index', table_name='services')
    op.drop_index('services_clinic_id_index', table_name='services')
    
    # Drop table
    op.drop_table('services')
