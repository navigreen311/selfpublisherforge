"""Add marketing table enhancements and missing indexes."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add channels column to launch_plans if not present
    try:
        op.add_column("launch_plans", sa.Column("channels", ARRAY(sa.Text()), nullable=True))
    except Exception:
        pass  # Column may already exist

    # Create indexes (ignore if exists)
    try:
        op.create_index("idx_launch_plans_book_id", "launch_plans", ["book_id"])
    except Exception:
        pass
    try:
        op.create_index("idx_social_posts_scheduled_at", "social_posts", ["scheduled_at"])
    except Exception:
        pass
    try:
        op.create_index("idx_arc_campaigns_book_id", "arc_campaigns", ["book_id"])
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index("idx_arc_campaigns_book_id")
    except Exception:
        pass
    try:
        op.drop_index("idx_social_posts_scheduled_at")
    except Exception:
        pass
    try:
        op.drop_index("idx_launch_plans_book_id")
    except Exception:
        pass
    try:
        op.drop_column("launch_plans", "channels")
    except Exception:
        pass
