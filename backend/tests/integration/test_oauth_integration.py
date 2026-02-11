"""Integration tests for OAuth authentication flow.

Tests the complete OAuth flow including authorization URL generation,
callback handling, state validation, user creation/linking, and token issuance.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from httpx import Response

from app.modules.auth import service
from app.modules.auth.oauth_providers import OAuthTokens, OAuthUserInfo
from app.models.user import User, OAuthAccount, UserRole
from app.models.organization import Organization
from app.core.security import hash_password
from app.core.exceptions import AppException


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


async def _seed_user(db, *, email="oauth@test.com"):
    """Create a user + org for OAuth linking tests."""
    org_id = uuid4()
    org = Organization(id=org_id, name="TestOrg", slug=f"testorg-{str(org_id)[:8]}")
    db.add(org)

    user_id = uuid4()
    user = User(
        id=user_id,
        org_id=org_id,
        email=email,
        name="Test User",
        password_hash=hash_password("TestP@ss123"),
        role=UserRole.OWNER,
        email_verified=True,
    )
    db.add(user)
    await db.flush()
    return user


# ---------------------------------------------------------------------------
# Google OAuth integration tests
# ---------------------------------------------------------------------------


class TestGoogleOAuthIntegration:
    """Test complete Google OAuth flow."""

    @pytest.mark.asyncio
    async def test_generate_google_auth_url(self):
        """Test Google authorization URL generation."""
        with patch("app.modules.auth.oauth_providers.get_settings") as mock_settings:
            mock_settings.return_value.GOOGLE_CLIENT_ID = "test-client-id"
            mock_settings.return_value.GOOGLE_CLIENT_SECRET = "test-secret"
            mock_settings.return_value.GOOGLE_REDIRECT_URI = "http://localhost/callback"

            result = service.generate_google_auth_url()

            assert result.provider == "google"
            assert "accounts.google.com/o/oauth2/v2/auth" in result.authorization_url
            assert "client_id=test-client-id" in result.authorization_url
            # State should be stored
            assert "state=" in result.authorization_url

    @pytest.mark.asyncio
    async def test_google_callback_new_user(self, db_session):
        """Test Google callback creates new user when no existing user."""
        # Mock the provider to avoid actual API calls
        mock_provider = MagicMock()
        mock_provider.exchange_code = AsyncMock(
            return_value=OAuthTokens(
                access_token="google-access-token",
                refresh_token="google-refresh-token",
            )
        )
        mock_provider.get_user_info = AsyncMock(
            return_value=OAuthUserInfo(
                provider_user_id="google-123",
                email="newuser@example.com",
                name="New User",
                avatar_url="https://example.com/avatar.jpg",
            )
        )

        with patch("app.modules.auth.service.get_oauth_provider", return_value=mock_provider):
            # Generate state and store it
            state = "test-state-token"
            service._store_oauth_state(state, "google")

            result = await service.handle_google_callback(
                db_session,
                code="test-code",
                state=state,
            )

            assert result["user"]["email"] == "newuser@example.com"
            assert result["user"]["name"] == "New User"
            assert result["tokens"].access_token
            assert result["tokens"].refresh_token

        # Verify user was created
        from sqlalchemy import select
        user_result = await db_session.execute(
            select(User).where(User.email == "newuser@example.com")
        )
        user = user_result.scalar_one_or_none()
        assert user is not None
        assert user.email_verified is True  # OAuth users are pre-verified

        # Verify OAuth account was linked
        oauth_result = await db_session.execute(
            select(OAuthAccount).where(OAuthAccount.user_id == user.id)
        )
        oauth_account = oauth_result.scalar_one_or_none()
        assert oauth_account is not None
        assert oauth_account.provider == "google"
        assert oauth_account.provider_user_id == "google-123"

    @pytest.mark.asyncio
    async def test_google_callback_existing_user(self, db_session):
        """Test Google callback links to existing user with same email."""
        # Create existing user
        existing_user = await _seed_user(db_session, email="existing@example.com")

        # Mock the provider
        mock_provider = MagicMock()
        mock_provider.exchange_code = AsyncMock(
            return_value=OAuthTokens(access_token="google-access-token")
        )
        mock_provider.get_user_info = AsyncMock(
            return_value=OAuthUserInfo(
                provider_user_id="google-456",
                email="existing@example.com",
                name="Existing User",
            )
        )

        with patch("app.modules.auth.service.get_oauth_provider", return_value=mock_provider):
            state = "test-state-token"
            service._store_oauth_state(state, "google")

            result = await service.handle_google_callback(
                db_session,
                code="test-code",
                state=state,
            )

            assert result["user"]["id"] == str(existing_user.id)
            assert result["user"]["email"] == "existing@example.com"

        # Verify OAuth account was created and linked
        from sqlalchemy import select
        oauth_result = await db_session.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == existing_user.id,
                OAuthAccount.provider == "google",
            )
        )
        oauth_account = oauth_result.scalar_one_or_none()
        assert oauth_account is not None
        assert oauth_account.provider_user_id == "google-456"

    @pytest.mark.asyncio
    async def test_google_callback_existing_oauth_link(self, db_session):
        """Test Google callback with existing OAuth link."""
        # Create user and OAuth link
        user = await _seed_user(db_session, email="linked@example.com")
        oauth_account = OAuthAccount(
            id=uuid4(),
            user_id=user.id,
            provider="google",
            provider_user_id="google-789",
            provider_email="linked@example.com",
            access_token="old-token",
        )
        db_session.add(oauth_account)
        await db_session.flush()

        # Mock the provider
        mock_provider = MagicMock()
        mock_provider.exchange_code = AsyncMock(
            return_value=OAuthTokens(
                access_token="new-google-token",
                refresh_token="new-refresh",
            )
        )
        mock_provider.get_user_info = AsyncMock(
            return_value=OAuthUserInfo(
                provider_user_id="google-789",
                email="linked@example.com",
                name="Linked User",
                avatar_url="https://example.com/new-avatar.jpg",
            )
        )

        with patch("app.modules.auth.service.get_oauth_provider", return_value=mock_provider):
            state = "test-state-token"
            service._store_oauth_state(state, "google")

            result = await service.handle_google_callback(
                db_session,
                code="test-code",
                state=state,
            )

            assert result["user"]["id"] == str(user.id)

        # Verify OAuth account tokens were updated
        await db_session.refresh(oauth_account)
        assert oauth_account.access_token == "new-google-token"
        assert oauth_account.refresh_token == "new-refresh"
        assert oauth_account.avatar_url == "https://example.com/new-avatar.jpg"

    @pytest.mark.asyncio
    async def test_google_callback_invalid_state(self, db_session):
        """Test Google callback rejects invalid state parameter."""
        with pytest.raises(AppException) as exc_info:
            await service.handle_google_callback(
                db_session,
                code="test-code",
                state="invalid-state",
            )

        assert exc_info.value.code == "OAUTH_INVALID_STATE"

    @pytest.mark.asyncio
    async def test_google_callback_missing_state(self, db_session):
        """Test Google callback rejects missing state parameter."""
        with pytest.raises(AppException) as exc_info:
            await service.handle_google_callback(
                db_session,
                code="test-code",
                state=None,
            )

        assert exc_info.value.code == "OAUTH_INVALID_STATE"


# ---------------------------------------------------------------------------
# GitHub OAuth integration tests
# ---------------------------------------------------------------------------


class TestGitHubOAuthIntegration:
    """Test complete GitHub OAuth flow."""

    @pytest.mark.asyncio
    async def test_generate_github_auth_url(self):
        """Test GitHub authorization URL generation."""
        with patch("app.modules.auth.oauth_providers.get_settings") as mock_settings:
            mock_settings.return_value.GITHUB_CLIENT_ID = "github-client-id"
            mock_settings.return_value.GITHUB_CLIENT_SECRET = "github-secret"
            mock_settings.return_value.GITHUB_REDIRECT_URI = "http://localhost/callback"

            result = service.generate_github_auth_url()

            assert result.provider == "github"
            assert "github.com/login/oauth/authorize" in result.authorization_url
            assert "client_id=github-client-id" in result.authorization_url

    @pytest.mark.asyncio
    async def test_github_callback_new_user(self, db_session):
        """Test GitHub callback creates new user."""
        mock_provider = MagicMock()
        mock_provider.exchange_code = AsyncMock(
            return_value=OAuthTokens(access_token="github-token")
        )
        mock_provider.get_user_info = AsyncMock(
            return_value=OAuthUserInfo(
                provider_user_id="github-999",
                email="githubuser@example.com",
                name="GitHub User",
                avatar_url="https://github.com/avatar.png",
            )
        )

        with patch("app.modules.auth.service.get_oauth_provider", return_value=mock_provider):
            state = "test-state-token"
            service._store_oauth_state(state, "github")

            result = await service.handle_github_callback(
                db_session,
                code="test-code",
                state=state,
            )

            assert result["user"]["email"] == "githubuser@example.com"
            assert result["tokens"].access_token

        # Verify user and OAuth account
        from sqlalchemy import select
        user_result = await db_session.execute(
            select(User).where(User.email == "githubuser@example.com")
        )
        user = user_result.scalar_one_or_none()
        assert user is not None

        oauth_result = await db_session.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user.id,
                OAuthAccount.provider == "github",
            )
        )
        oauth_account = oauth_result.scalar_one_or_none()
        assert oauth_account is not None
        assert oauth_account.provider_user_id == "github-999"

    @pytest.mark.asyncio
    async def test_github_callback_existing_user(self, db_session):
        """Test GitHub callback links to existing user."""
        existing_user = await _seed_user(db_session, email="gitexist@example.com")

        mock_provider = MagicMock()
        mock_provider.exchange_code = AsyncMock(
            return_value=OAuthTokens(access_token="github-token")
        )
        mock_provider.get_user_info = AsyncMock(
            return_value=OAuthUserInfo(
                provider_user_id="github-111",
                email="gitexist@example.com",
                name="GitHub Existing",
            )
        )

        with patch("app.modules.auth.service.get_oauth_provider", return_value=mock_provider):
            state = "test-state-token"
            service._store_oauth_state(state, "github")

            result = await service.handle_github_callback(
                db_session,
                code="test-code",
                state=state,
            )

            # Should link to existing user, not create new one
            assert result["user"]["id"] == str(existing_user.id)

        # Verify no duplicate users
        from sqlalchemy import select, func
        count_result = await db_session.execute(
            select(func.count()).select_from(User).where(User.email == "gitexist@example.com")
        )
        user_count = count_result.scalar()
        assert user_count == 1


# ---------------------------------------------------------------------------
# State management tests
# ---------------------------------------------------------------------------


class TestOAuthStateManagement:
    """Test OAuth state parameter CSRF protection."""

    @pytest.mark.asyncio
    async def test_state_storage_and_validation(self):
        """Test state is stored and validated correctly."""
        state = "unique-state-token"
        service._store_oauth_state(state, "google")

        # Should validate successfully
        service._validate_oauth_state(state, "google")

        # Should fail second time (one-time use)
        with pytest.raises(AppException) as exc_info:
            service._validate_oauth_state(state, "google")
        assert exc_info.value.code == "OAUTH_INVALID_STATE"

    @pytest.mark.asyncio
    async def test_state_provider_mismatch(self):
        """Test state validation fails for wrong provider."""
        state = "test-state"
        service._store_oauth_state(state, "google")

        with pytest.raises(AppException) as exc_info:
            service._validate_oauth_state(state, "github")

        assert exc_info.value.code == "OAUTH_INVALID_STATE"

    @pytest.mark.asyncio
    async def test_state_expiration(self):
        """Test state expires after 10 minutes."""
        import time
        from datetime import timedelta

        state = "expiring-state"
        service._store_oauth_state(state, "google")

        # Manually expire the state
        service._oauth_states[state]["created_at"] -= timedelta(minutes=11)

        with pytest.raises(AppException) as exc_info:
            service._validate_oauth_state(state, "google")

        assert exc_info.value.code == "OAUTH_STATE_EXPIRED"


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestOAuthErrorHandling:
    """Test OAuth error scenarios."""

    @pytest.mark.asyncio
    async def test_callback_provider_api_failure(self, db_session):
        """Test callback handles provider API failures gracefully."""
        mock_provider = MagicMock()
        mock_provider.exchange_code = AsyncMock(
            side_effect=AppException(
                status_code=401,
                code="OAUTH_TOKEN_ERROR",
                message="Failed to exchange code",
            )
        )

        with patch("app.modules.auth.service.get_oauth_provider", return_value=mock_provider):
            state = "test-state"
            service._store_oauth_state(state, "google")

            with pytest.raises(AppException) as exc_info:
                await service.handle_google_callback(
                    db_session,
                    code="bad-code",
                    state=state,
                )

            assert exc_info.value.code == "OAUTH_TOKEN_ERROR"

    @pytest.mark.asyncio
    async def test_callback_missing_email(self, db_session):
        """Test callback handles missing email gracefully."""
        mock_provider = MagicMock()
        mock_provider.exchange_code = AsyncMock(
            return_value=OAuthTokens(access_token="token")
        )
        mock_provider.get_user_info = AsyncMock(
            side_effect=AppException(
                status_code=400,
                code="OAUTH_NO_EMAIL",
                message="No email available",
            )
        )

        with patch("app.modules.auth.service.get_oauth_provider", return_value=mock_provider):
            state = "test-state"
            service._store_oauth_state(state, "google")

            with pytest.raises(AppException) as exc_info:
                await service.handle_google_callback(
                    db_session,
                    code="test-code",
                    state=state,
                )

            assert exc_info.value.code == "OAUTH_NO_EMAIL"
