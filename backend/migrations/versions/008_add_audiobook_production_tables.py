"""Add audiobook production tables.

Creates five tables for the audiobook production system:
- audiobook_voices: TTS voice configurations
- audiobook_projects: audiobook production projects linked to books
- audiobook_chapters: per-chapter audio generation tracking
- audiobook_pronunciation: custom word pronunciations
- audiobook_generation_jobs: async generation job queue

Revision ID: c1d2e3f4a5b6
Revises: b7c8d9e0f1a2
Create Date: 2026-02-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # -- Enum types ----------------------------------------------------------
    voice_provider = postgresql.ENUM(
        "coqui_xtts",
        "elevenlabs",
        "piper",
        "custom_clone",
        name="voice_provider",
        create_type=False,
    )
    voice_type = postgresql.ENUM(
        "narrator",
        "character",
        "custom",
        name="voice_type",
        create_type=False,
    )
    audiobook_project_status = postgresql.ENUM(
        "draft",
        "configuring",
        "generating",
        "reviewing",
        "mastering",
        "complete",
        "published",
        name="audiobook_project_status",
        create_type=False,
    )
    audiobook_chapter_status = postgresql.ENUM(
        "pending",
        "preprocessing",
        "generating",
        "post_processing",
        "review",
        "approved",
        "failed",
        name="audiobook_chapter_status",
        create_type=False,
    )
    audiobook_job_type = postgresql.ENUM(
        "chapter_generate",
        "chapter_regenerate",
        "segment_regenerate",
        "master_merge",
        "quality_check",
        "format_convert",
        name="audiobook_job_type",
        create_type=False,
    )
    audiobook_job_status = postgresql.ENUM(
        "queued",
        "processing",
        "completed",
        "failed",
        "cancelled",
        name="audiobook_job_status",
        create_type=False,
    )

    # Create enum types in the database
    voice_provider.create(op.get_bind(), checkfirst=True)
    voice_type.create(op.get_bind(), checkfirst=True)
    audiobook_project_status.create(op.get_bind(), checkfirst=True)
    audiobook_chapter_status.create(op.get_bind(), checkfirst=True)
    audiobook_job_type.create(op.get_bind(), checkfirst=True)
    audiobook_job_status.create(op.get_bind(), checkfirst=True)

    # -- audiobook_voices ----------------------------------------------------
    op.create_table(
        "audiobook_voices",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("provider", voice_provider, nullable=False),
        sa.Column("provider_voice_id", sa.String(255), nullable=True),
        sa.Column("voice_type", voice_type, nullable=False),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("age_range", sa.String(30), nullable=True),
        sa.Column("accent", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("sample_audio_url", sa.Text, nullable=True),
        sa.Column("clone_source_url", sa.Text, nullable=True),
        sa.Column("voice_settings", postgresql.JSONB, nullable=True),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("cost_per_minute", sa.Numeric(10, 4), nullable=True),
        sa.Column("is_system_voice", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_index("ix_audiobook_voices_provider", "audiobook_voices", ["provider"])
    op.create_index("ix_audiobook_voices_voice_type", "audiobook_voices", ["voice_type"])
    op.create_index("ix_audiobook_voices_active", "audiobook_voices", ["active"])
    op.create_index(
        "ix_audiobook_voices_voice_settings_gin", "audiobook_voices", ["voice_settings"], postgresql_using="gin"
    )
    op.create_index("ix_audiobook_voices_org_id_created_at", "audiobook_voices", ["org_id", "created_at"])
    op.create_index(
        "ix_audiobook_voices_deleted_at_partial",
        "audiobook_voices",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # -- audiobook_projects --------------------------------------------------
    op.create_table(
        "audiobook_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "book_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("status", audiobook_project_status, nullable=False, server_default="draft"),
        sa.Column(
            "narrator_voice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audiobook_voices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("character_voices", postgresql.JSONB, nullable=True),
        sa.Column("narration_style", postgresql.JSONB, nullable=True),
        sa.Column("output_format", sa.String(20), nullable=False, server_default="mp3"),
        sa.Column("sample_rate", sa.Integer, nullable=False, server_default="44100"),
        sa.Column("bit_rate", sa.Integer, nullable=False, server_default="192"),
        sa.Column("channels", sa.Integer, nullable=False, server_default="1"),
        sa.Column("target_platform", sa.String(50), nullable=False, server_default="acx"),
        sa.Column("total_chapters", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_chapters", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_duration_seconds", sa.Integer, nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("actual_cost", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("master_audio_url", sa.Text, nullable=True),
        sa.Column("cover_audio_url", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("settings", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
    )
    op.create_index("ix_audiobook_projects_status", "audiobook_projects", ["status"])
    op.create_index("ix_audiobook_projects_target_platform", "audiobook_projects", ["target_platform"])
    op.create_index(
        "ix_audiobook_projects_character_voices_gin", "audiobook_projects", ["character_voices"], postgresql_using="gin"
    )
    op.create_index(
        "ix_audiobook_projects_narration_style_gin", "audiobook_projects", ["narration_style"], postgresql_using="gin"
    )
    op.create_index("ix_audiobook_projects_metadata_gin", "audiobook_projects", ["metadata"], postgresql_using="gin")
    op.create_index("ix_audiobook_projects_settings_gin", "audiobook_projects", ["settings"], postgresql_using="gin")
    op.create_index("ix_audiobook_projects_org_id_created_at", "audiobook_projects", ["org_id", "created_at"])
    op.create_index(
        "ix_audiobook_projects_deleted_at_partial",
        "audiobook_projects",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # -- audiobook_chapters --------------------------------------------------
    op.create_table(
        "audiobook_chapters",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "audiobook_project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "chapter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chapters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("chapter_number", sa.Integer, nullable=False),
        sa.Column("chapter_title", sa.String(500), nullable=True),
        sa.Column("source_text", sa.Text, nullable=False),
        sa.Column("word_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", audiobook_chapter_status, nullable=False, server_default="pending"),
        sa.Column(
            "voice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audiobook_voices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ssml_text", sa.Text, nullable=True),
        sa.Column("audio_url", sa.Text, nullable=True),
        sa.Column("waveform_data", postgresql.JSONB, nullable=True),
        sa.Column("duration_seconds", sa.Float, nullable=False, server_default="0"),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("generation_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("generation_params", postgresql.JSONB, nullable=True),
        sa.Column("quality_metrics", postgresql.JSONB, nullable=True),
        sa.Column("review_notes", sa.Text, nullable=True),
        sa.Column("audio_edits", postgresql.JSONB, nullable=True),
        sa.Column("cost_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 4), nullable=False, server_default="0"),
    )
    op.create_index("ix_audiobook_chapters_status", "audiobook_chapters", ["status"])
    op.create_index("ix_audiobook_chapters_chapter_number", "audiobook_chapters", ["chapter_number"])
    op.create_index(
        "ix_audiobook_chapters_generation_params_gin",
        "audiobook_chapters",
        ["generation_params"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_audiobook_chapters_quality_metrics_gin", "audiobook_chapters", ["quality_metrics"], postgresql_using="gin"
    )
    op.create_index(
        "ix_audiobook_chapters_deleted_at_partial",
        "audiobook_chapters",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # -- audiobook_pronunciation ---------------------------------------------
    op.create_table(
        "audiobook_pronunciation",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "audiobook_project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("word", sa.String(255), nullable=False),
        sa.Column("phonetic", sa.String(500), nullable=False),
        sa.Column("ssml_phoneme", sa.String(500), nullable=True),
        sa.Column("audio_sample_url", sa.Text, nullable=True),
        sa.Column("context", sa.Text, nullable=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_index("ix_audiobook_pronunciation_word", "audiobook_pronunciation", ["word"])
    op.create_index("ix_audiobook_pronunciation_active", "audiobook_pronunciation", ["active"])
    op.create_index("ix_audiobook_pronunciation_org_id_created_at", "audiobook_pronunciation", ["org_id", "created_at"])
    op.create_index(
        "ix_audiobook_pronunciation_deleted_at_partial",
        "audiobook_pronunciation",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # -- audiobook_generation_jobs -------------------------------------------
    op.create_table(
        "audiobook_generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "audiobook_project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "chapter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audiobook_chapters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("job_type", audiobook_job_type, nullable=False),
        sa.Column("status", audiobook_job_status, nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="5"),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("input_params", postgresql.JSONB, nullable=True),
        sa.Column("output", postgresql.JSONB, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
    )
    op.create_index("ix_audiobook_generation_jobs_status", "audiobook_generation_jobs", ["status"])
    op.create_index("ix_audiobook_generation_jobs_job_type", "audiobook_generation_jobs", ["job_type"])
    op.create_index("ix_audiobook_generation_jobs_priority", "audiobook_generation_jobs", ["priority"])
    op.create_index("ix_audiobook_generation_jobs_celery_task_id", "audiobook_generation_jobs", ["celery_task_id"])
    op.create_index(
        "ix_audiobook_generation_jobs_input_params_gin",
        "audiobook_generation_jobs",
        ["input_params"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_audiobook_generation_jobs_output_gin", "audiobook_generation_jobs", ["output"], postgresql_using="gin"
    )
    op.create_index(
        "ix_audiobook_generation_jobs_deleted_at_partial",
        "audiobook_generation_jobs",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("audiobook_generation_jobs")
    op.drop_table("audiobook_pronunciation")
    op.drop_table("audiobook_chapters")
    op.drop_table("audiobook_projects")
    op.drop_table("audiobook_voices")

    # Drop enum types
    sa.Enum(name="audiobook_job_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="audiobook_job_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="audiobook_chapter_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="audiobook_project_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="voice_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="voice_provider").drop(op.get_bind(), checkfirst=True)
