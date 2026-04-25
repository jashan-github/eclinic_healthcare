"""create_languages_table

Revision ID: create_languages_table_001
Revises: create_location_tables_001
Create Date: 2025-12-26 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_languages_table_001'
down_revision = 'create_location_tables_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create languages table
    op.create_table(
        'languages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('language_name', sa.String(255), nullable=True, comment='Language name (e.g., English, Spanish, French)'),
        sa.Column('language_code', sa.String(255), nullable=True, comment='Language code (e.g., en, es, fr)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    
    # Create indexes for languages
    op.create_index('languages_language_code_index', 'languages', ['language_code'])
    op.create_index('languages_language_name_index', 'languages', ['language_name'])
    op.create_index('ix_languages_id', 'languages', ['id'])


def downgrade() -> None:
    # Drop languages table
    op.drop_table('languages')

