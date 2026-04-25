"""create_push_subscriptions_table

Create push_subscriptions table for browser Web Push subscriptions.

Revision ID: push_subscriptions_001
Revises: webinar_payments_amount_001
Create Date: 2026-01-27 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "push_subscriptions_001"
down_revision = "webinar_payments_amount_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "push_subscriptions",
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
        sa.Column("endpoint", sa.String(2048), nullable=False),
        sa.Column("p256dh", sa.String(255), nullable=False),
        sa.Column("auth", sa.String(255), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="push_subscriptions_pkey"),
        sa.UniqueConstraint("endpoint", name="push_subscriptions_endpoint_unique"),
    )
    op.create_index(
        "push_subscriptions_user_id_index",
        "push_subscriptions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "push_subscriptions_endpoint_index",
        "push_subscriptions",
        ["endpoint"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("push_subscriptions_endpoint_index", table_name="push_subscriptions")
    op.drop_index("push_subscriptions_user_id_index", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")
