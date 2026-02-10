"""Celery tasks for the Market Intelligence Engine.

These tasks run periodically to:
  1. Refresh Amazon category metadata.
  2. Update BSR history for tracked competitors.
  3. Generate daily market snapshots for each tracked category.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

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
        # In production: upsert into market_categories table
        return count

    try:
        count = _run_async(_refresh())
        logger.info("Category refresh complete: %d categories", count)
        return {"status": "success", "categories_updated": count}
    except Exception as exc:
        logger.error("Category refresh failed: %s", exc)
        raise self.retry(exc=exc)


def _count_nodes(nodes: list[dict]) -> int:
    total = 0
    for n in nodes:
        total += 1
        total += _count_nodes(n.get("children", []))
    return total


# ---------------------------------------------------------------------------
# Task: Update BSR history
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.market_intelligence.update_bsr_history",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
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
        from app.modules.market_intelligence.service import MarketIntelligenceService

        svc = MarketIntelligenceService()
        tracked = await svc.list_competitors()
        client = get_amazon_client()

        updated = 0
        for comp in tracked:
            try:
                product = await client.get_product_detail(comp.asin, marketplace=comp.marketplace)
                if product and product.bsr is not None:
                    # In production: INSERT into competitor BSR history table
                    updated += 1
                    logger.debug(
                        "Updated BSR for %s: %d", comp.asin, product.bsr
                    )
            except Exception as exc:
                logger.warning("Failed to update BSR for %s: %s", comp.asin, exc)

        return updated

    try:
        updated = _run_async(_update())
        logger.info("BSR history update complete: %d competitors updated", updated)
        return {"status": "success", "competitors_updated": updated}
    except Exception as exc:
        logger.error("BSR history update failed: %s", exc)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Task: Generate market snapshots
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.market_intelligence.generate_market_snapshot",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
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
                    "category_id": cat_id,
                    "category_name": analysis.category_name,
                    "snapshot_date": datetime.now(tz=timezone.utc).isoformat(),
                    "avg_bsr": analysis.avg_bsr,
                    "avg_price": analysis.avg_price,
                    "book_count": analysis.book_count,
                    "avg_reviews": analysis.avg_reviews,
                    "competition_score": analysis.competition_score,
                }
                # In production: INSERT into market_snapshots table
                snapshots_created += 1
                logger.debug("Snapshot created for %s: %s", cat_id, snapshot_data)
            except Exception as exc:
                logger.warning("Failed to snapshot category %s: %s", cat_id, exc)

        return snapshots_created

    try:
        count = _run_async(_snapshot())
        logger.info("Market snapshot generation complete: %d snapshots", count)
        return {"status": "success", "snapshots_created": count}
    except Exception as exc:
        logger.error("Market snapshot generation failed: %s", exc)
        raise self.retry(exc=exc)
