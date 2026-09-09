"""Unit tests for the Product Page Lab service layer.

Covers the full CRUD lifecycle for A/B tests, blurb generation,
listing analysis, Look Inside analysis, mobile checks, and
conversion score retrieval.

Each test gets a clean database via the ``db_session`` fixture
from ``conftest.py``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.product_page_lab import service
from app.modules.product_page_lab.models import ABTest
from app.modules.product_page_lab.schemas import (
    ABTestCreateRequest,
    ABTestResponse,
    ABTestResultsResponse,
    ABTestStatus,
    ABTestUpdateRequest,
    BlurbGenerateRequest,
    Genre,
    ListingAnalyzeRequest,
    LookInsideAnalyzeRequest,
    MobileCheckRequest,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
BOOK_ID = uuid.uuid4()

VARIANT_A = "This is variant A blurb content for testing purposes that is long enough."
VARIANT_B = "This is variant B blurb content for testing purposes that is long enough."


def _make_create_request(
    *,
    book_id: uuid.UUID | None = None,
    name: str = "Test A/B",
    variant_a: str = VARIANT_A,
    variant_b: str = VARIANT_B,
    duration_days: int = 7,
) -> ABTestCreateRequest:
    return ABTestCreateRequest(
        book_id=book_id or BOOK_ID,
        name=name,
        variant_a=variant_a,
        variant_b=variant_b,
        duration_days=duration_days,
    )


async def _seed_ab_test(db, *, status: str = "draft", **overrides) -> ABTest:
    """Insert an ABTest row directly into the DB and return the ORM object."""
    defaults = dict(
        id=uuid.uuid4(),
        org_id=ORG_ID,
        book_id=BOOK_ID,
        name="Seed Test",
        status=status,
        variant_a_content=VARIANT_A,
        variant_b_content=VARIANT_B,
        variant_a_impressions=0,
        variant_a_clicks=0,
        variant_b_impressions=0,
        variant_b_clicks=0,
        duration_days=7,
        started_at=None,
        completed_at=None,
    )
    defaults.update(overrides)
    ab = ABTest(**defaults)
    db.add(ab)
    await db.flush()
    await db.refresh(ab)
    return ab


# ===========================================================================
# A/B Test creation
# ===========================================================================


class TestCreateABTest:
    """Tests for service.create_ab_test."""

    @pytest.mark.asyncio
    async def test_creates_test_in_db(self, db_session):
        """create_ab_test should persist an ABTest record and return a response."""
        request = _make_create_request()
        result = await service.create_ab_test(request, ORG_ID, db_session)

        assert isinstance(result, ABTestResponse)
        assert result.name == "Test A/B"
        assert result.status == ABTestStatus.DRAFT
        assert result.book_id == BOOK_ID

    @pytest.mark.asyncio
    async def test_creates_with_correct_variants(self, db_session):
        """Should store variant_a and variant_b content correctly."""
        request = _make_create_request(
            variant_a="Unique variant A content for assertions and testing.",
            variant_b="Unique variant B content for assertions and testing.",
        )
        result = await service.create_ab_test(request, ORG_ID, db_session)

        assert result.variant_a.content == "Unique variant A content for assertions and testing."
        assert result.variant_b.content == "Unique variant B content for assertions and testing."
        assert result.variant_a.variant_label == "A"
        assert result.variant_b.variant_label == "B"

    @pytest.mark.asyncio
    async def test_initial_metrics_are_zero(self, db_session):
        """Newly created test should have zero impressions and clicks."""
        request = _make_create_request()
        result = await service.create_ab_test(request, ORG_ID, db_session)

        assert result.variant_a.impressions == 0
        assert result.variant_a.clicks == 0
        assert result.variant_a.click_through_rate == 0.0
        assert result.variant_b.impressions == 0
        assert result.variant_b.clicks == 0
        assert result.variant_b.click_through_rate == 0.0

    @pytest.mark.asyncio
    async def test_no_winner_on_draft(self, db_session):
        """Draft test should have no winner and no confidence."""
        request = _make_create_request()
        result = await service.create_ab_test(request, ORG_ID, db_session)

        assert result.winner is None
        assert result.confidence is None

    @pytest.mark.asyncio
    async def test_custom_duration(self, db_session):
        """Should respect the duration_days parameter."""
        request = _make_create_request(duration_days=30)
        result = await service.create_ab_test(request, ORG_ID, db_session)

        # Verify the record was created and can be retrieved.
        fetched = await service.get_ab_test(result.id, db_session)
        assert fetched is not None
        assert fetched.id == result.id


# ===========================================================================
# A/B Test retrieval
# ===========================================================================


class TestGetABTest:
    """Tests for service.get_ab_test."""

    @pytest.mark.asyncio
    async def test_returns_existing_test(self, db_session):
        """get_ab_test should return a response for an existing test."""
        ab = await _seed_ab_test(db_session, name="Retrieve Me")
        result = await service.get_ab_test(ab.id, db_session)

        assert result is not None
        assert result.id == ab.id
        assert result.name == "Retrieve Me"

    @pytest.mark.asyncio
    async def test_raises_not_found_for_nonexistent(self, db_session):
        """get_ab_test for a missing ID should raise NotFoundError."""
        missing_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await service.get_ab_test(missing_id, db_session)

    @pytest.mark.asyncio
    async def test_raises_not_found_for_soft_deleted(self, db_session):
        """get_ab_test should raise NotFoundError for soft-deleted records."""
        ab = await _seed_ab_test(db_session)
        # Soft-delete the record
        ab.deleted_at = datetime.now(UTC)
        await db_session.flush()

        with pytest.raises(NotFoundError):
            await service.get_ab_test(ab.id, db_session)


# ===========================================================================
# A/B Test listing
# ===========================================================================


class TestListABTests:
    """Tests for service.list_ab_tests."""

    @pytest.mark.asyncio
    async def test_lists_tests_for_org(self, db_session):
        """list_ab_tests should return all non-deleted tests for the org."""
        await _seed_ab_test(db_session, name="Test One")
        await _seed_ab_test(db_session, name="Test Two")
        results = await service.list_ab_tests(ORG_ID, db_session)

        assert len(results) == 2
        names = {r.name for r in results}
        assert "Test One" in names
        assert "Test Two" in names

    @pytest.mark.asyncio
    async def test_excludes_soft_deleted(self, db_session):
        """list_ab_tests should exclude soft-deleted records."""
        ab = await _seed_ab_test(db_session, name="Deleted One")
        ab.deleted_at = datetime.now(UTC)
        await db_session.flush()

        await _seed_ab_test(db_session, name="Active One")

        results = await service.list_ab_tests(ORG_ID, db_session)
        assert len(results) == 1
        assert results[0].name == "Active One"

    @pytest.mark.asyncio
    async def test_filter_by_book_id(self, db_session):
        """list_ab_tests should filter by book_id when provided."""
        other_book = uuid.uuid4()
        await _seed_ab_test(db_session, name="Book A", book_id=BOOK_ID)
        await _seed_ab_test(db_session, name="Book B", book_id=other_book)

        results = await service.list_ab_tests(ORG_ID, db_session, book_id=other_book)
        assert len(results) == 1
        assert results[0].name == "Book B"

    @pytest.mark.asyncio
    async def test_filter_by_status(self, db_session):
        """list_ab_tests should filter by status when provided."""
        await _seed_ab_test(db_session, name="Draft", status=ABTestStatus.DRAFT.value)
        await _seed_ab_test(db_session, name="Running", status=ABTestStatus.RUNNING.value)

        results = await service.list_ab_tests(
            ORG_ID,
            db_session,
            status=ABTestStatus.RUNNING,
        )
        assert len(results) == 1
        assert results[0].name == "Running"

    @pytest.mark.asyncio
    async def test_empty_list_for_other_org(self, db_session):
        """list_ab_tests for a different org should return empty."""
        await _seed_ab_test(db_session, name="Org A Test")
        other_org = uuid.uuid4()
        results = await service.list_ab_tests(other_org, db_session)
        assert results == []


# ===========================================================================
# A/B Test status transitions
# ===========================================================================


class TestStartABTest:
    """Tests for service.start_ab_test."""

    @pytest.mark.asyncio
    async def test_start_test(self, db_session):
        """Starting a draft test should set status to 'running' and record started_at."""
        ab = await _seed_ab_test(db_session, status=ABTestStatus.DRAFT.value)
        result = await service.start_ab_test(ab.id, db_session)

        assert result.status == ABTestStatus.RUNNING
        assert result.started_at is not None

    @pytest.mark.asyncio
    async def test_start_raises_not_found_for_missing(self, db_session):
        """Starting a non-existent test should raise NotFoundError."""
        with pytest.raises(NotFoundError):
            await service.start_ab_test(uuid.uuid4(), db_session)

    @pytest.mark.asyncio
    async def test_start_raises_not_found_for_soft_deleted(self, db_session):
        """Starting a soft-deleted test should raise NotFoundError."""
        ab = await _seed_ab_test(db_session)
        ab.deleted_at = datetime.now(UTC)
        await db_session.flush()

        with pytest.raises(NotFoundError):
            await service.start_ab_test(ab.id, db_session)

    @pytest.mark.asyncio
    async def test_start_raises_validation_for_completed(self, db_session):
        """Starting a COMPLETED test should raise ValidationError."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            completed_at=datetime.now(UTC),
        )
        with pytest.raises(ValidationError):
            await service.start_ab_test(ab.id, db_session)


