"""add_medical_fields_to_user_profiles

Revision ID: add_medical_fields_001
Revises: update_location_to_uuids
Create Date: 2025-12-26 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_medical_fields_001'
down_revision = 'update_location_to_uuids'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns already exist before adding (idempotent)
    # This migration may have been partially applied or columns added by merge_heads_001
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user_profiles')]
    
    # Add medical/demographic fields to user_profiles table (only if they don't exist)
    if 'blood_type' not in columns:
        op.add_column('user_profiles', sa.Column('blood_type', sa.String(length=10), nullable=True, comment='Blood type (O+, A+, B+, AB+, O-, A-, B-, AB-)'))
    
    if 'marital_status' not in columns:
        op.add_column('user_profiles', sa.Column('marital_status', sa.String(length=50), nullable=True, comment='Marital status (Single, Married, Divorced, Widowed)'))
    
    if 'preferred_language_id' not in columns:
        op.add_column('user_profiles', sa.Column('preferred_language_id', postgresql.UUID(as_uuid=True), nullable=True))
        # Add foreign key constraint for preferred_language_id
        op.create_foreign_key(
            'fk_user_profiles_preferred_language_id',
            'user_profiles', 'languages',
            ['preferred_language_id'], ['id'],
            ondelete='SET NULL'
        )
        # Create index for preferred_language_id
        op.create_index('ix_user_profiles_preferred_language_id', 'user_profiles', ['preferred_language_id'])
    
    if 'medical_info' not in columns:
        op.add_column('user_profiles', sa.Column('medical_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Medical information (conditions, allergies, medications) as JSON'))
    
    # Add family_contact_phone to contact_details table (only if it doesn't exist)
    contact_columns = [col['name'] for col in inspector.get_columns('contact_details')]
    if 'family_contact_phone' not in contact_columns:
        op.add_column('contact_details', sa.Column('family_contact_phone', sa.String(length=20), nullable=True, comment='Family contact number'))


def downgrade():
    # Remove family_contact_phone from contact_details
    op.drop_column('contact_details', 'family_contact_phone')
    
    # Remove index and foreign key for preferred_language_id
    op.drop_index('ix_user_profiles_preferred_language_id', table_name='user_profiles')
    op.drop_constraint('fk_user_profiles_preferred_language_id', 'user_profiles', type_='foreignkey')
    
    # Remove medical/demographic fields from user_profiles
    op.drop_column('user_profiles', 'medical_info')
    op.drop_column('user_profiles', 'preferred_language_id')
    op.drop_column('user_profiles', 'marital_status')
    op.drop_column('user_profiles', 'blood_type')

