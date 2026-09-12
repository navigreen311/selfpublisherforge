"""Business logic for dictation sessions, voice commands, and settings."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.dictation.models import DictationCommand, DictationSession, DictationSettings
from app.modules.dictation.schemas import (
    CommandCreateRequest,
    CommandListResponse,
    CommandResponse,
    RefineResponse,
    RefineSessionRequest,
    RefineTextRequest,
    SessionCreateRequest,
    SessionListItem,
    SessionListResponse,
    SessionResponse,
    SessionUpdateRequest,
    SettingsResponse,
    SettingsUpdateRequest,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default system commands (seeded on first list access for an org)
# ---------------------------------------------------------------------------

SYSTEM_COMMANDS: list[tuple[str, str, str | None]] = [
    ("new paragraph", "new_paragraph", "Insert a paragraph break"),
    ("new line", "new_line", "Insert a line break"),
    ("period", "insert_period", "Insert a period"),
    ("comma", "insert_comma", "Insert a comma"),
    ("question mark", "insert_question_mark", "Insert a question mark"),
    ("delete that", "delete_last_sentence", "Delete the last sentence"),
    ("undo", "undo", "Undo the last action"),
    ("bold that", "apply_bold", "Apply bold to last phrase"),
    ("italic that", "apply_italic", "Apply italic to last phrase"),
    ("chapter break", "chapter_break", "Insert a chapter break"),
    ("stop dictation", "stop_dictation", "End the dictation session"),
    ("read that back", "read_back", "Read the last passage aloud"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _session_to_response(session: DictationSession) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        org_id=session.org_id,
        title=session.title,
        project_id=session.project_id,
        language=session.language,
        status=session.status.value if hasattr(session.status, "value") else session.status,
        raw_transcript=session.raw_transcript,
        refined_text=session.refined_text,
        refinement_applied=session.refinement_applied,
        word_count=session.words_dictated,
        words_after_refinement=session.words_after_refinement,
        duration_seconds=session.duration_seconds,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _command_to_response(cmd: DictationCommand) -> CommandResponse:
    return CommandResponse(
        id=cmd.id,
        trigger_phrase=cmd.command_phrase,
        action=cmd.action,
        description=cmd.description,
        is_system=cmd.is_system,
        org_id=cmd.org_id,
        created_at=cmd.created_at,
    )


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


async def create_session(
    db: AsyncSession,
    org_id: UUID,
    user_id: UUID,
    request: SessionCreateRequest,
) -> SessionResponse:
    """Start a new dictation session."""
    session = DictationSession(
        user_id=user_id,
        org_id=org_id,
        title=request.title,
        project_id=request.project_id,
        language=request.language,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info("Created dictation session %s for user %s", session.id, user_id)
    return _session_to_response(session)


async def update_session(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
    request: SessionUpdateRequest,
) -> SessionResponse:
    """Update session status, save transcript, etc."""
    query = select(DictationSession).where(
        DictationSession.id == session_id,
        DictationSession.deleted_at.is_(None),
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise AppException(
            status_code=404,
            code="SESSION_NOT_FOUND",
            message="Dictation session not found",
        )

    if session.user_id != user_id:
        raise AppException(
            status_code=403,
            code="ACCESS_DENIED",
            message="Access denied",
        )

    action = request.action
    if action == "pause":
        session.status = "paused"
    elif action == "resume":
        session.status = "active"
    elif action == "end":
        session.status = "ended"

    if request.raw_transcript is not None:
        session.raw_transcript = request.raw_transcript
        session.words_dictated = len(request.raw_transcript.split())

    if request.duration_seconds is not None:
        session.duration_seconds = request.duration_seconds

    session.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(session)

    logger.info("Updated dictation session %s — action=%s", session_id, action)
    return _session_to_response(session)


async def get_session(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
) -> SessionResponse:
    """Get session details by ID."""
    query = select(DictationSession).where(
        DictationSession.id == session_id,
        DictationSession.deleted_at.is_(None),
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise AppException(
            status_code=404,
            code="SESSION_NOT_FOUND",
            message="Dictation session not found",
        )

    if session.user_id != user_id:
        raise AppException(
            status_code=403,
            code="ACCESS_DENIED",
            message="Access denied",
        )

    return _session_to_response(session)


async def list_sessions(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> SessionListResponse:
    """List a user's dictation sessions (paginated, newest first)."""
    base = select(DictationSession).where(
        DictationSession.user_id == user_id,
        DictationSession.deleted_at.is_(None),
    )

    # Total count
    count_q = select(func.count()).select_from(base.subquery())
    total = await db.scalar(count_q) or 0

    # Paginate
    offset = (page - 1) * page_size
    query = base.order_by(DictationSession.created_at.desc()).limit(page_size).offset(offset)
    result = await db.execute(query)
    sessions = result.scalars().all()

    items = [
        SessionListItem(
            id=s.id,
            title=s.title,
            status=s.status.value if hasattr(s.status, "value") else s.status,
            word_count=s.words_dictated,
            duration_seconds=s.duration_seconds,
            refinement_applied=s.refinement_applied,
            created_at=s.created_at,
        )
        for s in sessions
    ]

    return SessionListResponse(sessions=items, total=total)


