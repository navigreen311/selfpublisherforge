"""Unit tests for dictation service functions."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.dictation.models import (
    DictationCommand,
    DictationSession,
    SessionStatus,
)
from app.modules.dictation.schemas import (
    CommandCreateRequest,
    RefineSessionRequest,
    RefineTextRequest,
    SessionCreateRequest,
    SessionUpdateRequest,
    SettingsUpdateRequest,
)
from app.modules.dictation.service import (
    create_command,
    create_session,
    delete_command,
    get_session,
    get_settings,
    list_commands,
    list_sessions,
    refine_session,
    refine_text,
    update_session,
    update_settings,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
OTHER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")


# db, org_id, user_id fixtures are provided by conftest.py in this directory.


@pytest.fixture
def mock_refiner():
    """Patch DictationRefiner and return the mock instance."""
    with patch("app.services.voiceforge.dictation_refiner.DictationRefiner") as mock_cls:
        refiner = mock_cls.return_value
        refiner.refine_transcript = AsyncMock(
            return_value=MagicMock(
                refined_text="Refined text here.",
                diff=[],
                style_match_score=0.85,
            )
        )
        yield refiner


# ---------------------------------------------------------------------------
# Helper to seed a session in the real DB
# ---------------------------------------------------------------------------


async def _create_db_session(
    db: AsyncSession,
    user_id: uuid.UUID = USER_ID,
    org_id: uuid.UUID = ORG_ID,
    *,
    raw_transcript: str | None = None,
    title: str | None = "Test Session",
    status: SessionStatus = SessionStatus.ACTIVE,
) -> DictationSession:
    """Insert a DictationSession row and return the refreshed ORM object."""
    session = DictationSession(
        user_id=user_id,
        org_id=org_id,
        title=title,
        language="en",
        status=status,
        raw_transcript=raw_transcript,
        # The ORM column is words_dictated; word_count is the API field name.
        # DictationSessionResponse maps one to the other — this helper builds a
        # row, so it has to use the column.
        words_dictated=len(raw_transcript.split()) if raw_transcript else 0,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID):
    """create_session persists a new session and returns a response."""
    request = SessionCreateRequest(title="My Dictation", language="en")

    result = await create_session(db, org_id, user_id, request)

    assert result.title == "My Dictation"
    assert result.language == "en"
    assert result.user_id == user_id
    assert result.org_id == org_id
    assert result.status == "active"
    assert result.raw_transcript is None
    assert result.refinement_applied is False
    assert result.word_count == 0


@pytest.mark.asyncio
async def test_get_session(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID):
    """get_session returns the session matching id + user_id."""
    row = await _create_db_session(db, user_id, org_id, title="Lookup Test")

    result = await get_session(db, row.id, user_id)

    assert result.id == row.id
    assert result.title == "Lookup Test"
    assert result.org_id == org_id


@pytest.mark.asyncio
async def test_get_session_not_found(db: AsyncSession, user_id: uuid.UUID):
    """get_session raises 404 for a non-existent session."""
    fake_id = uuid.uuid4()

    with pytest.raises(AppException) as exc_info:
        await get_session(db, fake_id, user_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "SESSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_session_access_denied(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID):
    """get_session raises 403 when a different user tries to access."""
    row = await _create_db_session(db, user_id, org_id)

    with pytest.raises(AppException) as exc_info:
        await get_session(db, row.id, OTHER_USER_ID)

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ACCESS_DENIED"


@pytest.mark.asyncio
async def test_list_sessions(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID):
    """list_sessions returns paginated results for the given user."""
    for i in range(3):
        await _create_db_session(db, user_id, org_id, title=f"Session {i}")

    result = await list_sessions(db, user_id, page=1, page_size=10)

    assert result.total == 3
    assert len(result.sessions) == 3
    # Newest first
    assert result.sessions[0].title == "Session 2"


@pytest.mark.asyncio
async def test_list_sessions_pagination(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID):
    """list_sessions respects page_size and page parameters."""
    for i in range(5):
        await _create_db_session(db, user_id, org_id, title=f"Session {i}")

    page1 = await list_sessions(db, user_id, page=1, page_size=2)
    page2 = await list_sessions(db, user_id, page=2, page_size=2)

    assert page1.total == 5
    assert len(page1.sessions) == 2
    assert len(page2.sessions) == 2


@pytest.mark.asyncio
async def test_list_sessions_user_isolation(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID):
    """list_sessions only returns sessions for the specified user."""
    await _create_db_session(db, user_id, org_id, title="Mine")
    await _create_db_session(db, OTHER_USER_ID, org_id, title="Theirs")

    result = await list_sessions(db, user_id, page=1, page_size=10)

    assert result.total == 1
    assert result.sessions[0].title == "Mine"


@pytest.mark.asyncio
async def test_update_session(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID):
    """update_session modifies status and transcript fields."""
    row = await _create_db_session(db, user_id, org_id)

    request = SessionUpdateRequest(
        action="pause",
        raw_transcript="Hello world this is a test",
        duration_seconds=42,
    )
    result = await update_session(db, row.id, user_id, request)

    assert result.status == "paused"
    assert result.raw_transcript == "Hello world this is a test"
    assert result.word_count == 6
    assert result.duration_seconds == 42


@pytest.mark.asyncio
async def test_update_session_end(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID):
    """update_session sets status to ended."""
    row = await _create_db_session(db, user_id, org_id)

    request = SessionUpdateRequest(action="end")
    result = await update_session(db, row.id, user_id, request)

    assert result.status == "ended"


@pytest.mark.asyncio
async def test_update_session_not_found(db: AsyncSession, user_id: uuid.UUID):
    """update_session raises 404 for missing session."""
    request = SessionUpdateRequest(action="pause")

    with pytest.raises(AppException) as exc_info:
        await update_session(db, uuid.uuid4(), user_id, request)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_session_access_denied(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID):
    """update_session raises 403 for wrong user."""
    row = await _create_db_session(db, user_id, org_id)
    request = SessionUpdateRequest(action="pause")

    with pytest.raises(AppException) as exc_info:
        await update_session(db, row.id, OTHER_USER_ID, request)

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Refinement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refine_session(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID, mock_refiner):
    """refine_session calls DictationRefiner and persists the result."""
    row = await _create_db_session(db, user_id, org_id, raw_transcript="this is some raw dictation text")

    request = RefineSessionRequest(style_profile_id=None)
    result = await refine_session(db, row.id, user_id, request)

    assert result.refined_text == "Refined text here."
    assert result.original_length == 6  # "this is some raw dictation text"
    assert result.refined_length == 3  # "Refined text here."
    mock_refiner.refine_transcript.assert_awaited_once()


@pytest.mark.asyncio
async def test_refine_session_empty_transcript(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID, mock_refiner):
    """refine_session raises 422 when transcript is empty."""
    row = await _create_db_session(db, user_id, org_id, raw_transcript="")

    request = RefineSessionRequest()

    with pytest.raises(AppException) as exc_info:
        await refine_session(db, row.id, user_id, request)

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "EMPTY_TRANSCRIPT"


@pytest.mark.asyncio
async def test_refine_session_not_found(db: AsyncSession, user_id: uuid.UUID, mock_refiner):
    """refine_session raises 404 for missing session."""
    request = RefineSessionRequest()

    with pytest.raises(AppException) as exc_info:
        await refine_session(db, uuid.uuid4(), user_id, request)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_refine_text(mock_refiner):
    """refine_text refines arbitrary text without a session."""
    request = RefineTextRequest(text="some arbitrary dictation text here")
    result = await refine_text(request)

    assert result.refined_text == "Refined text here."
    assert result.original_length == 5
    assert result.refined_length == 3
    mock_refiner.refine_transcript.assert_awaited_once()


@pytest.mark.asyncio
async def test_refine_text_with_style_profile(mock_refiner):
    """refine_text passes style_profile_id to the refiner."""
    profile_id = uuid.uuid4()
    request = RefineTextRequest(text="dictate this now", style_profile_id=profile_id)
    result = await refine_text(request)

    assert result.style_profile_id == profile_id
    call_kwargs = mock_refiner.refine_transcript.call_args
    assert call_kwargs[1]["style_profile_id"] == str(profile_id)


# ---------------------------------------------------------------------------
# Voice commands
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_command(db: AsyncSession, org_id: uuid.UUID):
    """create_command persists a custom voice command."""
    request = CommandCreateRequest(
        trigger_phrase="highlight that",
        action="apply_highlight",
        description="Apply highlight to last phrase",
    )
    result = await create_command(db, org_id, request)

    assert result.trigger_phrase == "highlight that"
    assert result.action == "apply_highlight"
    assert result.is_system is False
    assert result.org_id == org_id


@pytest.mark.asyncio
async def test_list_commands(db: AsyncSession, org_id: uuid.UUID):
    """list_commands returns system commands + org-custom commands."""
    # Create a custom command first
    request = CommandCreateRequest(
        trigger_phrase="custom cmd",
        action="custom_action",
    )
    await create_command(db, org_id, request)

    result = await list_commands(db, org_id)

    # Should have 12 system commands + 1 custom
    assert result.total == 13
    system_cmds = [c for c in result.commands if c.is_system]
    custom_cmds = [c for c in result.commands if not c.is_system]
    assert len(system_cmds) == 12
    assert len(custom_cmds) == 1
    assert custom_cmds[0].trigger_phrase == "custom cmd"


@pytest.mark.asyncio
async def test_list_commands_org_isolation(db: AsyncSession, org_id: uuid.UUID):
    """list_commands does not return custom commands from other orgs."""
    other_org = uuid.uuid4()

    await create_command(db, org_id, CommandCreateRequest(trigger_phrase="mine", action="my_action"))
    await create_command(db, other_org, CommandCreateRequest(trigger_phrase="theirs", action="their_action"))

    result = await list_commands(db, org_id)

    custom_triggers = [c.trigger_phrase for c in result.commands if not c.is_system]
    assert "mine" in custom_triggers
    assert "theirs" not in custom_triggers


@pytest.mark.asyncio
async def test_delete_command(db: AsyncSession, org_id: uuid.UUID):
    """delete_command soft-deletes a custom command."""
    request = CommandCreateRequest(
        trigger_phrase="to delete",
        action="delete_action",
    )
    created = await create_command(db, org_id, request)

    await delete_command(db, created.id, org_id)

    # Should no longer appear in list
    result = await list_commands(db, org_id)
    ids = [c.id for c in result.commands]
    assert created.id not in ids


@pytest.mark.asyncio
async def test_delete_command_not_found(db: AsyncSession, org_id: uuid.UUID):
    """delete_command raises 404 for non-existent command."""
    with pytest.raises(AppException) as exc_info:
        await delete_command(db, uuid.uuid4(), org_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "COMMAND_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_system_command_forbidden(db: AsyncSession, org_id: uuid.UUID):
    """delete_command raises 403 for system commands."""
    # Seed system commands via list_commands
    await list_commands(db, org_id)

    # Find a system command
    from sqlalchemy import select

    result = await db.execute(select(DictationCommand).where(DictationCommand.is_system.is_(True)).limit(1))
    sys_cmd = result.scalar_one()

    with pytest.raises(AppException) as exc_info:
        await delete_command(db, sys_cmd.id, org_id)

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "CANNOT_DELETE_SYSTEM_COMMAND"


@pytest.mark.asyncio
async def test_delete_command_wrong_org(db: AsyncSession, org_id: uuid.UUID):
    """delete_command raises 403 when org_id doesn't match."""
    created = await create_command(db, org_id, CommandCreateRequest(trigger_phrase="test", action="test_action"))

    other_org = uuid.uuid4()
    with pytest.raises(AppException) as exc_info:
        await delete_command(db, created.id, other_org)

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ACCESS_DENIED"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_settings(db: AsyncSession, user_id: uuid.UUID):
    """get_settings returns default settings for a new user."""
    result = await get_settings(db, user_id)

    assert result.auto_punctuation is True
    assert result.voice_language == "en"
    assert result.noise_cancellation is True
    assert result.auto_save_interval_seconds == 30
    assert result.preferred_style_profile_id is None


