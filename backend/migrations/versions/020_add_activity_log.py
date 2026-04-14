"""Add activity_log table and extend projects with book_type + target_launch_date.

Revision ID: 020_add_activity_log
Revises: 019
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "020_add_activity_log"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- activity_log -----------------------------------------------------
    op.create_table(
        "activity_log",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        sa.Column("resource_id", UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_activity_log_org",
        "activity_log",
        ["org_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_activity_log_resource",
        "activity_log",
        ["resource_type", "resource_id"],
    )

    # --- projects extensions ---------------------------------------------
    # Use add_column with IF NOT EXISTS via check_existing pattern: try/except
    # is handled at the Alembic level; here we just add them.
    with op.batch_alter_table("projects") as batch:
        batch.add_column(sa.Column("book_type", sa.String(length=50), nullable=True))
        batch.add_column(sa.Column("target_launch_date", sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("projects") as batch:
        batch.drop_column("target_launch_date")
        batch.drop_column("book_type")

    op.drop_index("idx_activity_log_resource", table_name="activity_log")
    op.drop_index("idx_activity_log_org", table_name="activity_log")
    op.drop_table("activity_log")
