"""Extend pen_names with self-publisher fields and add pen_name_id to books.

Adds the author-identity fields required by the Pen Name Management System:
display_name, amazon_author_url, photo_url, genres[], is_default, book_count,
user_id. Also adds a nullable pen_name_id FK on the books table so each book
record can be attributed to a specific pen name.

Revision ID: 021_pen_names
Revises: 020_add_activity_log
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

revision = "021_pen_names"
down_revision = "020_add_activity_log"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    try:
        cols = {c["name"] for c in insp.get_columns(table)}
    except Exception:  # noqa: BLE001
        return False
    return column in cols


def upgrade() -> None:
    bind = op.get_bind()

    # --- pen_names extensions -------------------------------------------------
    with op.batch_alter_table("pen_names") as batch:
        if not _has_column(bind, "pen_names", "display_name"):
            batch.add_column(sa.Column("display_name", sa.String(length=255), nullable=True))
        if not _has_column(bind, "pen_names", "amazon_author_url"):
            batch.add_column(sa.Column("amazon_author_url", sa.Text(), nullable=True))
        if not _has_column(bind, "pen_names", "photo_url"):
            batch.add_column(sa.Column("photo_url", sa.Text(), nullable=True))
        if not _has_column(bind, "pen_names", "genres"):
            batch.add_column(
                sa.Column(
                    "genres",
                    ARRAY(sa.String()),
                    nullable=True,
                    server_default=sa.text("'{}'::varchar[]"),
                )
            )
        if not _has_column(bind, "pen_names", "is_default"):
            batch.add_column(
                sa.Column(
                    "is_default",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text("false"),
                )
            )
        if not _has_column(bind, "pen_names", "book_count"):
            batch.add_column(
                sa.Column(
                    "book_count",
                    sa.Integer(),
                    nullable=False,
                    server_default=sa.text("0"),
                )
            )
        if not _has_column(bind, "pen_names", "user_id"):
            batch.add_column(sa.Column("user_id", UUID(as_uuid=True), nullable=True))

    # Backfill display_name from name so the new column is populated even though
    # it stays nullable for backwards compat.
    op.execute(
        "UPDATE pen_names SET display_name = name "
        "WHERE display_name IS NULL AND name IS NOT NULL"
    )

    op.create_index(
        "ix_pen_names_user_id",
        "pen_names",
        ["user_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_pen_names_is_default",
        "pen_names",
        ["org_id", "is_default"],
        if_not_exists=True,
    )

    # --- books.pen_name_id ----------------------------------------------------
    if not _has_column(bind, "books", "pen_name_id"):
        with op.batch_alter_table("books") as batch:
            batch.add_column(
                sa.Column(
                    "pen_name_id",
                    UUID(as_uuid=True),
                    sa.ForeignKey("pen_names.id", ondelete="SET NULL"),
                    nullable=True,
                )
            )
        op.create_index(
            "ix_books_pen_name_id",
            "books",
            ["pen_name_id"],
            if_not_exists=True,
        )


def downgrade() -> None:
    # Drop books.pen_name_id
    try:
        op.drop_index("ix_books_pen_name_id", table_name="books")
    except Exception:  # noqa: BLE001
        pass
    with op.batch_alter_table("books") as batch:
        try:
            batch.drop_column("pen_name_id")
        except Exception:  # noqa: BLE001
            pass

    # Drop new pen_names columns
    for idx in ("ix_pen_names_is_default", "ix_pen_names_user_id"):
        try:
            op.drop_index(idx, table_name="pen_names")
        except Exception:  # noqa: BLE001
            pass
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
            except Exception:  # noqa: BLE001
                pass
