"""Tests for the public (unauthenticated) review endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import create_app
from app.modules.review_intelligence.models import BookReview
from app.modules.reviews_public.rate_limit import _in_memory_buckets


@pytest_asyncio.fixture
async def client(db_session):
    app = create_app()

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    # Reset in-memory rate limit bucket between tests.
    _in_memory_buckets.clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def _seed_reviews(db_session, book_id, count=3, rating=5.0, competitor=False):
    org = uuid.uuid4()
    for i in range(count):
        db_session.add(
            BookReview(
                org_id=org,
                book_id=book_id,
                source="amazon",
                star_rating=rating,
                title=f"R{i}",
                body=f"Great book {i}" + ("!" * 50),
                reviewer_name=f"Reader {i}",
                review_date=datetime.now(timezone.utc),
                is_competitor=competitor,
            )
        )
    await db_session.flush()


@pytest.mark.asyncio
async def test_public_reviews_returns_shape(client, db_session):
    book_id = uuid.uuid4()
    await _seed_reviews(db_session, book_id, count=3, rating=4.5)

    resp = await client.get(f"/api/v1/public/reviews/{book_id}?max=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["book_id"] == str(book_id)
    assert data["review_count"] == 3
    assert data["rating"] == 4.5
    assert len(data["reviews"]) == 3
    # No auth header was sent.
    for r in data["reviews"]:
        # Excerpt must NOT contain any placeholder for sensitive fields.
        assert "password" not in (r.get("body_excerpt") or "")


@pytest.mark.asyncio
async def test_public_reviews_excludes_competitor_reviews(client, db_session):
    book_id = uuid.uuid4()
    await _seed_reviews(db_session, book_id, count=2, rating=5.0, competitor=False)
    await _seed_reviews(db_session, book_id, count=5, rating=1.0, competitor=True)

    resp = await client.get(f"/api/v1/public/reviews/{book_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["review_count"] == 2
    assert data["rating"] == 5.0


@pytest.mark.asyncio
async def test_public_reviews_has_cors_and_cache_headers(client, db_session):
    book_id = uuid.uuid4()
    await _seed_reviews(db_session, book_id, count=1)

    resp = await client.get(f"/api/v1/public/reviews/{book_id}")
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"
    assert "max-age=" in resp.headers.get("cache-control", "")


@pytest.mark.asyncio
async def test_public_reviews_rate_limit_triggers_on_burst(client, db_session):
    book_id = uuid.uuid4()
    await _seed_reviews(db_session, book_id, count=1)

    # Monkey-patch the module-level constant down to a small number to
    # trigger the limit without needing hundreds of requests.
    import app.modules.reviews_public.rate_limit as rl_mod

    original_limit = rl_mod.PUBLIC_API_LIMIT
    rl_mod.PUBLIC_API_LIMIT = 5
    try:
        statuses = []
        for _ in range(8):
            r = await client.get(f"/api/v1/public/reviews/{book_id}")
            statuses.append(r.status_code)
        assert 429 in statuses, f"expected a 429 in {statuses}"
    finally:
        rl_mod.PUBLIC_API_LIMIT = original_limit
        _in_memory_buckets.clear()
