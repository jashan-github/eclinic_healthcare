"""add unique constraint for active chat rooms

Revision ID: 202601091049
Revises: 20250101000001
Create Date: 2026-01-09 10:49:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '202601091049'
down_revision: Union[str, None] = '20250101000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, handle duplicates: keep the most recent one, close others
    op.execute("""
        WITH duplicates AS (
            SELECT id, 
                   ROW_NUMBER() OVER (
                       PARTITION BY doctor_id, patient_id 
                       ORDER BY created_at DESC, id DESC
                   ) as rn
            FROM chat_rooms
            WHERE status = 'active'
        )
        UPDATE chat_rooms
        SET status = 'closed'
        WHERE id IN (
            SELECT id FROM duplicates WHERE rn > 1
        )
    """)
    
    # Create unique index: one active chat room per doctor-patient pair
    op.execute("""
        CREATE UNIQUE INDEX chat_rooms_unique_active_doctor_patient 
        ON chat_rooms (doctor_id, patient_id) 
        WHERE status = 'active'
    """)


def downgrade() -> None:
    op.drop_index('chat_rooms_unique_active_doctor_patient', table_name='chat_rooms')
