"""Embeddable Review Widget module (Feature 9).

Provides:
  * Authenticated CRUD: ``POST/GET/DELETE /api/v1/review-widgets``
  * Public embed JS: ``GET /api/v1/widgets/{id}.js``
  * Public reviews JSON (CORS-open): ``GET /api/v1/widgets/{id}/reviews``

Styles supported: ``card_grid``, ``carousel``, ``compact_list``.
"""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.review_intelligence.models import BookReview, ReviewWidget

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

public_router = APIRouter()  # Mounted at /api/v1 ; paths use /widgets/...
auth_router = APIRouter()    # Mounted at /api/v1/review-widgets

ALLOWED_STYLES = {"card_grid", "carousel", "compact_list"}
ALLOWED_THEMES = {"light", "dark", "auto"}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class WidgetCreate(BaseModel):
    book_id: UUID
    style: str = Field(default="card_grid")
    theme: str = Field(default="light")
    max_reviews: int = Field(default=3, ge=1, le=20)
    min_rating: int = Field(default=4, ge=1, le=5)
    show_options: dict[str, Any] | None = None


class WidgetRead(BaseModel):
    id: UUID
    book_id: UUID
    style: str
    theme: str
    max_reviews: int
    min_rating: int
    show_options: dict[str, Any] | None = None
    embed_code: str

    class Config:
        from_attributes = True


class ReviewExcerpt(BaseModel):
    rating: float
    title: str | None
    body_excerpt: str | None
    reviewer_name: str | None
    date: str | None


class WidgetReviewsResponse(BaseModel):
    book_id: UUID
    style: str
    theme: str
    rating: float
    review_count: int
    reviews: list[ReviewExcerpt]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _embed_code(widget_id: UUID, base_url: str = "") -> str:
    src = f"{base_url}/api/v1/widgets/{widget_id}.js"
    return (
        f'<script src="{src}" async '
        f'data-spf-widget="{widget_id}"></script>'
    )


def _to_read(w: ReviewWidget) -> WidgetRead:
    return WidgetRead(
        id=w.id,
        book_id=w.book_id,
        style=w.style,
        theme=w.theme,
        max_reviews=w.max_reviews,
        min_rating=w.min_rating,
        show_options=w.show_options,
        embed_code=_embed_code(w.id),
    )


async def _fetch_reviews_payload(
    db: AsyncSession, widget: ReviewWidget
) -> WidgetReviewsResponse:
    # Top N reviews for book at or above min_rating, ordered by helpfulness/date.
    stmt = (
        select(BookReview)
        .where(BookReview.book_id == widget.book_id)
        .where(BookReview.star_rating >= widget.min_rating)
        .order_by(desc(BookReview.helpful_count), desc(BookReview.review_date))
        .limit(widget.max_reviews)
    )
    result = await db.execute(stmt)
    top_reviews = list(result.scalars().all())

    # Aggregate stats: avg + count across all reviews for this book.
    all_stmt = select(BookReview).where(BookReview.book_id == widget.book_id)
    all_res = await db.execute(all_stmt)
    all_reviews = list(all_res.scalars().all())
    count = len(all_reviews)
    avg = (
        round(sum(r.star_rating for r in all_reviews) / count, 2) if count else 0.0
    )

    return WidgetReviewsResponse(
        book_id=widget.book_id,
        style=widget.style,
        theme=widget.theme,
        rating=avg,
        review_count=count,
        reviews=[
            ReviewExcerpt(
                rating=r.star_rating,
                title=r.title,
                body_excerpt=(r.body or "")[:240] if r.body else None,
                reviewer_name=r.reviewer_name,
                date=r.review_date.isoformat() if r.review_date else None,
            )
            for r in top_reviews
        ],
    )


def _cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Cache-Control": "public, max-age=300",
    }


# ---------------------------------------------------------------------------
# Authenticated CRUD
# ---------------------------------------------------------------------------


