"""Add royalty tax dashboard tables: tax_documents and platform_royalty_imports.

The ``royalty_records`` table already exists (created in 001_initial_schema).
This migration adds two new tables that support the Royalty Tracking & Tax
Dashboard (Feature 3):

* ``tax_documents`` - generated 1099/year-end summary PDFs and CSVs.
* ``platform_royalty_imports`` - tracking of CSV imports from KDP, Ingram, D2D.

Revision ID: 023_royalty_tax
Revises: 020_add_activity_log
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "023_royalty_tax"
down_revision = "020_add_activity_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- tax_documents ---------------------------------------------------
    op.create_table(
        "tax_documents",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ready"),
        sa.Column("format", sa.String(length=10), nullable=False, server_default="pdf"),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("gross_income", sa.Numeric(14, 2), nullable=True),
        sa.Column("total_expenses", sa.Numeric(14, 2), nullable=True),
        sa.Column("estimated_tax", sa.Numeric(14, 2), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_tax_documents_org_year",
        "tax_documents",
        ["org_id", "tax_year"],
    )
    op.create_index(
        "idx_tax_documents_type",
        "tax_documents",
        ["document_type"],
    )

    # --- platform_royalty_imports ---------------------------------------
    op.create_table(
        "platform_royalty_imports",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("source_filename", sa.String(length=500), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_platform_royalty_imports_org",
        "platform_royalty_imports",
        ["org_id", "imported_at"],
    )
    op.create_index(
        "idx_platform_royalty_imports_platform",
        "platform_royalty_imports",
        ["platform"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_platform_royalty_imports_platform",
        table_name="platform_royalty_imports",
    )
    op.drop_index(
        "idx_platform_royalty_imports_org",
        table_name="platform_royalty_imports",
    )
    op.drop_table("platform_royalty_imports")

    op.drop_index("idx_tax_documents_type", table_name="tax_documents")
    op.drop_index("idx_tax_documents_org_year", table_name="tax_documents")
    op.drop_table("tax_documents")
