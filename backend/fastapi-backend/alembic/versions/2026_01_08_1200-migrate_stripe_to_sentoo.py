"""migrate_stripe_to_sentoo

Revision ID: migrate_stripe_to_sentoo_001
Revises: create_patient_documents_001
Create Date: 2026-01-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'migrate_stripe_to_sentoo_001'
down_revision = 'create_patient_documents_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename Stripe-specific columns to generic payment gateway columns
    op.alter_column('appointment_payments', 'stripe_payment_intent_id',
                    new_column_name='sentoo_payment_id',
                    existing_type=sa.String(255),
                    existing_nullable=True)
    
    op.alter_column('appointment_payments', 'stripe_client_secret',
                    new_column_name='payment_url',
                    existing_type=sa.String(255),
                    existing_nullable=True)
    
    op.alter_column('appointment_payments', 'stripe_event_id',
                    new_column_name='sentoo_webhook_id',
                    existing_type=sa.String(255),
                    existing_nullable=True)
    
    # Update column comments
    op.execute("COMMENT ON COLUMN appointment_payments.sentoo_payment_id IS 'Sentoo Payment ID'")
    op.execute("COMMENT ON COLUMN appointment_payments.payment_url IS 'Sentoo payment URL for customer'")
    op.execute("COMMENT ON COLUMN appointment_payments.sentoo_webhook_id IS 'Sentoo webhook event ID (for idempotency)'")


def downgrade() -> None:
    # Revert column names back to Stripe naming
    op.alter_column('appointment_payments', 'sentoo_payment_id',
                    new_column_name='stripe_payment_intent_id',
                    existing_type=sa.String(255),
                    existing_nullable=True)
    
    op.alter_column('appointment_payments', 'payment_url',
                    new_column_name='stripe_client_secret',
                    existing_type=sa.String(255),
                    existing_nullable=True)
    
    op.alter_column('appointment_payments', 'sentoo_webhook_id',
                    new_column_name='stripe_event_id',
                    existing_type=sa.String(255),
                    existing_nullable=True)
    
    # Revert comments
    op.execute("COMMENT ON COLUMN appointment_payments.stripe_payment_intent_id IS 'Stripe PaymentIntent ID'")
    op.execute("COMMENT ON COLUMN appointment_payments.stripe_client_secret IS 'Stripe client secret (temporary, for frontend)'")
    op.execute("COMMENT ON COLUMN appointment_payments.stripe_event_id IS 'Stripe webhook event ID (for idempotency)'")
