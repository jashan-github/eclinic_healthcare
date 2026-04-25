"""create_appointment_payments_table

Create appointment_payments table for tracking Stripe payment intents and webhook events.
Supports idempotent payment processing.

Revision ID: create_appointment_payments_001
Revises: create_appointment_requests_001
Create Date: 2025-12-30 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_appointment_payments_001'
down_revision = 'create_appointment_requests_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create appointment_payments table.
    
    Tracks:
    - Payment intent creation
    - Stripe webhook events
    - Payment status
    - Idempotency keys
    """
    op.create_table(
        'appointment_payments',
        # Primary key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
            comment='Primary key (UUID)'
        ),
        # Foreign key to appointment_request
        sa.Column(
            'appointment_request_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('appointment_requests.id', ondelete='RESTRICT'),
            nullable=False,
            unique=True,
            index=True,
            comment='Appointment request ID (one payment per request)'
        ),
        # Stripe payment details
        sa.Column(
            'stripe_payment_intent_id',
            sa.String(255),
            nullable=True,
            unique=True,
            index=True,
            comment='Stripe PaymentIntent ID'
        ),
        sa.Column(
            'stripe_client_secret',
            sa.String(255),
            nullable=True,
            comment='Stripe client secret (temporary, for frontend)'
        ),
        # Payment amount (locked from request)
        sa.Column(
            'amount',
            sa.Numeric(10, 2),
            nullable=False,
            comment='Payment amount (locked from request price)'
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
            'stripe_event_id',
            sa.String(255),
            nullable=True,
            index=True,
            comment='Stripe webhook event ID (for idempotency)'
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
        sa.PrimaryKeyConstraint('id', name='appointment_payments_pkey'),
        # Check constraints
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='appointment_payments_status_check'
        ),
        sa.CheckConstraint(
            'amount > 0',
            name='appointment_payments_amount_check'
        ),
        sa.CheckConstraint(
            'LENGTH(currency) = 3',
            name='appointment_payments_currency_check'
        ),
        comment='Appointment payment tracking for Stripe integration'
    )
    
    # Create indexes for performance
    op.create_index(
        'ix_appointment_payments_request_status',
        'appointment_payments',
        ['appointment_request_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_appointment_payments_stripe_intent',
        'appointment_payments',
        ['stripe_payment_intent_id'],
        unique=True,
        postgresql_where=sa.text("stripe_payment_intent_id IS NOT NULL")
    )


def downgrade() -> None:
    """
    Drop appointment_payments table and indexes.
    """
    # Drop indexes first
    op.drop_index('ix_appointment_payments_stripe_intent', table_name='appointment_payments')
    op.drop_index('ix_appointment_payments_request_status', table_name='appointment_payments')
    
    # Drop table
    op.drop_table('appointment_payments')