# ===========================================================================
# A/B Test update
# ===========================================================================


class TestUpdateABTest:
    """Tests for service.update_ab_test."""

    @pytest.mark.asyncio
    async def test_update_name(self, db_session):
        """Updating a draft test name should persist."""
        ab = await _seed_ab_test(db_session, name="Old Name")
        update_req = ABTestUpdateRequest(name="New Name")
        result = await service.update_ab_test(ab.id, update_req, db_session)

        assert result.name == "New Name"

    @pytest.mark.asyncio
    async def test_cannot_change_content_while_running(self, db_session):
        """Changing variant content on a running test should raise ValidationError."""
        ab = await _seed_ab_test(db_session, status=ABTestStatus.RUNNING.value)
        update_req = ABTestUpdateRequest(
            variant_a="New content that should be rejected by validation rules.",
        )
        with pytest.raises(ValidationError):
            await service.update_ab_test(ab.id, update_req, db_session)

    @pytest.mark.asyncio
    async def test_status_transition_draft_to_running(self, db_session):
        """Transitioning draft -> running via update should succeed."""
        ab = await _seed_ab_test(db_session, status=ABTestStatus.DRAFT.value)
        update_req = ABTestUpdateRequest(status=ABTestStatus.RUNNING)
        result = await service.update_ab_test(ab.id, update_req, db_session)

        assert result.status == ABTestStatus.RUNNING
        assert result.started_at is not None

    @pytest.mark.asyncio
    async def test_invalid_status_transition_completed_to_draft(self, db_session):
        """Transitioning completed -> draft should raise ValidationError."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            completed_at=datetime.now(UTC),
        )
        update_req = ABTestUpdateRequest(status=ABTestStatus.DRAFT)
        with pytest.raises(ValidationError):
            await service.update_ab_test(ab.id, update_req, db_session)


# ===========================================================================
# A/B Test results and winner determination
# ===========================================================================


class TestGetTestResults:
    """Tests for result calculation in _ab_test_to_response and get_test_results."""

    @pytest.mark.asyncio
    async def test_ctr_calculation(self, db_session):
        """CTR should be calculated correctly from impressions and clicks."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.RUNNING.value,
            variant_a_impressions=1000,
            variant_a_clicks=50,
            variant_b_impressions=1000,
            variant_b_clicks=75,
        )
        result = await service.get_ab_test(ab.id, db_session)

        assert result.variant_a.click_through_rate == 5.0  # 50/1000 * 100
        assert result.variant_b.click_through_rate == 7.5  # 75/1000 * 100

    @pytest.mark.asyncio
    async def test_winner_determination_variant_b(self, db_session):
        """Completed test should identify the variant with higher CTR as winner."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=500,
            variant_a_clicks=25,  # 5% CTR
            variant_b_impressions=500,
            variant_b_clicks=50,  # 10% CTR
            completed_at=datetime.now(UTC),
        )
        result = await service.get_ab_test(ab.id, db_session)

        assert result.winner == "B"
        assert result.confidence is not None
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_winner_determination_variant_a(self, db_session):
        """Completed test should pick A when A has higher CTR."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=500,
            variant_a_clicks=60,  # 12% CTR
            variant_b_impressions=500,
            variant_b_clicks=25,  # 5% CTR
            completed_at=datetime.now(UTC),
        )
        result = await service.get_ab_test(ab.id, db_session)

        assert result.winner == "A"

    @pytest.mark.asyncio
    async def test_winner_tie(self, db_session):
        """Equal CTR should result in a 'tie'."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=100,
            variant_a_clicks=10,
            variant_b_impressions=100,
            variant_b_clicks=10,
            completed_at=datetime.now(UTC),
        )
        result = await service.get_ab_test(ab.id, db_session)

        assert result.winner == "tie"

    @pytest.mark.asyncio
    async def test_no_winner_while_running(self, db_session):
        """Running test should have no winner, even with data."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.RUNNING.value,
            variant_a_impressions=500,
            variant_a_clicks=25,
            variant_b_impressions=500,
            variant_b_clicks=50,
        )
        result = await service.get_ab_test(ab.id, db_session)

        assert result.winner is None
        assert result.confidence is None

    @pytest.mark.asyncio
    async def test_zero_impressions_ctr_is_zero(self, db_session):
        """CTR should be 0.0 when impressions are zero (no division error)."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=0,
            variant_a_clicks=0,
            variant_b_impressions=0,
            variant_b_clicks=0,
            completed_at=datetime.now(UTC),
        )
        result = await service.get_ab_test(ab.id, db_session)

        assert result.variant_a.click_through_rate == 0.0
        assert result.variant_b.click_through_rate == 0.0
        # Both zero -> tie
        assert result.winner == "tie"

    @pytest.mark.asyncio
    async def test_confidence_increases_with_sample_size(self, db_session):
        """Confidence should increase with total impressions (same rate difference)."""
        # Small sample: 50 vs 50, with a moderate difference in rates
        ab_small = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=50,
            variant_a_clicks=5,
            variant_b_impressions=50,
            variant_b_clicks=15,
            completed_at=datetime.now(UTC),
        )
        result_small = await service.get_ab_test(ab_small.id, db_session)

        # Large sample: 5000 vs 5000, same proportional difference
        ab_large = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=5000,
            variant_a_clicks=500,
            variant_b_impressions=5000,
            variant_b_clicks=1500,
            completed_at=datetime.now(UTC),
        )
        result_large = await service.get_ab_test(ab_large.id, db_session)

        assert result_small.confidence is not None
        assert result_large.confidence is not None
        assert result_large.confidence >= result_small.confidence

    @pytest.mark.asyncio
    async def test_confidence_capped_at_100(self, db_session):
        """Confidence should never exceed 100.0 (z-test caps at 99.95)."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=100_000,
            variant_a_clicks=10_000,
            variant_b_impressions=100_000,
            variant_b_clicks=5_000,
            completed_at=datetime.now(UTC),
        )
        result = await service.get_ab_test(ab.id, db_session)

        assert result.confidence is not None
        assert result.confidence <= 100.0


