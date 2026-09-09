"""Add proof_orders table for print proof ordering flow.

Revision ID: 025_print_proof
Revises: 020_add_activity_log
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "025_print_proof"
down_revision = "020_add_activity_log"
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
        sa.Column("publishing_id", UUID(as_uuid=True), nullable=True),
        sa.Column("book_id", UUID(as_uuid=True), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("interior_file_url", sa.Text(), nullable=True),
        sa.Column("cover_file_url", sa.Text(), nullable=True),
        sa.Column("shipping_name", sa.String(length=255), nullable=True),
        sa.Column("shipping_address", sa.Text(), nullable=True),
        sa.Column("shipping_method", sa.String(length=50), nullable=True),
        sa.Column("billing", JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("tracking_number", sa.String(length=100), nullable=True),
        sa.Column("estimated_delivery", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="ordered",
        ),
        sa.Column("checklist", JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("issues", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "approved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ordered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_proof_orders_org", "proof_orders", ["org_id", sa.text("ordered_at DESC")]
    )
    op.create_index("idx_proof_orders_status", "proof_orders", ["status"])
    op.create_index(
        "idx_proof_orders_publishing", "proof_orders", ["publishing_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_proof_orders_publishing", table_name="proof_orders")
    op.drop_index("idx_proof_orders_status", table_name="proof_orders")
    op.drop_index("idx_proof_orders_org", table_name="proof_orders")
    op.drop_table("proof_orders")
