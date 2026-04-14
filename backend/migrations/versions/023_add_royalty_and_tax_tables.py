"""Add royalty_entries, tax_expenses, quarterly_tax_payments tables.

Revision ID: 023_add_royalty_and_tax_tables
Revises: 020_add_activity_log
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "023_add_royalty_and_tax_tables"
# NOTE: Stream 1 owns 021 and 022 (roles/invitations/pen_names). At merge
# time the chain will be relinked to point at 022_add_roles_and_invitations.
down_revision = "020_add_activity_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- royalty_entries --------------------------------------------------
    op.create_table(
        "royalty_entries",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        # FK to pen_names added post-merge (Stream 1 owns pen_names table).
        sa.Column("pen_name_id", UUID(as_uuid=True), nullable=True),
        sa.Column("book_id", UUID(as_uuid=True), nullable=True),
        sa.Column("distributor", sa.String(length=50), nullable=False),
        sa.Column("royalty_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("units_sold", sa.Integer(), nullable=True),
        sa.Column("kenp_pages", sa.Integer(), nullable=True),
        sa.Column("royalty_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("period_month", sa.Integer(), nullable=True),
        sa.Column("period_year", sa.Integer(), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True, server_default="import"),
        sa.Column("import_batch_id", UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_royalties_org",
        "royalty_entries",
        ["org_id", "period_year", "period_month"],
    )
    op.create_index(
        "idx_royalties_distributor",
        "royalty_entries",
        ["org_id", "distributor"],
    )
    op.create_index(
        "idx_royalties_book",
        "royalty_entries",
        ["book_id"],
    )

    # --- tax_expenses -----------------------------------------------------
    op.create_table(
        "tax_expenses",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("expense_date", sa.Date(), nullable=True),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("receipt_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_tax_expenses_org",
        "tax_expenses",
        ["org_id", "tax_year"],
    )

    # --- quarterly_tax_payments ------------------------------------------
    op.create_table(
        "quarterly_tax_payments",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=False),
        sa.Column("estimated_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("actual_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("paid", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "org_id", "tax_year", "quarter", name="uq_quarterly_tax_org_year_quarter"
        ),
    )


def downgrade() -> None:
    op.drop_table("quarterly_tax_payments")
    op.drop_index("idx_tax_expenses_org", table_name="tax_expenses")
    op.drop_table("tax_expenses")
    op.drop_index("idx_royalties_book", table_name="royalty_entries")
    op.drop_index("idx_royalties_distributor", table_name="royalty_entries")
    op.drop_index("idx_royalties_org", table_name="royalty_entries")
    op.drop_table("royalty_entries")
