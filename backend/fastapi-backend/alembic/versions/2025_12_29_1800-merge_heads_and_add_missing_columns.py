"""merge_heads_and_add_missing_columns

Revision ID: merge_heads_001
Revises: add_doctor_profile_fields_001, create_doctor_availability_001
Create Date: 2025-12-29 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'merge_heads_001'
down_revision = ('add_doctor_profile_fields_001', 'create_doctor_availability_001')  # Multiple heads to merge
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns already exist before adding (idempotent)
    # Add medical/demographic fields from add_medical_fields_001 migration
    # These columns are expected by the UserProfile model but may be missing
    
    # Check and add blood_type if missing
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user_profiles')]
    
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
    
    # Check and add doctor-specific fields if missing
    if 'education' not in columns:
        op.add_column('user_profiles', sa.Column('education', sa.String(length=255), nullable=True, comment='Education details (e.g., MBBS, MD)'))
    
    if 'years_of_experience' not in columns:
        op.add_column('user_profiles', sa.Column('years_of_experience', sa.Integer(), nullable=True, comment='Years of professional experience'))
    
    # Check and add family_contact_phone to contact_details if missing
    contact_columns = [col['name'] for col in inspector.get_columns('contact_details')]
    if 'family_contact_phone' not in contact_columns:
        op.add_column('contact_details', sa.Column('family_contact_phone', sa.String(length=20), nullable=True, comment='Family contact number'))


def downgrade():
    # Remove columns in reverse order
    # Note: This is a merge migration, so downgrade should be careful
    # Check if columns exist before dropping
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user_profiles')]
    
    if 'years_of_experience' in columns:
        op.drop_column('user_profiles', 'years_of_experience')
    
    if 'education' in columns:
        op.drop_column('user_profiles', 'education')
    
    if 'medical_info' in columns:
        op.drop_column('user_profiles', 'medical_info')
    
    if 'preferred_language_id' in columns:
        op.drop_index('ix_user_profiles_preferred_language_id', table_name='user_profiles')
        op.drop_constraint('fk_user_profiles_preferred_language_id', 'user_profiles', type_='foreignkey')
        op.drop_column('user_profiles', 'preferred_language_id')
    
    if 'marital_status' in columns:
        op.drop_column('user_profiles', 'marital_status')
    
    if 'blood_type' in columns:
        op.drop_column('user_profiles', 'blood_type')
    
    # Remove family_contact_phone from contact_details
    contact_columns = [col['name'] for col in inspector.get_columns('contact_details')]
    if 'family_contact_phone' in contact_columns:
        op.drop_column('contact_details', 'family_contact_phone')
