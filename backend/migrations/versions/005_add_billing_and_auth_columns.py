"""Add Stripe billing columns to organizations table.

The billing service reads/writes stripe_customer_id,
stripe_subscription_id, current_period_start, current_period_end,
and cancel_at_period_end via raw SQL on the organizations table.
These columns were missing from the ORM model and the database schema.

Revision ID: 005_add_billing_and_auth_columns
Revises: 004_fix_constraints
Create Date: 2026-02-10
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "005_add_billing_and_auth_columns"
down_revision: str | None = "004_fix_constraints"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("organizations", "cancel_at_period_end")
    op.drop_column("organizations", "current_period_end")
    op.drop_column("organizations", "current_period_start")
    op.drop_column("organizations", "stripe_subscription_id")
    op.drop_column("organizations", "stripe_customer_id")
