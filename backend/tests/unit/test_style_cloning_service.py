"""Unit tests for Style Cloning service with DB persistence.

These tests mock the database layer (AsyncSession) to validate the service
logic for profile CRUD, NLP analysis orchestration, fingerprint retrieval,
and conformity checking.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.style_cloning.schemas import (
    ConformityCheckResult,
    CreateProfileRequest,
    FingerprintResponse,
    ProfileListResponse,
    ProfileResponse,
    ProfileStatus,
    StyleCard,
    VoiceFingerprint,
)
from tests.conftest import populate_server_defaults

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_TEXT = (
    "The old house stood at the end of the lane. Its walls were weathered "
    "by decades of storms. Paint peeled from the wooden shutters. Ivy crept "
    "up the eastern wall. The garden had grown wild with neglect. Roses "
    "tangled with weeds along the fence. A broken gate hung from rusty "
    "hinges. Inside, dust covered every surface. The floorboards creaked "
    "underfoot. Memories lingered in every room. The kitchen still smelled "
    "faintly of cinnamon. Sunlight filtered through cracked windows. "
    "Shadows danced on the faded wallpaper. An old clock ticked on the "
    "mantle. Time had moved on but the house remained."
)


def _make_mock_profile(
    *,
    profile_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    name: str = "Test Profile",
    description: str | None = "",
    genre: str | None = "",
    status: str = "pending",
    word_count: int = 0,
    sample_count: int = 0,
    confidence: float = 0.0,
    style_card: dict | None = None,
    voice_fingerprint: dict | None = None,
    sample_texts: list[str] | None = None,
    deleted_at: datetime | None = None,
) -> MagicMock:
    """Create a MagicMock that behaves like a StyleProfile ORM instance."""
    mock = MagicMock()
    mock.id = profile_id or uuid.uuid4()
    mock.org_id = org_id or uuid.uuid4()
    mock.name = name
    mock.description = description
    mock.genre = genre
    mock.status = status
    mock.word_count = word_count
    mock.sample_count = sample_count
    mock.confidence = confidence
    mock.style_card = style_card
    mock.voice_fingerprint = voice_fingerprint
    mock.sample_texts = sample_texts
    mock.deleted_at = deleted_at
    mock.created_at = datetime.now(UTC)
    mock.updated_at = datetime.now(UTC)
    return mock


def _make_scalars_result(profiles: list) -> MagicMock:
    """Create a mock db.execute() result whose .scalars().all() returns profiles."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = profiles
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock


def _make_scalar_one_result(profile) -> MagicMock:
    """Create a mock db.execute() result whose .scalar_one_or_none() returns a profile."""
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = profile
    return result_mock


def _make_voice_fingerprint_dict() -> dict:
    """Return a minimal VoiceFingerprint as a dict for storage."""
    return VoiceFingerprint(
        voice_vector=[0.0] * 200,
        dimension_labels=[f"dim_{i}" for i in range(200)],
    ).model_dump()


def _make_style_card_dict() -> dict:
    """Return a minimal StyleCard as a dict for storage."""
    return StyleCard(summary="Test style card summary").model_dump()


