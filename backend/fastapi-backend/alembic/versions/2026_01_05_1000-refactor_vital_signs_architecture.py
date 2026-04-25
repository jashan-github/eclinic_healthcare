"""Refactor vital signs architecture

Revision ID: refactor_vital_signs_001
Revises: create_vital_tables_001
Create Date: 2026-01-05 10:00:00.000000

This migration:
1. Creates vital_frequency table for frequency rules
2. Adds vital_name_id FK to patient_vital_signs
3. Adds numeric_value and text_value columns (replacing JSONB)
4. Adds unit column to store unit at time of recording
5. Keeps vital_data temporarily for data migration
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'refactor_vital_signs_001'
down_revision = 'create_vital_tables_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Refactor vital signs architecture"""
    
    # ==========================================================================
    # Create vital_frequency table
    # ==========================================================================
    op.create_table(
        'vital_frequency',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=True, comment="Patient user ID (NULL = applies to all patients or clinic/global default)"),
        sa.Column('vital_name_id', UUID(as_uuid=True), nullable=True, comment="Vital name ID (NULL = applies to all vital names)"),
        sa.Column('clinic_id', UUID(as_uuid=True), nullable=True, comment="Clinic ID (NULL = global default)"),
        sa.Column('frequency_type', sa.String(50), nullable=True, server_default='daily', comment="Frequency type: 'daily', 'weekly', 'custom'"),
        sa.Column('max_entries_per_day', sa.Integer(), nullable=False, server_default='1', comment="Maximum number of entries allowed per day (e.g., 1, 2, 4, 6)"),
        sa.Column('times_per_day', sa.Integer(), nullable=True, comment="Number of times per day (e.g., 2 = twice a day)"),
        sa.Column('preferred_times', JSONB, nullable=True, comment="Preferred times of day for recording (e.g., ['09:00', '17:00'])"),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment="Whether this frequency rule is active"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vital_name_id'], ['vital_names.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for vital_frequency
    op.create_index('ix_vital_frequency_patient_id', 'vital_frequency', ['patient_id'])
    op.create_index('ix_vital_frequency_vital_name_id', 'vital_frequency', ['vital_name_id'])
    op.create_index('ix_vital_frequency_clinic_id', 'vital_frequency', ['clinic_id'])
    op.create_index('ix_vital_frequency_is_active', 'vital_frequency', ['is_active'])
    op.create_index('ix_vital_frequency_patient_vital', 'vital_frequency', ['patient_id', 'vital_name_id'])
    op.create_index('ix_vital_frequency_clinic_vital', 'vital_frequency', ['clinic_id', 'vital_name_id'])
    op.create_index('ix_vital_frequency_deleted_at', 'vital_frequency', ['deleted_at'])
    
    # ==========================================================================
    # Modify patient_vital_signs table
    # ==========================================================================
    
    # Add new columns
    op.add_column('patient_vital_signs', 
        sa.Column('vital_name_id', UUID(as_uuid=True), nullable=True, comment="Vital name ID (FK to vital_names table)")
    )
    op.add_column('patient_vital_signs',
        sa.Column('numeric_value', sa.Numeric(10, 2), nullable=True, comment="Numeric value for vital signs with data_type='number'")
    )
    op.add_column('patient_vital_signs',
        sa.Column('text_value', sa.Text(), nullable=True, comment="Text value for vital signs with data_type='text' or 'select'")
    )
    op.add_column('patient_vital_signs',
        sa.Column('unit', sa.String(50), nullable=True, comment="Unit of measurement stored at time of recording")
    )
    
    # Add foreign key constraint for vital_name_id
    op.create_foreign_key(
        'fk_patient_vital_signs_vital_name_id',
        'patient_vital_signs', 'vital_names',
        ['vital_name_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Modify vital_data to be nullable (temporarily, for migration)
    op.alter_column('patient_vital_signs', 'vital_data',
        existing_type=JSONB,
        nullable=True,
        existing_nullable=False
    )
    
    # Create new indexes
    op.create_index('ix_patient_vital_signs_vital_name_id', 'patient_vital_signs', ['vital_name_id'])
    op.create_index('ix_patient_vital_signs_patient_vital_date', 'patient_vital_signs', ['patient_id', 'vital_name_id', 'record_date'])
    op.create_index('ix_patient_vital_signs_vital_name', 'patient_vital_signs', ['vital_name_id'])


def downgrade() -> None:
    """Revert vital signs architecture refactoring"""
    
    # Drop new indexes
    op.drop_index('ix_patient_vital_signs_vital_name', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_patient_vital_date', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_vital_name_id', table_name='patient_vital_signs')
    
    # Drop foreign key
    op.drop_constraint('fk_patient_vital_signs_vital_name_id', 'patient_vital_signs', type_='foreignkey')
    
    # Remove new columns
    op.drop_column('patient_vital_signs', 'unit')
    op.drop_column('patient_vital_signs', 'text_value')
    op.drop_column('patient_vital_signs', 'numeric_value')
    op.drop_column('patient_vital_signs', 'vital_name_id')
    
    # Restore vital_data to NOT NULL
    op.alter_column('patient_vital_signs', 'vital_data',
        existing_type=JSONB,
        nullable=False,
        existing_nullable=True
    )
    
    # Drop vital_frequency table indexes
    op.drop_index('ix_vital_frequency_deleted_at', table_name='vital_frequency')
    op.drop_index('ix_vital_frequency_clinic_vital', table_name='vital_frequency')
    op.drop_index('ix_vital_frequency_patient_vital', table_name='vital_frequency')
    op.drop_index('ix_vital_frequency_is_active', table_name='vital_frequency')
    op.drop_index('ix_vital_frequency_clinic_id', table_name='vital_frequency')
    op.drop_index('ix_vital_frequency_vital_name_id', table_name='vital_frequency')
    op.drop_index('ix_vital_frequency_patient_id', table_name='vital_frequency')
    
    # Drop vital_frequency table
    op.drop_table('vital_frequency')

