"""
Enhanced health-check endpoints.

- ``GET /health``          -- basic liveness (for load balancers)
- ``GET /health/ready``    -- readiness (DB, Redis, Elasticsearch)
- ``GET /health/detailed`` -- full diagnostics (admin only)
"""

from __future__ import annotations

import logging
import time
from typing import Any

import redis.asyncio as redis
from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, HTTPException, status
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import require_role
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

_start_time = time.time()


def _uptime_seconds() -> float:
    return round(time.time() - _start_time, 2)


async def _check_db(db: AsyncSession) -> dict[str, Any]:
    """Verify database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except (SQLAlchemyError, DBAPIError, ConnectionError, TimeoutError, OSError) as exc:
        logger.warning("Database health check failed", exc_info=True)
        return {"status": "unhealthy", "error": str(exc)}


async def _check_redis() -> dict[str, Any]:
    """Verify Redis connectivity."""
    settings = get_settings()
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        await r.close()
        return {"status": "healthy"}
    except (RedisConnectionError, RedisError, ConnectionError, TimeoutError, OSError) as exc:
        logger.warning("Redis health check failed", exc_info=True)
        return {"status": "unhealthy", "error": str(exc)}


async def _check_elasticsearch() -> dict[str, Any]:
    """Verify Elasticsearch connectivity."""
    settings = get_settings()
    try:
        es = AsyncElasticsearch(settings.ELASTICSEARCH_URL)
        info = await es.info()
        await es.close()
        return {"status": "healthy", "version": str(info.get("version", {}).get("number", "unknown"))}
    except (ConnectionError, TimeoutError, OSError, ValueError) as exc:
        logger.warning("Elasticsearch health check failed", exc_info=True)
        return {"status": "unhealthy", "error": str(exc)}


# -----------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------


@router.get("/health")
async def health_basic() -> dict[str, str]:
    """
    Basic liveness probe.

    Returns 200 as long as the process is running.  Suitable for
    Kubernetes liveness probes and load-balancer health checks.
    """
    settings = get_settings()
    return {"status": "healthy", "version": settings.APP_VERSION}


@router.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness probe.

    Checks connectivity to the primary backing services (database,
    Redis, Elasticsearch).  Returns 503 if any dependency is
    unreachable.
    """
    db_status = await _check_db(db)
    redis_status = await _check_redis()
    es_status = await _check_elasticsearch()

    dependencies = {
        "database": db_status,
        "redis": redis_status,
        "elasticsearch": es_status,
    }

    all_healthy = all(d["status"] == "healthy" for d in dependencies.values())

    result: dict[str, Any] = {
        "status": "ready" if all_healthy else "not_ready",
        "dependencies": dependencies,
    }

    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result,
        )

    return result


@router.get("/health/detailed")
async def health_detailed(
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(require_role("admin", "owner")),
) -> dict[str, Any]:
    """
    Detailed health report.

    Includes version, uptime and full dependency status.
    **Requires admin or owner role.**
    """
    settings = get_settings()

    db_status = await _check_db(db)
    redis_status = await _check_redis()
    es_status = await _check_elasticsearch()

    dependencies = {
        "database": db_status,
        "redis": redis_status,
        "elasticsearch": es_status,
    }

    all_healthy = all(d["status"] == "healthy" for d in dependencies.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.APP_VERSION,
        "uptime_seconds": _uptime_seconds(),
        "environment": "development" if settings.DEBUG else "production",
        "dependencies": dependencies,
    }
