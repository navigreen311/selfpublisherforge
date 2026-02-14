"""Search terms management service for Advertising Intelligence."""

from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.advertising.models import AdSearchTerm, KeywordBid


async def get_search_terms(db: AsyncSession, campaign_id, limit: int = 50) -> list:
    """Get search terms for a campaign, ordered by impressions descending."""
    result = await db.execute(
        select(AdSearchTerm)
        .where(
            and_(
                AdSearchTerm.campaign_id == campaign_id,
                AdSearchTerm.deleted_at.is_(None),
            )
        )
        .order_by(AdSearchTerm.impressions.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def add_search_term_as_keyword(db: AsyncSession, campaign_id, search_term_id) -> dict:
    """Promote a search term to a keyword bid for the campaign.

    Creates a new KeywordBid entry with the search term text and marks
    the search term's action_taken as 'added_as_keyword'.
    """
    # Get the search term
    result = await db.execute(
        select(AdSearchTerm).where(
            and_(
                AdSearchTerm.id == search_term_id,
                AdSearchTerm.campaign_id == campaign_id,
                AdSearchTerm.deleted_at.is_(None),
            )
        )
    )
    search_term = result.scalar_one_or_none()
    if not search_term:
        return {"success": False, "message": "Search term not found"}

    # Check if keyword already exists
    existing = await db.execute(
        select(KeywordBid).where(
            and_(
                KeywordBid.campaign_id == campaign_id,
                KeywordBid.keyword == search_term.search_term,
                KeywordBid.is_negative.is_(False),
            )
        )
    )
    if existing.scalar_one_or_none():
        return {"success": False, "message": "Keyword already exists for this campaign"}

    # Create keyword bid from search term
    keyword_bid = KeywordBid(
        campaign_id=campaign_id,
        keyword=search_term.search_term,
        match_type="exact",
        bid_amount=0.75,  # Default bid
        is_negative=False,
        is_active=True,
    )
    db.add(keyword_bid)

    # Mark search term action
    search_term.action_taken = "added_as_keyword"
    await db.flush()

    return {
        "success": True,
        "message": f"Search term '{search_term.search_term}' added as keyword",
        "keyword_bid_id": str(keyword_bid.id),
    }


async def negate_search_term(db: AsyncSession, campaign_id, search_term_id) -> dict:
    """Negate a search term by adding it as a negative keyword.

    Creates a new negative KeywordBid entry and marks the search term's
    action_taken as 'negated'.
    """
    # Get the search term
    result = await db.execute(
        select(AdSearchTerm).where(
            and_(
                AdSearchTerm.id == search_term_id,
                AdSearchTerm.campaign_id == campaign_id,
                AdSearchTerm.deleted_at.is_(None),
            )
        )
    )
    search_term = result.scalar_one_or_none()
    if not search_term:
        return {"success": False, "message": "Search term not found"}

    # Check if negative keyword already exists
    existing = await db.execute(
        select(KeywordBid).where(
            and_(
                KeywordBid.campaign_id == campaign_id,
                KeywordBid.keyword == search_term.search_term,
                KeywordBid.is_negative.is_(True),
            )
        )
    )
    if existing.scalar_one_or_none():
        return {"success": False, "message": "Negative keyword already exists for this campaign"}

    # Create negative keyword bid
    keyword_bid = KeywordBid(
        campaign_id=campaign_id,
        keyword=search_term.search_term,
        match_type="exact",
        bid_amount=0.0,
        is_negative=True,
        is_active=True,
    )
    db.add(keyword_bid)

    # Mark search term action
    search_term.action_taken = "negated"
    await db.flush()

    return {
        "success": True,
        "message": f"Search term '{search_term.search_term}' added as negative keyword",
        "keyword_bid_id": str(keyword_bid.id),
    }
