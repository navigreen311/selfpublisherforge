# W03: Market Intelligence — DB Persistence for Competitors + Snapshots

## Files to modify
- `backend/app/modules/market_intelligence/service.py` — Replace in-memory + synthetic data

## Context
Existing DB models in `app/models/market.py`:
- `CompetitorBook` — asin, title, author, bsr_current, bsr_history (JSONB), price, reviews_count, rating, cover_url, org_id, category, metadata_json
- `MarketSnapshot` — category_id (FK to market_categories), snapshot_date, top_100_asins, metrics (JSONB)
- `MarketCategory` — amazon_node_id, name, path, parent_id, book_count, avg_bsr, competition_score

## Task

### 1. Rewrite competitor methods to use DB

The class has `_tracked: dict[str, CompetitorDetail] = {}` class-level dict. Replace with DB queries.

Add `db: AsyncSession` parameter to the constructor or to each method. Since the router creates the service via `_service()`, update the router to pass db.

- `list_competitors(db, org_id, marketplace)` → `select(CompetitorBook).where(org_id==, deleted_at==None)`
- `track_competitor(db, org_id, request)` → Check if CompetitorBook with asin exists. If not, fetch from amazon client, create CompetitorBook, db.add(), flush, refresh
- `get_competitor(db, competitor_id)` → select by id

### 2. Replace synthetic snapshots with DB queries

`get_snapshots()` currently generates random data. Replace with:
```python
async def get_snapshots(self, db: AsyncSession, category_id=None, limit=30):
    query = select(MarketSnapshot).order_by(MarketSnapshot.snapshot_date.desc()).limit(limit)
    if category_id:
        # Find MarketCategory by amazon_node_id, then filter snapshots
        cat = await db.execute(select(MarketCategory).where(MarketCategory.amazon_node_id == category_id))
        cat_obj = cat.scalar_one_or_none()
        if cat_obj:
            query = query.where(MarketSnapshot.category_id == cat_obj.id)
    result = await db.execute(query)
    rows = result.scalars().all()
    # Convert to schema MarketSnapshot objects
    return [self._map_db_snapshot(r) for r in rows]
```

If no snapshots exist yet, return an empty list (don't generate fake data).

### 3. Update router.py

Add `db: AsyncSession = Depends(get_db)` to every endpoint. Pass it to the service. Update `_service()` to accept db or just pass db to each method call.

```python
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/competitors", response_model=list[CompetitorListItem])
async def list_competitors(
    marketplace: str = Query("US"),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketIntelligenceService()
    return await svc.list_competitors(db=db, marketplace=marketplace)
```

### 4. Keep amazon_client calls as-is

The categories, keywords, niche analysis endpoints that use `self._client` (the Amazon API client) should stay unchanged — they don't need DB persistence since they fetch real-time data.