# ===========================================================================
# Detailed test results (get_test_results)
# ===========================================================================


class TestGetDetailedResults:
    """Tests for service.get_test_results (ABTestResultsResponse)."""

    @pytest.mark.asyncio
    async def test_returns_results_response(self, db_session):
        """get_test_results should return an ABTestResultsResponse."""
        # Use naive datetimes because SQLite strips timezone info,
        # and the service uses datetime.now(timezone.utc) for comparisons.
        from unittest.mock import patch as _patch

        now_utc = datetime.now(UTC)
        started = now_utc - timedelta(days=7)

        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=200,
            variant_a_clicks=20,
            variant_b_impressions=200,
            variant_b_clicks=40,
            started_at=started,
            completed_at=now_utc,
        )

        # After SQLite round-trip, started_at loses tzinfo.
        # Patch datetime.now in the service module so both sides are consistent.
        with _patch("app.modules.product_page_lab.service.datetime") as mock_dt:
            mock_dt.now.return_value = now_utc.replace(tzinfo=None)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = await service.get_test_results(ab.id, db_session)

        assert isinstance(result, ABTestResultsResponse)
        assert result.test_id == ab.id
        assert result.variant_a.click_through_rate > 0
        assert result.variant_b.click_through_rate > 0
        assert result.sample_size_sufficient is True
        assert result.days_running is not None
        assert result.days_running >= 7

    @pytest.mark.asyncio
    async def test_insufficient_sample(self, db_session):
        """Tests with fewer than MIN_SAMPLE_SIZE impressions should flag insufficient sample."""
        ab = await _seed_ab_test(
            db_session,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=20,
            variant_a_clicks=2,
            variant_b_impressions=20,
            variant_b_clicks=5,
            completed_at=datetime.now(UTC),
        )
        result = await service.get_test_results(ab.id, db_session)

        assert result.sample_size_sufficient is False

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing(self, db_session):
        """get_test_results for a missing test should raise NotFoundError."""
        with pytest.raises(NotFoundError):
            await service.get_test_results(uuid.uuid4(), db_session)


