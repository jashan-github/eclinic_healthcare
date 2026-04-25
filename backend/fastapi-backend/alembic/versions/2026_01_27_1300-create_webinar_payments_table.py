"""create_webinar_payments_table

Create webinar_payments table for tracking Sentoo payment transactions and webhook events for webinar registrations.
Supports idempotent payment processing.

Revision ID: create_webinar_payments_001
Revises: add_hipaa_form_filled_001
Create Date: 2026-01-27 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_webinar_payments_001'
down_revision = 'add_hipaa_form_filled_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create webinar_payments table.
    
    Tracks:
    - Payment intent creation for webinar registrations
    - Sentoo webhook events
    - Payment status
    - Idempotency keys
    - One payment per user per webinar (unique constraint)
    """
    op.create_table(
        'webinar_payments',
        # Primary key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
            comment='Primary key (UUID)'
        ),
        # Foreign keys
        sa.Column(
            'webinar_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
            comment='Webinar ID (from webinar service)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='RESTRICT'),
            nullable=False,
            index=True,
            comment='User ID who registered/paid for the webinar'
        ),
        # Sentoo payment details
        sa.Column(
            'sentoo_payment_id',
            sa.String(255),
            nullable=True,
            unique=True,
            index=True,
            comment='Sentoo Payment ID'
        ),
        sa.Column(
            'payment_url',
            sa.String(500),
            nullable=True,
            comment='Sentoo payment URL for customer'
        ),
        # Payment amount (locked from webinar price)
        sa.Column(
            'amount',
            sa.Numeric(10, 2),
            nullable=False,
            comment='Payment amount (locked from webinar price)'
        ),
        sa.Column(
            'currency',
            sa.String(3),
            nullable=False,
            server_default='INR',
            comment='Currency code (ISO 4217)'
        ),
        # Payment status
        sa.Column(
            'status',
            sa.String(50),
            nullable=False,
            server_default='PENDING',
            index=True,
            comment='Payment status: PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED'
        ),
        # Idempotency
        sa.Column(
            'idempotency_key',
            sa.String(255),
            nullable=True,
            unique=True,
            index=True,
            comment='Idempotency key for webhook processing'
        ),
        # Webhook tracking
        sa.Column(
            'sentoo_webhook_id',
            sa.String(255),
            nullable=True,
            index=True,
            comment='Sentoo webhook event ID (for idempotency)'
        ),
        sa.Column(
            'webhook_received_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Webhook event received timestamp'
        ),
        # Error tracking
        sa.Column(
            'error_message',
            sa.Text(),
            nullable=True,
            comment='Error message if payment failed'
        ),
        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
            comment='Payment creation timestamp (UTC)'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment='Payment update timestamp (UTC)'
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint('id', name='webinar_payments_pkey'),
        # Check constraints
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='webinar_payments_status_check'
        ),
        sa.CheckConstraint(
            'amount > 0',
            name='webinar_payments_amount_check'
        ),
        sa.CheckConstraint(
            'LENGTH(currency) = 3',
            name='webinar_payments_currency_check'
        ),
        # Unique constraint: one payment per user per webinar
        sa.UniqueConstraint('webinar_id', 'user_id', name='webinar_payments_webinar_user_unique'),
        comment='Webinar payment tracking for Sentoo integration'
    )
    
    # Create indexes for performance
    op.create_index(
        'ix_webinar_payments_webinar_status',
        'webinar_payments',
        ['webinar_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_webinar_payments_user_status',
        'webinar_payments',
        ['user_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_webinar_payments_sentoo_id',
        'webinar_payments',
        ['sentoo_payment_id'],
        unique=True,
        postgresql_where=sa.text("sentoo_payment_id IS NOT NULL")
    )


def downgrade() -> None:
    """
    Drop webinar_payments table and indexes.
    """
    # Drop indexes first
    op.drop_index('ix_webinar_payments_sentoo_id', table_name='webinar_payments')
    op.drop_index('ix_webinar_payments_user_status', table_name='webinar_payments')
    op.drop_index('ix_webinar_payments_webinar_status', table_name='webinar_payments')
    
    # Drop table
    op.drop_table('webinar_payments')
