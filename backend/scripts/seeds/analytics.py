"""Seed demo analytics, revenue, and royalty data."""

import random
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import PortfolioMetricSnapshot, RoyaltyRecord


async def seed_analytics(db: AsyncSession, org_id: uuid.UUID, book_ids: dict[str, uuid.UUID]) -> None:
    """Seed 12 months of revenue and royalty data.

    Args:
        db: Database session
        org_id: Organization ID
        book_ids: Dict mapping book titles to book IDs
    """
    # Only seed for published books
    published_book = book_ids.get("The Dragon's Prophecy")
    if not published_book:
        print("⚠ No published book found, skipping analytics")
        return

    # Check if data already exists
    existing = await db.execute(
        select(RoyaltyRecord).where(RoyaltyRecord.org_id == org_id, RoyaltyRecord.book_id == published_book).limit(1)
    )
    if existing.scalar_one_or_none():
        print("✓ Analytics data already exists, skipping")
        return

    # Generate 12 months of royalty data
    platforms = ["KDP", "IngramSpark", "Draft2Digital"]
    marketplaces = ["US", "UK", "CA", "AU", "DE"]

    total_records = 0
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=365)

    # Generate monthly records for each platform/marketplace combo
    current_date = start_date
    while current_date < end_date:
        period_start = current_date
        period_end = current_date + timedelta(days=30)

        for platform in platforms:
            for marketplace in marketplaces:
                # Simulate realistic sales patterns
                base_units = random.randint(20, 100)
                # Add some seasonal variation
                month = current_date.month
                seasonal_multiplier = 1.5 if month in [11, 12] else 0.8 if month in [6, 7, 8] else 1.0
                units_sold = int(base_units * seasonal_multiplier)
                units_refunded = random.randint(0, int(units_sold * 0.05))
                net_units = units_sold - units_refunded

                # Pricing varies by marketplace
                if marketplace in ["US", "CA"]:
                    list_price = Decimal("4.99")
                elif marketplace == "UK":
                    list_price = Decimal("3.99")
                elif marketplace == "AU":
                    list_price = Decimal("6.99")
                else:  # DE
                    list_price = Decimal("4.49")

                # Royalty rates
                royalty_rate = Decimal("0.70") if platform == "KDP" else Decimal("0.60")

                gross_revenue = list_price * net_units
                net_revenue = gross_revenue * royalty_rate

                royalty = RoyaltyRecord(
                    org_id=org_id,
                    book_id=published_book,
                    platform=platform,
                    marketplace=marketplace,
                    title="The Dragon's Prophecy",
                    asin="B08ABCD123" if platform == "KDP" else None,
                    isbn="978-1234567890" if platform != "KDP" else None,
                    format_type="ebook",
                    units_sold=units_sold,
                    units_refunded=units_refunded,
                    net_units=net_units,
                    list_price=list_price,
                    royalty_rate=royalty_rate,
                    gross_revenue=gross_revenue,
                    net_revenue=net_revenue,
                    currency="USD",
                    period_start=period_start,
                    period_end=period_end,
                    raw_data={
                        "platform": platform,
                        "marketplace": marketplace,
                        "import_date": datetime.now(UTC).isoformat(),
                    },
                )
                db.add(royalty)
                total_records += 1

        current_date = period_end

    # Generate portfolio metric snapshots (monthly)
    current_date = start_date
    while current_date < end_date:
        # Check if snapshot exists
        existing_snapshot = await db.execute(
            select(PortfolioMetricSnapshot).where(
                PortfolioMetricSnapshot.org_id == org_id,
                PortfolioMetricSnapshot.snapshot_date >= current_date,
                PortfolioMetricSnapshot.snapshot_date < current_date + timedelta(days=30),
            )
        )
        if existing_snapshot.scalar_one_or_none():
            current_date += timedelta(days=30)
            continue

        # Calculate metrics for this period
        month_total_revenue = Decimal(random.randint(1500, 4500))
        month_total_units = random.randint(300, 800)

        snapshot = PortfolioMetricSnapshot(
            org_id=org_id,
            snapshot_date=current_date,
            total_books=1,
            total_revenue=month_total_revenue,
            total_units_sold=month_total_units,
            total_expenses=Decimal("250.00"),  # Cover design, marketing, etc.
            net_profit=month_total_revenue - Decimal("250.00"),
            avg_roi=Decimal("12.5"),
            platform_breakdown={
                "KDP": float(month_total_revenue * Decimal("0.60")),
                "IngramSpark": float(month_total_revenue * Decimal("0.25")),
                "Draft2Digital": float(month_total_revenue * Decimal("0.15")),
            },
            format_breakdown={
                "ebook": float(month_total_revenue),
            },
            top_books=[
                {
                    "title": "The Dragon's Prophecy",
                    "revenue": float(month_total_revenue),
                    "units": month_total_units,
                }
            ],
            metrics_data={
                "avg_price": 4.99,
                "conversion_rate": 0.025,
            },
        )
        db.add(snapshot)

        current_date += timedelta(days=30)

    await db.commit()

    print(f"✓ Seeded {total_records} royalty records and portfolio snapshots")
