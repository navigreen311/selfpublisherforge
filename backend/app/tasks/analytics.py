"""Celery tasks for analytics background processing.

Tasks:
  - daily_metric_aggregation: Computes and stores daily portfolio metric snapshots
  - scheduled_report_generation: Generates scheduled/queued reports
  - royalty_sync: Syncs royalty data from connected publishing platform accounts
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.tasks import celery_app
from app.database import async_session

logger = logging.getLogger(__name__)

# Mapping from PublishingPlatform enum values to analytics Platform enum values.
# The publishing module uses "ingramspark" / "d2d" while the analytics module
# uses "ingram_spark" / "draft2digital".
_PUBLISHING_TO_ANALYTICS_PLATFORM: dict[str, str] = {
    "kdp": "kdp",
    "ingramspark": "ingram_spark",
    "d2d": "draft2digital",
    "acx": "other",
}

# Environment variable names that, when set, indicate an API client is
# available for the given publishing platform.
_PLATFORM_API_ENV_KEYS: dict[str, str] = {
    "kdp": "KDP_API_CLIENT_ID",
    "ingramspark": "INGRAM_SPARK_API_KEY",
    "d2d": "D2D_API_KEY",
    "acx": "ACX_API_KEY",
}


def _run_async(coro):
    """Run an async coroutine from synchronous Celery task context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="analytics.daily_metric_aggregation",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def daily_metric_aggregation(self, org_id: str | None = None) -> dict[str, Any]:
    """Compute and store daily portfolio metric snapshots.

    If org_id is provided, only aggregates for that org.
    Otherwise, aggregates for all active organizations.
    """
    logger.info("Starting daily metric aggregation (org_id=%s)", org_id)

    async def _aggregate():
        from app.modules.analytics.metrics import compute_portfolio_metrics
        from app.modules.analytics.aggregator import save_portfolio_snapshot
        from app.modules.analytics.models import RoyaltyRecord
        from sqlalchemy import select, func, and_

        async with async_session() as db:
            try:
                if org_id:
                    org_ids = [UUID(org_id)]
                else:
                    # Get all distinct org_ids from royalty records
                    query = select(func.distinct(RoyaltyRecord.org_id)).where(
                        RoyaltyRecord.deleted_at.is_(None)
                    )
                    result = await db.execute(query)
                    org_ids = [row[0] for row in result.all()]

                now = datetime.now(timezone.utc)
                snapshots_created = 0

                for oid in org_ids:
                    try:
                        metrics = await compute_portfolio_metrics(db, oid, as_of=now)
                        await save_portfolio_snapshot(
                            db,
                            oid,
                            snapshot_date=now,
                            metrics_data={
                                "total_books": metrics.total_books,
                                "total_revenue": str(metrics.total_revenue),
                                "total_units_sold": metrics.total_units_sold,
                                "total_expenses": str(metrics.total_expenses),
                                "net_profit": str(metrics.net_profit),
                                "avg_roi": str(metrics.avg_roi),
                                "platform_breakdown": {
                                    k: str(v) for k, v in metrics.platform_breakdown.items()
                                },
                                "format_breakdown": metrics.format_breakdown,
                                "top_books": metrics.top_books,
                            },
                        )
                        snapshots_created += 1
                    except Exception as exc:
                        logger.error("Failed to aggregate metrics for org %s: %s", oid, exc)

                await db.commit()
                return {"snapshots_created": snapshots_created, "org_count": len(org_ids)}

            except Exception:
                await db.rollback()
                raise

    try:
        result = _run_async(_aggregate())
        logger.info("Daily metric aggregation complete: %s", result)
        return result
    except Exception as exc:
        logger.error("Daily metric aggregation failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="analytics.scheduled_report_generation",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def scheduled_report_generation(self, report_id: str) -> dict[str, Any]:
    """Generate a queued report by its ID.

    Used for async report generation dispatched from the API.
    """
    logger.info("Starting report generation for report_id=%s", report_id)

    async def _generate():
        from app.modules.analytics.models import Report
        from app.modules.analytics.report_builder import generate_report
        from sqlalchemy import select, and_

        async with async_session() as db:
            try:
                query = select(Report).where(
                    and_(
                        Report.id == UUID(report_id),
                        Report.deleted_at.is_(None),
                    )
                )
                result = await db.execute(query)
                report = result.scalar_one_or_none()

                if not report:
                    return {"error": f"Report {report_id} not found"}

                report = await generate_report(db, report)
                await db.commit()

                return {
                    "report_id": str(report.id),
                    "status": report.status,
                    "file_path": report.file_path,
                    "file_size": report.file_size,
                }

            except Exception:
                await db.rollback()
                raise

    try:
        result = _run_async(_generate())
        logger.info("Report generation complete: %s", result)
        return result
    except Exception as exc:
        logger.error("Report generation failed for %s: %s", report_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="analytics.royalty_sync",
    bind=True,
    max_retries=3,
    default_retry_delay=600,
)
def royalty_sync(self, org_id: str, platform: str | None = None) -> dict[str, Any]:
    """Sync royalty data from connected publishing platform accounts.

    Queries the organization's publishing accounts and, for each active
    account, either processes pending CSV imports or attempts an API-based
    sync when the platform's API client credentials are configured via
    environment variables.

    Args:
        org_id: Organization UUID to sync royalties for.
        platform: Optional platform filter (e.g. ``"kdp"``).  When *None*,
            all active publishing accounts for the org are checked.

    Returns:
        A dict with ``status``, ``records_synced``, ``platforms_checked``,
        and per-platform details.
    """
    logger.info("Starting royalty sync for org_id=%s, platform=%s", org_id, platform)

    async def _sync() -> dict[str, Any]:
        from sqlalchemy import select, and_, update

        from app.models.publishing import PublishingAccount, PublishingAccountStatus
        from app.modules.analytics.models import RoyaltyRecord
        from app.modules.analytics.schemas import Platform as AnalyticsPlatform
        from app.modules.analytics.royalty_importer import (
            import_royalties,
            PLATFORM_PARSERS,
        )

        async with async_session() as db:
            try:
                # ----------------------------------------------------------
                # 1. Discover connected publishing accounts for this org
                # ----------------------------------------------------------
                conditions = [
                    PublishingAccount.org_id == UUID(org_id),
                    PublishingAccount.deleted_at.is_(None),
                    PublishingAccount.status == PublishingAccountStatus.ACTIVE,
                ]
                if platform:
                    conditions.append(
                        PublishingAccount.platform == platform
                    )

                query = select(PublishingAccount).where(and_(*conditions))
                result = await db.execute(query)
                accounts = result.scalars().all()

                if not accounts:
                    logger.info(
                        "No active publishing accounts found for org %s (platform=%s)",
                        org_id,
                        platform,
                    )
                    return {
                        "status": "completed",
                        "records_synced": 0,
                        "platforms_checked": 0,
                        "details": [],
                        "message": "No active publishing accounts found for this organization.",
                    }

                total_records_synced = 0
                platforms_checked = 0
                platform_details: list[dict[str, Any]] = []

                # ----------------------------------------------------------
                # 2. Process each account independently
                # ----------------------------------------------------------
                for account in accounts:
                    acct_platform: str = (
                        account.platform.value
                        if hasattr(account.platform, "value")
                        else str(account.platform)
                    )
                    analytics_platform_key = _PUBLISHING_TO_ANALYTICS_PLATFORM.get(
                        acct_platform
                    )
                    detail: dict[str, Any] = {
                        "account_id": str(account.id),
                        "platform": acct_platform,
                        "records_synced": 0,
                        "errors": [],
                    }
                    platforms_checked += 1

                    try:
                        records_for_account = 0

                        # --------------------------------------------------
                        # 2a. Check for pending CSV imports on this account
                        # --------------------------------------------------
                        if account.credentials_encrypted and analytics_platform_key:
                            # The credentials_encrypted field may hold a
                            # base64-encoded CSV payload that was uploaded
                            # for batch processing but not yet imported.
                            # Try to treat it as pending CSV import data.
                            csv_records = await _try_csv_import(
                                db,
                                org_id=UUID(org_id),
                                analytics_platform_key=analytics_platform_key,
                                csv_data=None,  # No pending queue yet
                            )
                            records_for_account += csv_records

                        # --------------------------------------------------
                        # 2b. Attempt API sync if env-var credentials exist
                        # --------------------------------------------------
                        env_key = _PLATFORM_API_ENV_KEYS.get(acct_platform)
                        if env_key and os.environ.get(env_key):
                            api_records = await _try_api_sync(
                                db,
                                org_id=UUID(org_id),
                                account=account,
                                acct_platform=acct_platform,
                                analytics_platform_key=analytics_platform_key,
                            )
                            records_for_account += api_records

                        # --------------------------------------------------
                        # 2c. Upsert any newly discovered royalty data
                        #     (de-duplicate against existing records)
                        # --------------------------------------------------
                        # De-duplication is handled inside the import helpers
                        # above, so we just accumulate the count.

                        total_records_synced += records_for_account
                        detail["records_synced"] = records_for_account
                        detail["status"] = "synced"

                        # --------------------------------------------------
                        # 2d. Update account's last-synced timestamp
                        # --------------------------------------------------
                        account.updated_at = datetime.now(timezone.utc)

                    except Exception as exc:
                        logger.error(
                            "Royalty sync failed for account %s (platform=%s): %s",
                            account.id,
                            acct_platform,
                            exc,
                            exc_info=True,
                        )
                        detail["status"] = "error"
                        detail["errors"].append(str(exc))
                        # Continue processing other accounts; one failure
                        # must not block the rest.

                    platform_details.append(detail)

                await db.commit()

                status = "completed"
                if all(d.get("status") == "error" for d in platform_details):
                    status = "failed"
                elif any(d.get("status") == "error" for d in platform_details):
                    status = "partial"

                return {
                    "status": status,
                    "records_synced": total_records_synced,
                    "platforms_checked": platforms_checked,
                    "details": platform_details,
                }

            except Exception:
                await db.rollback()
                raise

    try:
        result = _run_async(_sync())
        logger.info("Royalty sync complete for org %s: %s", org_id, result)
        return result
    except Exception as exc:
        logger.error("Royalty sync failed for org %s: %s", org_id, exc)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Internal helpers for royalty_sync
# ---------------------------------------------------------------------------

async def _try_csv_import(
    db,
    org_id: UUID,
    analytics_platform_key: str,
    csv_data: str | None,
) -> int:
    """Attempt to import royalty records from a pending CSV payload.

    Returns the number of records successfully imported.
    """
    if csv_data is None:
        # No pending CSV data to process for this cycle.
        return 0

    from app.modules.analytics.schemas import Platform as AnalyticsPlatform
    from app.modules.analytics.royalty_importer import import_royalties

    try:
        analytics_platform = AnalyticsPlatform(analytics_platform_key)
    except ValueError:
        logger.warning("Unknown analytics platform key: %s", analytics_platform_key)
        return 0

    result = await import_royalties(db, org_id, analytics_platform, csv_data)
    if result.errors:
        logger.warning(
            "CSV import had %d error(s) for org %s / %s: %s",
            len(result.errors),
            org_id,
            analytics_platform_key,
            result.errors[:5],
        )
    return result.records_imported


async def _try_api_sync(
    db,
    org_id: UUID,
    account,
    acct_platform: str,
    analytics_platform_key: str | None,
) -> int:
    """Attempt an API-based royalty sync for a single publishing account.

    If the platform exposes an API client (indicated by the corresponding
    environment variable), this fetches recent royalty data and upserts
    records into the ``royalty_records`` table.

    Returns the number of records upserted.
    """
    from sqlalchemy import select, and_
    from app.modules.analytics.models import RoyaltyRecord

    records_synced = 0

    # ------------------------------------------------------------------
    # Fetch royalty data from the platform API.
    # Each platform would have its own client; for now we provide the
    # scaffolding and log when credentials are present but no SDK is
    # installed.
    # ------------------------------------------------------------------
    api_records: list[dict[str, Any]] = []

    if acct_platform == "kdp":
        api_records = await _fetch_kdp_royalties(account)
    elif acct_platform == "ingramspark":
        api_records = await _fetch_ingramspark_royalties(account)
    elif acct_platform == "d2d":
        api_records = await _fetch_d2d_royalties(account)
    else:
        logger.info("No API sync handler for platform '%s'; skipping.", acct_platform)
        return 0

    # ------------------------------------------------------------------
    # Upsert each record, de-duplicating by (org, platform, title,
    # period_start, marketplace).
    # ------------------------------------------------------------------
    for rec_data in api_records:
        try:
            existing_query = select(RoyaltyRecord).where(
                and_(
                    RoyaltyRecord.org_id == org_id,
                    RoyaltyRecord.platform == rec_data.get("platform", analytics_platform_key),
                    RoyaltyRecord.title == rec_data["title"],
                    RoyaltyRecord.period_start == rec_data["period_start"],
                    RoyaltyRecord.marketplace == rec_data.get("marketplace", "US"),
                    RoyaltyRecord.deleted_at.is_(None),
                )
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                # Update existing record with fresh data
                for field in (
                    "units_sold", "units_refunded", "net_units",
                    "gross_revenue", "net_revenue", "list_price",
                    "royalty_rate", "currency",
                ):
                    if field in rec_data:
                        setattr(existing, field, rec_data[field])
                existing.updated_at = datetime.now(timezone.utc)
                existing.raw_data = rec_data.get("raw_data", existing.raw_data)
            else:
                record = RoyaltyRecord(
                    org_id=org_id,
                    platform=rec_data.get("platform", analytics_platform_key),
                    marketplace=rec_data.get("marketplace", "US"),
                    title=rec_data["title"],
                    asin=rec_data.get("asin"),
                    isbn=rec_data.get("isbn"),
                    format_type=rec_data.get("format_type", "ebook"),
                    units_sold=rec_data.get("units_sold", 0),
                    units_refunded=rec_data.get("units_refunded", 0),
                    net_units=rec_data.get("net_units", 0),
                    list_price=rec_data.get("list_price", Decimal("0.00")),
                    royalty_rate=rec_data.get("royalty_rate", Decimal("0.70")),
                    gross_revenue=rec_data.get("gross_revenue", Decimal("0.00")),
                    net_revenue=rec_data.get("net_revenue", Decimal("0.00")),
                    currency=rec_data.get("currency", "USD"),
                    period_start=rec_data["period_start"],
                    period_end=rec_data["period_end"],
                    raw_data=rec_data.get("raw_data"),
                )
                db.add(record)

            records_synced += 1
        except Exception as exc:
            logger.warning(
                "Failed to upsert royalty record for org %s: %s",
                org_id,
                exc,
            )

    if records_synced:
        await db.flush()

    return records_synced


async def _fetch_kdp_royalties(account) -> list[dict[str, Any]]:
    """Fetch royalty data from the Amazon KDP Reporting API.

    Requires ``KDP_API_CLIENT_ID`` and ``KDP_API_CLIENT_SECRET`` env vars.
    Returns a list of normalised royalty record dicts ready for upsert.
    """
    client_id = os.environ.get("KDP_API_CLIENT_ID", "")
    client_secret = os.environ.get("KDP_API_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        logger.debug("KDP API credentials not fully configured; skipping API sync.")
        return []

    # TODO: Implement actual KDP API call once Amazon exposes a stable
    # reporting endpoint and the project adds an HTTP client dependency.
    # The implementation would:
    #   1. Authenticate via OAuth using client_id / client_secret
    #   2. Request the latest monthly royalty report
    #   3. Parse the response and return normalised dicts matching the
    #      RoyaltyRecord field schema
    logger.info(
        "KDP API client is configured for account %s; "
        "API fetch will be performed when the KDP SDK is integrated.",
        account.id,
    )
    return []


async def _fetch_ingramspark_royalties(account) -> list[dict[str, Any]]:
    """Fetch royalty data from the IngramSpark publisher API.

    Requires ``INGRAM_SPARK_API_KEY`` env var.
    Returns a list of normalised royalty record dicts ready for upsert.
    """
    api_key = os.environ.get("INGRAM_SPARK_API_KEY", "")
    if not api_key:
        logger.debug("IngramSpark API key not configured; skipping API sync.")
        return []

    # TODO: Implement IngramSpark API integration.
    # The implementation would:
    #   1. Authenticate with the IngramSpark REST API using the api_key
    #   2. Pull compensation reports for the current period
    #   3. Return normalised dicts matching the RoyaltyRecord field schema
    logger.info(
        "IngramSpark API key is configured for account %s; "
        "API fetch will be performed when the IngramSpark client is integrated.",
        account.id,
    )
    return []


async def _fetch_d2d_royalties(account) -> list[dict[str, Any]]:
    """Fetch royalty data from the Draft2Digital reporting API.

    Requires ``D2D_API_KEY`` env var.
    Returns a list of normalised royalty record dicts ready for upsert.
    """
    api_key = os.environ.get("D2D_API_KEY", "")
    if not api_key:
        logger.debug("D2D API key not configured; skipping API sync.")
        return []

    # TODO: Implement Draft2Digital API integration.
    # The implementation would:
    #   1. Authenticate using the D2D partner API key
    #   2. Retrieve the payout/royalty report for the current period
    #   3. Return normalised dicts matching the RoyaltyRecord field schema
    logger.info(
        "D2D API key is configured for account %s; "
        "API fetch will be performed when the D2D client is integrated.",
        account.id,
    )
    return []


# ---------- Celery Beat Schedule (for periodic tasks) ----------
# Merge analytics tasks into the existing beat schedule rather than overwriting it.

ANALYTICS_BEAT_SCHEDULE = {
    "daily-metric-aggregation": {
        "task": "analytics.daily_metric_aggregation",
        "schedule": 86400.0,  # Every 24 hours
        "args": (None,),  # All orgs
    },
}

_existing_schedule = getattr(celery_app.conf, "beat_schedule", None) or {}
_existing_schedule.update(ANALYTICS_BEAT_SCHEDULE)
celery_app.conf.beat_schedule = _existing_schedule