@auth_router.post("", response_model=WidgetRead, status_code=status.HTTP_201_CREATED)
async def create_widget(
    payload: WidgetCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WidgetRead:
    if payload.style not in ALLOWED_STYLES:
        raise HTTPException(400, f"style must be one of {sorted(ALLOWED_STYLES)}")
    if payload.theme not in ALLOWED_THEMES:
        raise HTTPException(400, f"theme must be one of {sorted(ALLOWED_THEMES)}")
    if not user["org_id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "org_id required")

    widget = ReviewWidget(
        org_id=user["org_id"],
        book_id=payload.book_id,
        style=payload.style,
        theme=payload.theme,
        max_reviews=payload.max_reviews,
        min_rating=payload.min_rating,
        show_options=payload.show_options or {},
    )
    db.add(widget)
    await db.flush()
    await db.refresh(widget)
    return _to_read(widget)


@auth_router.get("", response_model=list[WidgetRead])
async def list_widgets(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WidgetRead]:
    stmt = (
        select(ReviewWidget)
        .where(ReviewWidget.org_id == user["org_id"])
        .order_by(desc(ReviewWidget.created_at))
    )
    res = await db.execute(stmt)
    return [_to_read(w) for w in res.scalars().all()]


@auth_router.get("/{widget_id}", response_model=WidgetRead)
async def get_widget(
    widget_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WidgetRead:
    stmt = select(ReviewWidget).where(
        ReviewWidget.id == widget_id, ReviewWidget.org_id == user["org_id"]
    )
    res = await db.execute(stmt)
    widget = res.scalar_one_or_none()
    if not widget:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Widget not found")
    return _to_read(widget)


@auth_router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    stmt = select(ReviewWidget).where(
        ReviewWidget.id == widget_id, ReviewWidget.org_id == user["org_id"]
    )
    res = await db.execute(stmt)
    widget = res.scalar_one_or_none()
    if not widget:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Widget not found")
    await db.delete(widget)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Public endpoints (no auth, CORS-open)
# ---------------------------------------------------------------------------


async def _load_widget(db: AsyncSession, widget_id: UUID) -> ReviewWidget:
    stmt = select(ReviewWidget).where(ReviewWidget.id == widget_id)
    res = await db.execute(stmt)
    widget = res.scalar_one_or_none()
    if not widget:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Widget not found")
    return widget


@public_router.get("/widgets/{widget_id}/reviews")
async def public_widget_reviews(
    widget_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    widget = await _load_widget(db, widget_id)
    payload = await _fetch_reviews_payload(db, widget)
    return Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        headers=_cors_headers(),
    )


@public_router.get("/widgets/{widget_id}.js")
async def public_widget_js(
    widget_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    widget = await _load_widget(db, widget_id)
    payload = await _fetch_reviews_payload(db, widget)
    data_json = payload.model_dump_json()
    js = _render_embed_js(str(widget_id), data_json)
    headers = _cors_headers()
    return Response(
        content=js,
        media_type="application/javascript; charset=utf-8",
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Embed JS renderer — shadow DOM widget
# ---------------------------------------------------------------------------


def _render_embed_js(widget_id: str, initial_payload_json: str) -> str:
    """Return a self-contained IIFE that renders the widget into a shadow DOM.

    It locates its own <script> tag by ``data-spf-widget`` attribute, creates
    a host element, attaches a closed-style shadow root, and injects scoped
    CSS + HTML for the chosen style. Includes a "Powered by
    SelfPublisherForge" attribution link.
    """
    safe_id = json.dumps(widget_id)
    safe_payload = initial_payload_json.replace("</", "<\\/")
    return f"""
(function() {{
  var WIDGET_ID = {safe_id};
  var DATA = {safe_payload};

  function h(tag, attrs, children) {{
    var el = document.createElement(tag);
    if (attrs) for (var k in attrs) {{
      if (k === 'class') el.className = attrs[k];
      else if (k === 'html') el.innerHTML = attrs[k];
      else el.setAttribute(k, attrs[k]);
    }}
    (children || []).forEach(function(c) {{
      if (c == null) return;
      el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }});
    return el;
  }}

  function stars(rating) {{
    var full = Math.floor(rating);
    var half = (rating - full) >= 0.5;
    var s = '';
    for (var i = 0; i < full; i++) s += '\u2605';
    if (half) s += '\u00BD';
    for (var j = full + (half ? 1 : 0); j < 5; j++) s += '\u2606';
    return s;
  }}

  var script = document.querySelector('script[data-spf-widget="' + WIDGET_ID + '"]');
  if (!script) return;
  var host = document.createElement('div');
  host.className = 'spf-widget-host';
  script.parentNode.insertBefore(host, script);
  var root = host.attachShadow({{ mode: 'open' }});

  var theme = DATA.theme || 'light';
  var style = DATA.style || 'card_grid';

  var css = `
    :host, .wrap {{ all: initial; }}
    .wrap {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      color: ${{theme === 'dark' ? '#eee' : '#222'}};
      background: ${{theme === 'dark' ? '#1b1b1b' : '#fff'}};
      border: 1px solid ${{theme === 'dark' ? '#333' : '#e5e5e5'}};
      border-radius: 8px;
      padding: 16px;
      max-width: 720px;
      line-height: 1.4;
    }}
    .header {{ display: flex; align-items: center; gap: 8px; font-weight: 600; margin-bottom: 12px; }}
    .stars {{ color: #f5a623; font-size: 18px; letter-spacing: 1px; }}
    .rating {{ font-size: 16px; }}
    .count {{ color: ${{theme === 'dark' ? '#aaa' : '#666'}}; font-size: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .carousel {{ display: flex; gap: 12px; overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 8px; }}
    .carousel .review {{ min-width: 260px; scroll-snap-align: start; }}
    .compact {{ display: flex; flex-direction: column; gap: 8px; }}
    .review {{
      background: ${{theme === 'dark' ? '#262626' : '#fafafa'}};
      border: 1px solid ${{theme === 'dark' ? '#333' : '#eee'}};
      border-radius: 6px; padding: 10px 12px; font-size: 14px;
    }}
    .review .rv-stars {{ color: #f5a623; font-size: 13px; margin-bottom: 4px; }}
    .review .rv-body {{ margin: 4px 0; }}
    .review .rv-meta {{ font-size: 12px; color: ${{theme === 'dark' ? '#999' : '#777'}}; }}
    .footer {{ margin-top: 12px; font-size: 11px; text-align: right; }}
    .footer a {{ color: ${{theme === 'dark' ? '#8ab4f8' : '#2a66d9'}}; text-decoration: none; }}
  `;

  var styleEl = h('style', {{ html: css }}, []);
  var wrap = h('div', {{ class: 'wrap' }}, []);

  var header = h('div', {{ class: 'header' }}, [
    h('span', {{ class: 'stars' }}, [stars(DATA.rating || 0)]),
    h('span', {{ class: 'rating' }}, [(DATA.rating || 0).toFixed(1) + ' out of 5']),
    h('span', {{ class: 'count' }}, ['(' + (DATA.review_count || 0) + ' reviews)'])
  ]);
  wrap.appendChild(header);

  var container;
  if (style === 'carousel') container = h('div', {{ class: 'carousel' }}, []);
  else if (style === 'compact_list') container = h('div', {{ class: 'compact' }}, []);
  else container = h('div', {{ class: 'grid' }}, []);

  (DATA.reviews || []).forEach(function(r) {{
    var review = h('div', {{ class: 'review' }}, [
      h('div', {{ class: 'rv-stars' }}, [stars(r.rating || 0)]),
      r.title ? h('div', {{ class: 'rv-title' }}, [r.title]) : null,
      h('div', {{ class: 'rv-body' }}, ['"' + (r.body_excerpt || '') + '"']),
      h('div', {{ class: 'rv-meta' }}, [
        (r.reviewer_name || 'Anonymous') + (r.date ? ' \u00b7 ' + r.date.slice(0, 10) : '')
      ])
    ]);
    container.appendChild(review);
  }});
  wrap.appendChild(container);

  var footer = h('div', {{ class: 'footer' }}, []);
  footer.innerHTML = 'Powered by <a href="https://selfpublisherforge.com" target="_blank" rel="noopener">SelfPublisherForge</a>';
  wrap.appendChild(footer);

  root.appendChild(styleEl);
  root.appendChild(wrap);
}})();
"""