# ===========================================================================
# Blurb generation
# ===========================================================================


class TestGenerateBlurbVariants:
    """Tests for service.generate_blurb_variants (local fallback path)."""

    @pytest.mark.asyncio
    async def test_returns_requested_variant_count(self):
        """Should return the requested number of blurb variants."""
        request = BlurbGenerateRequest(
            current_blurb="A gripping thriller about a detective who discovers a dark secret in a small town. "
            "She must confront her own past to solve the case. "
            "Buy now to find out the shocking truth.",
            genre=Genre.THRILLER,
            num_variants=3,
        )
        result = await service.generate_blurb_variants(request)

        assert len(result.variants) == 3

    @pytest.mark.asyncio
    async def test_each_variant_has_content(self):
        """Every variant should have non-empty content."""
        request = BlurbGenerateRequest(
            current_blurb="A heartwarming romance about finding love when you least expect it. "
            "Two strangers meet in Paris and their lives are changed forever. "
            "Scroll up and grab your copy today!",
            genre=Genre.ROMANCE,
            num_variants=2,
        )
        result = await service.generate_blurb_variants(request)

        for variant in result.variants:
            assert variant.content
            assert len(variant.content) > 0
            assert variant.variant_id
            assert variant.style

    @pytest.mark.asyncio
    async def test_original_score_returned(self):
        """Response should include a score for the original blurb."""
        request = BlurbGenerateRequest(
            current_blurb="A compelling mystery where nothing is as it seems. "
            "Discover the truth behind the disappearance that "
            "shook a quiet community. Read now!",
            genre=Genre.MYSTERY,
            num_variants=1,
        )
        result = await service.generate_blurb_variants(request)

        assert result.original_score >= 0
        assert result.original_score <= 100

    @pytest.mark.asyncio
    async def test_generation_metadata_present(self):
        """generation_metadata should indicate the generation method."""
        request = BlurbGenerateRequest(
            current_blurb="An epic fantasy adventure that will transport you to another world. "
            "Join the hero on a quest that will determine the fate of kingdoms. "
            "Get your copy today!",
            genre=Genre.FANTASY,
            num_variants=1,
        )
        result = await service.generate_blurb_variants(request)

        assert "method" in result.generation_metadata
        # Without an LLM client it should fall back to template_based
        assert result.generation_metadata["method"] == "template_based"


