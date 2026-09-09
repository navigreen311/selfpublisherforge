"""Celery tasks for analytics background processing.

Tasks:
  - daily_metric_aggregation: Computes and stores daily portfolio metric snapshots
  - scheduled_report_generation: Generates scheduled/queued reports
  - royalty_sync: Syncs royalty data from connected publishing platform accounts

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
import hashlib
import hmac
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session
from app.tasks import celery_app

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
    "kdp": "KDP_ACCESS_KEY",
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
    soft_time_limit=3300,
    time_limit=3600,
)
def daily_metric_aggregation(self, org_id: str | None = None) -> dict[str, Any]:
    """Compute and store daily portfolio metric snapshots.

    If org_id is provided, only aggregates for that org.
    Otherwise, aggregates for all active organizations.
    """
    logger.info("Starting daily metric aggregation (org_id=%s)", org_id)

    async def _aggregate():
        from sqlalchemy import func, select

        from app.modules.analytics.aggregator import save_portfolio_snapshot
        from app.modules.analytics.metrics import compute_portfolio_metrics
        from app.modules.analytics.models import RoyaltyRecord

        async with async_session() as db:
            try:
                if org_id:
                    org_ids = [UUID(org_id)]
                else:
                    # Get all distinct org_ids from royalty records
                    query = select(func.distinct(RoyaltyRecord.org_id)).where(RoyaltyRecord.deleted_at.is_(None))
                    result = await db.execute(query)
                    org_ids = [row[0] for row in result.all()]

                now = datetime.now(UTC)
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
                                "platform_breakdown": {k: str(v) for k, v in metrics.platform_breakdown.items()},
                                "format_breakdown": metrics.format_breakdown,
                                "top_books": metrics.top_books,
                            },
                        )
                        snapshots_created += 1
                    except (ValueError, TypeError, KeyError) as exc:
                        logger.exception("Failed to aggregate metrics for org %s: %s", oid, exc)

                await db.commit()
                return {"snapshots_created": snapshots_created, "org_count": len(org_ids)}

            except (SQLAlchemyError, ValueError, TypeError, KeyError) as exc:
                logger.error("DB error during daily metric aggregation: %s", exc, exc_info=True)
                await db.rollback()
                raise

    try:
        result = _run_async(_aggregate())
        logger.info("Daily metric aggregation complete: %s", result)
        return result
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.exception("Daily metric aggregation failed: %s", exc)
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="analytics.scheduled_report_generation",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1800,
    time_limit=3600,
)
def scheduled_report_generation(self, report_id: str) -> dict[str, Any]:
    """Generate a queued report by its ID.

    Used for async report generation dispatched from the API.
    """
    logger.info("Starting report generation for report_id=%s", report_id)

    async def _generate():
        from sqlalchemy import and_, select

        from app.modules.analytics.models import Report
        from app.modules.analytics.report_builder import generate_report

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

            except (SQLAlchemyError, ValueError, TypeError, KeyError) as exc:
                logger.error("DB error during report generation for %s: %s", report_id, exc, exc_info=True)
                await db.rollback()
                raise

    try:
        result = _run_async(_generate())
        logger.info("Report generation complete: %s", result)
        return result
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.exception("Report generation failed for %s: %s", report_id, exc)
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="analytics.royalty_sync",
    bind=True,
    max_retries=3,
    default_retry_delay=600,
    soft_time_limit=300,
    time_limit=600,
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
        from sqlalchemy import and_, select

        from app.models.publishing import PublishingAccount, PublishingAccountStatus

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
                    conditions.append(PublishingAccount.platform == platform)

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
                        account.platform.value if hasattr(account.platform, "value") else str(account.platform)
                    )
                    analytics_platform_key = _PUBLISHING_TO_ANALYTICS_PLATFORM.get(acct_platform)
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
                            # Use the CSV import queue module if available.
                            csv_data = account.credentials_encrypted
                            try:
                                from app.modules.analytics.csv_queue import process_csv_import

                                count = await process_csv_import(db, account.id, account.platform, csv_data)
                                logger.info("CSV import completed: %d records for account %s", count, account.id)
                                records_for_account += count
                            except ImportError:
                                logger.warning(
                                    "CSV import queue module not available; skipping for account %s", account.id
                                )
                                # Fall back to the legacy _try_csv_import helper
                                csv_records = await _try_csv_import(
                                    db,
                                    org_id=UUID(org_id),
                                    analytics_platform_key=analytics_platform_key,
                                    csv_data=None,
                                )
                                records_for_account += csv_records
                            except Exception as exc:
                                logger.error("CSV import failed for account %s: %s", account.id, exc)

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
                        account.updated_at = datetime.now(UTC)

                    except (
                        ConnectionError,
                        TimeoutError,
                        ValueError,
                        KeyError,
                        httpx.HTTPError,
                    ) as exc:
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

            except (SQLAlchemyError, ValueError, TypeError, KeyError) as exc:
                logger.error("DB error during royalty sync for org %s: %s", org_id, exc, exc_info=True)
                await db.rollback()
                raise

    try:
        result = _run_async(_sync())
        logger.info("Royalty sync complete for org %s: %s", org_id, result)
        return result
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.exception("Royalty sync failed for org %s: %s", org_id, exc)
        raise self.retry(exc=exc) from exc


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
        logger.debug(
            "No pending CSV data to process for org %s (platform=%s); " "CSV queue integration pending.",
            org_id,
            analytics_platform_key,
        )
        return 0

    from app.modules.analytics.royalty_importer import import_royalties
    from app.modules.analytics.schemas import Platform as AnalyticsPlatform

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
    from sqlalchemy import and_, select

    from app.modules.analytics.models import RoyaltyRecord

    records_synced = 0

    # ------------------------------------------------------------------
    # Fetch royalty data from the platform API.
    # Each platform has its own client implementation.  KDP, IngramSpark,
    # and D2D handlers are wired up below; additional platforms will log a
    # warning until their API integrations are complete.
    # ------------------------------------------------------------------
    api_records: list[dict[str, Any]] = []

    if acct_platform == "kdp":
        api_records = await _fetch_kdp_royalties(account)
    elif acct_platform == "ingramspark":
        api_records = await _fetch_ingramspark_royalties(account)
    elif acct_platform == "d2d":
        api_records = await _fetch_d2d_royalties(account)
    else:
        logger.warning(
            "No API sync handler for platform '%s'; skipping. " "API integration pending for this platform.",
            acct_platform,
        )
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
                    "units_sold",
                    "units_refunded",
                    "net_units",
                    "gross_revenue",
                    "net_revenue",
                    "list_price",
                    "royalty_rate",
                    "currency",
                ):
                    if field in rec_data:
                        setattr(existing, field, rec_data[field])
                existing.updated_at = datetime.now(UTC)
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
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning(
                "Failed to upsert royalty record for org %s: %s",
                org_id,
                exc,
                exc_info=True,
            )

    if records_synced:
        await db.flush()

    return records_synced


async def _fetch_kdp_royalties(account) -> list[dict[str, Any]]:
    """Fetch royalty data from the Amazon KDP Reporting API.

    Requires ``KDP_ACCESS_KEY`` and ``KDP_SECRET_KEY`` env vars.
    Authenticates using HMAC-SHA256 signed requests against the KDP
    sales reporting endpoint.

    Returns a list of normalised royalty record dicts ready for upsert.
    """
    access_key = os.environ.get("KDP_ACCESS_KEY", "")
    secret_key = os.environ.get("KDP_SECRET_KEY", "")
    if not access_key or not secret_key:
        logger.warning(
            "KDP API credentials (KDP_ACCESS_KEY / KDP_SECRET_KEY) not configured; "
            "skipping API sync for account %s.",
            account.id,
        )
        return []

    base_url = os.environ.get("KDP_API_BASE_URL", "https://kdp.amazon.com/api/reports/v1")

    # Determine the reporting period: last full calendar month.
    now = datetime.now(UTC)
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = first_of_this_month - timedelta(microseconds=1)
    period_start = (first_of_this_month - timedelta(days=1)).replace(day=1)

    report_url = f"{base_url}/royalties"
    params = {
        "startDate": period_start.strftime("%Y-%m-%d"),
        "endDate": period_end.strftime("%Y-%m-%d"),
        "granularity": "MONTHLY",
    }

    logger.info(
        "Fetching KDP royalties for account %s, period %s to %s",
        account.id,
        params["startDate"],
        params["endDate"],
    )

    response_data = await _kdp_api_request(
        method="GET",
        url=report_url,
        params=params,
        access_key=access_key,
        secret_key=secret_key,
    )

    if response_data is None:
        return []

    return _parse_kdp_royalty_response(response_data, period_start, period_end)


def _kdp_sign_request(
    method: str,
    url: str,
    timestamp: str,
    access_key: str,
    secret_key: str,
    params: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build HMAC-SHA256 signed headers for the KDP Reporting API.

    The signing scheme follows Amazon's standard pattern:
      1. Build a canonical string from the HTTP method, path, sorted query
         parameters, and timestamp.
      2. Sign the canonical string with the secret key using HMAC-SHA256.
      3. Return the Authorization and timestamp headers.
    """
    from urllib.parse import urlencode, urlparse

    parsed = urlparse(url)
    canonical_path = parsed.path or "/"

    # Sort query parameters for deterministic signing
    sorted_params = ""
    if params:
        sorted_params = urlencode(sorted(params.items()))

    canonical_string = f"{method.upper()}\n{canonical_path}\n{sorted_params}\n{timestamp}"

    signature = hmac.new(
        secret_key.encode("utf-8"),
        canonical_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        "Authorization": f"KDP-HMAC-SHA256 Credential={access_key}, Signature={signature}",
        "X-KDP-Timestamp": timestamp,
        "X-KDP-Content-SHA256": hashlib.sha256(b"").hexdigest(),
        "Accept": "application/json",
        "User-Agent": "SelfPublisherForge/0.1.0",
    }


