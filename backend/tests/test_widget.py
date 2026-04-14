"""Tests for the embeddable review widget JS + widget-config endpoint."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app
from app.modules.reviews_public.widget import WIDGET_JS


@pytest_asyncio.fixture
async def client(db_session):
    app = create_app()

    async def _override_get_db():
        yield db_session

    def _override_user():
        return {
            "user_id": uuid.uuid4(),
            "org_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
            "role": "admin",
        }

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Widget JS static asset
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_widget_served_with_javascript_content_type(client):
    resp = await client.get("/widget/reviews.js")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/javascript")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert "max-age=" in resp.headers.get("cache-control", "")
    assert "SPF" in resp.text or "book-id" in resp.text


def test_widget_js_avoids_innerhtml_with_user_content():
    # No `innerHTML` assignment. textContent-only rendering prevents XSS
    # from attacker-controlled review bodies.
    assert ".innerHTML" not in WIDGET_JS
    # It must use textContent or element creation for user-provided fields.
    assert "textContent" in WIDGET_JS
    # It must not call eval() or Function() on any data.
    assert "eval(" not in WIDGET_JS
    assert "new Function(" not in WIDGET_JS


def test_widget_js_size_budget():
    # 8KB uncompressed budget.
    assert len(WIDGET_JS.encode("utf-8")) < 8 * 1024


def test_widget_js_supports_data_attributes_and_auto_theme():
    for attr in ("data-book-id", "data-style", "data-theme", "data-max"):
        assert attr in WIDGET_JS
    assert "prefers-color-scheme" in WIDGET_JS


# ---------------------------------------------------------------------------
# widget-config endpoint (authenticated)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_widget_config_returns_embed_code_and_api_url(client):
    book_id = str(uuid.uuid4())
    resp = await client.post(
        "/api/v1/reviews/widget-config",
        json={
            "book_id": book_id,
            "style": "compact",
            "theme": "dark",
            "max_reviews": 3,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "<script" in body["embed_code"]
    assert "/widget/reviews.js" in body["embed_code"]
    assert f'data-book-id="{book_id}"' in body["embed_code"]
    assert 'data-theme="dark"' in body["embed_code"]
    assert f"/api/v1/public/reviews/{book_id}" in body["api_url"]


@pytest.mark.asyncio
async def test_widget_config_rejects_invalid_book_id(client):
    resp = await client.post(
        "/api/v1/reviews/widget-config",
        json={"book_id": "not-a-uuid", "style": "compact"},
    )
    assert resp.status_code == 400
