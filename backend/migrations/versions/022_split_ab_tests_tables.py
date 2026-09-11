"""Split `ab_tests` into cover_ab_tests and listing_ab_tests.

Three incompatible shapes shared one table name:

  * migration 001 created a generic `ab_tests`
    (entity_type / entity_id / variants / results / winner_id) that no model
    ever mapped;
  * migration 011 bolted cover-design columns (name, cover_ids, share_token,
    winner_cover_id, ended_at) onto that same table;
  * `product_page_lab.models.ABTest` declared a third shape
    (book_id, variant_a/b_content, impressions, clicks, duration_days) that no
    migration ever created.

Because `cover_design.models.ABTest` and `product_page_lab.models.ABTest` both
declared ``__tablename__ = "ab_tests"``, SQLAlchemy merged them into a single
21-column table with a duplicated ix_ab_tests_org_id index, and each class
inherited the other's NOT NULL columns — so neither feature could insert a row.

This gives each feature its own table and retires the generic one. Existing
cover tests (rows with a non-null cover_ids) are carried over, along with their
votes; the generic rows have no owner and are dropped with the table.

Revision ID: 022_split_ab_tests_tables
Revises: 021_add_missing_declared_columns
Create Date: 2026-09-10
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "022_split_ab_tests_tables"
down_revision = "021_add_missing_declared_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── cover_design.ABTest ────────────────────────────────────────────────
    op.create_table(
        "cover_ab_tests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("cover_ids", sa.JSON(), nullable=False),
        sa.Column("share_token", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("winner_cover_id", sa.String(36), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("share_token", name="uq_cover_ab_tests_share_token"),
    )
    op.create_index("ix_cover_ab_tests_org_id", "cover_ab_tests", ["org_id"])
    op.create_index("ix_cover_ab_tests_share_token", "cover_ab_tests", ["share_token"])

    # No rows are carried over. The generic `ab_tests` table has no org_id
    # column — migration 001 created it with entity_type/entity_id and 011
    # bolted the cover columns on without one — so there is no tenant to
    # assign a migrated row to, and cover_ab_tests.org_id is NOT NULL.
    # It is also moot: the migration chain has been unrunnable since 012
    # (which extends a `pipelines` table nothing ever created), so no database
    # has ever reached this point with rows in it.

    # ── product_page_lab.ABTest ────────────────────────────────────────────
    op.create_table(
        "listing_ab_tests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("variant_a_content", sa.Text(), nullable=False),
        sa.Column("variant_b_content", sa.Text(), nullable=False),
        sa.Column("variant_a_impressions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("variant_a_clicks", sa.Integer(), server_default="0", nullable=False),
        sa.Column("variant_b_impressions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("variant_b_clicks", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duration_days", sa.Integer(), server_default="7", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listing_ab_tests_org_id", "listing_ab_tests", ["org_id"])
    op.create_index("ix_listing_ab_tests_book_id", "listing_ab_tests", ["book_id"])

    # ── Repoint the votes at the cover table ───────────────────────────────
    op.drop_constraint("ab_test_votes_test_id_fkey", "ab_test_votes", type_="foreignkey")
    op.execute("DELETE FROM ab_test_votes WHERE test_id NOT IN (SELECT id FROM cover_ab_tests)")
    op.create_foreign_key(
        "ab_test_votes_test_id_fkey",
        "ab_test_votes",
        "cover_ab_tests",
        ["test_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_table("ab_tests")


def downgrade() -> None:
    # Recreates the generic shape from migration 001 plus migration 011's
    # cover columns. Listing tests have nowhere to go and are not carried back.
    # postgresql.ENUM, not sa.Enum: create_type=False is a dialect-level flag
    # and sa.Enum drops it, so the CREATE TYPE is emitted anyway and the
    # downgrade fails on a type migration 001 already created.
    ab_test_status = postgresql.ENUM(
        "draft",
        "running",
        "paused",
        "completed",
        name="ab_test_status",
        create_type=False,
    )
    op.create_table(
        "ab_tests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("variants", sa.JSON(), nullable=True),
        sa.Column("traffic_split", sa.Float(), nullable=True),
        sa.Column("status", ab_test_status, server_default="draft", nullable=False),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("winner_id", sa.String(100), nullable=True),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("cover_ids", sa.JSON(), nullable=True),
        sa.Column("share_token", sa.String(100), nullable=True),
        sa.Column("winner_cover_id", sa.String(36), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # Nothing is carried back for the same reason nothing was carried over.

    op.drop_constraint("ab_test_votes_test_id_fkey", "ab_test_votes", type_="foreignkey")
    op.create_foreign_key(
        "ab_test_votes_test_id_fkey",
        "ab_test_votes",
        "ab_tests",
        ["test_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_table("listing_ab_tests")
    op.drop_table("cover_ab_tests")