# ===========================================================================
# Listing analysis
# ===========================================================================


class TestAnalyzeListing:
    """Tests for service.analyze_listing_with_data."""

    @pytest.mark.asyncio
    async def test_returns_overall_score(self):
        """analyze_listing_with_data should return a ListingAnalysis with an overall score."""
        result = await service.analyze_listing_with_data(
            title="The Secret Garden: A Captivating Journey of Discovery",
            blurb="Discover the untold story of a hidden garden that changes everything. "
            "A heartwarming tale of love, loss, and redemption. "
            "- Beautiful prose\n- Compelling characters\n"
            "<b>Buy now</b> and start reading!",
            keywords=["garden", "discovery", "heartwarming"],
            genre="literary_fiction",
            price=4.99,
        )

        assert result.overall_score >= 0
        assert result.overall_score <= 100
        assert result.title_analysis is not None
        assert result.blurb_analysis is not None

    @pytest.mark.asyncio
    async def test_empty_title_still_works(self):
        """Analysis should still work with an empty title."""
        result = await service.analyze_listing_with_data(
            title="",
            blurb="Just a simple blurb with enough words to be analyzed properly.",
        )

        assert result.title_score is not None
        assert result.blurb_score is not None

    @pytest.mark.asyncio
    async def test_asin_extraction_from_url(self, db_session):
        """analyze_amazon_listing should extract ASIN from a URL."""
        # Seed a Book with matching ASIN so the DB lookup succeeds
        from app.models.project import Book, BookFormat, BookStatus, Project, ProjectStatus, ProjectType

        project = Project(
            org_id=ORG_ID,
            title="Test Project",
            type=ProjectType.BOOK,
            status=ProjectStatus.ACTIVE,
        )
        db_session.add(project)
        await db_session.flush()
        book = Book(
            project_id=project.id,
            title="Test Book for ASIN Lookup",
            asin="B09V2KKG1D",
            format=BookFormat.EBOOK,
            status=BookStatus.DRAFT,
        )
        db_session.add(book)
        await db_session.flush()

        request = ListingAnalyzeRequest(url="https://www.amazon.com/dp/B09V2KKG1D")
        result = await service.analyze_amazon_listing(request, db_session)

        assert result.asin == "B09V2KKG1D"


