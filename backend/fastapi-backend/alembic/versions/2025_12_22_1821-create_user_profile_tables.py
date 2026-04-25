"""create_user_profile_tables

Revision ID: create_user_profile_001
Revises: create_auth_tables_001
Create Date: 2025-12-22 18:21:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_user_profile_001'
down_revision = 'create_auth_tables_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure uuid-ossp extension exists (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('first_name', sa.String(255), nullable=True),
        sa.Column('last_name', sa.String(255), nullable=True),
        sa.Column('middle_name', sa.String(255), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar', sa.String(255), nullable=True),
        sa.Column('address_line_1', sa.String(255), nullable=True),
        sa.Column('address_line_2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('occupation', sa.String(255), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', name='user_profiles_user_id_unique'),
    )
    
    # Create indexes for user_profiles table
    op.create_index('user_profiles_user_id_index', 'user_profiles', ['user_id'])
    op.create_index('user_profiles_created_at_index', 'user_profiles', ['created_at'])
    op.create_index('user_profiles_deleted_at_index', 'user_profiles', ['deleted_at'])
    
    # Create contact_details table
    op.create_table(
        'contact_details',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_type', sa.String(50), nullable=False, server_default='primary'),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('phone_secondary', sa.String(20), nullable=True),
        sa.Column('fax', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('address_line_1', sa.String(255), nullable=True),
        sa.Column('address_line_2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('emergency_contact_name', sa.String(255), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for contact_details table
    op.create_index('contact_details_user_id_index', 'contact_details', ['user_id'])
    op.create_index('contact_details_contact_type_index', 'contact_details', ['contact_type'])
    op.create_index('contact_details_is_primary_index', 'contact_details', ['is_primary'])
    op.create_index('contact_details_email_index', 'contact_details', ['email'])
    op.create_index('contact_details_created_at_index', 'contact_details', ['created_at'])
    op.create_index('contact_details_deleted_at_index', 'contact_details', ['deleted_at'])


def downgrade() -> None:
    # Drop contact_details table
    op.drop_index('contact_details_deleted_at_index', table_name='contact_details')
    op.drop_index('contact_details_created_at_index', table_name='contact_details')
    op.drop_index('contact_details_email_index', table_name='contact_details')
    op.drop_index('contact_details_is_primary_index', table_name='contact_details')
    op.drop_index('contact_details_contact_type_index', table_name='contact_details')
    op.drop_index('contact_details_user_id_index', table_name='contact_details')
    op.drop_table('contact_details')
    
    # Drop user_profiles table
    op.drop_index('user_profiles_deleted_at_index', table_name='user_profiles')
    op.drop_index('user_profiles_created_at_index', table_name='user_profiles')
    op.drop_index('user_profiles_user_id_index', table_name='user_profiles')
    op.drop_table('user_profiles')

