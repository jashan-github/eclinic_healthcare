"""update_location_fields_to_uuids

Revision ID: update_location_fields_to_uuids_001
Revises: create_languages_table_001
Create Date: 2025-12-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_location_to_uuids'
down_revision = 'create_languages_table_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update contact_details and clinics tables to use UUID foreign keys
    instead of string fields for country, state, and city
    """
    
    # 1. Update contact_details table
    # Add new UUID columns
    op.add_column('contact_details', sa.Column('country_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('contact_details', sa.Column('state_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('contact_details', sa.Column('city_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create foreign key constraints
    op.create_foreign_key(
        'fk_contact_details_country_id',
        'contact_details', 'countries',
        ['country_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_contact_details_state_id',
        'contact_details', 'states',
        ['state_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_contact_details_city_id',
        'contact_details', 'cities',
        ['city_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create indexes for new foreign keys
    op.create_index('contact_details_country_id_index', 'contact_details', ['country_id'])
    op.create_index('contact_details_state_id_index', 'contact_details', ['state_id'])
    op.create_index('contact_details_city_id_index', 'contact_details', ['city_id'])
    
    # Drop old string columns (after migration, data should be migrated separately if needed)
    # Note: In production, you may want to migrate existing data first before dropping columns
    op.drop_column('contact_details', 'city')
    op.drop_column('contact_details', 'state')
    op.drop_column('contact_details', 'country')
    
    # 2. Update clinics table
    # Add new UUID column
    op.add_column('clinics', sa.Column('country_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_clinics_country_id',
        'clinics', 'countries',
        ['country_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for new foreign key
    op.create_index('clinics_country_id_index', 'clinics', ['country_id'])
    
    # Drop old string column
    op.drop_column('clinics', 'country')


def downgrade() -> None:
    """
    Revert changes: restore string columns and drop UUID foreign keys
    """
    
    # 1. Revert contact_details table
    # Add back string columns
    op.add_column('contact_details', sa.Column('country', sa.String(100), nullable=True))
    op.add_column('contact_details', sa.Column('state', sa.String(100), nullable=True))
    op.add_column('contact_details', sa.Column('city', sa.String(100), nullable=True))
    
    # Drop foreign key constraints
    op.drop_constraint('fk_contact_details_city_id', 'contact_details', type_='foreignkey')
    op.drop_constraint('fk_contact_details_state_id', 'contact_details', type_='foreignkey')
    op.drop_constraint('fk_contact_details_country_id', 'contact_details', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('contact_details_city_id_index', table_name='contact_details')
    op.drop_index('contact_details_state_id_index', table_name='contact_details')
    op.drop_index('contact_details_country_id_index', table_name='contact_details')
    
    # Drop UUID columns
    op.drop_column('contact_details', 'city_id')
    op.drop_column('contact_details', 'state_id')
    op.drop_column('contact_details', 'country_id')
    
    # 2. Revert clinics table
    # Add back string column
    op.add_column('clinics', sa.Column('country', sa.String(255), nullable=True))
    
    # Drop foreign key constraint
    op.drop_constraint('fk_clinics_country_id', 'clinics', type_='foreignkey')
    
    # Drop index
    op.drop_index('clinics_country_id_index', table_name='clinics')
    
    # Drop UUID column
    op.drop_column('clinics', 'country_id')

