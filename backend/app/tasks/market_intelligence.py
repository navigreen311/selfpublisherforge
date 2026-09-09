"""Celery tasks for the Market Intelligence Engine.

These tasks run periodically to:
  1. Refresh Amazon category metadata.
  2. Update BSR history for tracked competitors.
  3. Generate daily market snapshots for each tracked category.

Time limit strategy
-------------------
Each task declares explicit ``soft_time_limit`` and ``time_limit`` values
(in seconds) based on expected workload:
  - Quick   (notifications, status updates):   soft=60,   hard=120
  - Medium  (API calls, data sync):            soft=300,  hard=600
  - Long    (bulk imports, report generation):  soft=1800, hard=3600
  - V. Long (full analytics aggregation):       soft=3300, hard=3600
Global defaults in config.py are 3300/3600 but per-task limits take precedence.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, date, datetime

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session
from app.models.market import CompetitorBook, MarketCategory, MarketSnapshot
from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Task: Refresh category data
# ---------------------------------------------------------------------------


@celery_app.task(
    name="app.tasks.market_intelligence.refresh_category_data",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def refresh_category_data(self):
    """Refresh Amazon category tree and metadata.

    Scheduled to run daily.  Fetches the full category taxonomy and
    updates the local ``market_categories`` table.
    """
    logger.info("Starting category data refresh")

    async def _refresh():
        from app.modules.market_intelligence.amazon_client import get_amazon_client

        client = get_amazon_client()
        categories = await client.get_category_tree()
        count = _count_nodes(categories)
        logger.info("Fetched %d category nodes", count)

        # Flatten the tree and upsert each node into market_categories
        flat = _flatten_category_tree(categories)
        async with async_session() as session:
            async with session.begin():
                for node in flat:
                    result = await session.execute(
                        select(MarketCategory).where(MarketCategory.amazon_node_id == node["id"])
                    )
                    existing = result.scalar_one_or_none()
                    if existing:
                        existing.name = node["name"]
                        existing.book_count = node.get("book_count") or 0
                    else:
                        cat = MarketCategory(
                            amazon_node_id=node["id"],
                            name=node["name"],
                            book_count=node.get("book_count") or 0,
                        )
                        session.add(cat)
        return count

    try:
        count = _run_async(_refresh())
        logger.info("Category refresh complete: %d categories", count)
        return {"status": "success", "categories_updated": count}
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except SQLAlchemyError as exc:
        logger.error("Category refresh DB error: %s", exc)
        raise self.retry(exc=exc)
    except ConnectionError as exc:
        logger.error("Category refresh connection failed: %s", exc)
        raise self.retry(exc=exc)


def _count_nodes(nodes: list[dict]) -> int:
    total = 0
    for n in nodes:
        total += 1
        total += _count_nodes(n.get("children", []))
    return total


def _flatten_category_tree(nodes: list[dict]) -> list[dict]:
    """Flatten a nested category tree into a list of node dicts."""
    flat: list[dict] = []
    for n in nodes:
        flat.append(n)
        flat.extend(_flatten_category_tree(n.get("children", [])))
    return flat


# ---------------------------------------------------------------------------
# Task: Update BSR history
# ---------------------------------------------------------------------------


@celery_app.task(
    name="app.tasks.market_intelligence.update_bsr_history",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=1800,
    time_limit=3600,
)
def update_bsr_history(self):
    """Update BSR history for all tracked competitor books.

    Scheduled to run every 6 hours.  For each tracked ASIN, fetches
    the latest BSR and appends a data point to the ``competitor_books``
    BSR history.
    """
    logger.info("Starting BSR history update")

    async def _update():
        from app.modules.market_intelligence.amazon_client import get_amazon_client

        client = get_amazon_client()

        async with async_session() as session:
            async with session.begin():
                result = await session.execute(select(CompetitorBook).where(CompetitorBook.deleted_at.is_(None)))
                tracked = result.scalars().all()

            updated = 0
            for comp in tracked:
                marketplace = (comp.metadata_json or {}).get("marketplace", "US")
                try:
                    product = await client.get_product_detail(comp.asin, marketplace=marketplace)
                    if product and product.bsr is not None:
                        now_iso = datetime.now(tz=UTC).isoformat()
                        bsr_point = {
                            "date": now_iso,
                            "bsr": product.bsr,
                            "price": product.price,
                        }
                        async with session.begin():
                            history = list(comp.bsr_history or [])
                            history.append(bsr_point)
                            comp.bsr_history = history
                            comp.bsr_current = product.bsr
                            session.add(comp)
                        updated += 1
                        logger.debug("Updated BSR for %s: %d", comp.asin, product.bsr)
                except (SQLAlchemyError, ConnectionError) as exc:
                    logger.warning("Failed to update BSR for %s: %s", comp.asin, exc)

        return updated

    try:
        updated = _run_async(_update())
        logger.info("BSR history update complete: %d competitors updated", updated)
        return {"status": "success", "competitors_updated": updated}
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except SQLAlchemyError as exc:
        logger.error("BSR history update DB error: %s", exc)
        raise self.retry(exc=exc)
    except ConnectionError as exc:
        logger.error("BSR history update connection failed: %s", exc)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Task: Generate market snapshots
# ---------------------------------------------------------------------------


@celery_app.task(
    name="app.tasks.market_intelligence.generate_market_snapshot",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def generate_market_snapshot(self, category_id: str | None = None):
    """Generate a daily market snapshot for a category.

    Scheduled to run once per day per tracked category.  Computes
    aggregate statistics and stores them in ``market_snapshots``.
    """
    logger.info("Generating market snapshot for category=%s", category_id)

    async def _snapshot():
        from app.modules.market_intelligence.service import MarketIntelligenceService

        svc = MarketIntelligenceService()
        target_ids = [category_id] if category_id else ["154606011", "18574", "10399"]

        snapshots_created = 0
        for cat_id in target_ids:
            try:
                analysis = await svc.get_category_analysis(cat_id)
                snapshot_data = {
                    "avg_bsr": analysis.avg_bsr,
                    "avg_price": analysis.avg_price,
                    "book_count": analysis.book_count,
                    "avg_reviews": analysis.avg_reviews,
                    "competition_score": analysis.competition_score,
                }

                async with async_session() as session:
                    async with session.begin():
                        # Look up or create the MarketCategory row for this node
                        cat_result = await session.execute(
                            select(MarketCategory).where(
                                MarketCategory.amazon_node_id == cat_id,
                                MarketCategory.deleted_at.is_(None),
                            )
                        )
                        cat_obj = cat_result.scalar_one_or_none()
                        if cat_obj is None:
                            cat_obj = MarketCategory(
                                amazon_node_id=cat_id,
                                name=analysis.category_name,
                                book_count=analysis.book_count,
                            )
                            session.add(cat_obj)
                            await session.flush()

                        snapshot = MarketSnapshot(
                            category_id=cat_obj.id,
                            snapshot_date=date.today(),
                            metrics=snapshot_data,
                        )
                        session.add(snapshot)

                snapshots_created += 1
                logger.debug("Snapshot created for %s: %s", cat_id, snapshot_data)
            except (SQLAlchemyError, ConnectionError) as exc:
                logger.warning("Failed to snapshot category %s: %s", cat_id, exc)

        return snapshots_created

    try:
        count = _run_async(_snapshot())
        logger.info("Market snapshot generation complete: %d snapshots", count)
        return {"status": "success", "snapshots_created": count}
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except SQLAlchemyError as exc:
        logger.error("Market snapshot generation DB error: %s", exc)
        raise self.retry(exc=exc)
    except ConnectionError as exc:
        logger.error("Market snapshot generation connection failed: %s", exc)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Celery Beat schedule entry (to be registered in celery config)
# ---------------------------------------------------------------------------

CELERY_BEAT_SCHEDULE = {
    "refresh-category-data-daily": {
        "task": "app.tasks.market_intelligence.refresh_category_data",
        "schedule": 86400.0,  # Every 24 hours
    },
    "update-bsr-history-6h": {
        "task": "app.tasks.market_intelligence.update_bsr_history",
        "schedule": 21600.0,  # Every 6 hours
    },
    "generate-market-snapshot-daily": {
        "task": "app.tasks.market_intelligence.generate_market_snapshot",
        "schedule": 86400.0,  # Every 24 hours
    },
}