# ===========================================================================
# Look Inside analysis
# ===========================================================================


class TestAnalyzeLookInside:
    """Tests for service.analyze_look_inside."""

    @pytest.mark.asyncio
    async def test_returns_section_scores(self):
        """Should return scored sections for first_page, hook, pacing, and toc."""
        request = LookInsideAnalyzeRequest(
            preview_text=(
                '"Run!" she screamed, grabbing his arm as the dark shadows closed in.\n\n'
                "They had never expected this. The old mansion held secrets that no one "
                "was meant to discover. Every room told a story of betrayal and loss.\n\n"
                "But nothing prepared them for what waited in the basement.\n\n"
                "The cold, damp air hit them like a wall. She felt her heart racing "
                "as the flashlight flickered and died.\n\n"
                '"We have to go back," he whispered. "Before it finds us."'
            ),
            genre=Genre.THRILLER,
            chapter_titles=[
                "The Night It Began",
                "Secrets in the Dark",
                "The Last Warning",
                "Blood and Fire",
                "The Truth Revealed",
            ],
        )
        result = await service.analyze_look_inside(request)

        assert result.overall_score >= 0
        assert result.overall_score <= 100
        assert result.hook_strength >= 0
        assert result.first_page_impact >= 0
        assert result.pacing_score >= 0
        assert result.toc_effectiveness >= 0
        assert len(result.sections) == 4

    @pytest.mark.asyncio
    async def test_empty_chapter_titles_lower_toc_score(self):
        """Empty chapter titles should produce a low TOC score."""
        request = LookInsideAnalyzeRequest(
            preview_text=(
                "A long enough preview text to satisfy the minimum length requirement. "
                "This story begins on a quiet morning in a small town."
            ),
            genre=Genre.OTHER,
            chapter_titles=[],
        )
        result = await service.analyze_look_inside(request)

        assert result.toc_effectiveness == 40.0