def _mock_db() -> AsyncMock:
    """Create a standard mocked AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock(side_effect=populate_server_defaults)
    return db


# ===================================================================
# TestCreateProfile
# ===================================================================


class TestCreateProfile:
    """Tests for service.create_profile."""

    @staticmethod
    def _make_refresh(org_id: uuid.UUID):
        """Return a refresh side-effect that simulates DB defaults.

        SQLAlchemy ORM mapped_column defaults may not be applied to Python
        attributes until the object is refreshed from the database. This
        side-effect simulates that behavior by ensuring server-generated
        fields (id, timestamps) and column defaults (word_count, etc.) are
        present on the object after refresh.
        """

        async def _refresh_side_effect(obj, *args, **kwargs):
            if not hasattr(obj, "id") or obj.id is None:
                obj.id = uuid.uuid4()
            obj.org_id = org_id
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)
            # Apply column defaults that the real DB would provide
            if obj.word_count is None:
                obj.word_count = 0
            if obj.sample_count is None:
                obj.sample_count = 0
            if obj.confidence is None:
                obj.confidence = 0.0

        return _refresh_side_effect

    @pytest.mark.asyncio
    async def test_creates_profile_in_db(self):
        """create_profile should add a StyleProfile to the session and return a response."""
        db = _mock_db()
        org_id = uuid.uuid4()
        request = CreateProfileRequest(name="Test Profile", genre="fiction")

        db.refresh.side_effect = self._make_refresh(org_id)

        from app.modules.style_cloning.service import create_profile

        result = await create_profile(db, org_id, request)

        db.add.assert_called_once()
        db.flush.assert_called_once()
        db.refresh.assert_called_once()
        assert isinstance(result, ProfileResponse)
        assert result.name == "Test Profile"
        assert result.genre == "fiction"
        assert result.status == ProfileStatus.pending

    @pytest.mark.asyncio
    async def test_creates_profile_without_samples_is_pending(self):
        """A profile created without sample_texts should have status 'pending'."""
        db = _mock_db()
        org_id = uuid.uuid4()
        request = CreateProfileRequest(name="No Samples")

        db.refresh.side_effect = self._make_refresh(org_id)

        from app.modules.style_cloning.service import create_profile

        result = await create_profile(db, org_id, request)

        assert result.status == ProfileStatus.pending
        assert result.word_count == 0
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_creates_with_sample_texts_runs_analysis(self):
        """If sample_texts provided, should run NLP analysis and set status to ready."""
        db = _mock_db()
        org_id = uuid.uuid4()
        request = CreateProfileRequest(
            name="Analyzed",
            sample_texts=[SAMPLE_TEXT],
        )

        db.refresh.side_effect = self._make_refresh(org_id)

        from app.modules.style_cloning.service import create_profile

        result = await create_profile(db, org_id, request)

        assert result.status == ProfileStatus.ready
        assert result.word_count > 0
        assert result.confidence > 0.0
        assert result.style_card is not None

    @pytest.mark.asyncio
    async def test_create_profile_sets_description_and_genre(self):
        """create_profile should propagate description and genre from request."""
        db = _mock_db()
        org_id = uuid.uuid4()
        request = CreateProfileRequest(
            name="Detailed",
            description="A detailed test profile",
            genre="mystery",
        )

        db.refresh.side_effect = self._make_refresh(org_id)

        from app.modules.style_cloning.service import create_profile

        result = await create_profile(db, org_id, request)

        assert result.description == "A detailed test profile"
        assert result.genre == "mystery"

    @pytest.mark.asyncio
    async def test_create_profile_empty_sample_texts_stays_pending(self):
        """An explicit empty list of sample_texts should result in pending status."""
        db = _mock_db()
        org_id = uuid.uuid4()
        request = CreateProfileRequest(name="Empty Samples", sample_texts=[])

        db.refresh.side_effect = self._make_refresh(org_id)

        from app.modules.style_cloning.service import create_profile

        result = await create_profile(db, org_id, request)

        assert result.status == ProfileStatus.pending


# ===================================================================
# TestListProfiles
# ===================================================================


class TestListProfiles:
    """Tests for service.list_profiles."""

    @pytest.mark.asyncio
    async def test_returns_org_profiles(self):
        """list_profiles should query by org_id and return non-deleted profiles."""
        org_id = uuid.uuid4()
        profile_a = _make_mock_profile(org_id=org_id, name="Profile A")
        profile_b = _make_mock_profile(org_id=org_id, name="Profile B")

        db = _mock_db()
        db.execute.return_value = _make_scalars_result([profile_a, profile_b])

        from app.modules.style_cloning.service import list_profiles

        result = await list_profiles(db, org_id)

        assert isinstance(result, ProfileListResponse)
        assert result.total == 2
        assert len(result.items) == 2
        assert result.items[0].name == "Profile A"
        assert result.items[1].name == "Profile B"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_profiles(self):
        """list_profiles should return an empty list when org has no profiles."""
        org_id = uuid.uuid4()
        db = _mock_db()
        db.execute.return_value = _make_scalars_result([])

        from app.modules.style_cloning.service import list_profiles

        result = await list_profiles(db, org_id)

        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_excludes_deleted_profiles(self):
        """list_profiles should not include soft-deleted profiles.

        The filtering is done in SQL, so we just verify that the service
        correctly passes through whatever the DB returns.
        """
        org_id = uuid.uuid4()
        active_profile = _make_mock_profile(org_id=org_id, name="Active")
        # Simulate that the DB query already filtered out deleted profiles
        db = _mock_db()
        db.execute.return_value = _make_scalars_result([active_profile])

        from app.modules.style_cloning.service import list_profiles

        result = await list_profiles(db, org_id)

        assert result.total == 1
        assert result.items[0].name == "Active"


# ===================================================================
# TestGetProfile
# ===================================================================


class TestGetProfile:
    """Tests for service.get_profile."""

    @pytest.mark.asyncio
    async def test_returns_profile_by_id(self):
        """get_profile should return a profile when found."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        profile = _make_mock_profile(profile_id=profile_id, org_id=org_id, name="Found Me")

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import get_profile

        result = await get_profile(db, profile_id, org_id)

        assert result is not None
        assert isinstance(result, ProfileResponse)
        assert result.name == "Found Me"
        assert result.id == profile_id

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """get_profile should return None when profile does not exist."""
        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(None)

        from app.modules.style_cloning.service import get_profile

        result = await get_profile(db, uuid.uuid4(), uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_other_org(self):
        """get_profile returns None if profile belongs to a different org.

        Org isolation is enforced at the SQL level; the service trusts DB results.
        """
        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(None)

        from app.modules.style_cloning.service import get_profile

        result = await get_profile(db, uuid.uuid4(), uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_profile_with_style_card(self):
        """get_profile should reconstruct StyleCard from stored dict."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        card_dict = _make_style_card_dict()
        profile = _make_mock_profile(
            profile_id=profile_id,
            org_id=org_id,
            name="With Card",
            style_card=card_dict,
            status="ready",
        )

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import get_profile

        result = await get_profile(db, profile_id, org_id)

        assert result is not None
        assert result.style_card is not None
        assert isinstance(result.style_card, StyleCard)
        assert result.style_card.summary == "Test style card summary"


# ===================================================================
# TestDeleteProfile
# ===================================================================


class TestDeleteProfile:
    """Tests for service.delete_profile."""

    @pytest.mark.asyncio
    async def test_soft_deletes(self):
        """delete_profile should set deleted_at, not remove the record."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        profile = _make_mock_profile(profile_id=profile_id, org_id=org_id, name="Delete Me")

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import delete_profile

        result = await delete_profile(db, profile_id, org_id)

        assert result is True
        assert profile.deleted_at is not None
        assert profile.updated_at is not None
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(self):
        """delete_profile should return False when profile does not exist."""
        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(None)

        from app.modules.style_cloning.service import delete_profile

        result = await delete_profile(db, uuid.uuid4(), uuid.uuid4())

        assert result is False
        db.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_sets_updated_at(self):
        """delete_profile should update the updated_at timestamp."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        old_updated = datetime(2024, 1, 1, tzinfo=UTC)
        profile = _make_mock_profile(profile_id=profile_id, org_id=org_id, name="Timestamp Check")
        profile.updated_at = old_updated

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import delete_profile

        await delete_profile(db, profile_id, org_id)

        assert profile.updated_at != old_updated
        assert profile.deleted_at is not None


# ===================================================================
# TestGetFingerprint
# ===================================================================


class TestGetFingerprint:
    """Tests for service.get_fingerprint."""

    @pytest.mark.asyncio
    async def test_returns_fingerprint_for_analyzed_profile(self):
        """get_fingerprint should return FingerprintResponse with voice data."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        fp_dict = _make_voice_fingerprint_dict()
        profile = _make_mock_profile(
            profile_id=profile_id,
            org_id=org_id,
            voice_fingerprint=fp_dict,
            status="ready",
        )

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import get_fingerprint

        result = await get_fingerprint(db, profile_id, org_id)

        assert result is not None
        assert isinstance(result, FingerprintResponse)
        assert result.profile_id == profile_id
        assert isinstance(result.fingerprint, VoiceFingerprint)
        assert len(result.fingerprint.voice_vector) == 200

    @pytest.mark.asyncio
    async def test_returns_none_for_unanalyzed(self):
        """get_fingerprint returns None if profile has no fingerprint (pending)."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        profile = _make_mock_profile(
            profile_id=profile_id,
            org_id=org_id,
            voice_fingerprint=None,
            status="pending",
        )

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import get_fingerprint

        result = await get_fingerprint(db, profile_id, org_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_nonexistent_profile(self):
        """get_fingerprint returns None if profile not found."""
        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(None)

        from app.modules.style_cloning.service import get_fingerprint

        result = await get_fingerprint(db, uuid.uuid4(), uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_fingerprint_has_all_metric_categories(self):
        """get_fingerprint response should contain all five metric categories."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        fp_dict = _make_voice_fingerprint_dict()
        profile = _make_mock_profile(
            profile_id=profile_id,
            org_id=org_id,
            voice_fingerprint=fp_dict,
        )

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import get_fingerprint

        result = await get_fingerprint(db, profile_id, org_id)

        assert result is not None
        fp = result.fingerprint
        assert fp.vocabulary is not None
        assert fp.sentence is not None
        assert fp.paragraph is not None
        assert fp.rhetorical is not None
        assert fp.dialogue is not None


# ===================================================================
# TestAnalyzeProfile
# ===================================================================


class TestAnalyzeProfile:
    """Tests for service.analyze_profile."""

    @pytest.mark.asyncio
    async def test_analyze_adds_samples_and_runs_pipeline(self):
        """analyze_profile should append texts and update status to ready."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        profile = _make_mock_profile(
            profile_id=profile_id,
            org_id=org_id,
            name="Incremental",
            sample_texts=[],
            status="pending",
        )

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        async def _refresh_side_effect(obj, *args, **kwargs):
            pass  # profile already mutated in place by _run_analysis

        db.refresh.side_effect = _refresh_side_effect

        from app.modules.style_cloning.service import analyze_profile

        result = await analyze_profile(db, profile_id, org_id, [SAMPLE_TEXT])

        assert result is not None
        assert result.status == ProfileStatus.ready
        assert result.word_count > 0
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_appends_to_existing_samples(self):
        """analyze_profile should merge new samples with existing ones."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        existing_text = "Existing sample text. " * 20
        profile = _make_mock_profile(
            profile_id=profile_id,
            org_id=org_id,
            sample_texts=[existing_text],
        )

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)
        db.refresh.side_effect = AsyncMock()

        from app.modules.style_cloning.service import analyze_profile

        result = await analyze_profile(db, profile_id, org_id, [SAMPLE_TEXT])

        assert result is not None
        # The profile should now have 2 sample texts
        assert len(profile.sample_texts) == 2

    @pytest.mark.asyncio
    async def test_analyze_returns_none_for_missing_profile(self):
        """analyze_profile returns None if profile not found."""
        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(None)

        from app.modules.style_cloning.service import analyze_profile

        result = await analyze_profile(db, uuid.uuid4(), uuid.uuid4(), [SAMPLE_TEXT])

        assert result is None
        db.flush.assert_not_called()


# ===================================================================
# TestConformityCheck
# ===================================================================


class TestConformityCheck:
    """Tests for service.conformity_check."""

    @pytest.mark.asyncio
    async def test_returns_conformity_result(self):
        """conformity_check should return a scored result for analyzed profiles."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        fp_dict = _make_voice_fingerprint_dict()
        profile = _make_mock_profile(
            profile_id=profile_id,
            org_id=org_id,
            voice_fingerprint=fp_dict,
            status="ready",
        )

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import conformity_check

        result = await conformity_check(db, profile_id, org_id, SAMPLE_TEXT)

        assert result is not None
        assert isinstance(result, ConformityCheckResult)
        assert 0 <= result.overall_score <= 100
        assert 0 <= result.vocabulary_score <= 100
        assert 0 <= result.sentence_score <= 100
        assert isinstance(result.feedback, list)

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_profile(self):
        """conformity_check returns None if profile not found."""
        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(None)

        from app.modules.style_cloning.service import conformity_check

        result = await conformity_check(db, uuid.uuid4(), uuid.uuid4(), "Some text.")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_unanalyzed_profile(self):
        """conformity_check returns None if profile has no fingerprint."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        profile = _make_mock_profile(
            profile_id=profile_id,
            org_id=org_id,
            voice_fingerprint=None,
            status="pending",
        )

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import conformity_check

        result = await conformity_check(db, profile_id, org_id, "Some text.")

        assert result is None

    @pytest.mark.asyncio
    async def test_conformity_scores_are_bounded(self):
        """All sub-scores in a conformity result should be between 0 and 100."""
        org_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        fp_dict = _make_voice_fingerprint_dict()
        profile = _make_mock_profile(
            profile_id=profile_id,
            org_id=org_id,
            voice_fingerprint=fp_dict,
        )

        db = _mock_db()
        db.execute.return_value = _make_scalar_one_result(profile)

        from app.modules.style_cloning.service import conformity_check

        result = await conformity_check(db, profile_id, org_id, SAMPLE_TEXT)

        assert result is not None
        assert 0 <= result.overall_score <= 100
        assert 0 <= result.vocabulary_score <= 100
        assert 0 <= result.sentence_score <= 100
        assert 0 <= result.paragraph_score <= 100
        assert 0 <= result.rhetorical_score <= 100
        assert 0 <= result.dialogue_score <= 100


