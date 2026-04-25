"""create_clinic_locations_table

Revision ID: create_clinic_locations_001
Revises: add_share_with_doctor_consent
Create Date: 2026-01-08 06:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_clinic_locations_001'
down_revision = 'add_share_with_doctor_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create clinic_locations table
    op.create_table(
        'clinic_locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clinics.id', ondelete='CASCADE'), nullable=False, index=True, comment='Foreign key to clinics table'),
        sa.Column('name', sa.String(255), nullable=False, comment='Branch/location name'),
        sa.Column('branch_type', sa.String(100), nullable=True, comment='Type of branch (Main Branch, Sub Branch, etc.)'),
        sa.Column('address', sa.Text(), nullable=True, comment='Full address'),
        sa.Column('building_name', sa.String(255), nullable=True, comment='Building name or number'),
        sa.Column('street_name', sa.String(255), nullable=True, comment='Street name'),
        sa.Column('pincode', sa.String(20), nullable=True, comment='Postal/ZIP code'),
        sa.Column('phone', sa.String(50), nullable=True, comment='Contact phone number'),
        sa.Column('email', sa.String(255), nullable=True, comment='Contact email'),
        sa.Column('country_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('countries.id', ondelete='SET NULL'), nullable=True, index=True, comment='Foreign key to countries table'),
        sa.Column('state_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('states.id', ondelete='SET NULL'), nullable=True, index=True, comment='Foreign key to states table'),
        sa.Column('city_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cities.id', ondelete='SET NULL'), nullable=True, index=True, comment='Foreign key to cities table'),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True, comment='Geographic latitude'),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True, comment='Geographic longitude'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false', comment='Is this the primary location?'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes
    op.create_index('clinic_locations_clinic_id_index', 'clinic_locations', ['clinic_id'])
    op.create_index('clinic_locations_country_id_index', 'clinic_locations', ['country_id'])
    op.create_index('clinic_locations_state_id_index', 'clinic_locations', ['state_id'])
    op.create_index('clinic_locations_city_id_index', 'clinic_locations', ['city_id'])
    op.create_index('clinic_locations_is_primary_index', 'clinic_locations', ['is_primary'])
    op.create_index('clinic_locations_created_at_index', 'clinic_locations', ['created_at'])
    op.create_index('clinic_locations_deleted_at_index', 'clinic_locations', ['deleted_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('clinic_locations_deleted_at_index', table_name='clinic_locations')
    op.drop_index('clinic_locations_created_at_index', table_name='clinic_locations')
    op.drop_index('clinic_locations_is_primary_index', table_name='clinic_locations')
    op.drop_index('clinic_locations_city_id_index', table_name='clinic_locations')
    op.drop_index('clinic_locations_state_id_index', table_name='clinic_locations')
    op.drop_index('clinic_locations_country_id_index', table_name='clinic_locations')
    op.drop_index('clinic_locations_clinic_id_index', table_name='clinic_locations')
    
    # Drop table
    op.drop_table('clinic_locations')
