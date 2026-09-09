"""initial_schema

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-02-09
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Enums ──────────────────────────────────────────────────────────
    plan_tier = postgresql.ENUM(
        "free", "starter", "pro", "business", "enterprise",
        name="plan_tier", create_type=False,
    )
    subscription_status = postgresql.ENUM(
        "active", "trialing", "past_due", "canceled", "unpaid",
        name="subscription_status", create_type=False,
    )
    user_role = postgresql.ENUM(
        "owner", "admin", "editor", "writer", "viewer",
        name="user_role", create_type=False,
    )
    project_type = postgresql.ENUM(
        "book", "series", "course",
        name="project_type", create_type=False,
    )
    project_status = postgresql.ENUM(
        "draft", "active", "archived", "completed",
        name="project_status", create_type=False,
    )
    book_format = postgresql.ENUM(
        "ebook", "print", "audio",
        name="book_format", create_type=False,
    )
    book_status = postgresql.ENUM(
        "draft", "writing", "editing", "formatting", "published", "archived",
        name="book_status", create_type=False,
    )
    series_status = postgresql.ENUM(
        "planned", "active", "completed", "abandoned",
        name="series_status", create_type=False,
    )
    content_type = postgresql.ENUM(
        "fiction", "nonfiction", "poetry", "screenplay",
        name="content_type", create_type=False,
    )
    manuscript_status = postgresql.ENUM(
        "draft", "revision", "final", "archived",
        name="manuscript_status", create_type=False,
    )
    chapter_status = postgresql.ENUM(
        "outline", "draft", "revision", "final",
        name="chapter_status", create_type=False,
    )
    asset_type_enum = postgresql.ENUM(
        "cover", "image", "document", "audio", "video",
        name="asset_type", create_type=False,
    )
    publishing_platform = postgresql.ENUM(
        "kdp", "ingramspark", "d2d", "acx",
        name="publishing_platform", create_type=False,
    )
    publishing_account_status = postgresql.ENUM(
        "active", "inactive", "error", "pending",
        name="publishing_account_status", create_type=False,
    )
    listing_status = postgresql.ENUM(
        "draft", "pending", "live", "suppressed", "removed",
        name="listing_status", create_type=False,
    )
    validation_type = postgresql.ENUM(
        "format", "content", "metadata", "cover",
        name="validation_type", create_type=False,
    )
    scan_type_enum = postgresql.ENUM(
        "copyright", "trademark", "content_policy", "ai_disclosure",
        name="scan_type", create_type=False,
    )
    risk_level = postgresql.ENUM(
        "green", "yellow", "red",
        name="risk_level", create_type=False,
    )
    campaign_platform = postgresql.ENUM(
        "amazon_ads", "facebook", "bookbub", "google", "tiktok",
        name="campaign_platform", create_type=False,
    )
    campaign_status = postgresql.ENUM(
        "draft", "active", "paused", "completed", "archived",
        name="campaign_status", create_type=False,
    )
    ad_creative_type = postgresql.ENUM(
        "image", "video", "text", "carousel",
        name="ad_creative_type", create_type=False,
    )
    launch_plan_status = postgresql.ENUM(
        "planning", "active", "completed", "canceled",
        name="launch_plan_status", create_type=False,
    )
    agent_type_enum = postgresql.ENUM(
        "research", "writing", "editing", "marketing", "analytics", "publishing",
        name="agent_type", create_type=False,
    )
    permission_level = postgresql.ENUM(
        "read_only", "suggest", "execute", "autonomous",
        name="permission_level", create_type=False,
    )
    agent_task_status = postgresql.ENUM(
        "pending", "running", "completed", "failed", "canceled",
        name="agent_task_status", create_type=False,
    )
    budget_type_enum = postgresql.ENUM(
        "daily", "weekly", "monthly", "per_task",
        name="budget_type", create_type=False,
    )
    actor_type_enum = postgresql.ENUM(
        "user", "agent", "system",
        name="actor_type", create_type=False,
    )
    ab_test_status = postgresql.ENUM(
        "draft", "running", "completed", "canceled",
        name="ab_test_status", create_type=False,
    )
    report_status = postgresql.ENUM(
        "pending", "generating", "completed", "failed",
        name="report_status", create_type=False,
    )

    # Create all enums
    for enum_type in [
        plan_tier, subscription_status, user_role, project_type, project_status,
        book_format, book_status, series_status, content_type, manuscript_status,
        chapter_status, asset_type_enum, publishing_platform, publishing_account_status,
        listing_status, validation_type, scan_type_enum, risk_level, campaign_platform,
        campaign_status, ad_creative_type, launch_plan_status, agent_type_enum,
        permission_level, agent_task_status, budget_type_enum, actor_type_enum,
        ab_test_status, report_status,
    ]:
        enum_type.create(op.get_bind(), checkfirst=True)

    # ── organizations ──────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("plan_tier", plan_tier, server_default="free", nullable=False),
        sa.Column("subscription_status", subscription_status, server_default="active", nullable=False),
        sa.Column("settings", postgresql.JSONB(), nullable=True),
        sa.Column("limits", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])
    op.create_index("ix_organizations_plan_tier", "organizations", ["plan_tier"])
    op.create_index("ix_organizations_subscription_status", "organizations", ["subscription_status"])
    op.create_index("ix_organizations_settings_gin", "organizations", ["settings"], postgresql_using="gin")
    op.create_index("ix_organizations_limits_gin", "organizations", ["limits"], postgresql_using="gin")
    op.create_index(
        "ix_organizations_deleted_at_partial", "organizations", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── users ──────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", user_role, server_default="viewer", nullable=False),
        sa.Column("preferences", postgresql.JSONB(), nullable=True),
        sa.Column("onboarding_state", sa.String(50), nullable=True),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_org_id", "users", ["org_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_preferences_gin", "users", ["preferences"], postgresql_using="gin")
    op.create_index(
        "ix_users_deleted_at_partial", "users", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_users_org_id_created_at", "users", ["org_id", "created_at"])

    # ── api_keys ───────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index("ix_api_keys_org_id", "api_keys", ["org_id"])
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("ix_api_keys_scopes_gin", "api_keys", ["scopes"], postgresql_using="gin")
    op.create_index(
        "ix_api_keys_deleted_at_partial", "api_keys", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── user_sessions ──────────────────────────────────────────────────
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("device_info", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_device_info_gin", "user_sessions", ["device_info"], postgresql_using="gin")
    op.create_index(
        "ix_user_sessions_deleted_at_partial", "user_sessions", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── pen_names ──────────────────────────────────────────────────────
    op.create_table(
        "pen_names",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("brand_guidelines", postgresql.JSONB(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pen_names_org_id", "pen_names", ["org_id"])
    op.create_index("ix_pen_names_active", "pen_names", ["active"])
    op.create_index("ix_pen_names_brand_guidelines_gin", "pen_names", ["brand_guidelines"], postgresql_using="gin")
    op.create_index(
        "ix_pen_names_deleted_at_partial", "pen_names", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_pen_names_org_id_created_at", "pen_names", ["org_id", "created_at"])

    # ── projects ───────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("type", project_type, nullable=False),
        sa.Column("status", project_status, server_default="draft", nullable=False),
        sa.Column("settings", postgresql.JSONB(), nullable=True),
        sa.Column("pen_name_id", sa.Uuid(), sa.ForeignKey("pen_names.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_org_id", "projects", ["org_id"])
    op.create_index("ix_projects_pen_name_id", "projects", ["pen_name_id"])
    op.create_index("ix_projects_type", "projects", ["type"])
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_settings_gin", "projects", ["settings"], postgresql_using="gin")
    op.create_index(
        "ix_projects_deleted_at_partial", "projects", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_projects_org_id_created_at", "projects", ["org_id", "created_at"])

    # ── books ──────────────────────────────────────────────────────────
    op.create_table(
        "books",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("subtitle", sa.String(500), nullable=True),
        sa.Column("isbn", sa.String(20), nullable=True),
        sa.Column("asin", sa.String(20), nullable=True),
        sa.Column("format", book_format, server_default="ebook", nullable=False),
        sa.Column("status", book_status, server_default="draft", nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_books_project_id", "books", ["project_id"])
    op.create_index("ix_books_isbn", "books", ["isbn"])
    op.create_index("ix_books_asin", "books", ["asin"])
    op.create_index("ix_books_format", "books", ["format"])
    op.create_index("ix_books_status", "books", ["status"])
    op.create_index("ix_books_metadata_gin", "books", ["metadata"], postgresql_using="gin")
    op.create_index(
        "ix_books_deleted_at_partial", "books", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── series ─────────────────────────────────────────────────────────
    op.create_table(
        "series",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("genre_id", sa.Uuid(), nullable=True),
        sa.Column("book_order", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("reading_order", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("status", series_status, server_default="planned", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_series_org_id", "series", ["org_id"])
    op.create_index("ix_series_status", "series", ["status"])
    op.create_index("ix_series_book_order_gin", "series", ["book_order"], postgresql_using="gin")
    op.create_index("ix_series_reading_order_gin", "series", ["reading_order"], postgresql_using="gin")
    op.create_index(
        "ix_series_deleted_at_partial", "series", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_series_org_id_created_at", "series", ["org_id", "created_at"])

    # ── book_versions ──────────────────────────────────────────────────
    op.create_table(
        "book_versions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("manuscript_url", sa.Text(), nullable=True),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_book_versions_book_id", "book_versions", ["book_id"])
    op.create_index("ix_book_versions_created_by", "book_versions", ["created_by"])
    op.create_index(
        "ix_book_versions_deleted_at_partial", "book_versions", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── manuscripts ────────────────────────────────────────────────────
    op.create_table(
        "manuscripts",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_type", content_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", manuscript_status, server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_manuscripts_book_id", "manuscripts", ["book_id"])
    op.create_index("ix_manuscripts_status", "manuscripts", ["status"])
    op.create_index("ix_manuscripts_content_type", "manuscripts", ["content_type"])
    op.create_index(
        "ix_manuscripts_deleted_at_partial", "manuscripts", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── chapters ───────────────────────────────────────────────────────
    op.create_table(
        "chapters",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("manuscript_id", sa.Uuid(), sa.ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", chapter_status, server_default="outline", nullable=False),
        sa.Column("ai_metrics", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chapters_manuscript_id", "chapters", ["manuscript_id"])
    op.create_index("ix_chapters_status", "chapters", ["status"])
    op.create_index("ix_chapters_order_index", "chapters", ["order_index"])
    op.create_index("ix_chapters_ai_metrics_gin", "chapters", ["ai_metrics"], postgresql_using="gin")
    op.create_index(
        "ix_chapters_deleted_at_partial", "chapters", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    # Full-text index on chapters.content using gin_trgm_ops
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chapters_content_fulltext "
        "ON chapters USING gin (content gin_trgm_ops)"
    )

    # ── style_profiles ─────────────────────────────────────────────────
    op.create_table(
        "style_profiles",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("voice_fingerprint", postgresql.JSONB(), nullable=True),
        sa.Column("vocabulary_stats", postgresql.JSONB(), nullable=True),
        sa.Column("sentence_patterns", postgresql.JSONB(), nullable=True),
        sa.Column("sample_sources", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_style_profiles_org_id", "style_profiles", ["org_id"])
    op.create_index("ix_style_profiles_voice_fingerprint_gin", "style_profiles", ["voice_fingerprint"], postgresql_using="gin")
    op.create_index("ix_style_profiles_vocabulary_stats_gin", "style_profiles", ["vocabulary_stats"], postgresql_using="gin")
    op.create_index("ix_style_profiles_sentence_patterns_gin", "style_profiles", ["sentence_patterns"], postgresql_using="gin")
    op.create_index("ix_style_profiles_sample_sources_gin", "style_profiles", ["sample_sources"], postgresql_using="gin")
    op.create_index(
        "ix_style_profiles_deleted_at_partial", "style_profiles", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_style_profiles_org_id_created_at", "style_profiles", ["org_id", "created_at"])

    # ── writing_sessions ───────────────────────────────────────────────
    op.create_table(
        "writing_sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chapter_id", sa.Uuid(), sa.ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("words_written", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duration_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ai_assists_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_writing_sessions_user_id", "writing_sessions", ["user_id"])
    op.create_index("ix_writing_sessions_book_id", "writing_sessions", ["book_id"])
    op.create_index("ix_writing_sessions_chapter_id", "writing_sessions", ["chapter_id"])
    op.create_index(
        "ix_writing_sessions_deleted_at_partial", "writing_sessions", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── content_assets ─────────────────────────────────────────────────
    op.create_table(
        "content_assets",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("asset_type", asset_type_enum, nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_assets_org_id", "content_assets", ["org_id"])
    op.create_index("ix_content_assets_asset_type", "content_assets", ["asset_type"])
    op.create_index("ix_content_assets_mime_type", "content_assets", ["mime_type"])
    op.create_index("ix_content_assets_metadata_gin", "content_assets", ["metadata"], postgresql_using="gin")
    op.create_index(
        "ix_content_assets_deleted_at_partial", "content_assets", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_content_assets_org_id_created_at", "content_assets", ["org_id", "created_at"])

    # ── market_categories ──────────────────────────────────────────────
    op.create_table(
        "market_categories",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("amazon_node_id", sa.String(50), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("path", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("parent_id", sa.Uuid(), sa.ForeignKey("market_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("book_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("avg_bsr", sa.Float(), nullable=True),
        sa.Column("competition_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("amazon_node_id"),
    )
    op.create_index("ix_market_categories_amazon_node_id", "market_categories", ["amazon_node_id"])
    op.create_index("ix_market_categories_parent_id", "market_categories", ["parent_id"])
    op.create_index("ix_market_categories_path_gin", "market_categories", ["path"], postgresql_using="gin")
    op.create_index("ix_market_categories_competition_score", "market_categories", ["competition_score"])
    op.create_index(
        "ix_market_categories_deleted_at_partial", "market_categories", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── market_keywords ────────────────────────────────────────────────
    op.create_table(
        "market_keywords",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("keyword", sa.String(500), nullable=False),
        sa.Column("search_volume", sa.Integer(), nullable=True),
        sa.Column("competition_score", sa.Float(), nullable=True),
        sa.Column("cpc_estimate", sa.Numeric(10, 4), nullable=True),
        sa.Column("trend_direction", sa.String(20), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_keywords_keyword", "market_keywords", ["keyword"])
    op.create_index("ix_market_keywords_search_volume", "market_keywords", ["search_volume"])
    op.create_index("ix_market_keywords_competition_score", "market_keywords", ["competition_score"])
    op.create_index(
        "ix_market_keywords_deleted_at_partial", "market_keywords", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── competitor_books ───────────────────────────────────────────────
    op.create_table(
        "competitor_books",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("asin", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("bsr_current", sa.Integer(), nullable=True),
        sa.Column("bsr_history", postgresql.JSONB(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("reviews_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("category_ids", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asin"),
    )
    op.create_index("ix_competitor_books_asin", "competitor_books", ["asin"])
    op.create_index("ix_competitor_books_bsr_current", "competitor_books", ["bsr_current"])
    op.create_index("ix_competitor_books_bsr_history_gin", "competitor_books", ["bsr_history"], postgresql_using="gin")
    op.create_index("ix_competitor_books_category_ids_gin", "competitor_books", ["category_ids"], postgresql_using="gin")
    op.create_index(
        "ix_competitor_books_deleted_at_partial", "competitor_books", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── competitor_reviews ─────────────────────────────────────────────
    op.create_table(
        "competitor_reviews",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("competitor_book_id", sa.Uuid(), sa.ForeignKey("competitor_books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("weakness_signals", postgresql.JSONB(), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_competitor_reviews_competitor_book_id", "competitor_reviews", ["competitor_book_id"])
    op.create_index("ix_competitor_reviews_rating", "competitor_reviews", ["rating"])
    op.create_index("ix_competitor_reviews_sentiment_score", "competitor_reviews", ["sentiment_score"])
    op.create_index("ix_competitor_reviews_weakness_signals_gin", "competitor_reviews", ["weakness_signals"], postgresql_using="gin")
    op.create_index(
        "ix_competitor_reviews_deleted_at_partial", "competitor_reviews", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    # Full-text index on competitor_reviews.review_text using gin_trgm_ops
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_competitor_reviews_review_text_fulltext "
        "ON competitor_reviews USING gin (review_text gin_trgm_ops)"
    )

    # ── market_snapshots ───────────────────────────────────────────────
    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("category_id", sa.Uuid(), sa.ForeignKey("market_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("top_100_asins", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("metrics", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_snapshots_category_id", "market_snapshots", ["category_id"])
    op.create_index("ix_market_snapshots_snapshot_date", "market_snapshots", ["snapshot_date"])
    op.create_index("ix_market_snapshots_top_100_asins_gin", "market_snapshots", ["top_100_asins"], postgresql_using="gin")
    op.create_index("ix_market_snapshots_metrics_gin", "market_snapshots", ["metrics"], postgresql_using="gin")
    op.create_index(
        "ix_market_snapshots_deleted_at_partial", "market_snapshots", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── publishing_accounts ────────────────────────────────────────────
    op.create_table(
        "publishing_accounts",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("platform", publishing_platform, nullable=False),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
        sa.Column("status", publishing_account_status, server_default="pending", nullable=False),
        sa.Column("health_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_publishing_accounts_org_id", "publishing_accounts", ["org_id"])
    op.create_index("ix_publishing_accounts_platform", "publishing_accounts", ["platform"])
    op.create_index("ix_publishing_accounts_status", "publishing_accounts", ["status"])
    op.create_index(
        "ix_publishing_accounts_deleted_at_partial", "publishing_accounts", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_publishing_accounts_org_id_created_at", "publishing_accounts", ["org_id", "created_at"])

    # ── listings ───────────────────────────────────────────────────────
    op.create_table(
        "listings",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("publishing_account_id", sa.Uuid(), sa.ForeignKey("publishing_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform_id", sa.String(100), nullable=True),
        sa.Column("status", listing_status, server_default="draft", nullable=False),
        sa.Column("listing_data", postgresql.JSONB(), nullable=True),
        sa.Column("last_synced", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listings_book_id", "listings", ["book_id"])
    op.create_index("ix_listings_publishing_account_id", "listings", ["publishing_account_id"])
    op.create_index("ix_listings_status", "listings", ["status"])
    op.create_index("ix_listings_listing_data_gin", "listings", ["listing_data"], postgresql_using="gin")
    op.create_index(
        "ix_listings_deleted_at_partial", "listings", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── upload_validations ─────────────────────────────────────────────
    op.create_table(
        "upload_validations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("validation_type", validation_type, nullable=False),
        sa.Column("results", postgresql.JSONB(), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("errors", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("warnings", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_upload_validations_book_id", "upload_validations", ["book_id"])
    op.create_index("ix_upload_validations_validation_type", "upload_validations", ["validation_type"])
    op.create_index("ix_upload_validations_passed", "upload_validations", ["passed"])
    op.create_index("ix_upload_validations_results_gin", "upload_validations", ["results"], postgresql_using="gin")
    op.create_index("ix_upload_validations_errors_gin", "upload_validations", ["errors"], postgresql_using="gin")
    op.create_index("ix_upload_validations_warnings_gin", "upload_validations", ["warnings"], postgresql_using="gin")
    op.create_index(
        "ix_upload_validations_deleted_at_partial", "upload_validations", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── compliance_scans ───────────────────────────────────────────────
    op.create_table(
        "compliance_scans",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scan_type", scan_type_enum, nullable=False),
        sa.Column("findings", postgresql.JSONB(), nullable=True),
        sa.Column("risk_level", risk_level, server_default="green", nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_compliance_scans_book_id", "compliance_scans", ["book_id"])
    op.create_index("ix_compliance_scans_scan_type", "compliance_scans", ["scan_type"])
    op.create_index("ix_compliance_scans_risk_level", "compliance_scans", ["risk_level"])
    op.create_index("ix_compliance_scans_findings_gin", "compliance_scans", ["findings"], postgresql_using="gin")
    op.create_index("ix_compliance_scans_reviewed_by", "compliance_scans", ["reviewed_by"])
    op.create_index(
        "ix_compliance_scans_deleted_at_partial", "compliance_scans", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── pricing_rules ──────────────────────────────────────────────────
    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("strategy", sa.String(100), nullable=False),
        sa.Column("rules", postgresql.JSONB(), nullable=True),
        sa.Column("current_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("last_adjusted", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pricing_rules_book_id", "pricing_rules", ["book_id"])
    op.create_index("ix_pricing_rules_strategy", "pricing_rules", ["strategy"])
    op.create_index("ix_pricing_rules_rules_gin", "pricing_rules", ["rules"], postgresql_using="gin")
    op.create_index(
        "ix_pricing_rules_deleted_at_partial", "pricing_rules", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── campaigns ──────────────────────────────────────────────────────
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="SET NULL"), nullable=True),
        sa.Column("platform", campaign_platform, nullable=False),
        sa.Column("status", campaign_status, server_default="draft", nullable=False),
        sa.Column("budget", sa.Numeric(12, 2), nullable=True),
        sa.Column("spend", sa.Numeric(12, 2), nullable=True),
        sa.Column("results", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_campaigns_org_id", "campaigns", ["org_id"])
    op.create_index("ix_campaigns_book_id", "campaigns", ["book_id"])
    op.create_index("ix_campaigns_platform", "campaigns", ["platform"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_index("ix_campaigns_results_gin", "campaigns", ["results"], postgresql_using="gin")
    op.create_index(
        "ix_campaigns_deleted_at_partial", "campaigns", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_campaigns_org_id_created_at", "campaigns", ["org_id", "created_at"])

    # ── ad_creatives ───────────────────────────────────────────────────
    op.create_table(
        "ad_creatives",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", ad_creative_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("performance", postgresql.JSONB(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ad_creatives_campaign_id", "ad_creatives", ["campaign_id"])
    op.create_index("ix_ad_creatives_type", "ad_creatives", ["type"])
    op.create_index("ix_ad_creatives_active", "ad_creatives", ["active"])
    op.create_index("ix_ad_creatives_performance_gin", "ad_creatives", ["performance"], postgresql_using="gin")
    op.create_index(
        "ix_ad_creatives_deleted_at_partial", "ad_creatives", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── launch_plans ───────────────────────────────────────────────────
    op.create_table(
        "launch_plans",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("launch_date", sa.Date(), nullable=True),
        sa.Column("phases", postgresql.JSONB(), nullable=True),
        sa.Column("status", launch_plan_status, server_default="planning", nullable=False),
        sa.Column("checklist", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_launch_plans_book_id", "launch_plans", ["book_id"])
    op.create_index("ix_launch_plans_status", "launch_plans", ["status"])
    op.create_index("ix_launch_plans_launch_date", "launch_plans", ["launch_date"])
    op.create_index("ix_launch_plans_phases_gin", "launch_plans", ["phases"], postgresql_using="gin")
    op.create_index("ix_launch_plans_checklist_gin", "launch_plans", ["checklist"], postgresql_using="gin")
    op.create_index(
        "ix_launch_plans_deleted_at_partial", "launch_plans", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── email_sequences ────────────────────────────────────────────────
    op.create_table(
        "email_sequences",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("trigger", sa.String(100), nullable=True),
        sa.Column("emails", postgresql.JSONB(), nullable=True),
        sa.Column("subscriber_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("performance", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_sequences_org_id", "email_sequences", ["org_id"])
    op.create_index("ix_email_sequences_trigger", "email_sequences", ["trigger"])
    op.create_index("ix_email_sequences_emails_gin", "email_sequences", ["emails"], postgresql_using="gin")
    op.create_index("ix_email_sequences_performance_gin", "email_sequences", ["performance"], postgresql_using="gin")
    op.create_index(
        "ix_email_sequences_deleted_at_partial", "email_sequences", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_email_sequences_org_id_created_at", "email_sequences", ["org_id", "created_at"])

    # ── reader_panels ──────────────────────────────────────────────────
    op.create_table(
        "reader_panels",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("panel_size", sa.Integer(), server_default="0", nullable=False),
        sa.Column("recruitment_criteria", postgresql.JSONB(), nullable=True),
        sa.Column("tests", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reader_panels_org_id", "reader_panels", ["org_id"])
    op.create_index("ix_reader_panels_recruitment_criteria_gin", "reader_panels", ["recruitment_criteria"], postgresql_using="gin")
    op.create_index("ix_reader_panels_tests_gin", "reader_panels", ["tests"], postgresql_using="gin")
    op.create_index(
        "ix_reader_panels_deleted_at_partial", "reader_panels", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_reader_panels_org_id_created_at", "reader_panels", ["org_id", "created_at"])

    # ── agents ─────────────────────────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("agent_type", agent_type_enum, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("configuration", postgresql.JSONB(), nullable=True),
        sa.Column("permission_level", permission_level, server_default="suggest", nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agents_org_id", "agents", ["org_id"])
    op.create_index("ix_agents_agent_type", "agents", ["agent_type"])
    op.create_index("ix_agents_permission_level", "agents", ["permission_level"])
    op.create_index("ix_agents_active", "agents", ["active"])
    op.create_index("ix_agents_configuration_gin", "agents", ["configuration"], postgresql_using="gin")
    op.create_index(
        "ix_agents_deleted_at_partial", "agents", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_agents_org_id_created_at", "agents", ["org_id", "created_at"])

    # ── agent_tasks ────────────────────────────────────────────────────
    op.create_table(
        "agent_tasks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_type", sa.String(100), nullable=False),
        sa.Column("input", postgresql.JSONB(), nullable=True),
        sa.Column("output", postgresql.JSONB(), nullable=True),
        sa.Column("status", agent_task_status, server_default="pending", nullable=False),
        sa.Column("cost_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_tasks_agent_id", "agent_tasks", ["agent_id"])
    op.create_index("ix_agent_tasks_task_type", "agent_tasks", ["task_type"])
    op.create_index("ix_agent_tasks_status", "agent_tasks", ["status"])
    op.create_index("ix_agent_tasks_input_gin", "agent_tasks", ["input"], postgresql_using="gin")
    op.create_index("ix_agent_tasks_output_gin", "agent_tasks", ["output"], postgresql_using="gin")
    op.create_index(
        "ix_agent_tasks_deleted_at_partial", "agent_tasks", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── agent_workflows ────────────────────────────────────────────────
    op.create_table(
        "agent_workflows",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("steps", postgresql.JSONB(), nullable=True),
        sa.Column("trigger_conditions", postgresql.JSONB(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_workflows_org_id", "agent_workflows", ["org_id"])
    op.create_index("ix_agent_workflows_active", "agent_workflows", ["active"])
    op.create_index("ix_agent_workflows_steps_gin", "agent_workflows", ["steps"], postgresql_using="gin")
    op.create_index("ix_agent_workflows_trigger_conditions_gin", "agent_workflows", ["trigger_conditions"], postgresql_using="gin")
    op.create_index(
        "ix_agent_workflows_deleted_at_partial", "agent_workflows", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_agent_workflows_org_id_created_at", "agent_workflows", ["org_id", "created_at"])

    # ── agent_budgets ──────────────────────────────────────────────────
    op.create_table(
        "agent_budgets",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("budget_type", budget_type_enum, nullable=False),
        sa.Column("limit_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("spent_value", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("period", sa.String(50), nullable=True),
        sa.Column("alerts_sent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_budgets_org_id", "agent_budgets", ["org_id"])
    op.create_index("ix_agent_budgets_budget_type", "agent_budgets", ["budget_type"])
    op.create_index(
        "ix_agent_budgets_deleted_at_partial", "agent_budgets", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_agent_budgets_org_id_created_at", "agent_budgets", ["org_id", "created_at"])

    # ── audit_trail ────────────────────────────────────────────────────
    op.create_table(
        "audit_trail",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("actor_type", actor_type_enum, nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_trail_org_id", "audit_trail", ["org_id"])
    op.create_index("ix_audit_trail_actor_type", "audit_trail", ["actor_type"])
    op.create_index("ix_audit_trail_actor_id", "audit_trail", ["actor_id"])
    op.create_index("ix_audit_trail_action", "audit_trail", ["action"])
    op.create_index("ix_audit_trail_resource_type", "audit_trail", ["resource_type"])
    op.create_index("ix_audit_trail_resource_id", "audit_trail", ["resource_id"])
    op.create_index("ix_audit_trail_details_gin", "audit_trail", ["details"], postgresql_using="gin")
    op.create_index("ix_audit_trail_timestamp_brin", "audit_trail", ["timestamp"], postgresql_using="brin")
    op.create_index("ix_audit_trail_org_id_created_at", "audit_trail", ["org_id", "created_at"])

    # ── analytics_events ───────────────────────────────────────────────
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("data", postgresql.JSONB(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analytics_events_org_id", "analytics_events", ["org_id"])
    op.create_index("ix_analytics_events_event_type", "analytics_events", ["event_type"])
    op.create_index("ix_analytics_events_entity_type", "analytics_events", ["entity_type"])
    op.create_index("ix_analytics_events_entity_id", "analytics_events", ["entity_id"])
    op.create_index("ix_analytics_events_data_gin", "analytics_events", ["data"], postgresql_using="gin")
    op.create_index("ix_analytics_events_timestamp_brin", "analytics_events", ["timestamp"], postgresql_using="brin")
    op.create_index("ix_analytics_events_org_id_created_at", "analytics_events", ["org_id", "created_at"])

    # ── royalty_records ────────────────────────────────────────────────
    op.create_table(
        "royalty_records",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("book_id", sa.Uuid(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("units_sold", sa.Integer(), server_default="0", nullable=False),
        sa.Column("revenue", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("royalty", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_royalty_records_book_id", "royalty_records", ["book_id"])
    op.create_index("ix_royalty_records_platform", "royalty_records", ["platform"])
    op.create_index("ix_royalty_records_period_start", "royalty_records", ["period_start"])
    op.create_index("ix_royalty_records_period_end", "royalty_records", ["period_end"])
    op.create_index(
        "ix_royalty_records_deleted_at_partial", "royalty_records", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── portfolio_metrics ──────────────────────────────────────────────
    op.create_table(
        "portfolio_metrics",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_books", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_revenue", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("roi_by_book", postgresql.JSONB(), nullable=True),
        sa.Column("projections", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolio_metrics_org_id", "portfolio_metrics", ["org_id"])
    op.create_index("ix_portfolio_metrics_snapshot_date", "portfolio_metrics", ["snapshot_date"])
    op.create_index("ix_portfolio_metrics_roi_by_book_gin", "portfolio_metrics", ["roi_by_book"], postgresql_using="gin")
    op.create_index("ix_portfolio_metrics_projections_gin", "portfolio_metrics", ["projections"], postgresql_using="gin")
    op.create_index(
        "ix_portfolio_metrics_deleted_at_partial", "portfolio_metrics", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_portfolio_metrics_org_id_created_at", "portfolio_metrics", ["org_id", "created_at"])

    # ── ab_tests ───────────────────────────────────────────────────────
    op.create_table(
        "ab_tests",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("variants", postgresql.JSONB(), nullable=True),
        sa.Column("traffic_split", sa.Float(), nullable=True),
        sa.Column("status", ab_test_status, server_default="draft", nullable=False),
        sa.Column("results", postgresql.JSONB(), nullable=True),
        sa.Column("winner_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ab_tests_entity_type", "ab_tests", ["entity_type"])
    op.create_index("ix_ab_tests_entity_id", "ab_tests", ["entity_id"])
    op.create_index("ix_ab_tests_status", "ab_tests", ["status"])
    op.create_index("ix_ab_tests_variants_gin", "ab_tests", ["variants"], postgresql_using="gin")
    op.create_index("ix_ab_tests_results_gin", "ab_tests", ["results"], postgresql_using="gin")
    op.create_index(
        "ix_ab_tests_deleted_at_partial", "ab_tests", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── reports ────────────────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("parameters", postgresql.JSONB(), nullable=True),
        sa.Column("generated_url", sa.Text(), nullable=True),
        sa.Column("status", report_status, server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_org_id", "reports", ["org_id"])
    op.create_index("ix_reports_report_type", "reports", ["report_type"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_parameters_gin", "reports", ["parameters"], postgresql_using="gin")
    op.create_index(
        "ix_reports_deleted_at_partial", "reports", ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_reports_org_id_created_at", "reports", ["org_id", "created_at"])


def downgrade() -> None:
    # Drop all tables in reverse order of creation
    tables = [
        "reports", "ab_tests", "portfolio_metrics", "royalty_records",
        "analytics_events", "audit_trail", "agent_budgets", "agent_workflows",
        "agent_tasks", "agents", "reader_panels", "email_sequences",
        "launch_plans", "ad_creatives", "campaigns", "pricing_rules",
        "compliance_scans", "upload_validations", "listings",
        "publishing_accounts", "market_snapshots", "competitor_reviews",
        "competitor_books", "market_keywords", "market_categories",
        "content_assets", "writing_sessions", "style_profiles", "chapters",
        "manuscripts", "book_versions", "series", "books", "projects",
        "pen_names", "user_sessions", "api_keys", "users", "organizations",
    ]
    for table in tables:
        op.drop_table(table)

    # Drop all enum types
    enums = [
        "report_status", "ab_test_status", "actor_type", "budget_type",
        "agent_task_status", "permission_level", "agent_type",
        "launch_plan_status", "ad_creative_type", "campaign_status",
        "campaign_platform", "risk_level", "scan_type", "validation_type",
        "listing_status", "publishing_account_status", "publishing_platform",
        "asset_type", "chapter_status", "manuscript_status", "content_type",
        "series_status", "book_status", "book_format", "project_status",
        "project_type", "user_role", "subscription_status", "plan_tier",
    ]
    for enum_name in enums:
        postgresql.ENUM(name=enum_name).drop(op.get_bind(), checkfirst=True)
