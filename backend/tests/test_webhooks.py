"""Tests for the webhook event system."""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app
from app.modules.webhooks.events import EVENT_TYPES
from app.modules.webhooks.models import WebhookEndpoint, WebhookLog
from app.modules.webhooks.service import (
    build_envelope,
    deliver,
    generate_signing_secret,
    resolve_subscribers,
    sign_payload,
    verify_signature,
)


ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@contextmanager
def _patched_httpx(resp_cls):
    """Swap httpx.AsyncClient inside the webhook service with a fake that
    returns the given response class. Scoped narrowly to the service module
    so the test HTTP client is unaffected."""
    import app.modules.webhooks.service as svc_mod

    captured: dict = {}

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, content=None, headers=None):
            captured["url"] = url
            captured["content"] = content
            captured["headers"] = headers
            return resp_cls()

    original = svc_mod.httpx.AsyncClient
    svc_mod.httpx.AsyncClient = _FakeClient
    try:
        yield captured
    finally:
        svc_mod.httpx.AsyncClient = original


@pytest_asyncio.fixture
async def client(db_session):
    app = create_app()

    async def _override_get_db():
        yield db_session

    def _override_user():
        return {"user_id": uuid.uuid4(), "org_id": ORG_ID, "role": "admin"}

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# HMAC signing
# ---------------------------------------------------------------------------


def test_sign_payload_matches_manual_hmac():
    secret = "whsec_abcdefg"
    body = b'{"type":"book.published"}'
    signature = sign_payload(secret, body)
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert signature == expected


def test_verify_signature_is_timing_safe():
    secret = generate_signing_secret()
    body = b"payload"
    good = sign_payload(secret, body)
    assert verify_signature(secret, body, good) is True
    assert verify_signature(secret, body, "sha256=deadbeef") is False
    assert verify_signature(secret, body, "") is False


def test_generate_signing_secret_shape_and_uniqueness():
    a = generate_signing_secret()
    b = generate_signing_secret()
    assert a.startswith("whsec_")
    assert b.startswith("whsec_")
    assert a != b
    assert len(a) > 20


def test_event_envelope_has_required_fields():
    env = build_envelope("book.created", {"book_id": "abc"})
    assert env["type"] == "book.created"
    assert env["id"].startswith("evt_")
    assert env["data"] == {"book_id": "abc"}
    assert "created_at" in env


# ---------------------------------------------------------------------------
# Event catalog
# ---------------------------------------------------------------------------


def test_event_catalog_contains_required_events():
    for required in [
        "book.created",
        "book.published",
        "book.status_changed",
        "review.received",
        "export.completed",
    ]:
        assert required in EVENT_TYPES


# ---------------------------------------------------------------------------
# API: CRUD on webhook endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_list_endpoint(client):
    resp = await client.post(
        "/api/v1/webhooks",
        json={
            "url": "https://example.com/hook",
            "description": "Zapier",
            "events": ["book.created", "book.published"],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["url"] == "https://example.com/hook"
    assert body["events"] == ["book.created", "book.published"]
    assert body["signing_secret"].startswith("whsec_")
    assert body["signing_secret_masked"].startswith("whsec_***")

    list_resp = await client.get("/api/v1/webhooks")
    assert list_resp.status_code == 200
    entries = list_resp.json()
    assert len(entries) == 1
    # Full secret never returned on list.
    assert "signing_secret" not in entries[0] or not entries[0].get("signing_secret")


@pytest.mark.asyncio
async def test_create_endpoint_rejects_unknown_event(client):
    resp = await client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/h", "events": ["not.real"]},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_event_catalog_endpoint(client):
    resp = await client.get("/api/v1/webhooks/events")
    assert resp.status_code == 200
    catalog = resp.json()
    types = {e["type"] for e in catalog}
    assert "book.published" in types


# ---------------------------------------------------------------------------
# Test button path: HMAC is actually used
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_test_button_signs_payload_with_hmac(client):
    create = await client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.invalid/hook", "events": ["book.created"]},
    )
    endpoint_id = create.json()["id"]
    secret = create.json()["signing_secret"]

    class _Resp:
        status_code = 200
        text = "ok"

    with _patched_httpx(_Resp) as captured:
        resp = await client.post(f"/api/v1/webhooks/{endpoint_id}/test")

    assert resp.status_code == 200
    data = resp.json()
    assert data["delivered"] is True
    assert data["status_code"] == 200

    assert captured["url"].startswith("https://example.invalid")
    sig = captured["headers"]["X-Webhook-Signature"]
    assert sig.startswith("sha256=")
    # The signature must verify against the raw body with the secret.
    expected = sign_payload(secret, captured["content"])
    assert hmac.compare_digest(sig, expected)


# ---------------------------------------------------------------------------
# Dispatch + delivery logic (direct, no Celery)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_subscribers_filters_by_event_and_active(db_session):
    a = WebhookEndpoint(
        org_id=ORG_ID,
        url="https://a.example.com",
        events=["book.created"],
        signing_secret="whsec_a",
        active=True,
    )
    b = WebhookEndpoint(
        org_id=ORG_ID,
        url="https://b.example.com",
        events=["book.published"],
        signing_secret="whsec_b",
        active=True,
    )
    c = WebhookEndpoint(
        org_id=ORG_ID,
        url="https://c.example.com",
        events=["book.created"],
        signing_secret="whsec_c",
        active=False,
    )
    db_session.add_all([a, b, c])
    await db_session.flush()

    subs = await resolve_subscribers(db_session, "book.created", org_id=ORG_ID)
    urls = sorted(s.url for s in subs)
    assert urls == ["https://a.example.com"]


@pytest.mark.asyncio
async def test_deliver_marks_2xx_as_delivered(db_session):
    ep = WebhookEndpoint(
        org_id=ORG_ID,
        url="https://ex.example.com/h",
        events=["book.created"],
        signing_secret=generate_signing_secret(),
        active=True,
    )
    db_session.add(ep)
    await db_session.flush()

    envelope = build_envelope("book.created", {"book_id": "x"})

    class _Resp:
        status_code = 201
        text = "created"

    with _patched_httpx(_Resp):
        log = await deliver(db_session, ep, envelope)

    assert log.delivered is True
    assert log.status_code == 201
    assert log.retries == 0


@pytest.mark.asyncio
async def test_deliver_marks_5xx_as_not_delivered_and_logs(db_session):
    ep = WebhookEndpoint(
        org_id=ORG_ID,
        url="https://ex.example.com/h",
        events=["book.created"],
        signing_secret=generate_signing_secret(),
        active=True,
    )
    db_session.add(ep)
    await db_session.flush()

    envelope = build_envelope("book.created", {"book_id": "x"})

    class _Resp:
        status_code = 500
        text = "boom"

    with _patched_httpx(_Resp):
        log = await deliver(db_session, ep, envelope)

    assert log.delivered is False
    assert log.status_code == 500
    assert "boom" in (log.response_body or "")


# ---------------------------------------------------------------------------
# Retry backoff schedule
# ---------------------------------------------------------------------------


def test_retry_backoff_schedule_matches_spec():
    from app.modules.webhooks.tasks import (
        MAX_RETRIES,
        RETRY_BACKOFF_SECONDS,
    )

    # 1min, 5min, 15min, 1hr, 6hr -> 60, 300, 900, 3600, 21600
    assert RETRY_BACKOFF_SECONDS == [60, 300, 900, 3600, 21600]
    assert MAX_RETRIES == 5
