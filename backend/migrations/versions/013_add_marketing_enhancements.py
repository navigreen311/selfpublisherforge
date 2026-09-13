"""Add marketing table enhancements and missing indexes."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import ARRAY

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None

# Every statement here used to sit inside `try: ... except Exception: pass`.
# That does not work in Postgres: the first failing DDL aborts the whole
# transaction, and swallowing the Python exception leaves every later
# statement — including Alembic's own version bump — failing with
# "current transaction is aborted". The guards below ask the catalog instead.
#
# `social_posts` and `arc_campaigns` do not exist at this point in the chain;
# their indexes ship with the migration that creates them.

_INDEXES = [
    ("idx_launch_plans_book_id", "launch_plans", ["book_id"]),
    ("idx_social_posts_scheduled_at", "social_posts", ["scheduled_at"]),
    ("idx_arc_campaigns_book_id", "arc_campaigns", ["book_id"]),
]


def _inspector():
    return inspect(op.get_bind())


def _has_column(table: str, column: str) -> bool:
    insp = _inspector()
    if not insp.has_table(table):
        return False
    return any(c["name"] == column for c in insp.get_columns(table))


def _has_index(table: str, name: str) -> bool:
    insp = _inspector()
    if not insp.has_table(table):
        return False
    return any(i["name"] == name for i in insp.get_indexes(table))


def upgrade() -> None:
    if _inspector().has_table("launch_plans") and not _has_column("launch_plans", "channels"):
        op.add_column("launch_plans", sa.Column("channels", ARRAY(sa.Text()), nullable=True))

    for name, table, columns in _INDEXES:
        if _inspector().has_table(table) and not _has_index(table, name):
            op.create_index(name, table, columns)


def downgrade() -> None:
    for name, table, _columns in reversed(_INDEXES):
        if _has_index(table, name):
            op.drop_index(name, table_name=table)

    if _has_column("launch_plans", "channels"):
        op.drop_column("launch_plans", "channels")
