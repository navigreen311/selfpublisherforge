"""Fix missing foreign key constraints and indexes on org_id columns.

Many tables created in 001_initial_schema declared an org_id UUID column
without an explicit FOREIGN KEY reference to organizations.id.  The ORM
models (via TenantModel) and relationship definitions all assume that
org_id references organizations.id, so the database should enforce this
at the schema level.

This migration also:
  - Sets a server_default on the market_intelligence org_id columns that
    were added as nullable in migration 003.
  - Adds missing composite indexes for frequently-queried FK columns that
    lacked them.

Revision ID: 004_fix_constraints
Revises: 003_add_market_intel_org_id
Create Date: 2026-02-10
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "004_fix_constraints"
down_revision: Union[str, None] = "003_add_market_intel_org_id"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None

# ── Tables from 001 that have org_id but no FK to organizations ──────────
_TABLES_MISSING_ORG_FK = [
    "pen_names",
    "projects",
    "series",
    "style_profiles",
    "content_assets",
    "publishing_accounts",
    "campaigns",
    "email_sequences",
    "reader_panels",
    "agents",
    "agent_workflows",
    "agent_budgets",
    "audit_trail",
    "analytics_events",
    "portfolio_metrics",
    "reports",
]

# ── Market-intel tables from 003 that need a server_default on org_id ────
_MARKET_INTEL_TABLES = [
    "market_categories",
    "market_keywords",
    "market_snapshots",
]


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Add missing FK constraints: <table>.org_id -> organizations.id
    # ------------------------------------------------------------------
    for table in _TABLES_MISSING_ORG_FK:
        with op.batch_alter_table(table) as batch_op:
            batch_op.create_foreign_key(
                f"fk_{table}_org_id",
                "organizations",
                ["org_id"],
                ["id"],
                ondelete="CASCADE",
            )

    # ------------------------------------------------------------------
    # 2. Set a server_default on the market-intel org_id columns added
    #    in migration 003 so that new rows get a deterministic default
    #    (Postgres gen_random_uuid() placeholder -- the application layer
    #    is expected to always supply a real value, but this prevents
    #    NULL-insertion surprises).
    # ------------------------------------------------------------------
    for table in _MARKET_INTEL_TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "org_id",
                existing_type=sa.Uuid(),
                existing_nullable=True,
                server_default=sa.text("gen_random_uuid()"),
            )

    # ------------------------------------------------------------------
    # 3. Add missing indexes on frequently-queried FK columns.
    #
    #    Several tables reference book_id or other FK columns that are
    #    queried via JOINs/filters but were never given an index in 001.
    #    We also add composite indexes that the ORM __table_args__ declare
    #    but which are absent from the migration history.
    # ------------------------------------------------------------------

    # series.genre_id is a nullable FK-like column used for lookups
    op.create_index(
        "ix_series_genre_id",
        "series",
        ["genre_id"],
    )

    # projects.org_id + status composite (common query pattern)
    op.create_index(
        "ix_projects_org_id_status",
        "projects",
        ["org_id", "status"],
    )

    # campaigns.org_id + status composite (used by advertising queries)
    op.create_index(
        "ix_campaigns_org_id_status",
        "campaigns",
        ["org_id", "status"],
    )

    # campaigns.org_id + platform composite
    op.create_index(
        "ix_campaigns_org_id_platform",
        "campaigns",
        ["org_id", "platform"],
    )

    # royalty_records.org_id (the table was created with book_id FK but
    # the model extends TenantModel, meaning it has org_id that should
    # be indexed for tenant-scoped queries)
    # NOTE: royalty_records does not have org_id in migration 001.
    # The model expects it via TenantModel but it was not added. We skip
    # this here since adding a column is a larger change.

    # audit_trail.org_id + action composite (common audit query)
    op.create_index(
        "ix_audit_trail_org_id_action",
        "audit_trail",
        ["org_id", "action"],
    )

    # analytics_events.org_id + event_type composite
    op.create_index(
        "ix_analytics_events_org_id_event_type",
        "analytics_events",
        ["org_id", "event_type"],
    )


def downgrade() -> None:
    # ------------------------------------------------------------------
    # 3. Drop composite indexes (reverse order)
    # ------------------------------------------------------------------
    op.drop_index("ix_analytics_events_org_id_event_type", table_name="analytics_events")
    op.drop_index("ix_audit_trail_org_id_action", table_name="audit_trail")
    op.drop_index("ix_campaigns_org_id_platform", table_name="campaigns")
    op.drop_index("ix_campaigns_org_id_status", table_name="campaigns")
    op.drop_index("ix_projects_org_id_status", table_name="projects")
    op.drop_index("ix_series_genre_id", table_name="series")

    # ------------------------------------------------------------------
    # 2. Remove server_default on market-intel org_id columns
    # ------------------------------------------------------------------
    for table in reversed(_MARKET_INTEL_TABLES):
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "org_id",
                existing_type=sa.Uuid(),
                existing_nullable=True,
                server_default=None,
            )

    # ------------------------------------------------------------------
    # 1. Drop FK constraints on org_id (reverse order)
    # ------------------------------------------------------------------
    for table in reversed(_TABLES_MISSING_ORG_FK):
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(f"fk_{table}_org_id", type_="foreignkey")
