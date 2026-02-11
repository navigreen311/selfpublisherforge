"""OAuth provider abstraction and implementations for Google and GitHub.

This module provides a clean abstraction over different OAuth providers,
making it easy to add new providers and test OAuth flows.
"""

import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from app.core.exceptions import AppException


@dataclass
class OAuthTokens:
    """OAuth token response from provider."""
    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None
    token_type: str = "Bearer"


@dataclass
class OAuthUserInfo:
    """Normalized user information from OAuth provider."""
    provider_user_id: str
    email: str
    name: str
    avatar_url: str | None = None


class OAuthProvider(ABC):
    """Abstract base class for OAuth providers."""

    def __init__(self):
        self.settings = get_settings()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'google', 'github')."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is configured with necessary credentials."""
        pass

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Generate the OAuth authorization URL with CSRF state parameter."""
        pass

    @abstractmethod
    async def exchange_code(self, code: str) -> OAuthTokens:
        """Exchange authorization code for access and refresh tokens."""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Fetch user information using the access token."""
        pass

    def generate_state(self) -> str:
        """Generate a secure CSRF state token."""
        return secrets.token_urlsafe(32)


class GoogleOAuth(OAuthProvider):
    """Google OAuth 2.0 provider implementation."""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    SCOPES = "openid email profile"

    @property
    def provider_name(self) -> str:
        return "google"

    def is_configured(self) -> bool:
        """Check if Google OAuth is configured."""
        return bool(
            self.settings.GOOGLE_CLIENT_ID
            and self.settings.GOOGLE_CLIENT_SECRET
            and self.settings.GOOGLE_REDIRECT_URI
        )

    def get_authorization_url(self, state: str) -> str:
        """Build the Google OAuth2 authorization URL."""
        if not self.is_configured():
            raise AppException(
                status_code=501,
                code="OAUTH_NOT_CONFIGURED",
                message="Google OAuth is not configured.",
            )

        params = {
            "client_id": self.settings.GOOGLE_CLIENT_ID,
            "redirect_uri": self.settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": self.SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthTokens:
        """Exchange Google authorization code for tokens."""
        if not self.is_configured():
            raise AppException(
                status_code=501,
                code="OAUTH_NOT_CONFIGURED",
                message="Google OAuth is not configured.",
            )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": self.settings.GOOGLE_CLIENT_ID,
                        "client_secret": self.settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": self.settings.GOOGLE_REDIRECT_URI,
                        "grant_type": "authorization_code",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise AppException(
                    status_code=401,
                    code="OAUTH_TOKEN_ERROR",
                    message=f"Failed to exchange Google authorization code: {e.response.status_code}",
                ) from e
            except httpx.RequestError as e:
                raise AppException(
                    status_code=502,
                    code="OAUTH_NETWORK_ERROR",
                    message=f"Network error during Google token exchange: {e!s}",
                ) from e

            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise AppException(
                    status_code=401,
                    code="OAUTH_TOKEN_ERROR",
                    message="No access token in Google response.",
                )

            return OAuthTokens(
                access_token=access_token,
                refresh_token=token_data.get("refresh_token"),
                expires_in=token_data.get("expires_in"),
            )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Fetch Google user profile information."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise AppException(
                    status_code=401,
                    code="OAUTH_PROFILE_ERROR",
                    message=f"Failed to fetch Google user profile: {e.response.status_code}",
                ) from e
            except httpx.RequestError as e:
                raise AppException(
                    status_code=502,
                    code="OAUTH_NETWORK_ERROR",
                    message=f"Network error fetching Google profile: {e!s}",
                ) from e

            profile = response.json()

        google_id = profile.get("id")
        email = profile.get("email")

        if not google_id:
            raise AppException(
                status_code=400,
                code="OAUTH_INVALID_RESPONSE",
                message="Google profile missing user ID.",
            )

        if not email:
            raise AppException(
                status_code=400,
                code="OAUTH_NO_EMAIL",
                message="Google account does not have an email address.",
            )

        name = profile.get("name", email.split("@")[0])
        avatar = profile.get("picture")

        return OAuthUserInfo(
            provider_user_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar,
        )


