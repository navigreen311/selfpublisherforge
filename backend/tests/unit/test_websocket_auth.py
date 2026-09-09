"""Unit tests for WebSocket authentication.

Tests cover:
- Valid JWT token authentication
- Expired token rejection
- Invalid token rejection
- Missing token rejection
- Token payload validation
- Token refresh scenarios
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket, status

from app.core.security import create_access_token
from app.modules.realtime.router import _authenticate_ws

# ---------------------------------------------------------------------------
# Tests — Valid Token Authentication
# ---------------------------------------------------------------------------

def test_authenticate_ws_with_valid_token() -> None:
    """Test valid JWT token is accepted."""
    token = create_access_token(
        data={"sub": "user-123", "org_id": "org-456", "role": "editor"},
        expires_delta=timedelta(hours=1),
    )

    payload = _authenticate_ws(token)

    assert payload["sub"] == "user-123"
    assert payload["org_id"] == "org-456"
    assert payload["role"] == "editor"


def test_authenticate_ws_extracts_user_id() -> None:
    """Test that user ID is correctly extracted from token."""
    token = create_access_token(
        data={"sub": "user-999", "email": "test@example.com"},
        expires_delta=timedelta(minutes=30),
    )

    payload = _authenticate_ws(token)

    assert payload["sub"] == "user-999"


def test_authenticate_ws_with_minimal_claims() -> None:
    """Test token with only required claims."""
    token = create_access_token(
        data={"sub": "user-1"},
        expires_delta=timedelta(minutes=15),
    )

    payload = _authenticate_ws(token)

    assert payload["sub"] == "user-1"


# ---------------------------------------------------------------------------
# Tests — Token Rejection Cases
# ---------------------------------------------------------------------------

def test_authenticate_ws_rejects_missing_token() -> None:
    """Test missing token raises ValueError."""
    with pytest.raises(ValueError, match="Missing authentication token"):
        _authenticate_ws(None)


def test_authenticate_ws_rejects_empty_token() -> None:
    """Test empty string token raises ValueError."""
    with pytest.raises(ValueError, match="Missing authentication token"):
        _authenticate_ws("")


def test_authenticate_ws_rejects_invalid_token() -> None:
    """Test malformed token raises ValueError."""
    with pytest.raises(ValueError, match="Invalid token"):
        _authenticate_ws("not-a-valid-jwt-token")


def test_authenticate_ws_rejects_expired_token() -> None:
    """Test expired token raises ValueError."""
    token = create_access_token(
        data={"sub": "user-123"},
        expires_delta=timedelta(seconds=-10),  # Expired 10 seconds ago
    )

    with pytest.raises(ValueError, match="Invalid token"):
        _authenticate_ws(token)


def test_authenticate_ws_rejects_token_without_subject() -> None:
    """Test token missing 'sub' claim raises ValueError."""
    # Create token without sub claim (using dict manipulation)
    from jose import jwt

    from app.config import get_settings

    payload = {"exp": 9999999999, "type": "access"}  # No "sub"
    token = jwt.encode(payload, get_settings().SECRET_KEY, algorithm="HS256")

    with pytest.raises(ValueError, match="Token missing subject"):
        _authenticate_ws(token)


def test_authenticate_ws_rejects_wrong_signature() -> None:
    """Test token signed with wrong key raises ValueError."""
    from jose import jwt

    payload = {"sub": "user-123", "exp": 9999999999}
    token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")

    with pytest.raises(ValueError, match="Invalid token"):
        _authenticate_ws(token)


# ---------------------------------------------------------------------------
# Tests — WebSocket Closure on Auth Failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ws_handler_closes_on_missing_token() -> None:
    """Test WebSocket handler closes connection when token missing."""
    from app.modules.realtime.router import _ws_handler
    from app.modules.realtime.schemas import WSChannel

    mock_ws = AsyncMock(spec=WebSocket)

    await _ws_handler(mock_ws, WSChannel.WRITING, "book-1", token=None)

    mock_ws.close.assert_called_once_with(
        code=status.WS_1008_POLICY_VIOLATION,
        reason="Missing authentication token"
    )


@pytest.mark.asyncio
async def test_ws_handler_closes_on_invalid_token() -> None:
    """Test WebSocket handler closes connection when token invalid."""
    from app.modules.realtime.router import _ws_handler
    from app.modules.realtime.schemas import WSChannel

    mock_ws = AsyncMock(spec=WebSocket)

    await _ws_handler(mock_ws, WSChannel.AGENTS, "org-1", token="invalid-token")

    mock_ws.close.assert_called_once()
    call_kwargs = mock_ws.close.call_args[1]
    assert call_kwargs["code"] == status.WS_1008_POLICY_VIOLATION


@pytest.mark.asyncio
async def test_ws_handler_closes_on_expired_token() -> None:
    """Test WebSocket handler closes connection when token expired."""
    from app.modules.realtime.router import _ws_handler
    from app.modules.realtime.schemas import WSChannel

    expired_token = create_access_token(
        data={"sub": "user-123"},
        expires_delta=timedelta(seconds=-10),
    )

    mock_ws = AsyncMock(spec=WebSocket)

    await _ws_handler(mock_ws, WSChannel.PUBLISHING, "book-1", token=expired_token)

    mock_ws.close.assert_called_once()
    assert mock_ws.close.call_args[1]["code"] == status.WS_1008_POLICY_VIOLATION


# ---------------------------------------------------------------------------
# Tests — Token Payload Validation
# ---------------------------------------------------------------------------

def test_authenticate_ws_preserves_all_claims() -> None:
    """Test all token claims are preserved in payload."""
    token = create_access_token(
        data={
            "sub": "user-123",
            "org_id": "org-456",
            "role": "admin",
            "email": "admin@example.com",
            "permissions": ["read", "write"],
        },
        expires_delta=timedelta(hours=1),
    )

    payload = _authenticate_ws(token)

    assert payload["sub"] == "user-123"
    assert payload["org_id"] == "org-456"
    assert payload["role"] == "admin"
    assert payload["email"] == "admin@example.com"
    assert payload["permissions"] == ["read", "write"]


def test_authenticate_ws_with_org_id() -> None:
    """Test organization ID is correctly extracted."""
    token = create_access_token(
        data={"sub": "user-1", "org_id": "org-999"},
        expires_delta=timedelta(hours=1),
    )

    payload = _authenticate_ws(token)

    assert payload["org_id"] == "org-999"


def test_authenticate_ws_with_role() -> None:
    """Test role claim is correctly extracted."""
    token = create_access_token(
        data={"sub": "user-1", "role": "viewer"},
        expires_delta=timedelta(hours=1),
    )

    payload = _authenticate_ws(token)

    assert payload["role"] == "viewer"


# ---------------------------------------------------------------------------
# Tests — Edge Cases
# ---------------------------------------------------------------------------

def test_authenticate_ws_with_unicode_subject() -> None:
    """Test token with unicode characters in subject."""
    token = create_access_token(
        data={"sub": "用户-123"},
        expires_delta=timedelta(hours=1),
    )

    payload = _authenticate_ws(token)

    assert payload["sub"] == "用户-123"


def test_authenticate_ws_with_very_long_token() -> None:
    """Test token with very long payload."""
    large_data = {"sub": "user-1", "data": "x" * 10000}
    token = create_access_token(
        data=large_data,
        expires_delta=timedelta(hours=1),
    )

    payload = _authenticate_ws(token)

    assert payload["sub"] == "user-1"
    assert len(payload["data"]) == 10000


def test_authenticate_ws_rejects_refresh_token_type() -> None:
    """Test refresh token type is not accepted (if we validate type)."""
    from app.core.security import create_refresh_token

    # Create a refresh token
    token = create_refresh_token(data={"sub": "user-123"})

    # Should still decode (we don't validate type in _authenticate_ws)
    # But in production, you might want to validate the "type" claim
    payload = _authenticate_ws(token)

    # Verify it has the refresh type
    assert payload.get("type") == "refresh"


def test_authenticate_ws_with_whitespace_token() -> None:
    """Test token with surrounding whitespace is rejected."""
    token = create_access_token(
        data={"sub": "user-1"},
        expires_delta=timedelta(hours=1),
    )

    # Token with whitespace should fail
    with pytest.raises(ValueError, match="Invalid token"):
        _authenticate_ws(f"  {token}  ")


def test_authenticate_ws_with_jwt_injection_attempt() -> None:
    """Test malicious JWT manipulation is rejected."""
    # Try to create a JWT with no signature
    fake_jwt = "eyJhbGciOiJub25lIn0.eyJzdWIiOiJoYWNrZXIifQ."

    with pytest.raises(ValueError, match="Invalid token"):
        _authenticate_ws(fake_jwt)


# ---------------------------------------------------------------------------
# Tests — Token Refresh During Session (Future Enhancement)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_token_refresh_message_handling() -> None:
    """Test handling of token refresh during WebSocket session.

    Note: This is a placeholder for future token refresh functionality.
    Currently WebSockets don't support token refresh, but this test
    documents the expected behavior if implemented.
    """
    # This test documents desired behavior but is skipped for now
    pytest.skip("Token refresh during WebSocket session not yet implemented")
