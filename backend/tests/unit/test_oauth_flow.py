"""Unit tests for OAuth provider abstraction and flow logic.

Tests the OAuth provider abstraction layer (GoogleOAuth, GitHubOAuth)
including authorization URL generation, token exchange, and user info retrieval.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import HTTPStatusError, RequestError, Response

from app.core.exceptions import AppException
from app.modules.auth.oauth_providers import (
    GitHubOAuth,
    GoogleOAuth,
    OAuthTokens,
    OAuthUserInfo,
    get_oauth_provider,
)

# ---------------------------------------------------------------------------
# Test GoogleOAuth provider
# ---------------------------------------------------------------------------


class TestGoogleOAuth:
    """Test Google OAuth provider implementation."""

    @pytest.fixture
    def google_provider(self):
        """Create a GoogleOAuth instance with mocked settings."""
        with patch("app.modules.auth.oauth_providers.get_settings") as mock_settings:
            mock_settings.return_value.GOOGLE_CLIENT_ID = "test-client-id"
            mock_settings.return_value.GOOGLE_CLIENT_SECRET = "test-client-secret"
            mock_settings.return_value.GOOGLE_REDIRECT_URI = "http://localhost/callback"
            return GoogleOAuth()

    def test_provider_name(self, google_provider):
        """Test that provider name is 'google'."""
        assert google_provider.provider_name == "google"

    def test_is_configured_true(self, google_provider):
        """Test configuration check with valid credentials."""
        assert google_provider.is_configured() is True

    def test_is_configured_false(self):
        """Test configuration check with missing credentials."""
        with patch("app.modules.auth.oauth_providers.get_settings") as mock_settings:
            mock_settings.return_value.GOOGLE_CLIENT_ID = ""
            mock_settings.return_value.GOOGLE_CLIENT_SECRET = ""
            mock_settings.return_value.GOOGLE_REDIRECT_URI = ""
            provider = GoogleOAuth()
            assert provider.is_configured() is False

    def test_get_authorization_url(self, google_provider):
        """Test authorization URL generation."""
        state = "test-state-token"
        url = google_provider.get_authorization_url(state)

        assert "accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%2Fcallback" in url
        assert "state=test-state-token" in url
        assert "scope=openid+email+profile" in url

    def test_get_authorization_url_not_configured(self):
        """Test authorization URL generation when not configured."""
        with patch("app.modules.auth.oauth_providers.get_settings") as mock_settings:
            mock_settings.return_value.GOOGLE_CLIENT_ID = ""
            provider = GoogleOAuth()

            with pytest.raises(AppException) as exc_info:
                provider.get_authorization_url("test-state")

            assert exc_info.value.code == "OAUTH_NOT_CONFIGURED"

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, google_provider):
        """Test successful code exchange for tokens."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            tokens = await google_provider.exchange_code("test-code")

            assert isinstance(tokens, OAuthTokens)
            assert tokens.access_token == "test-access-token"
            assert tokens.refresh_token == "test-refresh-token"
            assert tokens.expires_in == 3600

    @pytest.mark.asyncio
    async def test_exchange_code_http_error(self, google_provider):
        """Test code exchange with HTTP error."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(AppException) as exc_info:
                await google_provider.exchange_code("bad-code")

            assert exc_info.value.code == "OAUTH_TOKEN_ERROR"

    @pytest.mark.asyncio
    async def test_exchange_code_network_error(self, google_provider):
        """Test code exchange with network error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=RequestError("Network error"))

            with pytest.raises(AppException) as exc_info:
                await google_provider.exchange_code("test-code")

            assert exc_info.value.code == "OAUTH_NETWORK_ERROR"

    @pytest.mark.asyncio
    async def test_exchange_code_missing_access_token(self, google_provider):
        """Test code exchange when response is missing access token."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"expires_in": 3600}  # Missing access_token
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(AppException) as exc_info:
                await google_provider.exchange_code("test-code")

            assert exc_info.value.code == "OAUTH_TOKEN_ERROR"

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, google_provider):
        """Test successful user info retrieval."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "12345",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            user_info = await google_provider.get_user_info("test-access-token")

            assert isinstance(user_info, OAuthUserInfo)
            assert user_info.provider_user_id == "12345"
            assert user_info.email == "user@example.com"
            assert user_info.name == "Test User"
            assert user_info.avatar_url == "https://example.com/avatar.jpg"

    @pytest.mark.asyncio
    async def test_get_user_info_missing_email(self, google_provider):
        """Test user info retrieval when email is missing."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "12345",
            "name": "Test User",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with pytest.raises(AppException) as exc_info:
                await google_provider.get_user_info("test-access-token")

            assert exc_info.value.code == "OAUTH_NO_EMAIL"

    @pytest.mark.asyncio
    async def test_get_user_info_missing_id(self, google_provider):
        """Test user info retrieval when ID is missing."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "user@example.com",
            "name": "Test User",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with pytest.raises(AppException) as exc_info:
                await google_provider.get_user_info("test-access-token")

            assert exc_info.value.code == "OAUTH_INVALID_RESPONSE"


# ---------------------------------------------------------------------------
# Test GitHubOAuth provider
# ---------------------------------------------------------------------------


