"""create_service_commissions_table

Create service_commissions table for admin-defined commission per service (rate 1-100, status ACTIVE/INACTIVE).

Revision ID: service_commissions_001
Revises: role_feature_permissions_001
Create Date: 2026-01-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "service_commissions_001"
down_revision = "role_feature_permissions_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "service_commissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "service_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("rate", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="ACTIVE",
            index=True,
        ),
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
        sa.PrimaryKeyConstraint("id", name="service_commissions_pkey"),
        sa.UniqueConstraint("service_id", name="service_commissions_service_id_unique"),
        sa.CheckConstraint(
            "rate >= 1 AND rate <= 100",
            name="service_commissions_rate_range_check",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="service_commissions_status_check",
        ),
    )
    op.create_index(
        "service_commissions_service_id_index",
        "service_commissions",
        ["service_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "service_commissions_service_id_index",
        table_name="service_commissions",
    )
    op.drop_table("service_commissions")
