"""Add pricing enhancements: pricing_strategies, scheduled_price_changes, price_change_history."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- pricing_strategies table ---
    op.create_table(
        "pricing_strategies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("book_ids", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- scheduled_price_changes table ---
    op.create_table(
        "scheduled_price_changes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("new_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("execute_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revert_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("revert_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- price_change_history table ---
    op.create_table(
        "price_change_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("old_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("new_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("source", sa.String(50), server_default="manual"),
        sa.Column("revenue_impact_pct", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Indexes ---
    op.create_index("idx_pricing_strategies_org", "pricing_strategies", ["org_id"])
    op.create_index("idx_scheduled_changes_execute", "scheduled_price_changes", ["execute_at"])
    op.create_index("idx_price_history_book", "price_change_history", ["book_id"])


def downgrade() -> None:
    op.drop_index("idx_price_history_book", table_name="price_change_history")
    op.drop_index("idx_scheduled_changes_execute", table_name="scheduled_price_changes")
    op.drop_index("idx_pricing_strategies_org", table_name="pricing_strategies")
    op.drop_table("price_change_history")
    op.drop_table("scheduled_price_changes")
    op.drop_table("pricing_strategies")