class TestGitHubOAuth:
    """Test GitHub OAuth provider implementation."""

    @pytest.fixture
    def github_provider(self):
        """Create a GitHubOAuth instance with mocked settings."""
        with patch("app.modules.auth.oauth_providers.get_settings") as mock_settings:
            mock_settings.return_value.GITHUB_CLIENT_ID = "test-github-client-id"
            mock_settings.return_value.GITHUB_CLIENT_SECRET = "test-github-secret"
            mock_settings.return_value.GITHUB_REDIRECT_URI = "http://localhost/callback"
            return GitHubOAuth()

    def test_provider_name(self, github_provider):
        """Test that provider name is 'github'."""
        assert github_provider.provider_name == "github"

    def test_is_configured_true(self, github_provider):
        """Test configuration check with valid credentials."""
        assert github_provider.is_configured() is True

    def test_get_authorization_url(self, github_provider):
        """Test authorization URL generation."""
        state = "test-state-token"
        url = github_provider.get_authorization_url(state)

        assert "github.com/login/oauth/authorize" in url
        assert "client_id=test-github-client-id" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%2Fcallback" in url
        assert "state=test-state-token" in url
        assert "scope=read%3Auser+user%3Aemail" in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, github_provider):
        """Test successful code exchange for tokens."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "gho_test_token",
            "token_type": "bearer",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            tokens = await github_provider.exchange_code("test-code")

            assert isinstance(tokens, OAuthTokens)
            assert tokens.access_token == "gho_test_token"
            assert tokens.refresh_token is None  # GitHub doesn't provide refresh tokens

    @pytest.mark.asyncio
    async def test_get_user_info_with_email(self, github_provider):
        """Test user info retrieval when email is in profile."""
        profile_response = MagicMock(spec=Response)
        profile_response.status_code = 200
        profile_response.json.return_value = {
            "id": 54321,
            "login": "testuser",
            "email": "user@example.com",
            "name": "Test User",
            "avatar_url": "https://github.com/avatar.png",
        }
        profile_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=profile_response)

            user_info = await github_provider.get_user_info("test-token")

            assert user_info.provider_user_id == "54321"
            assert user_info.email == "user@example.com"
            assert user_info.name == "Test User"
            assert user_info.avatar_url == "https://github.com/avatar.png"

    @pytest.mark.asyncio
    async def test_get_user_info_fetch_emails(self, github_provider):
        """Test user info retrieval when email must be fetched from /user/emails."""
        profile_response = MagicMock(spec=Response)
        profile_response.status_code = 200
        profile_response.json.return_value = {
            "id": 54321,
            "login": "testuser",
            "email": None,  # No email in profile
            "name": "Test User",
            "avatar_url": "https://github.com/avatar.png",
        }
        profile_response.raise_for_status = MagicMock()

        emails_response = MagicMock(spec=Response)
        emails_response.status_code = 200
        emails_response.json.return_value = [
            {"email": "secondary@example.com", "verified": True, "primary": False},
            {"email": "primary@example.com", "verified": True, "primary": True},
        ]

        async def mock_get(url, **kwargs):
            if "user/emails" in url:
                return emails_response
            return profile_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=mock_get)

            user_info = await github_provider.get_user_info("test-token")

            assert user_info.email == "primary@example.com"  # Primary verified email

    @pytest.mark.asyncio
    async def test_get_user_info_no_email(self, github_provider):
        """Test user info retrieval when no email is available."""
        profile_response = MagicMock(spec=Response)
        profile_response.status_code = 200
        profile_response.json.return_value = {
            "id": 54321,
            "login": "testuser",
            "email": None,
        }
        profile_response.raise_for_status = MagicMock()

        emails_response = MagicMock(spec=Response)
        emails_response.status_code = 200
        emails_response.json.return_value = []  # No emails

        async def mock_get(url, **kwargs):
            if "user/emails" in url:
                return emails_response
            return profile_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=mock_get)

            with pytest.raises(AppException) as exc_info:
                await github_provider.get_user_info("test-token")

            assert exc_info.value.code == "OAUTH_NO_EMAIL"


# ---------------------------------------------------------------------------
# Test provider factory
# ---------------------------------------------------------------------------


class TestProviderFactory:
    """Test the OAuth provider factory function."""

    def test_get_google_provider(self):
        """Test getting Google provider instance."""
        provider = get_oauth_provider("google")
        assert isinstance(provider, GoogleOAuth)
        assert provider.provider_name == "google"

    def test_get_github_provider(self):
        """Test getting GitHub provider instance."""
        provider = get_oauth_provider("github")
        assert isinstance(provider, GitHubOAuth)
        assert provider.provider_name == "github"

    def test_get_invalid_provider(self):
        """Test getting invalid provider raises exception."""
        with pytest.raises(AppException) as exc_info:
            get_oauth_provider("invalid")

        assert exc_info.value.code == "INVALID_PROVIDER"

    def test_case_insensitive(self):
        """Test provider factory is case-insensitive."""
        provider = get_oauth_provider("GOOGLE")
        assert isinstance(provider, GoogleOAuth)
