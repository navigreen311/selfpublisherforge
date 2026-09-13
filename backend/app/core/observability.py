"""Metrics and error tracking.

Two things this service claimed to have and did not:

  * a Prometheus scrape target. `docs/deploy.md` and the compose stack point a
    scraper at ``/metrics``, and nothing served it — the endpoint 404'd, so
    every dashboard built on it was empty.
  * exception aggregation. Unhandled errors went to the log and nowhere else,
    which means nobody learns about a 500 unless they happen to read the logs
    of the right container at the right time.

Both are wired here and registered once, by ``create_app``.

Neither is required to run the service. Metrics are always on because they cost
nothing and are useful in development; error tracking activates only when
``SENTRY_DSN`` is set, so a developer without one gets no network calls, no
warnings, and no behaviour change.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi import routing as fastapi_routing
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import BaseRoute

from app.config import get_settings

logger = logging.getLogger(__name__)

# A registry of our own rather than the process-wide default. The default is
# module-global, so a second create_app() in the same interpreter — which every
# test that builds its own app does — re-registers the same collector names and
# raises "Duplicated timeseries in CollectorRegistry".
REGISTRY = CollectorRegistry()

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests, by method, route template and status class.",
    labelnames=("method", "route", "status"),
    registry=REGISTRY,
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds, by method and route template.",
    labelnames=("method", "route"),
    registry=REGISTRY,
)


# Where the per-app route map is cached. Built lazily rather than at
# registration time because create_app() calls register_observability() before
# it includes any router — at registration time the app has almost no routes.
_ROUTE_MAP_ATTR = "_observability_route_templates"


def _relative_path(route: BaseRoute) -> str:
    """Last-resort label: the route's own path, without any mount prefix.

    Ambiguous — every router with a ``/{id}`` route collapses into one series —
    but still a *template*. Falling back to the concrete path instead would
    reintroduce exactly the cardinality blow-up this module exists to avoid, so
    an ambiguous label is the right way to degrade.
    """
    path = getattr(route, "path", None)
    return str(path) if path else "unmatched"


def _build_route_map(app: FastAPI) -> dict[int, str]:
    """Map each route object to its fully prefixed path.

    ``app.include_router(r, prefix="/api/v1/projects")`` does not rewrite the
    routes in ``r``; since FastAPI 0.141 the app holds an internal router node
    and dispatch puts the *unprefixed* route into ``scope["route"]`` — so a
    handler declared as ``@router.get("/{project_id}")`` reports ``/{project_id}``
    no matter where it was mounted, and every module's ``/{id}`` route shares one
    time series. ``iter_route_contexts`` is the flattener FastAPI's own OpenAPI
    generator uses to recover full paths, and it hands back the same route object
    that dispatch puts in the scope, which is what makes the lookup exact.

    Keyed by ``id`` because Starlette's ``Route`` is an unhashable dataclass.
    That is safe only because this map is stored on the app, which holds a
    strong reference to every route in it for as long as the map exists — so no
    key can be freed and its address reused by something else.
    """
    mapping: dict[int, str] = {}
    try:
        contexts = list(fastapi_routing.iter_route_contexts(app.routes))
    except Exception:  # pragma: no cover - defensive against FastAPI internals
        logger.warning("Could not enumerate routes; metrics will use unprefixed labels", exc_info=True)
        return mapping

    for ctx in contexts:
        path = getattr(ctx, "path", None)
        original = getattr(ctx, "original_route", None)
        if path and original is not None:
            mapping.setdefault(id(original), str(path))
    return mapping


def _route_template(request: Request) -> str:
    """Return the route pattern, not the concrete path.

    ``/api/v1/projects/{project_id}`` rather than the UUID the caller used.
    Labelling by raw path would mint a new time series per project and blow up
    the scrape payload — the standard Prometheus cardinality trap.
    """
    route = request.scope.get("route")
    if route is None:
        return "unmatched"

    app = request.scope.get("app")
    if app is None:
        return _relative_path(route)

    mapping = getattr(app.state, _ROUTE_MAP_ATTR, None)
    if mapping is None:
        mapping = _build_route_map(app)
        setattr(app.state, _ROUTE_MAP_ATTR, mapping)

    template = mapping.get(id(route))
    if template is None:
        # A route added after the map was built. Rebuild, then cache whatever we
        # settle on — including a fallback — so one unresolvable route cannot
        # make every subsequent request rebuild the map.
        mapping.update(_build_route_map(app))
        template = mapping.get(id(route))
        if template is None:
            template = _relative_path(route)
            mapping[id(route)] = template
    return template


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record count and duration for every request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # An unhandled exception is still a request that happened. Record
            # it as a 500 before re-raising, or the error rate under-reports
            # exactly when it matters most.
            REQUESTS.labels(request.method, _route_template(request), "5xx").inc()
            LATENCY.labels(request.method, _route_template(request)).observe(time.perf_counter() - started)
            raise

        route = _route_template(request)
        REQUESTS.labels(request.method, route, f"{response.status_code // 100}xx").inc()
        LATENCY.labels(request.method, route).observe(time.perf_counter() - started)
        return response


def init_error_tracking() -> bool:
    """Start Sentry if a DSN is configured. Returns whether it did.

    Import is deferred so the dependency is not required to import this module,
    and a missing or broken SDK degrades to "no error tracking" rather than
    taking the process down at startup.
    """
    settings = get_settings()
    dsn = getattr(settings, "SENTRY_DSN", None)
    if not dsn:
        logger.info("Error tracking disabled: SENTRY_DSN is not set")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        logger.warning("SENTRY_DSN is set but sentry-sdk is not installed; error tracking is off")
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.ENVIRONMENT,
        release=settings.APP_VERSION,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        # Bodies and headers can carry manuscripts, API keys and reader PII.
        # Off unless someone turns it on deliberately.
        send_default_pii=False,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    logger.info("Error tracking enabled for environment %r", settings.ENVIRONMENT)
    return True


def register_observability(app: FastAPI) -> None:
    """Mount ``/metrics`` and start error tracking."""
    app.add_middleware(MetricsMiddleware)

    @app.get(
        "/metrics",
        summary="Prometheus metrics",
        tags=["health"],
        include_in_schema=False,
    )
    async def metrics() -> Response:
        return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

    init_error_tracking()
