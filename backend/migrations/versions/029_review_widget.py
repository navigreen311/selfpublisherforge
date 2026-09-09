"""Add review_widgets table for embeddable review widgets (Feature 9).

Revision ID: 029_review_widget
Revises: 020_add_activity_log
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "029_review_widget"
down_revision = "020_add_activity_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_widgets",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("style", sa.String(length=50), nullable=False, server_default="card_grid"),
        sa.Column("theme", sa.String(length=20), nullable=False, server_default="light"),
        sa.Column("max_reviews", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("min_rating", sa.Integer(), nullable=False, server_default="4"),
        sa.Column(
            "show_options",
            JSONB(),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
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
        "idx_review_widgets_org_book",
        "review_widgets",
        ["org_id", "book_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_review_widgets_org_book", table_name="review_widgets")
    op.drop_table("review_widgets")