# ===================================================================
# TestToResponse (internal helper)
# ===================================================================


class TestToResponse:
    """Tests for the internal _to_response conversion helper."""

    def test_converts_orm_to_schema(self):
        """_to_response should produce a valid ProfileResponse from ORM data."""
        from app.modules.style_cloning.service import _to_response

        profile = _make_mock_profile(
            name="Converted",
            status="ready",
            word_count=500,
            sample_count=3,
            confidence=0.85,
        )

        result = _to_response(profile)

        assert isinstance(result, ProfileResponse)
        assert result.name == "Converted"
        assert result.status == ProfileStatus.ready
        assert result.word_count == 500
        assert result.sample_count == 3
        assert result.confidence == 0.85

    def test_handles_none_style_card(self):
        """_to_response should set style_card to None when not present."""
        from app.modules.style_cloning.service import _to_response

        profile = _make_mock_profile(style_card=None)
        result = _to_response(profile)

        assert result.style_card is None

    def test_reconstructs_style_card_from_dict(self):
        """_to_response should reconstruct StyleCard from stored dict."""
        from app.modules.style_cloning.service import _to_response

        card_dict = _make_style_card_dict()
        profile = _make_mock_profile(style_card=card_dict)
        result = _to_response(profile)

        assert result.style_card is not None
        assert isinstance(result.style_card, StyleCard)
        assert result.style_card.summary == "Test style card summary"

    def test_handles_empty_description_and_genre(self):
        """_to_response should default description/genre to '' when None."""
        from app.modules.style_cloning.service import _to_response

        profile = _make_mock_profile(description=None, genre=None)
        result = _to_response(profile)

        assert result.description == ""
        assert result.genre == ""


