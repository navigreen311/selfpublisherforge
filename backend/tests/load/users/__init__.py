"""User behavior patterns for load testing.

Each user class represents a different usage pattern:
- ReaderUser: Read-heavy users (60% of traffic)
- WriterUser: Content creators (30% of traffic)
- PowerUser: Full workflow users (10% of traffic)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from locust import HttpUser
from locust.exception import StopUser

from ..config import (
    API_PREFIX,
    REQUEST_TIMEOUT,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    TOKEN_REFRESH_THRESHOLD,
)

logger = logging.getLogger(__name__)


class AuthenticatedUser(HttpUser):
    """Base class for authenticated users with token management."""

    abstract = True
    access_token: str | None = None
    refresh_token: str | None = None
    token_expiry: datetime | None = None
    user_id: str | None = None
    org_id: str | None = None

    def on_start(self) -> None:
        """Called when a user starts - performs login."""
        self.login()

    def login(self) -> None:
        """Authenticate and store tokens."""
        response = self.client.post(
            f"{API_PREFIX}/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            timeout=REQUEST_TIMEOUT,
            name="/auth/login",
        )

        if response.status_code != 200:
            logger.error(f"Login failed: {response.status_code} - {response.text}")
            raise StopUser()

        data = response.json()

        # Handle MFA requirement if present
        if "mfa_required" in data:
            logger.error("MFA is enabled for test user - disable MFA for load testing")
            raise StopUser()

        tokens = data.get("tokens", {})
        self.access_token = tokens.get("access_token")
        self.refresh_token = tokens.get("refresh_token")

        if not self.access_token:
            logger.error("No access token received")
            raise StopUser()

        # Token expires in 15 minutes by default
        self.token_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)

        # Store user info
        user = data.get("user", {})
        self.user_id = user.get("id")
        self.org_id = user.get("org_id")

        logger.info(f"User logged in: {self.user_id}")

    def refresh_token_if_needed(self) -> None:
        """Refresh access token if it's about to expire."""
        if not self.token_expiry or not self.refresh_token:
            return

        time_until_expiry = (self.token_expiry - datetime.now(timezone.utc)).total_seconds()

        if time_until_expiry < TOKEN_REFRESH_THRESHOLD:
            self.refresh_access_token()

    def refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            logger.warning("No refresh token available, re-authenticating")
            self.login()
            return

        response = self.client.post(
            f"{API_PREFIX}/auth/refresh",
            json={"refresh_token": self.refresh_token},
            timeout=REQUEST_TIMEOUT,
            name="/auth/refresh",
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.token_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
            logger.debug("Token refreshed successfully")
        else:
            logger.warning(f"Token refresh failed: {response.status_code}, re-authenticating")
            self.login()

    def get_auth_headers(self) -> dict[str, str]:
        """Get authorization headers for authenticated requests."""
        self.refresh_token_if_needed()
        return {"Authorization": f"Bearer {self.access_token}"}

    def api_get(self, path: str, name: str | None = None, **kwargs: Any) -> Any:
        """Make an authenticated GET request."""
        return self.client.get(
            f"{API_PREFIX}/{path.lstrip('/')}",
            headers=self.get_auth_headers(),
            timeout=REQUEST_TIMEOUT,
            name=name or f"GET {path}",
            **kwargs,
        )

    def api_post(self, path: str, name: str | None = None, **kwargs: Any) -> Any:
        """Make an authenticated POST request."""
        return self.client.post(
            f"{API_PREFIX}/{path.lstrip('/')}",
            headers=self.get_auth_headers(),
            timeout=REQUEST_TIMEOUT,
            name=name or f"POST {path}",
            **kwargs,
        )

    def api_put(self, path: str, name: str | None = None, **kwargs: Any) -> Any:
        """Make an authenticated PUT request."""
        return self.client.put(
            f"{API_PREFIX}/{path.lstrip('/')}",
            headers=self.get_auth_headers(),
            timeout=REQUEST_TIMEOUT,
            name=name or f"PUT {path}",
            **kwargs,
        )

    def api_patch(self, path: str, name: str | None = None, **kwargs: Any) -> Any:
        """Make an authenticated PATCH request."""
        return self.client.patch(
            f"{API_PREFIX}/{path.lstrip('/')}",
            headers=self.get_auth_headers(),
            timeout=REQUEST_TIMEOUT,
            name=name or f"PATCH {path}",
            **kwargs,
        )

    def api_delete(self, path: str, name: str | None = None, **kwargs: Any) -> Any:
        """Make an authenticated DELETE request."""
        return self.client.delete(
            f"{API_PREFIX}/{path.lstrip('/')}",
            headers=self.get_auth_headers(),
            timeout=REQUEST_TIMEOUT,
            name=name or f"DELETE {path}",
            **kwargs,
        )