async def _kdp_api_request(
    method: str,
    url: str,
    params: dict[str, str] | None = None,
    access_key: str = "",
    secret_key: str = "",
    max_retries: int = 3,
) -> dict[str, Any] | None:
    """Execute an authenticated request to the KDP Reporting API with retry.

    Retries up to *max_retries* times using exponential backoff (1s, 2s, 4s).
    Returns the parsed JSON response body on success, or ``None`` on failure.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            headers = _kdp_sign_request(
                method=method,
                url=url,
                timestamp=timestamp,
                access_key=access_key,
                secret_key=secret_key,
                params=params,
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                )

            if response.status_code == 200:
                return response.json()

            # Retriable server errors
            if response.status_code in (429, 500, 502, 503, 504):
                logger.warning(
                    "KDP API returned %d on attempt %d/%d: %s",
                    response.status_code,
                    attempt + 1,
                    max_retries,
                    response.text[:500],
                )
                last_exception = httpx.HTTPStatusError(
                    f"KDP API error: {response.status_code}",
                    request=response.request,
                    response=response,
                )
            else:
                # Non-retriable client errors (400, 401, 403, etc.)
                logger.error(
                    "KDP API returned non-retriable status %d: %s",
                    response.status_code,
                    response.text[:500],
                )
                return None

        except httpx.TimeoutException as exc:
            logger.warning(
                "KDP API request timed out on attempt %d/%d: %s",
                attempt + 1,
                max_retries,
                exc,
            )
            last_exception = exc

        except httpx.RequestError as exc:
            logger.warning(
                "KDP API request failed on attempt %d/%d: %s",
                attempt + 1,
                max_retries,
                exc,
            )
            last_exception = exc

        # Exponential backoff: 1s, 2s, 4s
        if attempt < max_retries - 1:
            backoff = 2**attempt
            logger.debug("Retrying KDP API request in %ds ...", backoff)
            await asyncio.sleep(backoff)

    logger.error(
        "KDP API request failed after %d attempts. Last error: %s",
        max_retries,
        last_exception,
    )
    return None


# -- KDP marketplace code to human-readable name mapping --
_KDP_MARKETPLACE_MAP: dict[str, str] = {
    "ATVPDKIKX0DER": "US",
    "A1F83G8C2ARO7P": "UK",
    "A13V1IB3VIYZZH": "FR",
    "A1PA6795UKMFR9": "DE",
    "APJ6JRA9NG5V4": "IT",
    "A1RKKUPIHCS9HS": "ES",
    "A21TJRUUN4KGV": "IN",
    "A1VC6025VUSJ7K": "JP",
    "A3K6Y4MI8GDQMW": "CA",
    "A39IBJ37TRP1C6": "AU",
    "A2Q3Y263D00KWC": "BR",
    "A2VIGQ35RCS4UG": "MX",
    "A1805IZSGTT6HS": "NL",
}


def _parse_kdp_royalty_response(
    data: dict[str, Any],
    period_start: datetime,
    period_end: datetime,
) -> list[dict[str, Any]]:
    """Normalise KDP API response into internal royalty record dicts.

    Expected KDP response structure::

        {
            "reports": [
                {
                    "title": "My Book Title",
                    "asin": "B0...",
                    "isbn": "978...",
                    "marketplace": "ATVPDKIKX0DER",
                    "formatType": "EBOOK",
                    "unitsSold": 42,
                    "unitsRefunded": 1,
                    "netUnits": 41,
                    "listPrice": {"amount": "9.99", "currency": "USD"},
                    "royaltyRate": "0.70",
                    "grossRevenue": {"amount": "419.58", "currency": "USD"},
                    "netRevenue": {"amount": "286.93", "currency": "USD"}
                },
                ...
            ]
        }
    """
    records: list[dict[str, Any]] = []
    report_items = data.get("reports", [])

    if not report_items:
        logger.info("KDP API returned no royalty report items for the period.")
        return records

    for item in report_items:
        try:
            marketplace_code = item.get("marketplace", "")
            marketplace = _KDP_MARKETPLACE_MAP.get(marketplace_code, marketplace_code)

            list_price_obj = item.get("listPrice", {})
            gross_obj = item.get("grossRevenue", {})
            net_obj = item.get("netRevenue", {})

            currency = net_obj.get("currency") or gross_obj.get("currency") or list_price_obj.get("currency") or "USD"

            format_raw = item.get("formatType", "EBOOK").lower()
            format_map = {
                "ebook": "ebook",
                "paperback": "paperback",
                "hardcover": "hardcover",
                "audiobook": "audiobook",
            }
            format_type = format_map.get(format_raw, "ebook")

            record: dict[str, Any] = {
                "platform": "kdp",
                "marketplace": marketplace,
                "title": item.get("title", "Unknown Title"),
                "asin": item.get("asin"),
                "isbn": item.get("isbn"),
                "format_type": format_type,
                "units_sold": int(item.get("unitsSold", 0)),
                "units_refunded": int(item.get("unitsRefunded", 0)),
                "net_units": int(item.get("netUnits", 0)),
                "list_price": Decimal(str(list_price_obj.get("amount", "0.00"))),
                "royalty_rate": Decimal(str(item.get("royaltyRate", "0.70"))),
                "gross_revenue": Decimal(str(gross_obj.get("amount", "0.00"))),
                "net_revenue": Decimal(str(net_obj.get("amount", "0.00"))),
                "currency": currency,
                "period_start": period_start,
                "period_end": period_end,
                "raw_data": item,
            }
            records.append(record)
        except (ValueError, TypeError, KeyError) as exc:
            logger.warning("Failed to parse KDP royalty item: %s — %s", exc, item)
            continue

    logger.info(
        "Parsed %d royalty records from KDP API response (%d raw items).",
        len(records),
        len(report_items),
    )
    return records


async def _fetch_ingramspark_royalties(account) -> list[dict[str, Any]]:
    """Fetch royalty/compensation data from the IngramSpark publisher REST API.

    Prefers the new ``IngramSparkClient`` from ``app.modules.analytics.ingram_client``
    when available.  Falls back to the legacy env-var / HMAC approach if the
    module is not yet installed or the client factory returns ``None``.

    Requires ``INGRAM_SPARK_API_KEY`` and ``INGRAM_SPARK_API_SECRET`` env vars
    for the legacy path.

    The function targets the previous full calendar month and returns a list of
    normalised royalty record dicts ready for upsert into ``royalty_records``.
    """

    # ------------------------------------------------------------------
    # Try the new IngramSparkClient first.
    # ------------------------------------------------------------------
    try:
        from app.modules.analytics.ingram_client import get_ingram_client

        client = get_ingram_client()
        if client is not None:
            now = datetime.now(UTC)
            first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = first_of_this_month - timedelta(microseconds=1)
            period_start = (first_of_this_month - timedelta(days=1)).replace(day=1)

            logger.info(
                "Fetching IngramSpark royalties via IngramSparkClient for account %s, " "period %s to %s",
                account.id,
                period_start.strftime("%Y-%m-%d"),
                period_end.strftime("%Y-%m-%d"),
            )
            royalties = await client.fetch_royalties(period_start, period_end)
            logger.info(
                "IngramSparkClient returned %d royalty records for account %s.",
                len(royalties),
                account.id,
            )
            return royalties
        logger.info(
            "IngramSparkClient not configured (get_ingram_client() returned None); "
            "falling back to legacy API path for account %s.",
            account.id,
        )
    except ImportError:
        logger.info(
            "ingram_client module not available; falling back to legacy API path " "for account %s.",
            account.id,
        )
    except Exception as exc:
        logger.error(
            "IngramSparkClient failed for account %s: %s; falling back to legacy API path.",
            account.id,
            exc,
            exc_info=True,
        )

    # ------------------------------------------------------------------
    # Legacy path: direct env-var / HMAC authentication.
    # ------------------------------------------------------------------
    api_key = os.environ.get("INGRAM_SPARK_API_KEY", "")
    api_secret = os.environ.get("INGRAM_SPARK_API_SECRET", "")
    if not api_key:
        logger.warning(
            "IngramSpark API key (INGRAM_SPARK_API_KEY) not configured for "
            "account %s; skipping API sync. Pending API integration.",
            account.id,
        )
        return []
    if not api_secret:
        logger.warning(
            "IngramSpark API secret (INGRAM_SPARK_API_SECRET) not configured for "
            "account %s; skipping API sync. Pending API integration.",
            account.id,
        )
        return []

    base_url = os.environ.get(
        "INGRAM_SPARK_API_URL",
        "https://api.ingramspark.com/v1",
    )

    # ------------------------------------------------------------------
    # Determine the reporting period (previous full calendar month).
    # ------------------------------------------------------------------
    now = datetime.now(UTC)
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = first_of_this_month - timedelta(microseconds=1)
    period_start = (first_of_this_month - timedelta(days=1)).replace(day=1)

    params: dict[str, str] = {
        "startDate": period_start.strftime("%Y-%m-%d"),
        "endDate": period_end.strftime("%Y-%m-%d"),
    }

    # ------------------------------------------------------------------
    # Build HMAC-SHA256 signature for request authentication.
    # ------------------------------------------------------------------
    timestamp = str(int(time.time()))
    message = f"{api_key}{timestamp}"
    signature = hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "X-IngramSpark-Key": api_key,
        "X-IngramSpark-Signature": signature,
        "X-IngramSpark-Timestamp": timestamp,
        "Accept": "application/json",
        "User-Agent": "SelfPublisherForge/0.1.0",
    }

    logger.info(
        "Fetching IngramSpark compensations for account %s, period %s to %s",
        account.id,
        params["startDate"],
        params["endDate"],
    )

    # ------------------------------------------------------------------
    # Fetch compensation report with retries and exponential backoff.
    # ------------------------------------------------------------------
    response_data = await _ingramspark_api_request(
        url=f"{base_url}/compensation/reports",
        headers=headers,
        params=params,
        account_id=str(account.id),
    )

    if response_data is None:
        return []

    return _parse_ingramspark_response(response_data, period_start, period_end, account)


async def _ingramspark_api_request(
    url: str,
    headers: dict[str, str],
    params: dict[str, str],
    account_id: str,
    max_retries: int = 3,
) -> dict[str, Any] | list[Any] | None:
    """Execute an authenticated GET request to the IngramSpark API with retry.

    Retries up to *max_retries* times using exponential backoff (1 s, 2 s, 4 s).
    Returns the parsed JSON response on success, or ``None`` on failure.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                return response.json()

            # Retriable server / rate-limit errors
            if response.status_code in (429, 500, 502, 503, 504):
                logger.warning(
                    "IngramSpark API returned %d on attempt %d/%d: %s",
                    response.status_code,
                    attempt + 1,
                    max_retries,
                    response.text[:500],
                )
                last_exc = httpx.HTTPStatusError(
                    f"IngramSpark API error: {response.status_code}",
                    request=response.request,
                    response=response,
                )
            else:
                # Non-retriable client errors (400, 401, 403, etc.)
                logger.error(
                    "IngramSpark API returned non-retriable status %d for " "account %s: %s",
                    response.status_code,
                    account_id,
                    response.text[:500],
                )
                return None

        except httpx.TimeoutException as exc:
            logger.warning(
                "IngramSpark API request timed out on attempt %d/%d: %s",
                attempt + 1,
                max_retries,
                exc,
            )
            last_exc = exc

        except httpx.RequestError as exc:
            logger.warning(
                "IngramSpark API request failed on attempt %d/%d: %s",
                attempt + 1,
                max_retries,
                exc,
            )
            last_exc = exc

        # Exponential backoff: 1 s, 2 s, 4 s
        if attempt < max_retries - 1:
            backoff = 2**attempt
            logger.debug("Retrying IngramSpark API request in %ds ...", backoff)
            await asyncio.sleep(backoff)

    logger.error(
        "IngramSpark API request failed after %d attempts for account %s. " "Last error: %s",
        max_retries,
        account_id,
        last_exc,
    )
    return None


