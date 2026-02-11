"""Seed demo market intelligence data."""
import random
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import CompetitorBook, MarketKeyword

# Sample competitor books for Fantasy genre
FANTASY_COMPETITORS = [
    {
        "title": "The Last Dragonrider",
        "author": "Sarah Mitchell",
        "price": 5.99,
        "rating": 4.5,
        "reviews": 3421,
        "bsr": 1234,
    },
    {
        "title": "Shadows of the Realm",
        "author": "Marcus Chen",
        "price": 4.99,
        "rating": 4.3,
        "reviews": 2156,
        "bsr": 2341,
    },
    {
        "title": "The Crystal Throne",
        "author": "Emily Roberts",
        "price": 6.99,
        "rating": 4.7,
        "reviews": 5234,
        "bsr": 567,
    },
    {
        "title": "Wrath of the Phoenix",
        "author": "David Kim",
        "price": 4.99,
        "rating": 4.2,
        "reviews": 1876,
        "bsr": 3456,
    },
    {
        "title": "The Forgotten Kingdom",
        "author": "Lisa Anderson",
        "price": 5.49,
        "rating": 4.6,
        "reviews": 4123,
        "bsr": 891,
    },
    {
        "title": "Sword of Destiny",
        "author": "James Wilson",
        "price": 3.99,
        "rating": 4.1,
        "reviews": 987,
        "bsr": 5678,
    },
    {
        "title": "The Dark Prophecy",
        "author": "Michelle Torres",
        "price": 5.99,
        "rating": 4.4,
        "reviews": 2987,
        "bsr": 1567,
    },
    {
        "title": "Chronicles of Fire",
        "author": "Robert Lee",
        "price": 4.49,
        "rating": 4.0,
        "reviews": 756,
        "bsr": 7891,
    },
    {
        "title": "The Enchanted Blade",
        "author": "Jennifer Harris",
        "price": 6.49,
        "rating": 4.8,
        "reviews": 6789,
        "bsr": 234,
    },
    {
        "title": "Secrets of the Mage",
        "author": "Thomas Green",
        "price": 5.99,
        "rating": 4.3,
        "reviews": 2345,
        "bsr": 2134,
    },
]

# Sample keywords for Fantasy genre
FANTASY_KEYWORDS = [
    {"keyword": "epic fantasy", "volume": 45000, "competition": 0.75, "cpc": 0.45},
    {"keyword": "dragon books", "volume": 33000, "competition": 0.68, "cpc": 0.38},
    {
        "keyword": "fantasy adventure",
        "volume": 28000,
        "competition": 0.72,
        "cpc": 0.42,
    },
    {"keyword": "magic prophecy", "volume": 12000, "competition": 0.54, "cpc": 0.29},
    {"keyword": "quest fantasy", "volume": 18000, "competition": 0.61, "cpc": 0.35},
    {
        "keyword": "sword and sorcery",
        "volume": 15000,
        "competition": 0.58,
        "cpc": 0.32,
    },
    {"keyword": "dark fantasy", "volume": 22000, "competition": 0.65, "cpc": 0.40},
    {
        "keyword": "high fantasy books",
        "volume": 19000,
        "competition": 0.70,
        "cpc": 0.44,
    },
    {
        "keyword": "dragon rider series",
        "volume": 9500,
        "competition": 0.52,
        "cpc": 0.27,
    },
    {
        "keyword": "fantasy kingdom",
        "volume": 11000,
        "competition": 0.56,
        "cpc": 0.30,
    },
]


async def seed_market(db: AsyncSession, org_id: uuid.UUID) -> None:
    """Seed demo market intelligence data.

    Args:
        db: Database session
        org_id: Organization ID
    """
    # Check if data already exists
    existing = await db.execute(
        select(CompetitorBook).where(CompetitorBook.org_id == org_id).limit(1)
    )
    if existing.scalar_one_or_none():
        print("✓ Market data already exists, skipping")
        return

    total_books = 0
    total_keywords = 0

    # Seed competitor books
    for idx, book_data in enumerate(FANTASY_COMPETITORS, start=1):
        asin = f"B0{idx:02d}XYZ{random.randint(1000, 9999)}"

        # Generate BSR history (last 30 days)
        bsr_history = {}
        current_bsr = book_data["bsr"]
        for day in range(30):
            date_key = (
                datetime.now(UTC) - timedelta(days=30 - day)
            ).strftime("%Y-%m-%d")
            # BSR fluctuates
            fluctuation = random.randint(-500, 500)
            bsr_history[date_key] = max(100, current_bsr + fluctuation)
            current_bsr = bsr_history[date_key]

        competitor = CompetitorBook(
            org_id=org_id,
            asin=asin,
            title=book_data["title"],
            author=book_data["author"],
            bsr_current=book_data["bsr"],
            bsr_history=bsr_history,
            price=Decimal(str(book_data["price"])),
            reviews_count=book_data["reviews"],
            rating=book_data["rating"],
            category="Fantasy",
            category_ids=["17220", "17300"],
            publication_date=datetime.now(UTC) - timedelta(days=random.randint(180, 730)),
            description=f"An epic {book_data['title'].lower()} story...",
            keywords=["fantasy", "adventure", "magic"],
            page_count=random.randint(250, 450),
            formats=["ebook", "paperback"],
            series_info={
                "is_series": random.choice([True, False]),
                "book_number": random.randint(1, 3) if random.choice([True, False]) else None,
            },
            metadata_json={
                "scraped_at": datetime.now(UTC).isoformat(),
                "source": "amazon",
            },
        )
        db.add(competitor)
        total_books += 1

    # Seed market keywords
    for kw_data in FANTASY_KEYWORDS:
        # Check if keyword exists
        existing_kw = await db.execute(
            select(MarketKeyword).where(
                MarketKeyword.org_id == org_id,
                MarketKeyword.keyword == kw_data["keyword"],
            )
        )
        if existing_kw.scalar_one_or_none():
            continue

        keyword = MarketKeyword(
            org_id=org_id,
            keyword=kw_data["keyword"],
            search_volume=kw_data["volume"],
            competition_score=kw_data["competition"],
            cpc_estimate=Decimal(str(kw_data["cpc"])),
            trend_direction="stable",
            last_updated=datetime.now(UTC),
        )
        db.add(keyword)
        total_keywords += 1

    await db.commit()

    print(f"✓ Seeded {total_books} competitor books and {total_keywords} keywords")
