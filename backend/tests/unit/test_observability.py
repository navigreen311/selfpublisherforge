"""Tests for /metrics and error tracking.

The point of these is that the endpoint exists *and reports real traffic*. A
test asserting only that /metrics returns 200 would have passed against an
empty registry, which is the failure mode worth catching: a scrape target that
answers but never counts anything looks healthy on every dashboard.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.observability import CONTENT_TYPE_LATEST, init_error_tracking
from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_metrics_endpoint_is_served(app):
    """It exists at all — it used to 404 while the compose stack scraped it."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/metrics")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(CONTENT_TYPE_LATEST.split(";")[0])


@pytest.mark.asyncio
async def test_metrics_count_requests_by_route_template(app):
    """A served request shows up in the scrape, labelled by route pattern."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/health")
        body = (await client.get("/metrics")).text

    assert "http_requests_total" in body
    assert 'route="/health"' in body
    assert "http_request_duration_seconds" in body


@pytest.mark.asyncio
async def test_metrics_label_by_pattern_not_by_path(app):
    """Path parameters must not become labels.

    Labelling by concrete path mints a time series per project id and is the
    standard way a Prometheus deployment falls over. The label has to be the
    route template.

    Both halves are load-bearing. Asserting only the *absence* of the UUID
    passed while the label was ``/{project_id}`` — the unprefixed path of a
    router that was mounted under ``/api/v1/projects``. No id leaked, but every
    module with a ``/{id}`` route shared one series, which is its own kind of
    useless. Asserting the full mounted template is what makes this test able
    to fail.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/api/v1/projects/11111111-1111-1111-1111-111111111111")
        body = (await client.get("/metrics")).text

    assert 'route="/api/v1/projects/{project_id}"' in body
    assert "11111111-1111-1111-1111-111111111111" not in body


@pytest.mark.asyncio
async def test_routes_mounted_under_different_prefixes_do_not_share_a_series(app):
    """Two routers each declaring ``/{id}``-shaped paths stay distinguishable.

    This is the concrete cost of labelling by unprefixed path: a dashboard
    filtered to one module silently aggregates every module.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/api/v1/projects/11111111-1111-1111-1111-111111111111")
        await client.get("/api/v1/orgs/22222222-2222-2222-2222-222222222222")
        body = (await client.get("/metrics")).text

    labels = {
        line.split('route="', 1)[1].split('"', 1)[0]
        for line in body.splitlines()
        if line.startswith("http_requests_total{") and 'route="' in line
    }
    assert len([label for label in labels if label.startswith("/api/v1/")]) >= 2
    assert not any(label.count("/") < 2 and "{" in label for label in labels)


def test_error_tracking_is_off_without_a_dsn():
    """No DSN means no initialisation — and no network calls in development."""
    with patch("app.core.observability.get_settings") as mock_settings:
        mock_settings.return_value.SENTRY_DSN = None
        assert init_error_tracking() is False


def test_error_tracking_initialises_with_a_dsn():
    """A DSN initialises the SDK, with PII sending off."""
    with (
        patch("app.core.observability.get_settings") as mock_settings,
        patch("sentry_sdk.init") as mock_init,
    ):
        mock_settings.return_value.SENTRY_DSN = "https://key@example.invalid/1"
        mock_settings.return_value.ENVIRONMENT = "test"
        mock_settings.return_value.APP_VERSION = "1.2.3"
        mock_settings.return_value.SENTRY_TRACES_SAMPLE_RATE = 0.0

        assert init_error_tracking() is True

    kwargs = mock_init.call_args.kwargs
    assert kwargs["dsn"] == "https://key@example.invalid/1"
    assert kwargs["environment"] == "test"
    # Request bodies here carry manuscripts, API keys and reader PII.
    assert kwargs["send_default_pii"] is False
