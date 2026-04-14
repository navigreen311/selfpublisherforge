"""Add cover design studio tables (generation jobs, editor states, AB test votes).

Revision ID: 011
Revises: 010
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "011"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── covers ──────────────────────────────────────────────────────
    op.create_table(
        "covers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("project_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("subtitle", sa.String(300), nullable=True),
        sa.Column("author_name", sa.String(200), nullable=False),
        sa.Column("genre", sa.String(50), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("prompt_used", sa.Text(), nullable=True),
        sa.Column("width_px", sa.Integer(), nullable=True),
        sa.Column("height_px", sa.Integer(), nullable=True),
        sa.Column("dpi", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("bleed_px", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("platform", sa.String(30), nullable=False, server_default="amazon-kdp"),
        sa.Column("metadata_json", JSONB(), nullable=True),
        sa.Column("parent_cover_id", UUID(as_uuid=True), sa.ForeignKey("covers.id", ondelete="SET NULL"), nullable=True),
    )

    # ── extracted_products ──────────────────────────────────────────
    op.create_table(
        "extracted_products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("asin", sa.String(10), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("subtitle", sa.String(500), nullable=True),
        sa.Column("author", sa.String(300), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("bsr", sa.Integer(), nullable=True, index=True),
        sa.Column("bsr_categories", JSONB(), nullable=True),
        sa.Column("categories", JSONB(), nullable=True),
        sa.Column("keywords", JSONB(), nullable=True),
        sa.Column("reviews_json", JSONB(), nullable=True),
        sa.Column("page_url", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("marketplace", sa.String(30), nullable=False, server_default="amazon.com"),
        sa.Column("publication_date", sa.String(50), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("dimensions", sa.String(100), nullable=True),
        sa.Column("isbn", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", JSONB(), nullable=True),
    )

    # ── knowledge_clips ─────────────────────────────────────────────
    op.create_table(
        "knowledge_clips",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("clip_type", sa.String(20), nullable=False, server_default="text"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("tags", JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ── generation_jobs ─────────────────────────────────────────────
    op.create_table(
        "generation_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("request_data", JSONB(), nullable=False),
        sa.Column("result_cover_ids", JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── cover_editor_states ─────────────────────────────────────────
    op.create_table(
        "cover_editor_states",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("cover_id", UUID(as_uuid=True), sa.ForeignKey("covers.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("state_json", JSONB(), nullable=False),
    )

    # ── ab_test_votes ───────────────────────────────────────────────
    op.create_table(
        "ab_test_votes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("test_id", UUID(as_uuid=True), sa.ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("cover_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("ip_hash", sa.String(64), nullable=False, index=True),
        sa.Column("fingerprint", sa.String(64), nullable=True, index=True),
    )

    # Add cover-specific columns to existing ab_tests table
    op.add_column("ab_tests", sa.Column("name", sa.String(200), nullable=True))
    op.add_column("ab_tests", sa.Column("cover_ids", JSONB(), nullable=True))
    op.add_column("ab_tests", sa.Column("share_token", sa.String(100), nullable=True, unique=True))
    op.add_column("ab_tests", sa.Column("winner_cover_id", sa.String(36), nullable=True))
    op.add_column("ab_tests", sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("ab_tests", "ended_at")
    op.drop_column("ab_tests", "winner_cover_id")
    op.drop_column("ab_tests", "share_token")
    op.drop_column("ab_tests", "cover_ids")
    op.drop_column("ab_tests", "name")
    op.drop_table("ab_test_votes")
    op.drop_table("cover_editor_states")
    op.drop_table("generation_jobs")
    op.drop_table("knowledge_clips")
    op.drop_table("extracted_products")
    op.drop_table("covers")
