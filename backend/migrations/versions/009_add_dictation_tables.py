"""Add dictation_sessions and dictation_commands tables.

Adds two new tables for the voice dictation system:
- dictation_sessions: tracks individual dictation sessions with ASR metadata,
  transcript text, refinement state, and session metrics.
- dictation_commands: stores voice command phrases and their mapped actions.

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-02-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "c9d0e1f2a3b4"
down_revision: str | None = "c1d2e3f4a5b6"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # --- dictation_sessions ---
    op.create_table(
        "dictation_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("chapter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), server_default="active", nullable=False),
        sa.Column("duration_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("words_dictated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("words_after_refinement", sa.Integer(), server_default="0", nullable=False),
        sa.Column("raw_transcript", sa.Text(), nullable=True),
        sa.Column("refined_text", sa.Text(), nullable=True),
        sa.Column("asr_provider", sa.String(50), server_default="faster_whisper", nullable=False),
        sa.Column("asr_model", sa.String(100), server_default="large-v3", nullable=False),
        sa.Column("language", sa.String(10), server_default="en", nullable=False),
        sa.Column("audio_recording_url", sa.Text(), nullable=True),
        sa.Column("refinement_applied", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("refinement_style_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_metrics", postgresql.JSONB(), server_default="{}", nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["refinement_style_profile_id"], ["style_profiles.id"], ondelete="SET NULL"),
    )

    op.create_index("ix_dictation_sessions_org_id", "dictation_sessions", ["org_id"])
    op.create_index("ix_dictation_sessions_user_id", "dictation_sessions", ["user_id"])
    op.create_index("ix_dictation_sessions_chapter_id", "dictation_sessions", ["chapter_id"])
    op.create_index("ix_dictation_sessions_status", "dictation_sessions", ["status"])
    op.create_index("ix_dictation_sessions_asr_provider", "dictation_sessions", ["asr_provider"])
    op.create_index(
        "ix_dictation_sessions_session_metrics_gin",
        "dictation_sessions",
        ["session_metrics"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_dictation_sessions_deleted_at_partial",
        "dictation_sessions",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_dictation_sessions_org_id_created_at",
        "dictation_sessions",
        ["org_id", "created_at"],
    )

    # --- dictation_commands ---
    op.create_table(
        "dictation_commands",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("command_phrase", sa.String(255), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("is_system", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_dictation_commands_org_id", "dictation_commands", ["org_id"])
    op.create_index("ix_dictation_commands_command_phrase", "dictation_commands", ["command_phrase"])
    op.create_index("ix_dictation_commands_action", "dictation_commands", ["action"])
    op.create_index(
        "ix_dictation_commands_deleted_at_partial",
        "dictation_commands",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_dictation_commands_org_id_created_at",
        "dictation_commands",
        ["org_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("dictation_commands")
    op.drop_table("dictation_sessions")
