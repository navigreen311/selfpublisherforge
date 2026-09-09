"""Tests for accessibility pack and layout protection systems.

Uses an in-memory SQLite DB. Does NOT import app.main to avoid router
import chain failures.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.database import Base


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(PG_ARRAY, "sqlite")
def _compile_array_sqlite(element, compiler, **kw):
    return "TEXT"


@compiles(PG_UUID, "sqlite")
def _compile_pg_uuid_sqlite(element, compiler, **kw):
    return "CHAR(32)"


_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_TestSession = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


def _is_pg_only_index(idx) -> bool:
    dialect_opts = getattr(idx, "dialect_options", {})
    pg_opts = dialect_opts.get("postgresql", {})
    if pg_opts.get("using") or pg_opts.get("where") is not None or pg_opts.get("ops"):
        return True
    kw = getattr(idx, "kwargs", {})
    return bool(kw.get("postgresql_using") or kw.get("postgresql_where") is not None or kw.get("postgresql_ops"))


@event.listens_for(Base.metadata, "before_create")
def _patch_for_sqlite(target, connection, **kw):
    if connection.dialect.name != "sqlite":
        return
    for table in target.tables.values():
        for column in table.columns:
            if column.server_default is not None:
                sd = column.server_default
                sd_text = ""
                if hasattr(sd, "arg"):
                    sd_text = str(getattr(sd.arg, "text", sd.arg))
                if any(fn in sd_text.lower() for fn in ["gen_random_uuid", "uuid_generate"]):
                    column.server_default = None
        pg_indexes = [idx for idx in table.indexes if _is_pg_only_index(idx)]
        for idx in pg_indexes:
            table.indexes.discard(idx)
        seen: set[str] = set()
        dupes = []
        for idx in table.indexes:
            if idx.name in seen:
                dupes.append(idx)
            else:
                seen.add(idx.name)
        for idx in dupes:
            table.indexes.discard(idx)


import app.modules.specialty_books.models_accessibility

ORG_ID = uuid.uuid4()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with _TestSession() as session:
        yield session
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


from app.modules.specialty_books import service_accessibility as acc_svc
from app.modules.specialty_books import service_layout_protection as layout_svc
from app.modules.specialty_books.models_accessibility import AccessibilityVariant
from app.modules.specialty_books.service_accessibility import (
    DYSLEXIA_BACKGROUND_COLOR,
    DYSLEXIA_FONT_FAMILY,
    DYSLEXIA_LETTER_SPACING_PCT,
    DYSLEXIA_LINE_SPACING,
    DYSLEXIA_TEXT_ALIGNMENT,
    HIGH_CONTRAST_BG,
    HIGH_CONTRAST_FG,
    LARGE_PRINT_MIN_FONT_SIZE,
    VARIANT_DYSLEXIA,
    VARIANT_HIGH_CONTRAST,
    VARIANT_LARGE_PRINT,
    WCAG_AAA_CONTRAST,
    calculate_contrast_ratio,
)
from app.modules.specialty_books.service_layout_protection import (
    SEVERITY_CAUTION,
    SEVERITY_CRITICAL,
    SEVERITY_OK,
    SEVERITY_WARNING,
    _classify_zone,
    _determine_severity,
    _parse_trim_size,
)

# ===========================================================================
# Unit tests (no DB)
# ===========================================================================


class TestContrastRatio:
    def test_black_on_white_is_21(self):
        assert calculate_contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0, abs=0.1)

    def test_white_on_white_is_1(self):
        assert calculate_contrast_ratio("#FFFFFF", "#FFFFFF") == pytest.approx(1.0, abs=0.01)

    def test_symmetric(self):
        r1 = calculate_contrast_ratio("#000000", "#FFFFFF")
        r2 = calculate_contrast_ratio("#FFFFFF", "#000000")
        assert r1 == pytest.approx(r2, abs=0.001)

    def test_wcag_aaa_black_white(self):
        assert calculate_contrast_ratio("#000000", "#FFFFFF") >= WCAG_AAA_CONTRAST

    def test_invalid_hex_raises(self):
        with pytest.raises(ValueError):
            calculate_contrast_ratio("#GGG", "#FFFFFF")


class TestZoneClassification:
    def test_center_is_safe(self):
        assert _classify_zone(4.0, 5.0, 8.5, 11.0) == "safe"

    def test_near_outer_edge_is_trim_danger(self):
        assert _classify_zone(0.15, 5.0, 8.5, 11.0, is_left_page=True) == "trim_danger"

    def test_near_gutter_is_gutter(self):
        assert _classify_zone(8.2, 5.0, 8.5, 11.0, is_left_page=True) == "gutter"

    def test_beyond_trim_is_bleed(self):
        assert _classify_zone(-0.1, 5.0, 8.5, 11.0) == "bleed"

    def test_near_top_edge_is_caution(self):
        assert _classify_zone(4.0, 0.35, 8.5, 11.0) == "caution"


class TestGutterSeverity:
    def test_very_close_is_critical(self):
        assert _determine_severity(0.1) == SEVERITY_CRITICAL

    def test_moderate_is_warning(self):
        assert _determine_severity(0.35) == SEVERITY_WARNING

    def test_far_is_ok(self):
        assert _determine_severity(1.0) == SEVERITY_OK

    def test_caution_range(self):
        assert _determine_severity(0.6) == SEVERITY_CAUTION


class TestTrimSizeParsing:
    def test_standard_sizes(self):
        assert _parse_trim_size("8.5x11") == (8.5, 11.0)
        assert _parse_trim_size("6x9") == (6.0, 9.0)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            _parse_trim_size("invalid")


# ===========================================================================
# 11.1  Dyslexia-Friendly
# ===========================================================================


@pytest.mark.asyncio
async def test_dyslexia_friendly_settings(db_session: AsyncSession):
    book_id = uuid.uuid4()
    result = await acc_svc.generate_dyslexia_friendly(db_session, "coloring", book_id, ORG_ID)
    assert result["variant_type"] == VARIANT_DYSLEXIA
    assert result["variant_book_id"] != book_id
    s = result["settings"]
    assert s["font_family"] == DYSLEXIA_FONT_FAMILY
    assert s["line_spacing"] == DYSLEXIA_LINE_SPACING
    assert s["letter_spacing_pct"] == DYSLEXIA_LETTER_SPACING_PCT
    assert s["text_alignment"] == DYSLEXIA_TEXT_ALIGNMENT
    assert s["background_color"] == DYSLEXIA_BACKGROUND_COLOR


# ===========================================================================
# 11.2  Large Print
# ===========================================================================


@pytest.mark.asyncio
async def test_large_print_18pt_minimum(db_session: AsyncSession):
    book_id = uuid.uuid4()
    result = await acc_svc.generate_large_print(db_session, "coloring", book_id, ORG_ID)
    assert result["settings"]["min_font_size"] >= LARGE_PRINT_MIN_FONT_SIZE


@pytest.mark.asyncio
async def test_large_print_rejects_small_font(db_session: AsyncSession):
    book_id = uuid.uuid4()
    result = await acc_svc.generate_large_print(db_session, "coloring", book_id, ORG_ID, settings={"min_font_size": 14})
    assert result["settings"]["min_font_size"] >= LARGE_PRINT_MIN_FONT_SIZE


@pytest.mark.asyncio
async def test_large_print_wcag_aaa(db_session: AsyncSession):
    book_id = uuid.uuid4()
    result = await acc_svc.generate_large_print(db_session, "coloring", book_id, ORG_ID)
    assert result["settings"]["actual_contrast_ratio"] >= WCAG_AAA_CONTRAST
    assert result["settings"]["wcag_aaa_met"] is True


# ===========================================================================
# 11.3  High Contrast
# ===========================================================================


@pytest.mark.asyncio
async def test_high_contrast_pure_black_white(db_session: AsyncSession):
    book_id = uuid.uuid4()
    result = await acc_svc.generate_high_contrast(db_session, "coloring", book_id, ORG_ID)
    assert result["settings"]["foreground_color"] == HIGH_CONTRAST_FG
    assert result["settings"]["background_color"] == HIGH_CONTRAST_BG
    assert result["settings"]["actual_contrast_ratio"] == pytest.approx(21.0, abs=0.1)


@pytest.mark.asyncio
async def test_high_contrast_bold_elements(db_session: AsyncSession):
    book_id = uuid.uuid4()
    result = await acc_svc.generate_high_contrast(db_session, "coloring", book_id, ORG_ID)
    assert result["settings"]["bold_numbers"] is True
    assert result["settings"]["bold_instructions"] is True
    assert result["settings"]["min_grid_line_px"] >= 2


# ===========================================================================
# Compliance
# ===========================================================================


@pytest.mark.asyncio
async def test_wcag_aaa_compliance(db_session: AsyncSession):
    book_id = uuid.uuid4()
    report = await acc_svc.check_accessibility_compliance(db_session, "coloring", book_id, ORG_ID, standard="WCAG_AAA")
    assert report["standard"] == "WCAG AAA"
    assert report["total_checks"] >= 3
    contrast_check = next(c for c in report["checks"] if c["name"] == "contrast_ratio")
    assert contrast_check["passed"] is True


@pytest.mark.asyncio
async def test_wcag_aa_compliance(db_session: AsyncSession):
    book_id = uuid.uuid4()
    report = await acc_svc.check_accessibility_compliance(db_session, "coloring", book_id, ORG_ID, standard="WCAG_AA")
    assert report["standard"] == "WCAG AA"
    assert report["total_checks"] >= 3


# ===========================================================================
# Variant storage
# ===========================================================================


@pytest.mark.asyncio
async def test_variants_stored_in_db(db_session: AsyncSession):
    book_id = uuid.uuid4()
    await acc_svc.generate_dyslexia_friendly(db_session, "coloring", book_id, ORG_ID)
    await acc_svc.generate_large_print(db_session, "coloring", book_id, ORG_ID)
    await acc_svc.generate_high_contrast(db_session, "coloring", book_id, ORG_ID)
    result = await db_session.execute(
        select(AccessibilityVariant).where(AccessibilityVariant.source_book_id == book_id)
    )
    variants = result.scalars().all()
    assert len(variants) == 3
    assert {v.variant_type for v in variants} == {VARIANT_DYSLEXIA, VARIANT_LARGE_PRINT, VARIANT_HIGH_CONTRAST}


@pytest.mark.asyncio
async def test_original_unchanged(db_session: AsyncSession):
    """Variants do not modify the source book_id record."""
    book_id = uuid.uuid4()
    r1 = await acc_svc.generate_dyslexia_friendly(db_session, "coloring", book_id, ORG_ID)
    assert r1["source_book_id"] == book_id
    assert r1["variant_book_id"] != book_id


# ===========================================================================
# 10.1  Safe-Zone Heatmap
# ===========================================================================


@pytest.mark.asyncio
async def test_heatmap_classifies_zones(db_session: AsyncSession):
    book_id, page_id = uuid.uuid4(), uuid.uuid4()
    result = await layout_svc.generate_safe_zone_heatmap(db_session, "coloring", book_id, page_id, ORG_ID)
    assert result["book_id"] == book_id
    assert result["total_elements"] > 0
    for elem in result["detected_elements"]:
        assert elem["zone"] in ("bleed", "trim_danger", "caution", "safe", "gutter")


# ===========================================================================
# 10.2  Gutter Collision
# ===========================================================================


@pytest.mark.asyncio
async def test_gutter_detects_near_spine(db_session: AsyncSession):
    book_id = uuid.uuid4()
    result = await layout_svc.check_gutter_collisions(db_session, "coloring", book_id, ORG_ID)
    assert result["total_collisions"] > 0
    close = [c for c in result["collisions"] if c["distance_from_gutter"] < 0.5]
    assert len(close) > 0
    for c in result["collisions"]:
        assert c["severity"] in (SEVERITY_CRITICAL, SEVERITY_WARNING, SEVERITY_CAUTION)
        assert "auto_shift_available" in c


# ===========================================================================
# 10.3  Auto-Reflow
# ===========================================================================


@pytest.mark.asyncio
async def test_reflow_adjusts_margins(db_session: AsyncSession):
    book_id = uuid.uuid4()
    result = await layout_svc.generate_reflow(db_session, "coloring", book_id, ORG_ID, "6x9")
    assert result["new_book_id"] != book_id
    report = result["reflow_report"]
    assert report["content_scale_factor"] < 1.0
    assert report["text_elements_repositioned"] > 0
    assert "gutter_safety_check" in report


@pytest.mark.asyncio
async def test_reflow_invalid_trim(db_session: AsyncSession):
    book_id = uuid.uuid4()
    with pytest.raises(ValueError, match="Unrecognized trim size"):
        await layout_svc.generate_reflow(db_session, "coloring", book_id, ORG_ID, "invalid")