@pytest.mark.asyncio
async def test_get_settings_idempotent(db: AsyncSession, user_id: uuid.UUID):
    """get_settings creates defaults only once; subsequent calls return same data."""
    first = await get_settings(db, user_id)
    second = await get_settings(db, user_id)

    assert first.auto_punctuation == second.auto_punctuation
    assert first.voice_language == second.voice_language


@pytest.mark.asyncio
async def test_update_settings(db: AsyncSession, user_id: uuid.UUID):
    """update_settings modifies user dictation preferences."""
    # Ensure defaults exist
    await get_settings(db, user_id)

    request = SettingsUpdateRequest(
        auto_punctuation=False,
        voice_language="es",
        noise_cancellation=False,
        auto_save_interval_seconds=60,
    )
    result = await update_settings(db, user_id, request)

    assert result.auto_punctuation is False
    assert result.voice_language == "es"
    assert result.noise_cancellation is False
    assert result.auto_save_interval_seconds == 60


@pytest.mark.asyncio
async def test_update_settings_partial(db: AsyncSession, user_id: uuid.UUID):
    """update_settings only modifies fields that are provided."""
    await get_settings(db, user_id)

    request = SettingsUpdateRequest(voice_language="fr")
    result = await update_settings(db, user_id, request)

    # Only voice_language changed; others keep defaults
    assert result.voice_language == "fr"
    assert result.auto_punctuation is True
    assert result.noise_cancellation is True
    assert result.auto_save_interval_seconds == 30


@pytest.mark.asyncio
async def test_update_settings_creates_if_missing(db: AsyncSession, user_id: uuid.UUID):
    """update_settings creates settings row if none exists."""
    request = SettingsUpdateRequest(auto_punctuation=False)
    result = await update_settings(db, user_id, request)

    assert result.auto_punctuation is False
    # Other fields should be defaults
    assert result.voice_language == "en"
