"""create_webinars_table

Revision ID: create_webinars_001
Revises: create_clinic_locations_001
Create Date: 2026-01-08 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_webinars_001'
down_revision = 'create_clinic_locations_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create webinars table
    op.create_table(
        'webinars',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False, comment='Webinar title'),
        sa.Column('description', sa.Text(), nullable=True, comment='Webinar description'),
        sa.Column('webinar_date', sa.Date(), nullable=False, comment='Date of the webinar'),
        sa.Column('start_time', sa.Time(), nullable=False, comment='Start time'),
        sa.Column('end_time', sa.Time(), nullable=False, comment='End time'),
        sa.Column('pricing_type', sa.String(20), nullable=False, server_default='free', comment='Pricing type: free or paid'),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0.00', comment='Price for paid webinars'),
        sa.Column('participant_limit', sa.Integer(), nullable=True, comment='Maximum number of participants'),
        sa.Column('host_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True, comment='Host user ID'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True, comment='Creator user ID'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft', comment='Status: draft, scheduled, live, completed, cancelled'),
        sa.Column('visibility', sa.String(20), nullable=False, server_default='public', comment='Visibility: public or private'),
        sa.Column('agora_channel_name', sa.String(255), nullable=True, comment='Agora channel name for live streaming'),
        sa.Column('agora_token', sa.String(500), nullable=True, comment='Agora token for authentication'),
        sa.Column('registered_count', sa.Integer(), nullable=False, server_default='0', comment='Number of registered participants'),
        sa.Column('attended_count', sa.Integer(), nullable=False, server_default='0', comment='Number of attended participants'),
        sa.Column('agenda', sa.Text(), nullable=True, comment='Webinar agenda'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes
    op.create_index('webinars_host_id_index', 'webinars', ['host_id'])
    op.create_index('webinars_created_by_index', 'webinars', ['created_by'])
    op.create_index('webinars_status_index', 'webinars', ['status'])
    op.create_index('webinars_visibility_index', 'webinars', ['visibility'])
    op.create_index('webinars_webinar_date_index', 'webinars', ['webinar_date'])
    op.create_index('webinars_pricing_type_index', 'webinars', ['pricing_type'])
    op.create_index('webinars_created_at_index', 'webinars', ['created_at'])
    op.create_index('webinars_deleted_at_index', 'webinars', ['deleted_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('webinars_deleted_at_index', table_name='webinars')
    op.drop_index('webinars_created_at_index', table_name='webinars')
    op.drop_index('webinars_pricing_type_index', table_name='webinars')
    op.drop_index('webinars_webinar_date_index', table_name='webinars')
    op.drop_index('webinars_visibility_index', table_name='webinars')
    op.drop_index('webinars_status_index', table_name='webinars')
    op.drop_index('webinars_created_by_index', table_name='webinars')
    op.drop_index('webinars_host_id_index', table_name='webinars')
    
    # Drop table
    op.drop_table('webinars')
