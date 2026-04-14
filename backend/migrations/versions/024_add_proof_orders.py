"""Add proof_orders table for print proof ordering flow.

Revision ID: 024_add_proof_orders
Revises: 023_add_royalty_and_tax_tables
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "024_add_proof_orders"
down_revision = "023_add_royalty_and_tax_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "proof_orders",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("publishing_id", UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", UUID(as_uuid=True), nullable=True),
        sa.Column("interior_file_url", sa.Text(), nullable=False),
        sa.Column("cover_file_url", sa.Text(), nullable=False),
        sa.Column("trim_size", sa.String(length=50), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("interior_type", sa.String(length=50), nullable=True),
        sa.Column("shipping_name", sa.String(length=255), nullable=True),
        sa.Column("shipping_address", sa.Text(), nullable=True),
        sa.Column("shipping_city", sa.String(length=100), nullable=True),
        sa.Column("shipping_state", sa.String(length=10), nullable=True),
        sa.Column("shipping_zip", sa.String(length=20), nullable=True),
        sa.Column("shipping_method", sa.String(length=50), nullable=True),
        sa.Column("print_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("shipping_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("tracking_number", sa.String(length=100), nullable=True),
        sa.Column("estimated_delivery", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ordered"),
        sa.Column(
            "checklist",
            JSONB(),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("issues", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("skipped", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column(
            "ordered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index("idx_proof_orders_org", "proof_orders", ["org_id"])
    op.create_index(
        "idx_proof_orders_publishing", "proof_orders", ["publishing_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_proof_orders_publishing", table_name="proof_orders")
    op.drop_index("idx_proof_orders_org", table_name="proof_orders")
    op.drop_table("proof_orders")
