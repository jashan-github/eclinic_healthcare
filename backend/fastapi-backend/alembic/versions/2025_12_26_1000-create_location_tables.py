"""create_location_tables

Revision ID: create_location_tables_001
Revises: reorder_title_col
Create Date: 2025-12-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_location_tables_001'
down_revision = 'reorder_title_col'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create countries table
    op.create_table(
        'countries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('shortname', sa.String(10), nullable=False, comment='Country short name/code (e.g., US, IN, UK)'),
        sa.Column('name', sa.String(50), nullable=False, comment='Country full name'),
        sa.Column('phonecode', sa.Integer(), nullable=False, comment='International phone code'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for countries
    op.create_index('countries_shortname_index', 'countries', ['shortname'])
    op.create_index('countries_name_index', 'countries', ['name'])
    op.create_index('ix_countries_id', 'countries', ['id'])
    op.create_index('ix_countries_created_at', 'countries', ['created_at'])
    op.create_index('ix_countries_updated_at', 'countries', ['updated_at'])
    op.create_index('ix_countries_deleted_at', 'countries', ['deleted_at'])
    
    # Create states table
    op.create_table(
        'states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False, comment='State name'),
        sa.Column('icon', sa.String(255), nullable=True, comment='State icon path'),
        sa.Column('sortcode', sa.String(20), nullable=True, comment='State sort code'),
        sa.Column('country_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Foreign key to countries table'),
        sa.Column('state_id', sa.Integer(), nullable=True, comment='Legacy state ID (for backward compatibility)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create foreign key constraint for states
    op.create_foreign_key(
        'fk_states_country_id',
        'states', 'countries',
        ['country_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes for states
    op.create_index('states_country_id_index', 'states', ['country_id'])
    op.create_index('states_name_index', 'states', ['name'])
    op.create_index('ix_states_id', 'states', ['id'])
    op.create_index('ix_states_created_at', 'states', ['created_at'])
    op.create_index('ix_states_updated_at', 'states', ['updated_at'])
    op.create_index('ix_states_deleted_at', 'states', ['deleted_at'])
    
    # Create cities table
    op.create_table(
        'cities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False, comment='City name'),
        sa.Column('icon', sa.String(255), nullable=False, server_default='icons/state.png', comment='City icon path'),
        sa.Column('state_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Foreign key to states table'),
        sa.Column('city_id', sa.Integer(), nullable=True, comment='Legacy city ID (for backward compatibility)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create foreign key constraint for cities
    op.create_foreign_key(
        'fk_cities_state_id',
        'cities', 'states',
        ['state_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes for cities
    op.create_index('cities_state_id_index', 'cities', ['state_id'])
    op.create_index('cities_name_index', 'cities', ['name'])
    op.create_index('ix_cities_id', 'cities', ['id'])
    op.create_index('ix_cities_created_at', 'cities', ['created_at'])
    op.create_index('ix_cities_updated_at', 'cities', ['updated_at'])
    op.create_index('ix_cities_deleted_at', 'cities', ['deleted_at'])


def downgrade() -> None:
    # Drop cities table (cascade will handle foreign keys)
    op.drop_table('cities')
    
    # Drop states table (cascade will handle foreign keys)
    op.drop_table('states')
    
    # Drop countries table
    op.drop_table('countries')