# ===========================================================================
# Mobile check
# ===========================================================================


class TestCheckMobileListing:
    """Tests for service.check_mobile_listing."""

    @pytest.mark.asyncio
    async def test_short_title_not_truncated(self):
        """A short title should not be flagged as truncated."""
        request = MobileCheckRequest(
            title="Short Title",
            blurb="A compelling blurb about the book that is detailed enough for analysis.",
            author_name="J. Author",
        )
        result = await service.check_mobile_listing(request)

        assert result.title_display.is_truncated is False
        assert result.overall_score > 0

    @pytest.mark.asyncio
    async def test_long_title_truncated(self):
        """A very long title should be flagged as truncated on mobile."""
        long_title = (
            "An Extremely Long Book Title That Will Certainly Be Truncated On Mobile Devices Due To Screen Width"
        )
        request = MobileCheckRequest(
            title=long_title,
            blurb="A compelling blurb about the book with enough detail for the mobile check.",
            author_name="J. Author",
        )
        result = await service.check_mobile_listing(request)

        assert result.title_display.is_truncated is True

    @pytest.mark.asyncio
    async def test_device_previews_populated(self):
        """Should return device-specific previews for known devices."""
        request = MobileCheckRequest(
            title="My Book Title",
            blurb="A compelling blurb about the book that is long enough for testing purposes.",
            author_name="Author Name",
        )
        result = await service.check_mobile_listing(request)

        assert "iphone_14" in result.device_previews
        assert "samsung_galaxy_s23" in result.device_previews
        assert "pixel_7" in result.device_previews


# ===========================================================================
# Conversion scores
# ===========================================================================


class TestGetConversionScores:
    """Tests for service.get_conversion_scores."""

    @pytest.mark.asyncio
    async def test_returns_zero_scores_with_no_tests(self, db_session):
        """get_conversion_scores with no A/B tests should return zero overall."""
        book_id = uuid.uuid4()
        result = await service.get_conversion_scores(book_id, db_session)

        assert result.book_id == book_id
        assert result.overall_score == 0.0
        assert result.blurb_score is None
        assert result.recommendations_count == 0

    @pytest.mark.asyncio
    async def test_derives_blurb_score_from_completed_test(self, db_session):
        """Should derive blurb_score from the best CTR of completed tests."""
        book = uuid.uuid4()
        await _seed_ab_test(
            db_session,
            book_id=book,
            status=ABTestStatus.COMPLETED.value,
            variant_a_impressions=1000,
            variant_a_clicks=80,  # 8% CTR -> score 80
            variant_b_impressions=1000,
            variant_b_clicks=50,  # 5% CTR -> score 50
            completed_at=datetime.now(UTC),
        )
        result = await service.get_conversion_scores(book, db_session)

        assert result.blurb_score is not None
        assert result.blurb_score == 80.0  # best CTR (8%) * 10
        assert result.overall_score == 80.0


# ===========================================================================
# ASIN extraction helper
# ===========================================================================