# ===================================================================
# TestRunAnalysis (internal pipeline helper)
# ===================================================================


class TestRunAnalysis:
    """Tests for the internal _run_analysis pipeline helper."""

    def test_analysis_sets_ready_status(self):
        """_run_analysis should set status to 'ready' on success."""
        from app.modules.style_cloning.service import _run_analysis

        profile = _make_mock_profile(sample_texts=[SAMPLE_TEXT])
        _run_analysis(profile)

        assert profile.status == ProfileStatus.ready.value
        assert profile.word_count > 0
        assert profile.confidence > 0.0
        assert profile.voice_fingerprint is not None
        assert profile.style_card is not None

    def test_analysis_with_empty_samples_sets_failed(self):
        """_run_analysis should set status to 'failed' when no samples."""
        from app.modules.style_cloning.service import _run_analysis

        profile = _make_mock_profile(sample_texts=[])
        _run_analysis(profile)

        assert profile.status == ProfileStatus.failed.value

    def test_analysis_with_none_samples_sets_failed(self):
        """_run_analysis should set status to 'failed' when sample_texts is None."""
        from app.modules.style_cloning.service import _run_analysis

        profile = _make_mock_profile(sample_texts=None)
        _run_analysis(profile)

        assert profile.status == ProfileStatus.failed.value

    def test_analysis_sets_sample_count(self):
        """_run_analysis should record the number of samples processed."""
        from app.modules.style_cloning.service import _run_analysis

        texts = [SAMPLE_TEXT, SAMPLE_TEXT]
        profile = _make_mock_profile(sample_texts=texts)
        _run_analysis(profile)

        assert profile.sample_count == 2

    def test_analysis_updates_timestamp(self):
        """_run_analysis should update the updated_at timestamp."""
        from app.modules.style_cloning.service import _run_analysis

        old_time = datetime(2024, 1, 1, tzinfo=UTC)
        profile = _make_mock_profile(sample_texts=[SAMPLE_TEXT])
        profile.updated_at = old_time

        _run_analysis(profile)

        assert profile.updated_at != old_time

    def test_analysis_stores_fingerprint_as_dict(self):
        """_run_analysis should store voice_fingerprint as a serializable dict."""
        from app.modules.style_cloning.service import _run_analysis

        profile = _make_mock_profile(sample_texts=[SAMPLE_TEXT])
        _run_analysis(profile)

        assert isinstance(profile.voice_fingerprint, dict)
        assert "vocabulary" in profile.voice_fingerprint
        assert "sentence" in profile.voice_fingerprint
        assert "voice_vector" in profile.voice_fingerprint

    def test_analysis_stores_style_card_as_dict(self):
        """_run_analysis should store style_card as a serializable dict."""
        from app.modules.style_cloning.service import _run_analysis

        profile = _make_mock_profile(sample_texts=[SAMPLE_TEXT])
        _run_analysis(profile)

        assert isinstance(profile.style_card, dict)
        assert "summary" in profile.style_card
        assert "tone" in profile.style_card
