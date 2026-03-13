"""Add specialty books tables (Children's, Coloring, Puzzle + shared)."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 25+ specialty book tables with enums and indexes."""

    # ─────────────────────────────────────────────────────────────────────
    # 1. CREATE ENUM TYPES
    # ─────────────────────────────────────────────────────────────────────

    enum_defs = [
        ("sp_book_type", ["childrens", "coloring", "puzzle"]),
        ("sp_book_status", ["draft", "in_progress", "review", "published", "archived"]),
        ("sp_page_type", ["cover", "front_matter", "content", "back_matter"]),
        ("sp_story_mode", ["original", "retelling", "educational", "interactive"]),
        ("sp_illustration_style", ["watercolor", "cartoon", "realistic", "flat", "mixed_media"]),
        ("sp_line_style", ["thin", "medium", "thick", "variable"]),
        ("sp_puzzle_type", ["word_search", "crossword", "maze", "sudoku", "scramble", "cryptogram"]),
        ("sp_difficulty_mode", ["easy", "medium", "hard", "mixed"]),
        ("sp_asset_type", ["illustration", "line_art", "vector", "audio", "text"]),
        ("sp_license_type", ["open", "commercial", "restricted", "custom"]),
        ("sp_batch_job_status", ["queued", "processing", "completed", "failed", "cancelled"]),
        ("sp_isbn_status", ["available", "assigned", "used"]),
        ("sp_preflight_status", ["pending", "passed", "failed", "warnings"]),
        ("sp_variant_type", ["large_print", "high_contrast", "dyslexia_friendly", "audio_described"]),
        ("sp_word_source_type", ["curated", "imported", "ai_generated", "public_domain"]),
        ("sp_content_type", ["image", "text", "puzzle_grid"]),
        ("sp_template_type", ["about_author", "also_by", "cta", "coloring_tips", "answer_key"]),
        ("sp_complexity", ["simple", "moderate", "detailed", "intricate"]),
        ("sp_clue_style", ["definition", "fill_in_blank", "synonym", "ai_generated"]),
        ("sp_fear_inventory", ["none", "mild", "moderate"]),
    ]

    for enum_name, values in enum_defs:
        vals = ", ".join(f"'{v}'" for v in values)
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
                    CREATE TYPE {enum_name} AS ENUM ({vals});
                END IF;
            END $$;
        """)

    # ─────────────────────────────────────────────────────────────────────
    # 2. CHILDREN'S BOOKS TABLES
    # ─────────────────────────────────────────────────────────────────────

    op.execute("""
        CREATE TABLE IF NOT EXISTS childrens_books (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            title VARCHAR(500) NOT NULL,
            age_range VARCHAR(20),
            page_count INTEGER,
            trim_size VARCHAR(30),
            illustration_style sp_illustration_style,
            color_palette JSONB,
            story_mode sp_story_mode,
            is_bilingual BOOLEAN DEFAULT FALSE,
            fear_inventory sp_fear_inventory,
            status sp_book_status DEFAULT 'draft',
            settings JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS childrens_book_pages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            book_id UUID NOT NULL REFERENCES childrens_books(id) ON DELETE CASCADE,
            page_number INTEGER NOT NULL,
            page_type sp_page_type DEFAULT 'content',
            layout VARCHAR(100),
            text_content TEXT,
            translated_text TEXT,
            text_font VARCHAR(100),
            text_size INTEGER,
            text_color VARCHAR(20),
            text_position JSONB,
            text_plate JSONB,
            illustration_prompt TEXT,
            illustration_url TEXT,
            illustration_model VARCHAR(100),
            illustration_seed INTEGER,
            settings JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS childrens_book_characters (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            book_id UUID NOT NULL REFERENCES childrens_books(id) ON DELETE CASCADE,
            name VARCHAR(200) NOT NULL,
            species VARCHAR(100),
            description TEXT,
            reference_images JSONB,
            auto_append BOOLEAN DEFAULT TRUE,
            clothing_rules JSONB,
            scale_rules JSONB,
            settings JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    # ─────────────────────────────────────────────────────────────────────
    # 3. COLORING BOOKS TABLES
    # ─────────────────────────────────────────────────────────────────────

    op.execute("""
        CREATE TABLE IF NOT EXISTS coloring_books (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            title VARCHAR(500) NOT NULL,
            audience VARCHAR(50),
            page_count INTEGER,
            trim_size VARCHAR(30),
            line_style sp_line_style,
            line_weight FLOAT,
            complexity sp_complexity,
            stroke_uniformity FLOAT,
            single_sided BOOLEAN DEFAULT TRUE,
            status sp_book_status DEFAULT 'draft',
            settings JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS coloring_book_pages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            book_id UUID NOT NULL REFERENCES coloring_books(id) ON DELETE CASCADE,
            page_number INTEGER NOT NULL,
            page_type sp_page_type DEFAULT 'content',
            illustration_prompt TEXT,
            illustration_url TEXT,
            cleaned_url TEXT,
            vectorized_url TEXT,
            illustration_model VARCHAR(100),
            illustration_seed INTEGER,
            qa_scores JSONB,
            qa_passed BOOLEAN,
            settings JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    # ─────────────────────────────────────────────────────────────────────
    # 4. PUZZLE BOOKS TABLES
    # ─────────────────────────────────────────────────────────────────────

    op.execute("""
        CREATE TABLE IF NOT EXISTS puzzle_books (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            title VARCHAR(500) NOT NULL,
            audience VARCHAR(50),
            puzzle_config JSONB,
            difficulty_mode sp_difficulty_mode,
            themes TEXT[],
            seasonal_theme VARCHAR(100),
            word_difficulty VARCHAR(50),
            clue_style sp_clue_style,
            status sp_book_status DEFAULT 'draft',
            settings JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS puzzles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            book_id UUID NOT NULL REFERENCES puzzle_books(id) ON DELETE CASCADE,
            puzzle_type sp_puzzle_type NOT NULL,
            puzzle_number INTEGER NOT NULL,
            theme VARCHAR(200),
            difficulty sp_difficulty_mode,
            difficulty_score FLOAT,
            grid_size VARCHAR(20),
            grid_data JSONB,
            word_list TEXT[],
            clues JSONB,
            solution_data JSONB,
            qa_scores JSONB,
            qa_passed BOOLEAN,
            settings JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    # ─────────────────────────────────────────────────────────────────────
    # 5. SHARED TABLES
    # ─────────────────────────────────────────────────────────────────────

    op.execute("""
        CREATE TABLE IF NOT EXISTS asset_provenance (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            book_type sp_book_type NOT NULL,
            book_id UUID NOT NULL,
            page_id UUID,
            asset_type sp_asset_type NOT NULL,
            model VARCHAR(100),
            prompt_text TEXT,
            prompt_hash VARCHAR(64),
            seed INTEGER,
            settings JSONB,
            generated_url TEXT,
            generation_time_ms INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS font_licenses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            font_name VARCHAR(200) NOT NULL,
            license_type sp_license_type NOT NULL,
            commercial_print BOOLEAN DEFAULT FALSE,
            source VARCHAR(255),
            license_url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            book_type sp_book_type NOT NULL,
            batch_config JSONB,
            budget_limit_cents INTEGER,
            spent_cents INTEGER DEFAULT 0,
            status sp_batch_job_status DEFAULT 'queued',
            volumes_total INTEGER DEFAULT 0,
            volumes_completed INTEGER DEFAULT 0,
            pages_total INTEGER DEFAULT 0,
            pages_completed INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS content_fingerprints (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            book_type sp_book_type NOT NULL,
            book_id UUID NOT NULL,
            page_id UUID,
            content_type sp_content_type NOT NULL,
            phash VARCHAR(64),
            data_hash VARCHAR(64),
            ngram_fingerprint TEXT,
            jaccard_vector JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS originality_reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            book_type sp_book_type NOT NULL,
            book_id UUID NOT NULL,
            overall_score FLOAT,
            component_scores JSONB,
            cross_book_similarities JSONB,
            spam_risk_score FLOAT,
            details JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS book_series (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            name VARCHAR(300) NOT NULL,
            book_type sp_book_type NOT NULL,
            naming_format VARCHAR(200),
            branding_config JSONB,
            branding_locked BOOLEAN DEFAULT FALSE,
            volume_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS back_matter_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            template_type sp_template_type NOT NULL,
            content TEXT,
            cta_url TEXT,
            qr_code_url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS isbn_pool (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            isbn VARCHAR(20) NOT NULL UNIQUE,
            publisher_name VARCHAR(300),
            assigned_to_book_type sp_book_type,
            assigned_to_book_id UUID,
            barcode_url TEXT,
            status sp_isbn_status DEFAULT 'available',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS distributor_preflights (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            book_type sp_book_type NOT NULL,
            book_id UUID NOT NULL,
            distributor VARCHAR(100) NOT NULL,
            status sp_preflight_status DEFAULT 'pending',
            checks JSONB,
            issues JSONB,
            exported_url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS book_bundles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            title VARCHAR(500) NOT NULL,
            book_type sp_book_type NOT NULL,
            volume_ids JSONB,
            series_id UUID REFERENCES book_series(id) ON DELETE SET NULL,
            config JSONB,
            total_pages INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS accessibility_variants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            source_book_type sp_book_type NOT NULL,
            source_book_id UUID NOT NULL,
            variant_type sp_variant_type NOT NULL,
            variant_book_id UUID,
            settings JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS word_list_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL,
            name VARCHAR(300) NOT NULL,
            source_type sp_word_source_type NOT NULL,
            license VARCHAR(100),
            word_count INTEGER DEFAULT 0,
            dictionary JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    # ─────────────────────────────────────────────────────────────────────
    # 6. CREATE INDEXES
    # ─────────────────────────────────────────────────────────────────────

    indexes = [
        # Children's books
        ("ix_childrens_books_org_status", "childrens_books", "org_id, status"),
        ("ix_childrens_books_status", "childrens_books", "status"),
        ("ix_cb_pages_org_status", "childrens_book_pages", "org_id, page_type"),
        ("ix_cb_pages_book_id", "childrens_book_pages", "book_id"),
        ("ix_cb_chars_org_id", "childrens_book_characters", "org_id"),
        ("ix_cb_chars_book_id", "childrens_book_characters", "book_id"),

        # Coloring books
        ("ix_coloring_books_org_status", "coloring_books", "org_id, status"),
        ("ix_coloring_books_status", "coloring_books", "status"),
        ("ix_clr_pages_org_id", "coloring_book_pages", "org_id"),
        ("ix_clr_pages_book_id", "coloring_book_pages", "book_id"),

        # Puzzle books
        ("ix_puzzle_books_org_status", "puzzle_books", "org_id, status"),
        ("ix_puzzle_books_status", "puzzle_books", "status"),
        ("ix_puzzles_org_id", "puzzles", "org_id"),
        ("ix_puzzles_book_id", "puzzles", "book_id"),
        ("ix_puzzles_type", "puzzles", "puzzle_type"),

        # Shared tables
        ("ix_asset_prov_org_book_type", "asset_provenance", "org_id, book_type"),
        ("ix_asset_prov_book_id", "asset_provenance", "book_id"),
        ("ix_asset_prov_prompt_hash", "asset_provenance", "prompt_hash"),
        ("ix_font_licenses_name", "font_licenses", "font_name"),
        ("ix_batch_jobs_org_status", "batch_jobs", "org_id, status"),
        ("ix_batch_jobs_status", "batch_jobs", "status"),
        ("ix_content_fp_org_book_type", "content_fingerprints", "org_id, book_type"),
        ("ix_content_fp_book_id", "content_fingerprints", "book_id"),
        ("ix_content_fp_phash", "content_fingerprints", "phash"),
        ("ix_content_fp_data_hash", "content_fingerprints", "data_hash"),
        ("ix_orig_reports_org_book_type", "originality_reports", "org_id, book_type"),
        ("ix_orig_reports_book_id", "originality_reports", "book_id"),
        ("ix_book_series_org_type", "book_series", "org_id, book_type"),
        ("ix_back_matter_org_type", "back_matter_templates", "org_id, template_type"),
        ("ix_isbn_pool_org_status", "isbn_pool", "org_id, status"),
        ("ix_isbn_pool_isbn", "isbn_pool", "isbn"),
        ("ix_dist_preflight_org_status", "distributor_preflights", "org_id, status"),
        ("ix_dist_preflight_book_id", "distributor_preflights", "book_id"),
        ("ix_book_bundles_org_type", "book_bundles", "org_id, book_type"),
        ("ix_book_bundles_series_id", "book_bundles", "series_id"),
        ("ix_access_var_org_type", "accessibility_variants", "org_id, source_book_type"),
        ("ix_access_var_source_book", "accessibility_variants", "source_book_id"),
        ("ix_word_list_org_type", "word_list_sources", "org_id, source_type"),
    ]

    for idx_name, table, columns in indexes:
        op.execute(f"""
            CREATE INDEX IF NOT EXISTS {idx_name}
            ON {table}({columns})
        """)


def downgrade() -> None:
    """Drop all specialty book tables and enums."""

    # ─────────────────────────────────────────────────────────────────────
    # 1. DROP TABLES (reverse dependency order)
    # ─────────────────────────────────────────────────────────────────────

    tables = [
        "word_list_sources",
        "accessibility_variants",
        "book_bundles",
        "distributor_preflights",
        "isbn_pool",
        "back_matter_templates",
        "book_series",
        "originality_reports",
        "content_fingerprints",
        "batch_jobs",
        "font_licenses",
        "asset_provenance",
        "puzzles",
        "puzzle_books",
        "coloring_book_pages",
        "coloring_books",
        "childrens_book_characters",
        "childrens_book_pages",
        "childrens_books",
    ]

    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    # ─────────────────────────────────────────────────────────────────────
    # 2. DROP ENUM TYPES
    # ─────────────────────────────────────────────────────────────────────

    enums = [
        "sp_fear_inventory",
        "sp_clue_style",
        "sp_complexity",
        "sp_template_type",
        "sp_content_type",
        "sp_word_source_type",
        "sp_variant_type",
        "sp_preflight_status",
        "sp_isbn_status",
        "sp_batch_job_status",
        "sp_license_type",
        "sp_asset_type",
        "sp_difficulty_mode",
        "sp_puzzle_type",
        "sp_line_style",
        "sp_illustration_style",
        "sp_story_mode",
        "sp_page_type",
        "sp_book_status",
        "sp_book_type",
    ]

    for enum_name in enums:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
