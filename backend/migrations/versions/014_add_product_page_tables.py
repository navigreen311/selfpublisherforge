"""Add product page analysis, blurb, keyword, and A+ tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # listing_analyses
    op.create_table(
        "listing_analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("asin", sa.String(20), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("scores", JSONB(), server_default="{}", nullable=True),
        sa.Column("findings", JSONB(), server_default="{}", nullable=True),
        sa.Column("suggestions", JSONB(), server_default="{}", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_listing_analyses_asin", "listing_analyses", ["asin"])

    # generated_blurbs
    op.create_table(
        "generated_blurbs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("style", sa.String(50), nullable=True),
        sa.Column("html_content", sa.Text(), nullable=True),
        sa.Column("plain_content", sa.Text(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("selling_points", sa.Text(), nullable=True),
        sa.Column("target_reader", sa.Text(), nullable=True),
        sa.Column("tone", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # keyword_analyses
    op.create_table(
        "keyword_analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("current_keywords", ARRAY(sa.Text()), nullable=True),
        sa.Column("recommended", JSONB(), nullable=True),
        sa.Column("optimal_seven", ARRAY(sa.Text()), nullable=True),
        sa.Column("genre", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # aplus_plans
    op.create_table(
        "aplus_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("modules", JSONB(), server_default="[]", nullable=True),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("aplus_plans")
    op.drop_table("keyword_analyses")
    op.drop_table("generated_blurbs")
    op.drop_index("idx_listing_analyses_asin")
    op.drop_table("listing_analyses")