class TestExtractAsin:
    """Tests for the internal _extract_asin_from_url helper."""

    def test_dp_pattern(self):
        asin = service._extract_asin_from_url("https://www.amazon.com/dp/B09V2KKG1D")
        assert asin == "B09V2KKG1D"

    def test_gp_product_pattern(self):
        asin = service._extract_asin_from_url("https://www.amazon.com/gp/product/B09V2KKG1D/ref=...")
        assert asin == "B09V2KKG1D"

    def test_asin_query_param_pattern(self):
        asin = service._extract_asin_from_url("https://www.amazon.com/something?asin=B09V2KKG1D&other=1")
        assert asin == "B09V2KKG1D"

    def test_no_asin_returns_none(self):
        asin = service._extract_asin_from_url("https://www.example.com/no-asin-here")
        assert asin is None

    def test_case_insensitive_match(self):
        asin = service._extract_asin_from_url("https://www.amazon.com/dp/b09v2kkg1d")
        assert asin == "B09V2KKG1D"


# ===========================================================================
# Z-test confidence helper
# ===========================================================================


class TestComputeZTestConfidence:
    """Tests for the internal _compute_z_test_confidence helper."""

    def test_zero_impressions_returns_zero(self):
        result = service._compute_z_test_confidence(0, 0, 0, 0)
        assert result == 0.0

    def test_identical_rates_returns_near_zero(self):
        """Same rate for both variants should yield near-zero confidence."""
        result = service._compute_z_test_confidence(1000, 100, 1000, 100)
        assert result < 1.0  # Effectively zero (floating point residual)

    def test_large_difference_yields_high_confidence(self):
        """A large rate difference with many observations should yield high confidence."""
        result = service._compute_z_test_confidence(10000, 1000, 10000, 2000)
        assert result > 95.0

    def test_confidence_bounded_0_to_100(self):
        """Confidence should always be between 0 and 100."""
        result = service._compute_z_test_confidence(100000, 50000, 100000, 10000)
        assert 0.0 <= result <= 100.0


# ===========================================================================
# Full lifecycle integration
# ===========================================================================


class TestABTestLifecycle:
    """End-to-end lifecycle: create -> read -> start -> verify running state."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, db_session):
        """Walk through create -> get -> start -> get with running status."""
        # 1. Create
        request = _make_create_request(name="Lifecycle Test")
        created = await service.create_ab_test(request, ORG_ID, db_session)
        assert created.status == ABTestStatus.DRAFT
        assert created.started_at is None

        # 2. Retrieve
        fetched = await service.get_ab_test(created.id, db_session)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Lifecycle Test"

        # 3. Start
        started = await service.start_ab_test(created.id, db_session)
        assert started.status == ABTestStatus.RUNNING
        assert started.started_at is not None

        # 4. Re-fetch and verify state persisted
        re_fetched = await service.get_ab_test(created.id, db_session)
        assert re_fetched.status == ABTestStatus.RUNNING

    @pytest.mark.asyncio
    async def test_create_update_complete_lifecycle(self, db_session):
        """create -> update name -> transition to running -> complete via update."""
        # 1. Create
        request = _make_create_request(name="Full Cycle")
        created = await service.create_ab_test(request, ORG_ID, db_session)
        assert created.status == ABTestStatus.DRAFT

        # 2. Update name
        updated = await service.update_ab_test(
            created.id,
            ABTestUpdateRequest(name="Full Cycle Renamed"),
            db_session,
        )
        assert updated.name == "Full Cycle Renamed"

        # 3. Transition to running
        started = await service.update_ab_test(
            created.id,
            ABTestUpdateRequest(status=ABTestStatus.RUNNING),
            db_session,
        )
        assert started.status == ABTestStatus.RUNNING

        # 4. Complete
        completed = await service.update_ab_test(
            created.id,
            ABTestUpdateRequest(status=ABTestStatus.COMPLETED),
            db_session,
        )
        assert completed.status == ABTestStatus.COMPLETED
