"""Add series read-through analytics: series_id/series_order on books + series_sales_data.

Revision ID: 024_series_read_through
Revises: 020_add_activity_log
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "024_series_read_through"
down_revision = "020_add_activity_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend books with series_id (FK) and series_order
    with op.batch_alter_table("books") as batch:
        batch.add_column(
            sa.Column(
                "series_id",
                UUID(as_uuid=True),
                sa.ForeignKey("series.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch.add_column(sa.Column("series_order", sa.Integer(), nullable=True))

    op.create_index("ix_books_series_id", "books", ["series_id"])
    op.create_index(
        "ix_books_series_order", "books", ["series_id", "series_order"]
    )

    # Series sales data (per-book / per-period rollup used for read-through)
    op.create_table(
        "series_sales_data",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "series_id",
            UUID(as_uuid=True),
            sa.ForeignKey("series.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("series_order", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("unique_buyers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("units_sold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "revenue",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "avg_days_from_prev",
            sa.Numeric(6, 2),
            nullable=True,
        ),
        sa.Column("bsr_avg", sa.Integer(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("rating_avg", sa.Numeric(3, 2), nullable=True),
        sa.Column(
            "metadata",
            JSONB(),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_series_sales_series",
        "series_sales_data",
        ["series_id", "series_order"],
    )
    op.create_index(
        "idx_series_sales_org_period",
        "series_sales_data",
        ["org_id", "period_start", "period_end"],
    )
    op.create_index(
        "idx_series_sales_book",
        "series_sales_data",
        ["book_id", "period_start"],
    )


def downgrade() -> None:
    op.drop_index("idx_series_sales_book", table_name="series_sales_data")
    op.drop_index("idx_series_sales_org_period", table_name="series_sales_data")
    op.drop_index("idx_series_sales_series", table_name="series_sales_data")
    op.drop_table("series_sales_data")

    op.drop_index("ix_books_series_order", table_name="books")
    op.drop_index("ix_books_series_id", table_name="books")
    with op.batch_alter_table("books") as batch:
        batch.drop_column("series_order")
        batch.drop_column("series_id")
