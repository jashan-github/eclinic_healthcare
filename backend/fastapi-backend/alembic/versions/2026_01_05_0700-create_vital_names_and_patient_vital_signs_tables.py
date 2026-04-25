"""Create vital names and patient vital signs tables

Revision ID: create_vital_tables_001
Revises: dynamic_currency_2026
Create Date: 2026-01-05 07:00:00.000000

This migration:
1. Creates vital_names table for managing vital sign names
2. Creates patient_vital_signs table for storing patient vital sign readings
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'create_vital_tables_001'
down_revision = 'dynamic_currency_2026'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vital names and patient vital signs tables"""
    
    # ==========================================================================
    # Create vital_names table
    # ==========================================================================
    op.create_table(
        'vital_names',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, unique=True, comment="Vital sign name (e.g., 'Weight (lbs)', 'BP Systolic')"),
        sa.Column('unit', sa.String(50), nullable=True, comment="Unit of measurement (e.g., 'lbs', 'mmHg', 'per min')"),
        sa.Column('display_order', sa.String(10), nullable=True, server_default='0', comment="Display order for sorting"),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment="Whether this vital name is active"),
        sa.Column('data_type', sa.String(50), nullable=True, server_default='number', comment="Data type: number, text, select, etc."),
        sa.Column('options', sa.String(500), nullable=True, comment="JSON string for select options (if data_type is 'select')"),
        sa.Column('max_entries_per_day', sa.String(10), nullable=True, server_default='1', comment="Maximum number of entries allowed per day for doctors (e.g., '1', '2', '4', '6'). Default is 1."),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for vital_names
    op.create_index('ix_vital_names_name', 'vital_names', ['name'])
    op.create_index('ix_vital_names_is_active', 'vital_names', ['is_active'])
    op.create_index('ix_vital_names_display_order', 'vital_names', ['display_order'])
    op.create_index('ix_vital_names_deleted_at', 'vital_names', ['deleted_at'])
    
    # ==========================================================================
    # Create patient_vital_signs table
    # ==========================================================================
    op.create_table(
        'patient_vital_signs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False, comment="Patient user ID"),
        sa.Column('clinic_id', UUID(as_uuid=True), nullable=False, comment="Clinic ID"),
        sa.Column('doctor_id', UUID(as_uuid=True), nullable=True, comment="Doctor user ID who recorded the vital signs"),
        sa.Column('appointment_id', UUID(as_uuid=True), nullable=True, comment="Associated appointment ID (if recorded during appointment)"),
        sa.Column('record_date', sa.DateTime(timezone=True), nullable=False, comment="Date when vital signs were recorded"),
        sa.Column('vital_data', JSONB, nullable=False, comment="JSON object containing vital sign readings"),
        sa.Column('notes', sa.Text(), nullable=True, comment="Additional notes about the vital signs"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for patient_vital_signs
    op.create_index('ix_patient_vital_signs_patient_id', 'patient_vital_signs', ['patient_id'])
    op.create_index('ix_patient_vital_signs_clinic_id', 'patient_vital_signs', ['clinic_id'])
    op.create_index('ix_patient_vital_signs_doctor_id', 'patient_vital_signs', ['doctor_id'])
    op.create_index('ix_patient_vital_signs_appointment_id', 'patient_vital_signs', ['appointment_id'])
    op.create_index('ix_patient_vital_signs_record_date', 'patient_vital_signs', ['record_date'])
    op.create_index('ix_patient_vital_signs_patient_date', 'patient_vital_signs', ['patient_id', 'record_date'])
    op.create_index('ix_patient_vital_signs_clinic_date', 'patient_vital_signs', ['clinic_id', 'record_date'])
    op.create_index('ix_patient_vital_signs_deleted_at', 'patient_vital_signs', ['deleted_at'])


def downgrade() -> None:
    """Drop vital names and patient vital signs tables"""
    
    # Drop indexes first
    op.drop_index('ix_patient_vital_signs_deleted_at', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_clinic_date', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_patient_date', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_record_date', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_appointment_id', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_doctor_id', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_clinic_id', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_patient_id', table_name='patient_vital_signs')
    
    op.drop_index('ix_vital_names_deleted_at', table_name='vital_names')
    op.drop_index('ix_vital_names_display_order', table_name='vital_names')
    op.drop_index('ix_vital_names_is_active', table_name='vital_names')
    op.drop_index('ix_vital_names_name', table_name='vital_names')
    
    # Drop tables
    op.drop_table('patient_vital_signs')
    op.drop_table('vital_names')

