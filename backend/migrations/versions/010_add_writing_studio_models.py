"""Add chapter_versions, editor_settings tables and enhance chapters/writing_sessions.

Creates the chapter_versions and editor_settings tables for the Writing Studio
feature. Also adds new columns to the chapters table (target_word_count,
chapter_type) and enhances writing_sessions with org_id, manuscript_id,
started_at, ended_at, and active columns. The chapters.content column is
migrated from TEXT to JSONB to support TipTap rich-text JSON storage.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-02-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "d0e1f2a3b4c5"
down_revision: str | None = "c9d0e1f2a3b4"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # 1. Alter chapters table
    # ---------------------------------------------------------------
    # Convert content from TEXT to JSONB (TipTap JSON storage)
    op.execute("ALTER TABLE chapters " "ALTER COLUMN content TYPE JSONB USING content::jsonb")

    # Drop the old GIN trigram index on text content (incompatible with JSONB)
    op.execute("DROP INDEX IF EXISTS ix_chapters_content_fulltext")

    # Create a standard GIN index for JSONB content
    op.create_index(
        "ix_chapters_content_gin",
        "chapters",
        ["content"],
        postgresql_using="gin",
    )

    # Add new columns to chapters
    op.add_column(
        "chapters",
        sa.Column("target_word_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "chapters",
        sa.Column(
            "chapter_type",
            sa.String(50),
            server_default="chapter",
            nullable=False,
        ),
    )

    # The existing column uses an enum; we widen to VARCHAR(50) for flexibility
    op.execute("ALTER TABLE chapters " "ALTER COLUMN status TYPE VARCHAR(50) USING status::text")
    op.execute("ALTER TABLE chapters ALTER COLUMN status SET DEFAULT 'draft'")

    # ---------------------------------------------------------------
    # 2. Alter writing_sessions table
    # ---------------------------------------------------------------
    op.add_column(
        "writing_sessions",
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_writing_sessions_org_id",
        "writing_sessions",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_writing_sessions_org_id", "writing_sessions", ["org_id"])

    op.add_column(
        "writing_sessions",
        sa.Column(
            "manuscript_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_writing_sessions_manuscript_id",
        "writing_sessions",
        "manuscripts",
        ["manuscript_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.add_column(
        "writing_sessions",
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "writing_sessions",
        sa.Column(
            "ended_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "writing_sessions",
        sa.Column(
            "active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
    )

    # Add the requested composite indexes for writing_sessions
    op.create_index(
        "idx_writing_sessions_user",
        "writing_sessions",
        ["user_id"],
    )
    op.create_index(
        "idx_writing_sessions_manuscript",
        "writing_sessions",
        ["manuscript_id"],
    )

    # ---------------------------------------------------------------
    # 3. Create chapter_versions table
    # ---------------------------------------------------------------
    op.create_table(
        "chapter_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chapter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=True),
        sa.Column("word_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index(
        "idx_chapter_versions_chapter",
        "chapter_versions",
        [sa.text("chapter_id"), sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_chapter_versions_deleted_at_partial",
        "chapter_versions",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ---------------------------------------------------------------
    # 4. Create editor_settings table
    # ---------------------------------------------------------------
    op.create_table(
        "editor_settings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("font_family", sa.String(100), server_default="Georgia", nullable=False),
        sa.Column("font_size", sa.Integer(), server_default="16", nullable=False),
        sa.Column("theme", sa.String(20), server_default="light", nullable=False),
        sa.Column("line_height", sa.Float(), server_default="1.8", nullable=False),
        sa.Column("show_ai_panel", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("show_chapter_panel", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("style_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "tone_preference",
            sa.String(50),
            server_default="match_profile",
            nullable=False,
        ),
        sa.Column(
            "length_preference",
            sa.String(20),
            server_default="medium",
            nullable=False,
        ),
        sa.Column(
            "auto_save_interval_seconds",
            sa.Integer(),
            server_default="2",
            nullable=False,
        ),
        sa.Column("daily_word_goal", sa.Integer(), server_default="1000", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["style_profile_id"], ["style_profiles.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", name="uq_editor_settings_user_id"),
    )

    op.create_index(
        "ix_editor_settings_deleted_at_partial",
        "editor_settings",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    # Drop new tables
    op.drop_table("editor_settings")
    op.drop_table("chapter_versions")

    # Revert writing_sessions changes
    op.drop_index("idx_writing_sessions_manuscript", table_name="writing_sessions")
    op.drop_index("idx_writing_sessions_user", table_name="writing_sessions")
    op.drop_column("writing_sessions", "active")
    op.drop_column("writing_sessions", "ended_at")
    op.drop_column("writing_sessions", "started_at")
    op.drop_constraint("fk_writing_sessions_manuscript_id", "writing_sessions", type_="foreignkey")
    op.drop_column("writing_sessions", "manuscript_id")
    op.drop_constraint("fk_writing_sessions_org_id", "writing_sessions", type_="foreignkey")
    op.drop_index("ix_writing_sessions_org_id", table_name="writing_sessions")
    op.drop_column("writing_sessions", "org_id")

    # Revert chapters changes
    op.execute("ALTER TABLE chapters ALTER COLUMN status TYPE chapter_status " "USING status::chapter_status")
    op.drop_column("chapters", "chapter_type")
    op.drop_column("chapters", "target_word_count")

    op.drop_index("ix_chapters_content_gin", table_name="chapters")
    op.execute("ALTER TABLE chapters ALTER COLUMN content TYPE TEXT USING content::text")
    op.create_index(
        "ix_chapters_content_fulltext",
        "chapters",
        ["content"],
        postgresql_using="gin",
        postgresql_ops={"content": "gin_trgm_ops"},
    )