class GitHubOAuth(OAuthProvider):
    """GitHub OAuth 2.0 provider implementation."""

    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"
    SCOPES = "read:user user:email"

    @property
    def provider_name(self) -> str:
        return "github"

    def is_configured(self) -> bool:
        """Check if GitHub OAuth is configured."""
        return bool(
            self.settings.GITHUB_CLIENT_ID
            and self.settings.GITHUB_CLIENT_SECRET
            and self.settings.GITHUB_REDIRECT_URI
        )

    def get_authorization_url(self, state: str) -> str:
        """Build the GitHub OAuth authorization URL."""
        if not self.is_configured():
            raise AppException(
                status_code=501,
                code="OAUTH_NOT_CONFIGURED",
                message="GitHub OAuth is not configured.",
            )

        params = {
            "client_id": self.settings.GITHUB_CLIENT_ID,
            "redirect_uri": self.settings.GITHUB_REDIRECT_URI,
            "scope": self.SCOPES,
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthTokens:
        """Exchange GitHub authorization code for tokens."""
        if not self.is_configured():
            raise AppException(
                status_code=501,
                code="OAUTH_NOT_CONFIGURED",
                message="GitHub OAuth is not configured.",
            )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "client_id": self.settings.GITHUB_CLIENT_ID,
                        "client_secret": self.settings.GITHUB_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": self.settings.GITHUB_REDIRECT_URI,
                    },
                    headers={"Accept": "application/json"},
                    timeout=10.0,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise AppException(
                    status_code=401,
                    code="OAUTH_TOKEN_ERROR",
                    message=f"Failed to exchange GitHub authorization code: {e.response.status_code}",
                ) from e
            except httpx.RequestError as e:
                raise AppException(
                    status_code=502,
                    code="OAUTH_NETWORK_ERROR",
                    message=f"Network error during GitHub token exchange: {e!s}",
                ) from e

            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise AppException(
                    status_code=401,
                    code="OAUTH_TOKEN_ERROR",
                    message="No access token in GitHub response.",
                )

            return OAuthTokens(
                access_token=access_token,
                refresh_token=token_data.get("refresh_token"),
                expires_in=token_data.get("expires_in"),
            )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Fetch GitHub user profile and email information."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            # Fetch user profile
            try:
                profile_resp = await client.get(
                    self.USER_URL,
                    headers=headers,
                    timeout=10.0,
                )
                profile_resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise AppException(
                    status_code=401,
                    code="OAUTH_PROFILE_ERROR",
                    message=f"Failed to fetch GitHub user profile: {e.response.status_code}",
                ) from e
            except httpx.RequestError as e:
                raise AppException(
                    status_code=502,
                    code="OAUTH_NETWORK_ERROR",
                    message=f"Network error fetching GitHub profile: {e!s}",
                ) from e

            profile = profile_resp.json()

            github_id = str(profile.get("id"))
            email = profile.get("email")
            name = profile.get("name") or profile.get("login", "User")
            avatar = profile.get("avatar_url")

            if not github_id:
                raise AppException(
                    status_code=400,
                    code="OAUTH_INVALID_RESPONSE",
                    message="GitHub profile missing user ID.",
                )

            # GitHub may not return email in the profile; fetch from /user/emails
            if not email:
                try:
                    emails_resp = await client.get(
                        self.EMAILS_URL,
                        headers=headers,
                        timeout=10.0,
                    )
                    if emails_resp.status_code == 200:
                        emails = emails_resp.json()
                        # Prefer the primary verified email
                        for em in emails:
                            if em.get("primary") and em.get("verified"):
                                email = em["email"]
                                break
                        # Fallback to any verified email
                        if not email:
                            for em in emails:
                                if em.get("verified"):
                                    email = em["email"]
                                    break
                except (httpx.HTTPStatusError, httpx.RequestError):
                    # If we can't fetch emails, we'll raise below
                    pass

            if not email:
                raise AppException(
                    status_code=400,
                    code="OAUTH_NO_EMAIL",
                    message="GitHub account does not have a verified email address.",
                )

            return OAuthUserInfo(
                provider_user_id=github_id,
                email=email,
                name=name,
                avatar_url=avatar,
            )


# Factory function for getting providers
def get_oauth_provider(provider_name: str) -> OAuthProvider:
    """Get an OAuth provider instance by name.

    Args:
        provider_name: The provider name ('google' or 'github')

    Returns:
        An instance of the appropriate OAuth provider

    Raises:
        AppException: If the provider is not supported
    """
    providers = {
        "google": GoogleOAuth,
        "github": GitHubOAuth,
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise AppException(
            status_code=400,
            code="INVALID_PROVIDER",
            message=f"OAuth provider '{provider_name}' is not supported.",
        )

    return provider_class()
