"""create_fcm_tokens_table

Create fcm_tokens table for Firebase Cloud Messaging registration tokens.

Revision ID: fcm_tokens_001
Revises: push_subscriptions_001
Create Date: 2026-01-27 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "fcm_tokens_001"
down_revision = "push_subscriptions_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "fcm_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("token", sa.String(512), nullable=False),
        sa.Column("platform", sa.String(32), nullable=True),
        sa.Column("device_label", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="fcm_tokens_pkey"),
        sa.UniqueConstraint("token", name="fcm_tokens_token_unique"),
    )
    op.create_index(
        "fcm_tokens_user_id_index",
        "fcm_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "fcm_tokens_token_index",
        "fcm_tokens",
        ["token"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("fcm_tokens_token_index", table_name="fcm_tokens")
    op.drop_index("fcm_tokens_user_id_index", table_name="fcm_tokens")
    op.drop_table("fcm_tokens")
