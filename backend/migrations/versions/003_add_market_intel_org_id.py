"""Add org_id to market intelligence tables.

Revision ID: 003_add_market_intel_org_id
Revises: 002_refresh_tokens_oauth
Create Date: 2026-02-10
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "003_add_market_intel_org_id"
down_revision: str | None = "002_refresh_tokens_oauth"
branch_labels: str | None = None
depends_on: str | None = None

# Tables that need the org_id column
_TABLES = ["market_categories", "market_keywords", "market_snapshots"]


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("org_id", sa.Uuid(), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_org_id",
            table,
            "organizations",
            ["org_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table}_org_id", table, ["org_id"])


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_index(f"ix_{table}_org_id", table_name=table)
        op.drop_constraint(f"fk_{table}_org_id", table, type_="foreignkey")
        op.drop_column(table, "org_id")
