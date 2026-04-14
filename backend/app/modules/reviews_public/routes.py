"""Public (unauthenticated) review API + authenticated widget-config endpoint."""
from __future__ import annotations

from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.reviews_public.rate_limit import enforce_public_rate_limit
from app.modules.reviews_public.schemas import (
    PublicReviewsResponse,
    WidgetConfigRequest,
    WidgetConfigResponse,
)
from app.modules.reviews_public.service import (
    PUBLIC_CACHE_TTL,
    build_public_reviews,
)

public_router = APIRouter()
widget_config_router = APIRouter()


@public_router.get(
    "/public/reviews/{book_id}",
    response_model=PublicReviewsResponse,
    summary="Public reviews for a book (no auth, rate limited)",
)
async def public_reviews(
    book_id: UUID,
    request: Request,
    max: int = Query(3, ge=0, le=10),
    style: str = Query("compact"),  # accepted but not required by the backend
    db: AsyncSession = Depends(get_db),
) -> Response:
    await enforce_public_rate_limit(request)
    data = await build_public_reviews(db, book_id, max_reviews=max)
    body = data.model_dump_json()
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Cache-Control": f"public, max-age={PUBLIC_CACHE_TTL}",
            "Access-Control-Allow-Origin": "*",
            "X-Content-Type-Options": "nosniff",
        },
    )


@widget_config_router.post(
    "/reviews/widget-config",
    response_model=WidgetConfigResponse,
    summary="Generate embed code for the review widget",
)
async def widget_config(
    body: WidgetConfigRequest,
    request: Request,
    _user: dict = Depends(get_current_user),
) -> WidgetConfigResponse:
    settings = get_settings()
    # Best-effort public base URL: prefer the explicit PUBLIC_BASE_URL if
    # configured, otherwise reuse the inbound request's base URL.
    base = getattr(settings, "PUBLIC_BASE_URL", None) or str(request.base_url).rstrip("/")

    # Validate style / theme
    style = body.style if body.style in {"compact", "full", "badge"} else "compact"
    theme = body.theme if body.theme in {"light", "dark", "auto"} else "light"
    max_reviews = max(0, min(body.max_reviews, 10))

    try:
        book_uuid = str(UUID(body.book_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid book_id") from exc

    attrs = {
        "src": f"{base}/widget/reviews.js",
        "data-book-id": book_uuid,
        "data-style": style,
        "data-theme": theme,
        "data-max": str(max_reviews),
    }
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    embed_code = f"<script {attr_str} async></script>"

    api_qs = urlencode({"max": max_reviews, "style": style})
    api_url = f"{base}/api/v1/public/reviews/{book_uuid}?{api_qs}"

    return WidgetConfigResponse(embed_code=embed_code, api_url=api_url)