# ---------------------------------------------------------------------------
# Refinement
# ---------------------------------------------------------------------------


async def refine_session(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
    request: RefineSessionRequest,
) -> RefineResponse:
    """Apply DictationRefiner to a session's raw transcript."""
    from app.services.voiceforge.dictation_refiner import DictationRefiner

    # Fetch the ORM object directly for mutation
    query = select(DictationSession).where(
        DictationSession.id == session_id,
        DictationSession.deleted_at.is_(None),
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise AppException(
            status_code=404,
            code="SESSION_NOT_FOUND",
            message="Dictation session not found",
        )

    if session.user_id != user_id:
        raise AppException(
            status_code=403,
            code="ACCESS_DENIED",
            message="Access denied",
        )

    raw = session.raw_transcript or ""
    if not raw.strip():
        raise AppException(
            status_code=422,
            code="EMPTY_TRANSCRIPT",
            message="Session has no raw transcript to refine",
        )

    refiner = DictationRefiner()
    refined = await refiner.refine_transcript(
        raw,
        style_profile_id=str(request.style_profile_id) if request.style_profile_id else None,
    )

    refined_text = refined.refined_text
    session.refined_text = refined_text
    session.refinement_applied = True
    session.words_after_refinement = len(refined_text.split())
    session.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(session)

    logger.info("Refined dictation session %s", session_id)

    return RefineResponse(
        refined_text=refined_text,
        original_length=len(raw.split()),
        refined_length=len(refined_text.split()),
        style_profile_id=request.style_profile_id,
    )


async def refine_text(request: RefineTextRequest) -> RefineResponse:
    """One-off refinement of arbitrary text (no session required)."""
    from app.services.voiceforge.dictation_refiner import DictationRefiner

    refiner = DictationRefiner()
    refined = await refiner.refine_transcript(
        request.text,
        style_profile_id=str(request.style_profile_id) if request.style_profile_id else None,
    )

    return RefineResponse(
        refined_text=refined.refined_text,
        original_length=len(request.text.split()),
        refined_length=len(refined.refined_text.split()),
        style_profile_id=request.style_profile_id,
    )


# ---------------------------------------------------------------------------
# Voice commands
# ---------------------------------------------------------------------------


async def _ensure_system_commands(db: AsyncSession) -> None:
    """Seed default system commands if none exist yet."""
    count_q = select(func.count()).select_from(
        select(DictationCommand).where(DictationCommand.is_system.is_(True)).subquery()
    )
    count = await db.scalar(count_q) or 0
    if count > 0:
        return

    for trigger, action, desc in SYSTEM_COMMANDS:
        cmd = DictationCommand(
            # The column is command_phrase; trigger_phrase is the API field.
            # This constructor used the API name, so seeding the built-in
            # commands raised TypeError every time it was called — which is
            # why `list_commands` has only ever returned an org's own.
            command_phrase=trigger,
            action=action,
            description=desc,
            is_system=True,
            org_id=None,
        )
        db.add(cmd)

    await db.commit()
    logger.info("Seeded %d system dictation commands", len(SYSTEM_COMMANDS))


async def list_commands(
    db: AsyncSession,
    org_id: UUID,
) -> CommandListResponse:
    """List all voice commands (system + org-custom)."""
    await _ensure_system_commands(db)

    query = select(DictationCommand).where(
        DictationCommand.deleted_at.is_(None),
        (DictationCommand.is_system.is_(True)) | (DictationCommand.org_id == org_id),
    )
    result = await db.execute(query)
    commands = result.scalars().all()

    items = [_command_to_response(c) for c in commands]
    return CommandListResponse(commands=items, total=len(items))


async def create_command(
    db: AsyncSession,
    org_id: UUID,
    request: CommandCreateRequest,
) -> CommandResponse:
    """Create a custom voice command for an organization."""
    cmd = DictationCommand(
        # The ORM column is command_phrase; the request field is trigger_phrase.
        command_phrase=request.trigger_phrase,
        action=request.action,
        # NOTE: request.description is accepted by the API and then dropped —
        # DictationCommand has no description column. Passing it here raised
        # TypeError, so this endpoint has never created a command. Persisting
        # it needs a schema change; see the missing-columns list.
        is_system=False,
        org_id=org_id,
    )
    db.add(cmd)
    await db.commit()
    await db.refresh(cmd)

    logger.info("Created custom dictation command %s for org %s", cmd.id, org_id)
    return _command_to_response(cmd)


async def delete_command(
    db: AsyncSession,
    command_id: UUID,
    org_id: UUID,
) -> None:
    """Soft-delete a custom voice command. System commands cannot be deleted."""
    query = select(DictationCommand).where(
        DictationCommand.id == command_id,
        DictationCommand.deleted_at.is_(None),
    )
    result = await db.execute(query)
    cmd = result.scalar_one_or_none()

    if not cmd:
        raise AppException(
            status_code=404,
            code="COMMAND_NOT_FOUND",
            message="Voice command not found",
        )

    if cmd.is_system:
        raise AppException(
            status_code=403,
            code="CANNOT_DELETE_SYSTEM_COMMAND",
            message="System commands cannot be deleted",
        )

    if cmd.org_id != org_id:
        raise AppException(
            status_code=403,
            code="ACCESS_DENIED",
            message="Access denied",
        )

    cmd.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info("Deleted dictation command %s", command_id)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


async def get_settings(
    db: AsyncSession,
    user_id: UUID,
) -> SettingsResponse:
    """Get user dictation preferences, creating defaults if needed."""
    query = select(DictationSettings).where(DictationSettings.user_id == user_id)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = DictationSettings(user_id=user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return SettingsResponse(
        auto_punctuation=settings.auto_punctuation,
        voice_language=settings.voice_language,
        noise_cancellation=settings.noise_cancellation,
        auto_save_interval_seconds=settings.auto_save_interval_seconds,
        preferred_style_profile_id=settings.preferred_style_profile_id,
    )


async def update_settings(
    db: AsyncSession,
    user_id: UUID,
    request: SettingsUpdateRequest,
) -> SettingsResponse:
    """Update user dictation preferences."""
    query = select(DictationSettings).where(DictationSettings.user_id == user_id)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:
        settings = DictationSettings(user_id=user_id)
        db.add(settings)
        await db.flush()

    if request.auto_punctuation is not None:
        settings.auto_punctuation = request.auto_punctuation
    if request.voice_language is not None:
        settings.voice_language = request.voice_language
    if request.noise_cancellation is not None:
        settings.noise_cancellation = request.noise_cancellation
    if request.auto_save_interval_seconds is not None:
        settings.auto_save_interval_seconds = request.auto_save_interval_seconds
    if request.preferred_style_profile_id is not None:
        settings.preferred_style_profile_id = request.preferred_style_profile_id

    settings.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(settings)

    return SettingsResponse(
        auto_punctuation=settings.auto_punctuation,
        voice_language=settings.voice_language,
        noise_cancellation=settings.noise_cancellation,
        auto_save_interval_seconds=settings.auto_save_interval_seconds,
        preferred_style_profile_id=settings.preferred_style_profile_id,
    )
