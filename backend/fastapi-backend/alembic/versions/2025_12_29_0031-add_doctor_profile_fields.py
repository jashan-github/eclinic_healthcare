"""add_doctor_profile_fields

Revision ID: add_doctor_profile_fields_001
Revises: create_medical_services_001
Create Date: 2025-12-29 00:31:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_doctor_profile_fields_001'
down_revision = 'create_medical_services_001'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns already exist before adding (idempotent)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user_profiles')]
    
    # Add doctor-specific fields to user_profiles table (only if they don't exist)
    if 'education' not in columns:
        op.add_column('user_profiles', sa.Column('education', sa.String(length=255), nullable=True, comment='Education details (e.g., MBBS, MD)'))
    
    if 'years_of_experience' not in columns:
        op.add_column('user_profiles', sa.Column('years_of_experience', sa.Integer(), nullable=True, comment='Years of professional experience'))
    
    # Check if tables already exist (idempotent)
    existing_tables = inspector.get_table_names()
    
    # Create user_languages junction table (many-to-many: users <-> languages)
    if 'user_languages' not in existing_tables:
        op.create_table(
            'user_languages',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('language_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'language_id'),
        sa.UniqueConstraint('user_id', 'language_id', name='user_languages_user_id_language_id_unique')
        )
        op.create_index('user_languages_user_id_index', 'user_languages', ['user_id'])
        op.create_index('user_languages_language_id_index', 'user_languages', ['language_id'])
    
    # Create user_medical_services junction table (many-to-many: users <-> medical_services)
    if 'user_medical_services' not in existing_tables:
        op.create_table(
            'user_medical_services',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('medical_service_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['medical_service_id'], ['medical_services.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'medical_service_id'),
        sa.UniqueConstraint('user_id', 'medical_service_id', name='user_medical_services_user_id_medical_service_id_unique')
        )
        op.create_index('user_medical_services_user_id_index', 'user_medical_services', ['user_id'])
        op.create_index('user_medical_services_medical_service_id_index', 'user_medical_services', ['medical_service_id'])


def downgrade():
    # Drop junction tables
    op.drop_index('user_medical_services_medical_service_id_index', table_name='user_medical_services')
    op.drop_index('user_medical_services_user_id_index', table_name='user_medical_services')
    op.drop_table('user_medical_services')
    
    op.drop_index('user_languages_language_id_index', table_name='user_languages')
    op.drop_index('user_languages_user_id_index', table_name='user_languages')
    op.drop_table('user_languages')
    
    # Remove doctor-specific fields from user_profiles
    op.drop_column('user_profiles', 'years_of_experience')
    op.drop_column('user_profiles', 'education')

