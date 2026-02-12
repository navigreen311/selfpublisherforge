"""FastAPI router for dictation endpoints (/api/v1/dictation/...)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.dictation import schemas, service
from app.schemas.common import MessageResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /sessions — Start new dictation session
# ---------------------------------------------------------------------------
@router.post(
    "/sessions",
    response_model=schemas.SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start dictation session",
    description="Create and start a new voice dictation session.",
)
async def create_session(
    body: schemas.SessionCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new dictation session."""
    return await service.create_session(
        db,
        org_id=current_user["org_id"],
        user_id=current_user["user_id"],
        request=body,
    )


# ---------------------------------------------------------------------------
# PATCH /sessions/{session_id} — Update session (pause, resume, end)
# ---------------------------------------------------------------------------
@router.patch(
    "/sessions/{session_id}",
    response_model=schemas.SessionResponse,
    summary="Update dictation session",
    description="Update session state: pause, resume, or end. Optionally save transcript.",
)
async def update_session(
    session_id: UUID,
    body: schemas.SessionUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a dictation session."""
    return await service.update_session(
        db,
        session_id=session_id,
        user_id=current_user["user_id"],
        request=body,
    )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id} — Get session details & transcript
# ---------------------------------------------------------------------------
@router.get(
    "/sessions/{session_id}",
    response_model=schemas.SessionResponse,
    summary="Get dictation session",
    description="Retrieve session details, transcript, and refinement status.",
)
async def get_session(
    session_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dictation session by ID."""
    return await service.get_session(
        db,
        session_id=session_id,
        user_id=current_user["user_id"],
    )


# ---------------------------------------------------------------------------
# GET /sessions — List user's sessions
# ---------------------------------------------------------------------------
@router.get(
    "/sessions",
    response_model=schemas.SessionListResponse,
    summary="List dictation sessions",
    description="List the current user's dictation sessions with pagination.",
)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's dictation sessions."""
    return await service.list_sessions(
        db,
        user_id=current_user["user_id"],
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/refine — Refine session transcript
# ---------------------------------------------------------------------------
@router.post(
    "/sessions/{session_id}/refine",
    response_model=schemas.RefineResponse,
    summary="Refine session transcript",
    description="Apply AI style refinement to a session's raw transcript.",
)
async def refine_session(
    session_id: UUID,
    body: schemas.RefineSessionRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Refine a session's raw transcript."""
    return await service.refine_session(
        db,
        session_id=session_id,
        user_id=current_user["user_id"],
        request=body,
    )


# ---------------------------------------------------------------------------
# POST /refine-text — One-off text refinement
# ---------------------------------------------------------------------------
@router.post(
    "/refine-text",
    response_model=schemas.RefineResponse,
    summary="Refine arbitrary text",
    description="One-off AI refinement of arbitrary text without a session.",
)
async def refine_text(
    body: schemas.RefineTextRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Refine arbitrary text (no session required)."""
    return await service.refine_text(request=body)


# ---------------------------------------------------------------------------
# GET /commands — List available voice commands
# ---------------------------------------------------------------------------
@router.get(
    "/commands",
    response_model=schemas.CommandListResponse,
    summary="List voice commands",
    description="List all available voice commands (system defaults + org-custom).",
)
async def list_commands(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List voice commands."""
    return await service.list_commands(db, org_id=current_user["org_id"])


# ---------------------------------------------------------------------------
# POST /commands — Create custom voice command
# ---------------------------------------------------------------------------
@router.post(
    "/commands",
    response_model=schemas.CommandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create voice command",
    description="Create a custom voice command for the organization.",
)
async def create_command(
    body: schemas.CommandCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom voice command."""
    return await service.create_command(
        db,
        org_id=current_user["org_id"],
        request=body,
    )


# ---------------------------------------------------------------------------
# DELETE /commands/{command_id} — Delete custom voice command
# ---------------------------------------------------------------------------
@router.delete(
    "/commands/{command_id}",
    response_model=MessageResponse,
    summary="Delete voice command",
    description="Delete a custom voice command. System commands cannot be deleted.",
)
async def delete_command(
    command_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom voice command."""
    await service.delete_command(
        db,
        command_id=command_id,
        org_id=current_user["org_id"],
    )
    return MessageResponse(message=f"Command {command_id} deleted successfully")


# ---------------------------------------------------------------------------
# GET /settings — Get user dictation preferences
# ---------------------------------------------------------------------------
@router.get(
    "/settings",
    response_model=schemas.SettingsResponse,
    summary="Get dictation settings",
    description="Get the current user's dictation preferences.",
)
async def get_settings(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user dictation settings."""
    return await service.get_settings(db, user_id=current_user["user_id"])


# ---------------------------------------------------------------------------
# PATCH /settings — Update user dictation preferences
# ---------------------------------------------------------------------------
@router.patch(
    "/settings",
    response_model=schemas.SettingsResponse,
    summary="Update dictation settings",
    description="Update the current user's dictation preferences.",
)
async def update_settings(
    body: schemas.SettingsUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user dictation settings."""
    return await service.update_settings(
        db,
        user_id=current_user["user_id"],
        request=body,
    )
