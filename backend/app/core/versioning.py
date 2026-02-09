"""
API versioning utilities.

Provides helpers for managing API version routing, deprecation headers,
and preparing for future v2 support.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class APIVersion(str, Enum):
    """Supported API versions."""

    V1 = "v1"
    V2 = "v2"  # reserved for future use


# The currently-active default version.
CURRENT_VERSION: APIVersion = APIVersion.V1

# Versions that are deprecated but still functional.
DEPRECATED_VERSIONS: set[APIVersion] = set()

# Pattern to extract version from URL path: /api/v1/... -> v1
_VERSION_RE = re.compile(r"/api/(v\d+)/")


def extract_version(path: str) -> APIVersion | None:
    """
    Extract the API version from a request path.

    Returns ``None`` if no version segment is found.
    """
    match = _VERSION_RE.search(path)
    if match:
        raw = match.group(1)
        try:
            return APIVersion(raw)
        except ValueError:
            return None
    return None


def create_versioned_router(
    version: APIVersion,
    prefix: str,
    **kwargs: Any,
) -> APIRouter:
    """
    Create an ``APIRouter`` scoped to a specific API version.

    The returned router's prefix is ``/api/{version}/{prefix}``.

    Example::

        router = create_versioned_router(APIVersion.V1, "books", tags=["books"])
    """
    full_prefix = f"/api/{version.value}/{prefix.lstrip('/')}"
    return APIRouter(prefix=full_prefix, **kwargs)


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that inspects the request path for an API version and:

    1. Stores the resolved version on ``request.state.api_version``.
    2. Adds ``X-API-Version`` to the response.
    3. Adds ``Deprecation: true`` and ``Sunset`` headers when the
       requested version is deprecated.
    """

    def __init__(self, app: Any, sunset_date: str | None = None) -> None:
        super().__init__(app)
        self.sunset_date = sunset_date  # ISO-8601 date, e.g. "2026-06-01"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        version = extract_version(request.url.path)
        request.state.api_version = version or CURRENT_VERSION

        response = await call_next(request)

        if version:
            response.headers["X-API-Version"] = version.value

        if version and version in DEPRECATED_VERSIONS:
            response.headers["Deprecation"] = "true"
            if self.sunset_date:
                response.headers["Sunset"] = self.sunset_date

        return response
