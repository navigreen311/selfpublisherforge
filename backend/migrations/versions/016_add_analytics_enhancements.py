"""Add analytics enhancements: sales_data, bsr_tracking tables and report columns."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- sales_data table ---
    op.create_table(
        "sales_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("marketplace", sa.String(10), server_default="US"),
        sa.Column("format", sa.String(50), nullable=True),
        sa.Column("units", sa.Integer(), server_default="0"),
        sa.Column("revenue", sa.Numeric(10, 2), server_default="0"),
        sa.Column("royalties", sa.Numeric(10, 2), server_default="0"),
        sa.Column("kenp_read", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "org_id", "book_id", "date", "marketplace", "format", name="uq_sales_data_org_book_date_mp_fmt"
        ),
    )

    # --- bsr_tracking table ---
    op.create_table(
        "bsr_tracking",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marketplace", sa.String(10), server_default="US"),
        sa.Column("bsr", sa.Integer(), nullable=True),
        sa.Column("category_rank", sa.Integer(), nullable=True),
        sa.Column("category_name", sa.String(255), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Add columns to reports table if not already present ---
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("reports")]

    if "period_start" not in existing_columns:
        op.add_column("reports", sa.Column("period_start", sa.Date(), nullable=True))
    if "period_end" not in existing_columns:
        op.add_column("reports", sa.Column("period_end", sa.Date(), nullable=True))
    if "book_ids" not in existing_columns:
        op.add_column("reports", sa.Column("book_ids", postgresql.JSON(), nullable=True))
    if "sections" not in existing_columns:
        op.add_column("reports", sa.Column("sections", postgresql.JSON(), nullable=True))

    # --- Indexes ---
    op.create_index("idx_sales_data_org_date", "sales_data", ["org_id", "date"])
    op.create_index("idx_sales_data_book", "sales_data", ["book_id"])
    op.create_index("idx_bsr_tracking_book", "bsr_tracking", ["book_id"])


def downgrade() -> None:
    op.drop_index("idx_bsr_tracking_book", table_name="bsr_tracking")
    op.drop_index("idx_sales_data_book", table_name="sales_data")
    op.drop_index("idx_sales_data_org_date", table_name="sales_data")

    # Remove added columns from reports (safe to always try)
    op.drop_column("reports", "sections")
    op.drop_column("reports", "book_ids")
    op.drop_column("reports", "period_end")
    op.drop_column("reports", "period_start")

    op.drop_table("bsr_tracking")
    op.drop_table("sales_data")