def _parse_ingramspark_response(
    data: dict[str, Any] | list[Any],
    period_start: datetime,
    period_end: datetime,
    account: Any,
) -> list[dict[str, Any]]:
    """Normalise IngramSpark API response into internal royalty record dicts.

    Expected IngramSpark response structure::

        {
            "reports": [
                {
                    "title": "My Book Title",
                    "isbn": "9781234567890",
                    "isbn13": "9781234567890",
                    "marketplace": "US",
                    "format": "Paperback",
                    "units": 10,
                    "unitsRefunded": 0,
                    "quantitySold": 10,
                    "listPrice": 14.99,
                    "retailPrice": 14.99,
                    "royaltyRate": "0.40",
                    "grossRevenue": 149.90,
                    "grossAmount": 149.90,
                    "royalties": 59.96,
                    "netRevenue": 59.96,
                    "currency": "USD"
                },
                ...
            ]
        }
    """
    records: list[dict[str, Any]] = []

    # The API may return a top-level list or a dict with a reports/compensations key.
    if isinstance(data, list):
        report_items = data
    else:
        report_items = data.get("reports", data.get("compensations", []))

    if not report_items:
        logger.info(
            "IngramSpark API returned no compensation items for account %s.",
            account.id,
        )
        return records

    for entry in report_items:
        try:
            title = entry.get("title") or entry.get("bookTitle", "Unknown")
            units = int(entry.get("units", 0) or entry.get("quantitySold", 0))
            units_refunded = int(entry.get("unitsRefunded", 0))
            royalties = Decimal(str(entry.get("royalties", 0) or entry.get("netRevenue", 0)))
            currency = entry.get("currency", "USD")
            marketplace = entry.get("marketplace", "US")
            isbn = entry.get("isbn") or entry.get("isbn13")

            fmt = (entry.get("format", "paperback") or "paperback").lower()
            if fmt not in ("ebook", "paperback", "hardcover", "audiobook"):
                fmt = "paperback"

            list_price = Decimal(str(entry.get("listPrice", 0) or entry.get("retailPrice", 0)))
            gross = Decimal(str(entry.get("grossRevenue", 0) or entry.get("grossAmount", royalties)))
            royalty_rate = Decimal(str(entry.get("royaltyRate", "0.00")))

            records.append(
                {
                    "platform": "ingram_spark",
                    "marketplace": marketplace,
                    "title": title,
                    "isbn": isbn,
                    "format_type": fmt,
                    "units_sold": max(units, 0),
                    "units_refunded": units_refunded,
                    "net_units": units - units_refunded,
                    "list_price": list_price,
                    "royalty_rate": royalty_rate,
                    "gross_revenue": gross,
                    "net_revenue": royalties,
                    "currency": currency,
                    "period_start": period_start,
                    "period_end": period_end,
                    "raw_data": entry,
                }
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning(
                "Skipping unparseable IngramSpark compensation entry for " "account %s: %s",
                account.id,
                exc,
            )

    logger.info(
        "Parsed %d compensation records from IngramSpark API response " "(%d raw items) for account %s.",
        len(records),
        len(report_items),
        account.id,
    )
    return records


async def _fetch_d2d_royalties(account) -> list[dict[str, Any]]:
    """Fetch royalty/payout data from the Draft2Digital partner API.

    Prefers the new ``D2DClient`` from ``app.modules.analytics.d2d_client``
    when available.  Falls back to the legacy env-var / Bearer-token approach
    if the module is not yet installed or the client factory returns ``None``.

    Requires ``D2D_API_KEY`` env var for the legacy path.

    The function targets the previous full calendar month and returns a list of
    normalised royalty record dicts ready for upsert into ``royalty_records``.
    """

    # ------------------------------------------------------------------
    # Try the new D2DClient first.
    # ------------------------------------------------------------------
    try:
        from app.modules.analytics.d2d_client import get_d2d_client

        client = get_d2d_client()
        if client is not None:
            now = datetime.now(UTC)
            first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = first_of_this_month - timedelta(microseconds=1)
            period_start = (first_of_this_month - timedelta(days=1)).replace(day=1)

            logger.info(
                "Fetching D2D royalties via D2DClient for account %s, " "period %s to %s",
                account.id,
                period_start.strftime("%Y-%m-%d"),
                period_end.strftime("%Y-%m-%d"),
            )
            royalties = await client.fetch_royalties(period_start, period_end)
            logger.info(
                "D2DClient returned %d royalty records for account %s.",
                len(royalties),
                account.id,
            )
            return royalties
        logger.info(
            "D2DClient not configured (get_d2d_client() returned None); "
            "falling back to legacy API path for account %s.",
            account.id,
        )
    except ImportError:
        logger.info(
            "d2d_client module not available; falling back to legacy API path " "for account %s.",
            account.id,
        )
    except Exception as exc:
        logger.error(
            "D2DClient failed for account %s: %s; falling back to legacy API path.",
            account.id,
            exc,
            exc_info=True,
        )

    # ------------------------------------------------------------------
    # Legacy path: direct env-var / Bearer-token authentication.
    # ------------------------------------------------------------------
    api_key = os.environ.get("D2D_API_KEY", "")
    if not api_key:
        logger.warning(
            "D2D API key (D2D_API_KEY) not configured for account %s; " "skipping API sync. Pending API integration.",
            account.id,
        )
        return []

    base_url = os.environ.get(
        "D2D_API_URL",
        "https://api.draft2digital.com/v1",
    )

    # ------------------------------------------------------------------
    # Determine the reporting period (previous full calendar month).
    # ------------------------------------------------------------------
    now = datetime.now(UTC)
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = first_of_this_month - timedelta(microseconds=1)
    period_start = (first_of_this_month - timedelta(days=1)).replace(day=1)

    params: dict[str, str] = {
        "startDate": period_start.strftime("%Y-%m-%d"),
        "endDate": period_end.strftime("%Y-%m-%d"),
    }

    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "SelfPublisherForge/0.1.0",
    }

    logger.info(
        "Fetching D2D payouts for account %s, period %s to %s",
        account.id,
        params["startDate"],
        params["endDate"],
    )

    # ------------------------------------------------------------------
    # Fetch payout report with retries and exponential backoff.
    # ------------------------------------------------------------------
    response_data = await _d2d_api_request(
        url=f"{base_url}/payouts/reports",
        headers=headers,
        params=params,
        account_id=str(account.id),
    )

    if response_data is None:
        return []

    return _parse_d2d_response(response_data, period_start, period_end, account)


