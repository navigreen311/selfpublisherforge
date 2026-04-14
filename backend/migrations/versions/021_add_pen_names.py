"""Extend pen_names with profile/identity fields (Final Gaps Stream 1 / Pen Name Management).

The base ``pen_names`` table exists from earlier migrations with just (name, bio,
brand_guidelines, active). This migration brings it in line with the Final Gaps
spec: display_name/amazon_url/photo_url/genres[]/is_default/book_count/user_id.

Revision ID: 021_add_pen_names
Revises: 020_add_activity_log
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

revision = "021_add_pen_names"
down_revision = "020_add_activity_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Some columns may already exist in long-running environments; guard with
    # IF NOT EXISTS via inspection to keep the migration idempotent.
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_cols = {c["name"] for c in insp.get_columns("pen_names")}

    def add(col_name: str, column: sa.Column) -> None:
        if col_name not in existing_cols:
            op.add_column("pen_names", column)

    add("display_name", sa.Column("display_name", sa.String(length=255), nullable=True))
    add("amazon_author_url", sa.Column("amazon_author_url", sa.Text(), nullable=True))
    add("photo_url", sa.Column("photo_url", sa.Text(), nullable=True))
    add(
        "genres",
        sa.Column(
            "genres",
            ARRAY(sa.String()),
            nullable=True,
            server_default=sa.text("'{}'::text[]"),
        ),
    )
    add(
        "is_default",
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    add(
        "book_count",
        sa.Column(
            "book_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    add(
        "user_id",
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Backfill display_name from legacy `name` column so we don't break the
    # existing UI reading from pen_names.
    op.execute(
        "UPDATE pen_names SET display_name = name WHERE display_name IS NULL"
    )

    # Enforce one default pen name per org.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_pen_names_one_default_per_org "
        "ON pen_names (org_id) WHERE is_default = true"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_pen_names_one_default_per_org")
    with op.batch_alter_table("pen_names") as batch:
        for col in (
            "user_id",
            "book_count",
            "is_default",
            "genres",
            "photo_url",
            "amazon_author_url",
            "display_name",
        ):
            try:
                batch.drop_column(col)
            except Exception:
                pass
