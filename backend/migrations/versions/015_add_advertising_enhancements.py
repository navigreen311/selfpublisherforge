"""Add advertising enhancements: search terms, daily metrics, and campaign columns."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ad_search_terms
    op.create_table(
        "ad_search_terms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("search_term", sa.String(500), nullable=False),
        sa.Column("impressions", sa.Integer(), default=0),
        sa.Column("clicks", sa.Integer(), default=0),
        sa.Column("spend", sa.Numeric(10, 2), server_default="0"),
        sa.Column("sales", sa.Numeric(10, 2), server_default="0"),
        sa.Column("orders", sa.Integer(), default=0),
        sa.Column("action_taken", sa.String(50), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_ad_search_terms_campaign", "ad_search_terms", ["campaign_id"])

    # ad_daily_metrics
    op.create_table(
        "ad_daily_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("spend", sa.Numeric(10, 2), server_default="0"),
        sa.Column("sales", sa.Numeric(10, 2), server_default="0"),
        sa.Column("impressions", sa.Integer(), default=0),
        sa.Column("clicks", sa.Integer(), default=0),
        sa.Column("orders", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("campaign_id", "date", name="uq_ad_daily_metrics_campaign_date"),
    )
    op.create_index("idx_ad_daily_metrics_campaign_date", "ad_daily_metrics", ["campaign_id", "date"])

    # Add columns to campaigns table IF NOT EXISTS
    columns_to_add = [
        ("targeting_type", sa.String(50), True),
        ("match_types", postgresql.JSON(), True),
        ("bidding_strategy", sa.String(50), True),
        ("default_bid", sa.Float(), True),
        ("schedule_start", sa.Date(), True),
        ("schedule_end", sa.Date(), True),
        ("ad_type", sa.String(50), True),
    ]
    float_columns_with_default = [
        ("total_spend", sa.Float(), "0"),
        ("total_sales", sa.Float(), "0"),
    ]
    int_columns_with_default = [
        ("total_impressions", sa.Integer(), "0"),
        ("total_clicks", sa.Integer(), "0"),
        ("total_orders", sa.Integer(), "0"),
    ]

    for col_name, col_type, nullable in columns_to_add:
        try:
            op.add_column("campaigns", sa.Column(col_name, col_type, nullable=nullable))
        except Exception:
            pass

    for col_name, col_type, default in float_columns_with_default:
        try:
            op.add_column("campaigns", sa.Column(col_name, col_type, server_default=default, nullable=True))
        except Exception:
            pass

    for col_name, col_type, default in int_columns_with_default:
        try:
            op.add_column("campaigns", sa.Column(col_name, col_type, server_default=default, nullable=True))
        except Exception:
            pass


def downgrade() -> None:
    # Remove columns from campaigns
    for col_name in [
        "targeting_type", "match_types", "bidding_strategy", "default_bid",
        "schedule_start", "schedule_end", "ad_type",
        "total_spend", "total_sales", "total_impressions", "total_clicks", "total_orders",
    ]:
        try:
            op.drop_column("campaigns", col_name)
        except Exception:
            pass

    op.drop_index("idx_ad_daily_metrics_campaign_date")
    op.drop_table("ad_daily_metrics")
    op.drop_index("idx_ad_search_terms_campaign")
    op.drop_table("ad_search_terms")
