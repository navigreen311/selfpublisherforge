"""Celery tasks for Pricing Automation.

Periodic tasks:
  - check_competitor_prices: Periodically fetch and update competitor pricing data.
  - evaluate_auto_pricing_rules: Check active auto-apply rules and trigger price adjustments.
  - activate_scheduled_promotions: Activate promotions whose start_date has passed.
  - complete_expired_promotions: Mark promotions as completed when end_date has passed.

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
import statistics
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Bridge helper: run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="pricing.check_competitor_prices",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    soft_time_limit=300,
    time_limit=600,
)
def check_competitor_prices(self, org_id: str, book_id: str) -> dict:
    """Fetch latest competitor pricing data for a book.

    Queries all competitor price records for the given book, computes
    summary statistics (average, median, min, max), and compares them
    against any active pricing rules to detect significant price changes.

    Args:
        org_id: Organization UUID string.
        book_id: Book UUID string.

    Returns:
        Dict with task results including number of competitors found and
        price comparison data.
    """
    logger.info("Checking competitor prices for book=%s org=%s", book_id, org_id)

    async def _run():
        from app.database import async_session
        from app.modules.pricing_automation.models import (
            CompetitorPrice,
            PricingRule,
            RuleStatus,
        )

        async with async_session() as db:
            try:
                org_uuid = UUID(org_id)
                book_uuid = UUID(book_id)

                # 1. Fetch all competitor price records for this book
                stmt = (
                    select(CompetitorPrice)
                    .where(CompetitorPrice.org_id == org_uuid)
                    .where(CompetitorPrice.book_id == book_uuid)
                    .where(CompetitorPrice.deleted_at.is_(None))
                    .order_by(CompetitorPrice.snapshot_date.desc())
                )
                result = await db.execute(stmt)
                competitors = list(result.scalars().all())

                competitors_checked = len(competitors)
                price_changes_detected = []

                if not competitors:
                    logger.info(
                        "No competitor records found for book=%s org=%s",
                        book_id,
                        org_id,
                    )
                    return {
                        "org_id": org_id,
                        "book_id": book_id,
                        "competitors_checked": 0,
                        "competitors_updated": 0,
                        "price_summary": None,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "status": "completed",
                    }

                # 2. Compute summary statistics from competitor prices
                prices = [c.price for c in competitors]
                avg_price = round(statistics.mean(prices), 2)
                median_price = round(statistics.median(prices), 2)
                min_price = round(min(prices), 2)
                max_price = round(max(prices), 2)

                bsr_values = [c.bsr_rank for c in competitors if c.bsr_rank is not None]
                avg_bsr = round(statistics.mean(bsr_values)) if bsr_values else None

                price_summary = {
                    "avg_price": avg_price,
                    "median_price": median_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "avg_bsr": avg_bsr,
                    "total_competitors": competitors_checked,
                }

                # 3. Compare against active pricing rules for this book
                rules_stmt = (
                    select(PricingRule)
                    .where(PricingRule.org_id == org_uuid)
                    .where(PricingRule.book_id == book_uuid)
                    .where(PricingRule.status == RuleStatus.ACTIVE)
                    .where(PricingRule.deleted_at.is_(None))
                )
                rules_result = await db.execute(rules_stmt)
                active_rules = list(rules_result.scalars().all())

                for rule in active_rules:
                    # Detect if competitor average has moved outside rule bounds
                    if avg_price < rule.min_price:
                        price_changes_detected.append(
                            {
                                "rule_id": str(rule.id),
                                "rule_name": rule.name,
                                "alert": "competitor_avg_below_min",
                                "competitor_avg": avg_price,
                                "rule_min_price": rule.min_price,
                            }
                        )
                        logger.warning(
                            "Competitor avg price $%.2f below rule min $%.2f " "for rule=%s book=%s",
                            avg_price,
                            rule.min_price,
                            str(rule.id),
                            book_id,
                        )
                    if avg_price > rule.max_price:
                        price_changes_detected.append(
                            {
                                "rule_id": str(rule.id),
                                "rule_name": rule.name,
                                "alert": "competitor_avg_above_max",
                                "competitor_avg": avg_price,
                                "rule_max_price": rule.max_price,
                            }
                        )
                        logger.warning(
                            "Competitor avg price $%.2f above rule max $%.2f " "for rule=%s book=%s",
                            avg_price,
                            rule.max_price,
                            str(rule.id),
                            book_id,
                        )

                    # If the rule has a target price, flag significant deviation
                    if rule.target_price is not None and avg_price > 0:
                        deviation_pct = abs(avg_price - rule.target_price) / avg_price
                        if deviation_pct > 0.10:
                            price_changes_detected.append(
                                {
                                    "rule_id": str(rule.id),
                                    "rule_name": rule.name,
                                    "alert": "significant_price_deviation",
                                    "competitor_avg": avg_price,
                                    "target_price": rule.target_price,
                                    "deviation_pct": round(deviation_pct * 100, 1),
                                }
                            )

                await db.commit()

                return {
                    "org_id": org_id,
                    "book_id": book_id,
                    "competitors_checked": competitors_checked,
                    "competitors_updated": len(price_changes_detected),
                    "price_summary": price_summary,
                    "price_changes": price_changes_detected,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "status": "completed",
                }
            except ValueError as exc:
                await db.rollback()
                logger.error(
                    "Invalid UUID or data for book=%s org=%s: %s",
                    book_id,
                    org_id,
                    exc,
                    exc_info=True,
                )
                raise
            except SQLAlchemyError as exc:
                await db.rollback()
                logger.error(
                    "Database error during competitor price check for book=%s org=%s: %s",
                    book_id,
                    org_id,
                    exc,
                    exc_info=True,
                )
                raise
            except statistics.StatisticsError as exc:
                await db.rollback()
                logger.error(
                    "Statistics computation failed for book=%s org=%s: %s",
                    book_id,
                    org_id,
                    exc,
                    exc_info=True,
                )
                raise

    try:
        result = _run_async(_run())
        logger.info(
            "Competitor price check completed for book=%s: checked=%d changes=%d",
            book_id,
            result["competitors_checked"],
            result["competitors_updated"],
        )
        return cast("dict[Any, Any]", result)

    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error(
            "Competitor price check failed for book=%s org=%s: %s",
            book_id,
            org_id,
            str(exc),
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="pricing.evaluate_auto_pricing_rules",
    bind=True,
    max_retries=2,
    default_retry_delay=600,
    soft_time_limit=300,
    time_limit=600,
)
def evaluate_auto_pricing_rules(self, org_id: str) -> dict:
    """Evaluate and apply all active auto-pricing rules for an organization.

    Fetches all active rules with is_auto_apply=True, gathers competitor
    data for each rule's book, runs the appropriate pricing strategy, and
    records the recommended price if it differs from the current target.

    Args:
        org_id: Organization UUID string.

    Returns:
        Dict with evaluation results including rules evaluated and price changes.
    """
    logger.info("Evaluating auto-pricing rules for org=%s", org_id)

    async def _run():
        from app.database import async_session
        from app.modules.pricing_automation.models import (
            CompetitorPrice,
            PricingRule,
            RuleStatus,
        )
        from app.modules.pricing_automation.strategies import (
            StrategyContext,
            calculate_price,
        )

        async with async_session() as db:
            try:
                org_uuid = UUID(org_id)
                now = datetime.now(UTC)

                # 1. Fetch all active auto-apply rules for this org
                stmt = (
                    select(PricingRule)
                    .where(PricingRule.org_id == org_uuid)
                    .where(PricingRule.status == RuleStatus.ACTIVE)
                    .where(PricingRule.is_auto_apply.is_(True))
                    .where(PricingRule.deleted_at.is_(None))
                )
                result = await db.execute(stmt)
                rules = list(result.scalars().all())

                rules_evaluated = 0
                rules_triggered = 0
                price_changes = []

                for rule in rules:
                    rules_evaluated += 1

                    # 2. Gather competitor context for this rule's book
                    competitor_avg = None
                    competitor_median = None
                    competitor_min = None
                    competitor_max = None

                    if rule.book_id is not None:
                        comp_stmt = (
                            select(CompetitorPrice)
                            .where(CompetitorPrice.org_id == org_uuid)
                            .where(CompetitorPrice.book_id == rule.book_id)
                            .where(CompetitorPrice.deleted_at.is_(None))
                            .order_by(CompetitorPrice.snapshot_date.desc())
                            .limit(50)
                        )
                        comp_result = await db.execute(comp_stmt)
                        comp_records = list(comp_result.scalars().all())

                        if comp_records:
                            comp_prices = [c.price for c in comp_records]
                            competitor_avg = round(statistics.mean(comp_prices), 2)
                            competitor_median = round(statistics.median(comp_prices), 2)
                            competitor_min = round(min(comp_prices), 2)
                            competitor_max = round(max(comp_prices), 2)

                    # 3. Build strategy context
                    current_price = rule.target_price or rule.min_price
                    context = StrategyContext(
                        current_price=current_price,
                        min_price=rule.min_price,
                        max_price=rule.max_price,
                        book_format=rule.book_format.value,
                        competitor_avg_price=competitor_avg,
                        competitor_median_price=competitor_median,
                        competitor_min_price=competitor_min,
                        competitor_max_price=competitor_max,
                        parameters=rule.parameters or {},
                    )

                    # 4. Run the pricing strategy
                    try:
                        strategy_result = calculate_price(rule.strategy.value, context)
                    except (ValueError, KeyError, TypeError, ZeroDivisionError) as e:
                        logger.error(
                            "Strategy calculation failed for rule=%s strategy=%s org=%s: %s",
                            str(rule.id),
                            rule.strategy.value,
                            org_id,
                            e,
                            exc_info=True,
                        )
                        continue

                    # 5. Check if price changed and update the rule
                    recommended = strategy_result.recommended_price
                    if abs(recommended - current_price) >= 0.01:
                        rules_triggered += 1
                        rule.target_price = recommended
                        rule.last_applied_at = now

                        change_record = {
                            "rule_id": str(rule.id),
                            "rule_name": rule.name,
                            "book_id": str(rule.book_id) if rule.book_id else None,
                            "strategy": rule.strategy.value,
                            "previous_price": current_price,
                            "recommended_price": recommended,
                            "confidence": strategy_result.confidence,
                            "reasoning": strategy_result.reasoning,
                        }
                        price_changes.append(change_record)
                        logger.info(
                            "Price change triggered: rule=%s book=%s " "$%.2f -> $%.2f (confidence=%.2f)",
                            str(rule.id),
                            str(rule.book_id) if rule.book_id else "N/A",
                            current_price,
                            recommended,
                            strategy_result.confidence,
                        )
                    else:
                        # Update last_applied_at even if price didn't change
                        rule.last_applied_at = now

                await db.commit()

                return {
                    "org_id": org_id,
                    "rules_evaluated": rules_evaluated,
                    "rules_triggered": rules_triggered,
                    "price_changes": price_changes,
                    "timestamp": now.isoformat(),
                    "status": "completed",
                }
            except ValueError as exc:
                await db.rollback()
                logger.error(
                    "Invalid UUID or data during auto-pricing evaluation for org=%s: %s",
                    org_id,
                    exc,
                    exc_info=True,
                )
                raise
            except SQLAlchemyError as exc:
                await db.rollback()
                logger.error(
                    "Database error during auto-pricing evaluation for org=%s: %s",
                    org_id,
                    exc,
                    exc_info=True,
                )
                raise
            except (KeyError, AttributeError) as exc:
                await db.rollback()
                logger.error(
                    "Missing data during auto-pricing evaluation for org=%s: %s",
                    org_id,
                    exc,
                    exc_info=True,
                )
                raise

    try:
        result = _run_async(_run())
        logger.info(
            "Auto-pricing evaluation completed for org=%s: %d rules evaluated, " "%d triggered",
            org_id,
            result["rules_evaluated"],
            result["rules_triggered"],
        )
        return cast("dict[Any, Any]", result)

    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error(
            "Auto-pricing evaluation failed for org=%s: %s",
            org_id,
            str(exc),
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="pricing.activate_scheduled_promotions",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    soft_time_limit=60,
    time_limit=120,
)
def activate_scheduled_promotions(self) -> dict:
    """Activate promotions whose start_date has passed.

    Runs periodically (e.g., every 15 minutes) to find promotions with
    status=SCHEDULED and start_date <= now, then updates their status
    to ACTIVE.

    Returns:
        Dict with activation results including list of activated promotion IDs.
    """
    logger.info("Checking for promotions to activate")

    async def _run():
        from app.database import async_session
        from app.modules.pricing_automation.models import (
            Promotion,
            PromotionStatus,
        )

        async with async_session() as db:
            try:
                now = datetime.now(UTC)

                # Query promotions that are scheduled and ready to start
                stmt = (
                    select(Promotion)
                    .where(Promotion.status == PromotionStatus.SCHEDULED)
                    .where(Promotion.start_date <= now)
                    .where(Promotion.deleted_at.is_(None))
                )
                result = await db.execute(stmt)
                promotions = list(result.scalars().all())

                activated_ids = []

                for promo in promotions:
                    promo.status = PromotionStatus.ACTIVE
                    activated_ids.append(str(promo.id))
                    logger.info(
                        "Activated promotion: id=%s name='%s' book=%s " "promo_price=$%.2f (original=$%.2f)",
                        str(promo.id),
                        promo.name,
                        str(promo.book_id),
                        promo.promo_price,
                        promo.original_price,
                    )

                await db.commit()

                return {
                    "promotions_activated": len(activated_ids),
                    "activated_ids": activated_ids,
                    "timestamp": now.isoformat(),
                    "status": "completed",
                }
            except SQLAlchemyError as exc:
                await db.rollback()
                logger.error(
                    "Database error during promotion activation: %s",
                    exc,
                    exc_info=True,
                )
                raise
            except (AttributeError, TypeError) as exc:
                await db.rollback()
                logger.error(
                    "Data error during promotion activation: %s",
                    exc,
                    exc_info=True,
                )
                raise

    try:
        result = _run_async(_run())
        logger.info(
            "Promotion activation check completed: %d activated",
            result["promotions_activated"],
        )
        return cast("dict[Any, Any]", result)

    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error(
            "Promotion activation failed: %s",
            str(exc),
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="pricing.complete_expired_promotions",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    soft_time_limit=60,
    time_limit=120,
)
def complete_expired_promotions(self) -> dict:
    """Mark active promotions as completed when their end_date has passed.

    Runs periodically to find promotions with status=ACTIVE and
    end_date <= now, updates their status to COMPLETED, and records
    the original price for restoration.

    Returns:
        Dict with completion results including list of completed promotion IDs
        and their original prices.
    """
    logger.info("Checking for expired promotions")

    async def _run():
        from app.database import async_session
        from app.modules.pricing_automation.models import (
            Promotion,
            PromotionStatus,
        )

        async with async_session() as db:
            try:
                now = datetime.now(UTC)

                # Query active promotions whose end_date has passed
                stmt = (
                    select(Promotion)
                    .where(Promotion.status == PromotionStatus.ACTIVE)
                    .where(Promotion.end_date <= now)
                    .where(Promotion.deleted_at.is_(None))
                )
                result = await db.execute(stmt)
                promotions = list(result.scalars().all())

                completed_ids = []
                restored_prices = []

                for promo in promotions:
                    promo.status = PromotionStatus.COMPLETED
                    completed_ids.append(str(promo.id))
                    restored_prices.append(
                        {
                            "promotion_id": str(promo.id),
                            "book_id": str(promo.book_id),
                            "promo_price": promo.promo_price,
                            "original_price": promo.original_price,
                            "platform": promo.platform,
                        }
                    )
                    logger.info(
                        "Completed expired promotion: id=%s name='%s' book=%s " "restoring price $%.2f -> $%.2f",
                        str(promo.id),
                        promo.name,
                        str(promo.book_id),
                        promo.promo_price,
                        promo.original_price,
                    )

                await db.commit()

                return {
                    "promotions_completed": len(completed_ids),
                    "completed_ids": completed_ids,
                    "restored_prices": restored_prices,
                    "timestamp": now.isoformat(),
                    "status": "completed",
                }
            except SQLAlchemyError as exc:
                await db.rollback()
                logger.error(
                    "Database error during promotion expiration check: %s",
                    exc,
                    exc_info=True,
                )
                raise
            except (AttributeError, TypeError) as exc:
                await db.rollback()
                logger.error(
                    "Data error during promotion expiration check: %s",
                    exc,
                    exc_info=True,
                )
                raise

    try:
        result = _run_async(_run())
        logger.info(
            "Promotion expiration check completed: %d completed",
            result["promotions_completed"],
        )
        return cast("dict[Any, Any]", result)

    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error(
            "Promotion expiration check failed: %s",
            str(exc),
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


# ──────────────────── Celery Beat Schedule ────────────────────

# To be added to the celery beat schedule in the main celery config:
PRICING_BEAT_SCHEDULE = {
    "activate-scheduled-promotions": {
        "task": "pricing.activate_scheduled_promotions",
        "schedule": 900.0,  # Every 15 minutes
    },
    "complete-expired-promotions": {
        "task": "pricing.complete_expired_promotions",
        "schedule": 900.0,  # Every 15 minutes
    },
}
