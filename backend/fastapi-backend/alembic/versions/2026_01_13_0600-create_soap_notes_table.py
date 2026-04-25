"""create soap notes table

Revision ID: create_soap_notes_001
Revises: create_admin_settings_001
Create Date: 2026-01-13 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_soap_notes_001'
down_revision = 'create_admin_settings_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create soap_notes table
    op.create_table(
        'soap_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subjective', sa.Text(), nullable=True, comment="Subjective: Patient's symptoms, feelings, concerns"),
        sa.Column('objective', sa.Text(), nullable=True, comment="Objective: Observable findings, measurements, test results"),
        sa.Column('assessment', sa.Text(), nullable=True, comment="Assessment: Diagnosis, evaluation, clinical impression"),
        sa.Column('plan', sa.Text(), nullable=True, comment="Plan: Treatment plan, medications, follow-up actions"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        comment='SOAP Notes for patient appointments'
    )
    
    # Create indexes
    op.create_index('soap_notes_appointment_id_index', 'soap_notes', ['appointment_id'])
    op.create_index('soap_notes_doctor_id_index', 'soap_notes', ['doctor_id'])
    op.create_index('soap_notes_patient_id_index', 'soap_notes', ['patient_id'])
    op.create_index('soap_notes_created_at_index', 'soap_notes', ['created_at'])
    op.create_index('soap_notes_deleted_at_index', 'soap_notes', ['deleted_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('soap_notes_deleted_at_index', table_name='soap_notes')
    op.drop_index('soap_notes_created_at_index', table_name='soap_notes')
    op.drop_index('soap_notes_patient_id_index', table_name='soap_notes')
    op.drop_index('soap_notes_doctor_id_index', table_name='soap_notes')
    op.drop_index('soap_notes_appointment_id_index', table_name='soap_notes')
    
    # Drop table
    op.drop_table('soap_notes')
