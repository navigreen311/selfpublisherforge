"""Add specialty books module tables (children's, coloring, puzzle + shared).

Revision ID: specialty_001
Revises: None (standalone)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "specialty_001"
down_revision = None
branch_labels = ("specialty",)
depends_on = None


def upgrade() -> None:
    # ── Enum types ────────────────────────────────────────────────────
    age_range = sa.Enum(
        "baby", "toddler", "preschool", "early_reader", "chapter_book", "middle_grade",
        name="age_range",
    )
    illustration_style = sa.Enum(
        "watercolor", "cartoon", "digital_painting", "flat_vector",
        "pencil_sketch", "collage", "storybook_classic", "anime",
        name="illustration_style",
    )
    color_palette = sa.Enum(
        "bright", "pastel", "earthy", "monochrome", "neon", "warm", "cool", "muted",
        name="color_palette",
    )
    story_mode = sa.Enum(
        "ai_generated", "manual", "hybrid",
        name="story_mode",
    )
    bilingual_layout = sa.Enum(
        "side_by_side", "top_bottom", "alternating_pages",
        name="bilingual_layout",
    )
    fear_intensity = sa.Enum(
        "none", "mild", "moderate",
        name="fear_intensity",
    )
    page_layout = sa.Enum(
        "full_bleed_image", "image_top_text_bottom", "image_left_text_right",
        "image_right_text_left", "text_overlay", "vignette", "split_panel",
        name="page_layout",
    )
    text_position = sa.Enum(
        "top", "bottom", "left", "right", "center", "overlay",
        name="text_position",
    )
    book_status = sa.Enum(
        "draft", "in_progress", "review", "approved", "exported", "published",
        name="book_status",
    )
    audience = sa.Enum(
        "kids", "teens", "adults", "seniors",
        name="audience",
    )
    line_style = sa.Enum(
        "fine", "medium", "bold", "sketchy", "clean", "whimsical",
        name="line_style",
    )
    coloring_page_type = sa.Enum(
        "illustration", "pattern", "mandala", "scene", "border", "title_page",
        name="coloring_page_type",
    )
    puzzle_type = sa.Enum(
        "word_search", "crossword", "maze", "sudoku", "word_scramble",
        "cryptogram", "number_search", "word_connect",
        name="puzzle_type",
    )
    difficulty = sa.Enum(
        "easy", "medium", "hard", "expert",
        name="difficulty",
    )
    difficulty_mode = sa.Enum(
        "fixed", "progressive", "random", "chapter_based",
        name="difficulty_mode",
    )
    clue_style = sa.Enum(
        "standard", "trivia", "fill_in_blank", "thematic",
        name="clue_style",
    )
    word_difficulty = sa.Enum(
        "simple", "intermediate", "advanced", "expert",
        name="word_difficulty",
    )
    answer_key_position = sa.Enum(
        "back_of_book", "next_page", "same_page_upside_down", "none",
        name="answer_key_position",
    )
    book_type = sa.Enum(
        "childrens", "coloring", "puzzle",
        name="book_type",
    )
    asset_type = sa.Enum(
        "illustration", "line_art", "puzzle_grid", "cover", "reference_image",
        name="asset_type",
    )
    batch_status = sa.Enum(
        "pending", "running", "paused", "completed", "failed", "cancelled",
        name="batch_status",
    )
    isbn_status = sa.Enum(
        "available", "assigned", "used",
        name="isbn_status",
    )
    distributor_name = sa.Enum(
        "kdp", "ingram_spark", "bn_press",
        name="distributor_name",
    )
    preflight_status = sa.Enum(
        "pending", "passed", "failed", "warnings",
        name="preflight_status",
    )
    variant_type = sa.Enum(
        "dyslexia_friendly", "large_print", "high_contrast",
        name="variant_type",
    )
    template_type = sa.Enum(
        "about_author", "also_by", "review_request", "newsletter_signup", "custom",
        name="template_type",
    )
    license_type = sa.Enum(
        "open_source", "commercial", "personal", "sil_ofl",
        name="license_type",
    )
    word_list_source_type = sa.Enum(
        "built_in", "user_uploaded", "api", "curated",
        name="word_list_source_type",
    )

    # ── book_series (must come before coloring_books & book_bundles FK) ──
    op.create_table(
        "book_series",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("book_type", book_type, nullable=False),
        sa.Column("naming_format", sa.String(200), nullable=True),
        sa.Column("branding_config", JSONB(), nullable=True),
        sa.Column("branding_locked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("volume_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── childrens_books ──────────────────────────────────────────────
    op.create_table(
        "childrens_books",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("subtitle", sa.String(300), nullable=True),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("age_range", age_range, nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("trim_size", sa.String(20), nullable=False, server_default="8.5x8.5"),
        sa.Column("illustration_style", illustration_style, nullable=False),
        sa.Column("color_palette", color_palette, nullable=False),
        sa.Column("story_mode", story_mode, nullable=False),
        sa.Column("is_bilingual", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bilingual_language", sa.String(50), nullable=True),
        sa.Column("bilingual_layout", bilingual_layout, nullable=True),
        sa.Column("fear_intensity", fear_intensity, nullable=False),
        sa.Column("status", book_status, nullable=False, server_default="draft"),
        sa.Column("qa_score", sa.Float(), nullable=True),
    )

    # ── childrens_book_pages ─────────────────────────────────────────
    op.create_table(
        "childrens_book_pages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("book_id", UUID(as_uuid=True), sa.ForeignKey("childrens_books.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("page_type", sa.String(30), nullable=False, server_default="story"),
        sa.Column("layout", page_layout, nullable=False),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("translated_text", sa.Text(), nullable=True),
        sa.Column("text_font", sa.String(100), nullable=True),
        sa.Column("text_size", sa.Integer(), nullable=True),
        sa.Column("text_color", sa.String(20), nullable=True),
        sa.Column("text_position", text_position, nullable=True),
        sa.Column("text_plate_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("illustration_prompt", sa.Text(), nullable=True),
        sa.Column("illustration_url", sa.Text(), nullable=True),
        sa.Column("illustration_model", sa.String(50), nullable=True),
        sa.Column("illustration_seed", sa.String(50), nullable=True),
        sa.Column("contrast_score", sa.Float(), nullable=True),
        sa.Column("gutter_safe", sa.Boolean(), nullable=True),
    )

    # ── childrens_book_characters ────────────────────────────────────
    op.create_table(
        "childrens_book_characters",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("book_id", UUID(as_uuid=True), sa.ForeignKey("childrens_books.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("species", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_images", JSONB(), nullable=True),
        sa.Column("auto_append", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("clothing_rules", JSONB(), nullable=True),
        sa.Column("scale_rules", JSONB(), nullable=True),
        sa.Column("setting_rules", JSONB(), nullable=True),
        sa.Column("time_rules", JSONB(), nullable=True),
    )

    # ── coloring_books ───────────────────────────────────────────────
    op.create_table(
        "coloring_books",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("audience", audience, nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("trim_size", sa.String(20), nullable=False, server_default="8.5x11"),
        sa.Column("line_style", line_style, nullable=False),
        sa.Column("line_weight", sa.Float(), nullable=False, server_default="2.0"),
        sa.Column("complexity", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("stroke_uniformity", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("single_sided", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("series_id", UUID(as_uuid=True), sa.ForeignKey("book_series.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("status", book_status, nullable=False, server_default="draft"),
        sa.Column("qa_score", sa.Float(), nullable=True),
    )

    # ── coloring_book_pages ──────────────────────────────────────────
    op.create_table(
        "coloring_book_pages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("book_id", UUID(as_uuid=True), sa.ForeignKey("coloring_books.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("page_type", coloring_page_type, nullable=False),
        sa.Column("illustration_prompt", sa.Text(), nullable=True),
        sa.Column("illustration_url", sa.Text(), nullable=True),
        sa.Column("cleaned_url", sa.Text(), nullable=True),
        sa.Column("vectorized_url", sa.Text(), nullable=True),
        sa.Column("illustration_model", sa.String(50), nullable=True),
        sa.Column("illustration_seed", sa.String(50), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("closed_shapes_ok", sa.Boolean(), nullable=True),
        sa.Column("speck_free", sa.Boolean(), nullable=True),
        sa.Column("stroke_uniform", sa.Boolean(), nullable=True),
        sa.Column("ink_density_ok", sa.Boolean(), nullable=True),
        sa.Column("bg_pure_white", sa.Boolean(), nullable=True),
    )

    # ── puzzle_books ─────────────────────────────────────────────────
    op.create_table(
        "puzzle_books",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("audience", audience, nullable=False),
        sa.Column("puzzle_config", JSONB(), nullable=True),
        sa.Column("difficulty_mode", difficulty_mode, nullable=False),
        sa.Column("themes", JSONB(), nullable=True),
        sa.Column("seasonal_theme", sa.String(50), nullable=True),
        sa.Column("word_difficulty", word_difficulty, nullable=True),
        sa.Column("clue_style", clue_style, nullable=True),
        sa.Column("answer_key_position", answer_key_position, nullable=False),
        sa.Column("has_toc", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_hints", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("layout_mode", sa.String(30), nullable=True),
        sa.Column("status", book_status, nullable=False, server_default="draft"),
        sa.Column("qa_score", sa.Float(), nullable=True),
    )

    # ── puzzles ──────────────────────────────────────────────────────
    op.create_table(
        "puzzles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("book_id", UUID(as_uuid=True), sa.ForeignKey("puzzle_books.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("puzzle_type", puzzle_type, nullable=False),
        sa.Column("puzzle_number", sa.Integer(), nullable=False),
        sa.Column("theme", sa.String(100), nullable=True),
        sa.Column("difficulty", difficulty, nullable=False),
        sa.Column("difficulty_score", sa.Float(), nullable=True),
        sa.Column("grid_size", sa.String(20), nullable=True),
        sa.Column("grid_data", JSONB(), nullable=True),
        sa.Column("word_list", JSONB(), nullable=True),
        sa.Column("clues", JSONB(), nullable=True),
        sa.Column("answer_data", JSONB(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_unique_solution", sa.Boolean(), nullable=True),
    )

    # ── asset_provenance ─────────────────────────────────────────────
    op.create_table(
        "asset_provenance",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_type", book_type, nullable=False),
        sa.Column("book_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("page_id", UUID(as_uuid=True), nullable=True),
        sa.Column("asset_type", asset_type, nullable=False),
        sa.Column("model", sa.String(50), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("seed", sa.String(50), nullable=True),
        sa.Column("settings", JSONB(), nullable=True),
        sa.Column("generation_time_ms", sa.Integer(), nullable=True),
        sa.Column("cost_cents", sa.Integer(), nullable=True),
    )

    # ── font_licenses ────────────────────────────────────────────────
    op.create_table(
        "font_licenses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("font_name", sa.String(200), nullable=False),
        sa.Column("license_type", license_type, nullable=False),
        sa.Column("commercial_print", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("license_url", sa.Text(), nullable=True),
    )

    # ── batch_jobs ───────────────────────────────────────────────────
    op.create_table(
        "batch_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_type", book_type, nullable=False),
        sa.Column("batch_config", JSONB(), nullable=True),
        sa.Column("budget_limit_cents", sa.Integer(), nullable=True),
        sa.Column("spent_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", batch_status, nullable=False, server_default="pending"),
        sa.Column("volumes_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("volumes_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_completed", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── content_fingerprints ─────────────────────────────────────────
    op.create_table(
        "content_fingerprints",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_type", book_type, nullable=False),
        sa.Column("book_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("page_id", UUID(as_uuid=True), nullable=True),
        sa.Column("content_type", sa.String(30), nullable=False),
        sa.Column("phash", sa.String(64), nullable=True),
        sa.Column("data_hash", sa.String(64), nullable=True),
        sa.Column("ngram_fingerprint", sa.Text(), nullable=True),
        sa.Column("jaccard_vector", JSONB(), nullable=True),
    )

    # ── originality_reports ──────────────────────────────────────────
    op.create_table(
        "originality_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("book_type", book_type, nullable=False),
        sa.Column("book_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("component_scores", JSONB(), nullable=True),
        sa.Column("cross_book_similarities", JSONB(), nullable=True),
        sa.Column("spam_risk_score", sa.Float(), nullable=True),
    )

    # ── back_matter_templates ────────────────────────────────────────
    op.create_table(
        "back_matter_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("template_type", template_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("cta_url", sa.Text(), nullable=True),
        sa.Column("qr_code_url", sa.Text(), nullable=True),
    )

    # ── isbn_pool ────────────────────────────────────────────────────
    op.create_table(
        "isbn_pool",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("isbn", sa.String(20), nullable=False, unique=True, index=True),
        sa.Column("publisher_name", sa.String(300), nullable=True),
        sa.Column("assigned_to_book_type", sa.String(20), nullable=True),
        sa.Column("assigned_to_book_id", UUID(as_uuid=True), nullable=True),
        sa.Column("barcode_url", sa.Text(), nullable=True),
        sa.Column("status", isbn_status, nullable=False, server_default="available"),
    )

    # ── distributor_preflights ───────────────────────────────────────
    op.create_table(
        "distributor_preflights",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("book_type", book_type, nullable=False),
        sa.Column("book_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("distributor", distributor_name, nullable=False),
        sa.Column("status", preflight_status, nullable=False, server_default="pending"),
        sa.Column("checks", JSONB(), nullable=True),
        sa.Column("issues", JSONB(), nullable=True),
        sa.Column("exported_url", sa.Text(), nullable=True),
    )

    # ── book_bundles ─────────────────────────────────────────────────
    op.create_table(
        "book_bundles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("book_type", book_type, nullable=False),
        sa.Column("volume_ids", JSONB(), nullable=True),
        sa.Column("series_id", UUID(as_uuid=True), sa.ForeignKey("book_series.id", ondelete="SET NULL"), nullable=True),
        sa.Column("config", JSONB(), nullable=True),
        sa.Column("total_pages", sa.Integer(), nullable=True),
    )

    # ── accessibility_variants ───────────────────────────────────────
    op.create_table(
        "accessibility_variants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_book_type", book_type, nullable=False),
        sa.Column("source_book_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("variant_type", variant_type, nullable=False),
        sa.Column("variant_book_id", UUID(as_uuid=True), nullable=True),
        sa.Column("settings", JSONB(), nullable=True),
    )

    # ── word_list_sources ────────────────────────────────────────────
    op.create_table(
        "word_list_sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("source_type", word_list_source_type, nullable=False),
        sa.Column("license", sa.String(100), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("dictionary", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("word_list_sources")
    op.drop_table("accessibility_variants")
    op.drop_table("book_bundles")
    op.drop_table("distributor_preflights")
    op.drop_table("isbn_pool")
    op.drop_table("back_matter_templates")
    op.drop_table("originality_reports")
    op.drop_table("content_fingerprints")
    op.drop_table("batch_jobs")
    op.drop_table("font_licenses")
    op.drop_table("asset_provenance")
    op.drop_table("puzzles")
    op.drop_table("puzzle_books")
    op.drop_table("coloring_book_pages")
    op.drop_table("coloring_books")
    op.drop_table("childrens_book_characters")
    op.drop_table("childrens_book_pages")
    op.drop_table("childrens_books")
    op.drop_table("book_series")

    # Drop enum types
    for enum_name in [
        "word_list_source_type", "variant_type", "template_type",
        "preflight_status", "distributor_name", "isbn_status",
        "batch_status", "asset_type", "book_type",
        "answer_key_position", "word_difficulty", "clue_style",
        "difficulty_mode", "difficulty", "puzzle_type",
        "coloring_page_type", "line_style", "audience",
        "book_status", "text_position", "page_layout",
        "fear_intensity", "bilingual_layout", "story_mode",
        "color_palette", "illustration_style", "age_range",
        "license_type",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
