"""create_role_feature_permissions_table

Create role_feature_permissions table for admin-controlled doctor/staff tab visibility.

Revision ID: role_feature_permissions_001
Revises: fcm_tokens_001
Create Date: 2026-01-27 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "role_feature_permissions_001"
down_revision = "fcm_tokens_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "role_feature_permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("role_name", sa.String(32), nullable=False, index=True),
        sa.Column("feature_key", sa.String(64), nullable=False, index=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.PrimaryKeyConstraint("id", name="role_feature_permissions_pkey"),
        sa.UniqueConstraint(
            "role_name",
            "feature_key",
            name="role_feature_permissions_role_feature_unique",
        ),
    )
    op.create_index(
        "role_feature_permissions_role_name_index",
        "role_feature_permissions",
        ["role_name"],
        unique=False,
    )

    # Seed defaults: all features enabled for doctor and staff
    op.execute(
        """
        INSERT INTO role_feature_permissions (id, role_name, feature_key, enabled, created_at, updated_at)
        VALUES
            (uuid_generate_v4(), 'doctor', 'appointments', true, now(), now()),
            (uuid_generate_v4(), 'doctor', 'patients', true, now(), now()),
            (uuid_generate_v4(), 'doctor', 'payments', true, now(), now()),
            (uuid_generate_v4(), 'doctor', 'requests', true, now(), now()),
            (uuid_generate_v4(), 'doctor', 'webinars', true, now(), now()),
            (uuid_generate_v4(), 'doctor', 'messages', true, now(), now()),
            (uuid_generate_v4(), 'doctor', 'analytics', true, now(), now()),
            (uuid_generate_v4(), 'doctor', 'rx_templates', true, now(), now()),
            (uuid_generate_v4(), 'staff', 'patients', true, now(), now()),
            (uuid_generate_v4(), 'staff', 'payments', true, now(), now())
        ON CONFLICT (role_name, feature_key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index(
        "role_feature_permissions_role_name_index",
        table_name="role_feature_permissions",
    )
    op.drop_table("role_feature_permissions")