async def _d2d_api_request(
    url: str,
    headers: dict[str, str],
    params: dict[str, str],
    account_id: str,
    max_retries: int = 3,
) -> dict[str, Any] | list[Any] | None:
    """Execute an authenticated GET request to the D2D API with retry.

    Retries up to *max_retries* times using exponential backoff (1 s, 2 s, 4 s).
    Returns the parsed JSON response on success, or ``None`` on failure.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                return response.json()

            # Retriable server / rate-limit errors
            if response.status_code in (429, 500, 502, 503, 504):
                logger.warning(
                    "D2D API returned %d on attempt %d/%d: %s",
                    response.status_code,
                    attempt + 1,
                    max_retries,
                    response.text[:500],
                )
                last_exc = httpx.HTTPStatusError(
                    f"D2D API error: {response.status_code}",
                    request=response.request,
                    response=response,
                )
            else:
                # Non-retriable client errors (400, 401, 403, etc.)
                logger.error(
                    "D2D API returned non-retriable status %d for account %s: %s",
                    response.status_code,
                    account_id,
                    response.text[:500],
                )
                return None

        except httpx.TimeoutException as exc:
            logger.warning(
                "D2D API request timed out on attempt %d/%d: %s",
                attempt + 1,
                max_retries,
                exc,
            )
            last_exc = exc

        except httpx.RequestError as exc:
            logger.warning(
                "D2D API request failed on attempt %d/%d: %s",
                attempt + 1,
                max_retries,
                exc,
            )
            last_exc = exc

        # Exponential backoff: 1 s, 2 s, 4 s
        if attempt < max_retries - 1:
            backoff = 2**attempt
            logger.debug("Retrying D2D API request in %ds ...", backoff)
            await asyncio.sleep(backoff)

    logger.error(
        "D2D API request failed after %d attempts for account %s. Last error: %s",
        max_retries,
        account_id,
        last_exc,
    )
    return None


# -- D2D retailer slug to marketplace code mapping --
_D2D_RETAILER_MAP: dict[str, str] = {
    "amazon": "US",
    "amazon_uk": "UK",
    "amazon_de": "DE",
    "amazon_fr": "FR",
    "amazon_au": "AU",
    "amazon_ca": "CA",
    "apple": "US",
    "apple_books": "US",
    "barnes_and_noble": "US",
    "nook": "US",
    "kobo": "US",
    "tolino": "DE",
    "scribd": "US",
    "overdrive": "US",
    "libraries": "US",
    "hoopla": "US",
    "vivlio": "FR",
    "palace_marketplace": "US",
}


def _parse_d2d_response(
    data: dict[str, Any] | list[Any],
    period_start: datetime,
    period_end: datetime,
    account: Any,
) -> list[dict[str, Any]]:
    """Normalise Draft2Digital API response into internal royalty record dicts.

    Expected D2D response structure::

        {
            "payouts": [
                {
                    "title": "My Book Title",
                    "isbn": "9781234567890",
                    "retailer": "amazon",
                    "marketplace": "US",
                    "format": "ebook",
                    "unitsSold": 25,
                    "unitsRefunded": 0,
                    "listPrice": 4.99,
                    "royaltyAmount": 17.47,
                    "grossAmount": 24.95,
                    "currency": "USD"
                },
                ...
            ]
        }
    """
    records: list[dict[str, Any]] = []

    # The API may return a top-level list or a dict with a payouts/reports key.
    if isinstance(data, list):
        payout_items = data
    else:
        payout_items = data.get("payouts", data.get("reports", data.get("sales", [])))

    if not payout_items:
        logger.info("D2D API returned no payout items for account %s.", account.id)
        return records

    for entry in payout_items:
        try:
            title = entry.get("title") or entry.get("bookTitle", "Unknown")
            units = int(entry.get("unitsSold", 0) or entry.get("units", 0))
            units_refunded = int(entry.get("unitsRefunded", 0))
            royalties = Decimal(
                str(entry.get("royaltyAmount", 0) or entry.get("royalties", 0) or entry.get("netRevenue", 0))
            )
            currency = entry.get("currency", "USD")

            # Marketplace: prefer explicit field, fall back to retailer mapping.
            marketplace = entry.get("marketplace", "")
            if not marketplace:
                retailer = (entry.get("retailer", "") or "").lower()
                marketplace = _D2D_RETAILER_MAP.get(retailer, "US")

            isbn = entry.get("isbn") or entry.get("isbn13")

            fmt = (entry.get("format", "ebook") or "ebook").lower()
            if fmt not in ("ebook", "paperback", "hardcover", "audiobook"):
                fmt = "ebook"

            list_price = Decimal(str(entry.get("listPrice", 0) or entry.get("retailPrice", 0)))
            gross = Decimal(str(entry.get("grossAmount", 0) or entry.get("grossRevenue", royalties)))
            royalty_rate = Decimal(str(entry.get("royaltyRate", "0.00")))

            records.append(
                {
                    "platform": "draft2digital",
                    "marketplace": marketplace,
                    "title": title,
                    "isbn": isbn,
                    "format_type": fmt,
                    "units_sold": max(units, 0),
                    "units_refunded": units_refunded,
                    "net_units": units - units_refunded,
                    "list_price": list_price,
                    "royalty_rate": royalty_rate,
                    "gross_revenue": gross,
                    "net_revenue": royalties,
                    "currency": currency,
                    "period_start": period_start,
                    "period_end": period_end,
                    "raw_data": entry,
                }
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning(
                "Skipping unparseable D2D payout entry for account %s: %s",
                account.id,
                exc,
            )

    logger.info(
        "Parsed %d payout records from D2D API response (%d raw items) " "for account %s.",
        len(records),
        len(payout_items),
        account.id,
    )
    return records


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
