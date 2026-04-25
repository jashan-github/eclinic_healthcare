"""Add share_with_doctor consent field to patient_vital_signs

Revision ID: add_share_with_doctor_001
Revises: refactor_vital_signs_001
Create Date: 2026-01-07 16:03:00.000000

This migration:
1. Adds share_with_doctor boolean column to patient_vital_signs table
2. Sets default to False (patient must explicitly consent)
3. Adds index for efficient doctor queries
4. Sets existing records to False (no retroactive consent)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_share_with_doctor_001'
down_revision = 'refactor_vital_signs_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add share_with_doctor consent field"""
    
    # Add share_with_doctor column
    op.add_column(
        'patient_vital_signs',
        sa.Column(
            'share_with_doctor',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
            comment='Patient consent to share this vital sign with doctor for medical evaluation and care'
        )
    )
    
    # Add index for efficient doctor queries
    op.create_index(
        'ix_patient_vital_signs_share_with_doctor',
        'patient_vital_signs',
        ['share_with_doctor'],
        unique=False
    )
    
    # Add composite index for doctor queries (patient_id + share_with_doctor)
    op.create_index(
        'ix_patient_vital_signs_patient_consent',
        'patient_vital_signs',
        ['patient_id', 'share_with_doctor'],
        unique=False
    )


def downgrade() -> None:
    """Remove share_with_doctor consent field"""
    
    # Drop indexes
    op.drop_index('ix_patient_vital_signs_patient_consent', table_name='patient_vital_signs')
    op.drop_index('ix_patient_vital_signs_share_with_doctor', table_name='patient_vital_signs')
    
    # Drop column
    op.drop_column('patient_vital_signs', 'share_with_doctor')

