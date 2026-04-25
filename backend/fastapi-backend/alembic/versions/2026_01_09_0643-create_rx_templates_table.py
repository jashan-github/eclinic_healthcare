"""create rx_templates table

Revision ID: create_rx_templates_001
Revises: migrate_stripe_to_sentoo_001
Create Date: 2026-01-09 06:43:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_rx_templates_001'
down_revision = 'migrate_stripe_to_sentoo_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create rx_templates table
    op.create_table(
        'rx_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clinic_location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('letterhead_image_path', sa.String(500), nullable=True),
        sa.Column('template_name', sa.String(255), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clinic_location_id'], ['clinic_locations.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('rx_templates_doctor_id_index', 'rx_templates', ['doctor_id'])
    op.create_index('rx_templates_clinic_location_id_index', 'rx_templates', ['clinic_location_id'])
    op.create_index('rx_templates_is_default_index', 'rx_templates', ['is_default'])
    op.create_index('rx_templates_created_at_index', 'rx_templates', ['created_at'])
    op.create_index('rx_templates_deleted_at_index', 'rx_templates', ['deleted_at'])
    
    # Create partial unique index: only one default template per doctor per location
    op.execute("""
        CREATE UNIQUE INDEX rx_templates_unique_default_per_doctor_location 
        ON rx_templates (doctor_id, clinic_location_id) 
        WHERE is_default = true AND deleted_at IS NULL
    """)
    
    # Add table comment
    op.execute("COMMENT ON TABLE rx_templates IS 'RX prescription templates for doctors at clinic locations'")


def downgrade() -> None:
    op.drop_index('rx_templates_unique_default_per_doctor_location', table_name='rx_templates')
    op.drop_index('rx_templates_deleted_at_index', table_name='rx_templates')
    op.drop_index('rx_templates_created_at_index', table_name='rx_templates')
    op.drop_index('rx_templates_is_default_index', table_name='rx_templates')
    op.drop_index('rx_templates_clinic_location_id_index', table_name='rx_templates')
    op.drop_index('rx_templates_doctor_id_index', table_name='rx_templates')
    op.drop_table('rx_templates')
