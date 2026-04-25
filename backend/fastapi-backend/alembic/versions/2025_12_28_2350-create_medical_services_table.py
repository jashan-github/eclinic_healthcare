"""create_medical_services_table

Revision ID: create_medical_services_001
Revises: add_medical_fields_001
Create Date: 2025-12-28 23:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_medical_services_001'
down_revision = 'add_medical_fields_001'
branch_labels = None
depends_on = None


def upgrade():
    # Check if table already exists (idempotent)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'medical_services' in existing_tables:
        # Table already exists, skip creation
        return
    
    # Create medical_services table
    op.create_table(
        'medical_services',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('parent', sa.String(length=255), nullable=False, server_default='0', comment='Parent service ID (for hierarchical structure, default "0" for root)'),
        sa.Column('name', sa.String(length=50), nullable=True, comment='Service name'),
        sa.Column('image', sa.String(length=200), nullable=True, comment='Service image path/URL'),
        sa.Column('status', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='Service status (0=inactive, 1=active)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
    )
    
    # Create index on id
    op.create_index('ix_medical_services_id', 'medical_services', ['id'])
    
    # Create index on parent for hierarchical queries
    op.create_index('ix_medical_services_parent', 'medical_services', ['parent'])
    
    # Create index on status for filtering active services
    op.create_index('ix_medical_services_status', 'medical_services', ['status'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_medical_services_status', table_name='medical_services')
    op.drop_index('ix_medical_services_parent', table_name='medical_services')
    op.drop_index('ix_medical_services_id', table_name='medical_services')
    
    # Drop table
    op.drop_table('medical_services')

