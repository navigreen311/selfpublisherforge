"""Add missing org_id column to royalty_records table.

The RoyaltyRecord model extends TenantModel which provides an org_id
column, but the original 001_initial_schema migration did not include
org_id on the royalty_records table.  Migration 004_fix_constraints
acknowledged this gap but intentionally skipped it.

This migration adds the column, creates an index for tenant-scoped
queries, and adds a foreign key constraint to organizations.id.

Revision ID: b7c8d9e0f1a2
Revises: a3b4c5d6e7f8
Create Date: 2026-02-10
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "b7c8d9e0f1a2"
down_revision: str | None = "a3b4c5d6e7f8"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # 1. Add the org_id column (nullable initially so existing rows are not rejected)
    op.add_column(
        "royalty_records",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 2. Create an index for tenant-scoped lookups
    op.create_index(
        "ix_royalty_records_org_id",
        "royalty_records",
        ["org_id"],
    )

    # 3. Add foreign key constraint to organizations.id
    op.create_foreign_key(
        "fk_royalty_records_org_id",
        "royalty_records",
        "organizations",
        ["org_id"],
        ["id"],
    )


def downgrade() -> None:
    # Reverse order: drop FK, drop index, drop column
    op.drop_constraint("fk_royalty_records_org_id", "royalty_records", type_="foreignkey")
    op.drop_index("ix_royalty_records_org_id", table_name="royalty_records")
    op.drop_column("royalty_records", "org_id")
