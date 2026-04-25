"""create_patient_documents_table

Revision ID: create_patient_documents_001
Revises: create_webinars_001
Create Date: 2026-01-08 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_patient_documents_001'
down_revision = 'create_webinars_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create patient_documents table
    op.create_table(
        'patient_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment='Patient user ID'),
        sa.Column('document_type', sa.String(100), nullable=False, comment='Type of document (Blood Test Report, X-Ray, etc.)'),
        sa.Column('file_name', sa.String(255), nullable=False, comment='Original file name'),
        sa.Column('file_path', sa.String(500), nullable=False, comment='Relative path to file'),
        sa.Column('file_size', sa.BigInteger(), nullable=False, comment='File size in bytes'),
        sa.Column('file_extension', sa.String(10), nullable=False, comment='File extension (pdf, jpg, png, etc.)'),
        sa.Column('mime_type', sa.String(100), nullable=False, comment='MIME type of the file'),
        sa.Column('issued_by', sa.String(255), nullable=True, comment='Doctor/issuer name'),
        sa.Column('issued_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True, comment='Doctor user ID'),
        sa.Column('issued_date', sa.Date(), nullable=True, comment='Date document was issued'),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True, comment='User who uploaded the document'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Additional notes about the document'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes
    op.create_index('patient_documents_patient_id_index', 'patient_documents', ['patient_id'])
    op.create_index('patient_documents_issued_by_id_index', 'patient_documents', ['issued_by_id'])
    op.create_index('patient_documents_uploaded_by_index', 'patient_documents', ['uploaded_by'])
    op.create_index('patient_documents_document_type_index', 'patient_documents', ['document_type'])
    op.create_index('patient_documents_file_extension_index', 'patient_documents', ['file_extension'])
    op.create_index('patient_documents_issued_date_index', 'patient_documents', ['issued_date'])
    op.create_index('patient_documents_created_at_index', 'patient_documents', ['created_at'])
    op.create_index('patient_documents_deleted_at_index', 'patient_documents', ['deleted_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('patient_documents_deleted_at_index', table_name='patient_documents')
    op.drop_index('patient_documents_created_at_index', table_name='patient_documents')
    op.drop_index('patient_documents_issued_date_index', table_name='patient_documents')
    op.drop_index('patient_documents_file_extension_index', table_name='patient_documents')
    op.drop_index('patient_documents_document_type_index', table_name='patient_documents')
    op.drop_index('patient_documents_uploaded_by_index', table_name='patient_documents')
    op.drop_index('patient_documents_issued_by_id_index', table_name='patient_documents')
    op.drop_index('patient_documents_patient_id_index', table_name='patient_documents')
    
    # Drop table
    op.drop_table('patient_documents')
