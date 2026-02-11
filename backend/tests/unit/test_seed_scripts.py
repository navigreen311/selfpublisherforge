"""Tests for database seeding scripts."""
import pytest
from sqlalchemy import select

from app.models.organization import Organization
from app.models.user import User
from app.models.project import Project, Book
from app.models.content import Manuscript, Chapter
from app.modules.analytics.models import RoyaltyRecord, PortfolioMetricSnapshot
from app.models.market import CompetitorBook, MarketKeyword
from app.models.marketing import LaunchPlan, EmailSequence
from scripts.seeds.users import seed_users
from scripts.seeds.projects import seed_projects
from scripts.seeds.content import seed_content
from scripts.seeds.analytics import seed_analytics
from scripts.seeds.market import seed_market
from scripts.seeds.marketing import seed_marketing


@pytest.mark.asyncio
async def test_seed_users(db_session):
    """Test that seed_users creates users and organizations."""
    result = await seed_users(db_session)

    assert "users" in result
    assert "orgs" in result
    assert len(result["users"]) == 4
    assert len(result["orgs"]) == 4

    # Verify user exists
    user_result = await db_session.execute(
        select(User).where(User.email == "jane@example.com")
    )
    user = user_result.scalar_one_or_none()
    assert user is not None
    assert user.name == "Jane Doe"
    assert user.email_verified is True

    # Verify org exists
    org_result = await db_session.execute(
        select(Organization).where(Organization.slug == "janes-publishing")
    )
    org = org_result.scalar_one_or_none()
    assert org is not None
    assert org.name == "Jane's Publishing House"


@pytest.mark.asyncio
async def test_seed_users_idempotent(db_session):
    """Test that seed_users can be run multiple times safely."""
    # First run
    result1 = await seed_users(db_session)
    jane_id_1 = result1["users"]["jane@example.com"]

    # Second run
    result2 = await seed_users(db_session)
    jane_id_2 = result2["users"]["jane@example.com"]

    # Should return same IDs, not create duplicates
    assert jane_id_1 == jane_id_2

    # Verify only one Jane exists
    user_result = await db_session.execute(
        select(User).where(User.email == "jane@example.com")
    )
    users = user_result.scalars().all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_seed_projects(db_session):
    """Test that seed_projects creates projects and books."""
    # Setup: create org first
    user_data = await seed_users(db_session)
    jane_org_id = user_data["orgs"]["jane@example.com"]

    # Test
    result = await seed_projects(db_session, jane_org_id)

    assert "projects" in result
    assert "books" in result
    assert len(result["books"]) == 3

    # Verify book exists
    book_result = await db_session.execute(
        select(Book).where(Book.title == "The Dragon's Prophecy")
    )
    book = book_result.scalar_one_or_none()
    assert book is not None
    assert book.subtitle == "Book 1 of the Fire Chronicles"

    # Verify project exists
    project_result = await db_session.execute(
        select(Project).where(Project.id == book.project_id)
    )
    project = project_result.scalar_one_or_none()
    assert project is not None
    assert project.org_id == jane_org_id


@pytest.mark.asyncio
async def test_seed_content(db_session):
    """Test that seed_content creates chapters."""
    # Setup
    user_data = await seed_users(db_session)
    jane_org_id = user_data["orgs"]["jane@example.com"]
    project_data = await seed_projects(db_session, jane_org_id)
    book_ids = project_data["books"]

    # Test
    await seed_content(db_session, book_ids)

    # Verify chapters exist
    manuscript_result = await db_session.execute(
        select(Manuscript).join(Book).where(Book.title == "The Dragon's Prophecy")
    )
    manuscript = manuscript_result.scalar_one_or_none()
    assert manuscript is not None

    chapter_result = await db_session.execute(
        select(Chapter).where(Chapter.manuscript_id == manuscript.id)
    )
    chapters = chapter_result.scalars().all()
    assert len(chapters) == 5
    assert chapters[0].title == "The Awakening"


@pytest.mark.asyncio
async def test_seed_analytics(db_session):
    """Test that seed_analytics creates royalty records."""
    # Setup
    user_data = await seed_users(db_session)
    jane_org_id = user_data["orgs"]["jane@example.com"]
    project_data = await seed_projects(db_session, jane_org_id)
    book_ids = project_data["books"]

    # Test
    await seed_analytics(db_session, jane_org_id, book_ids)

    # Verify royalty records exist
    royalty_result = await db_session.execute(
        select(RoyaltyRecord).where(RoyaltyRecord.org_id == jane_org_id)
    )
    royalties = royalty_result.scalars().all()
    assert len(royalties) > 0

    # Verify portfolio snapshots exist
    snapshot_result = await db_session.execute(
        select(PortfolioMetricSnapshot).where(
            PortfolioMetricSnapshot.org_id == jane_org_id
        )
    )
    snapshots = snapshot_result.scalars().all()
    assert len(snapshots) > 0


@pytest.mark.asyncio
async def test_seed_market(db_session):
    """Test that seed_market creates competitor data."""
    # Setup
    user_data = await seed_users(db_session)
    jane_org_id = user_data["orgs"]["jane@example.com"]

    # Test
    await seed_market(db_session, jane_org_id)

    # Verify competitor books exist
    book_result = await db_session.execute(
        select(CompetitorBook).where(CompetitorBook.org_id == jane_org_id)
    )
    books = book_result.scalars().all()
    assert len(books) > 0
    assert books[0].category == "Fantasy"

    # Verify keywords exist
    keyword_result = await db_session.execute(
        select(MarketKeyword).where(MarketKeyword.org_id == jane_org_id)
    )
    keywords = keyword_result.scalars().all()
    assert len(keywords) > 0


@pytest.mark.asyncio
async def test_seed_marketing(db_session):
    """Test that seed_marketing creates campaigns and email templates."""
    # Setup
    user_data = await seed_users(db_session)
    jane_org_id = user_data["orgs"]["jane@example.com"]
    jane_user_id = user_data["users"]["jane@example.com"]
    project_data = await seed_projects(db_session, jane_org_id)
    book_ids = project_data["books"]

    # Test
    await seed_marketing(db_session, jane_org_id, jane_user_id, book_ids)

    # Verify launch plan exists
    plan_result = await db_session.execute(
        select(LaunchPlan).where(LaunchPlan.org_id == jane_org_id)
    )
    plan = plan_result.scalar_one_or_none()
    assert plan is not None
    assert plan.title == "Dragon's Prophecy Launch Campaign"

    # Verify email sequence exists
    sequence_result = await db_session.execute(
        select(EmailSequence).where(EmailSequence.org_id == jane_org_id)
    )
    sequence = sequence_result.scalar_one_or_none()
    assert sequence is not None
    assert sequence.name == "Dragon's Prophecy - Launch Sequence"


@pytest.mark.asyncio
async def test_seed_scripts_no_crashes(db_session):
    """Integration test: ensure all seed scripts run without crashing."""
    # This test verifies that the seed scripts can run in sequence
    # without raising exceptions, even if DB already has some data

    user_data = await seed_users(db_session)
    jane_org_id = user_data["orgs"]["jane@example.com"]
    jane_user_id = user_data["users"]["jane@example.com"]

    project_data = await seed_projects(db_session, jane_org_id)
    book_ids = project_data["books"]

    await seed_content(db_session, book_ids)
    await seed_analytics(db_session, jane_org_id, book_ids)
    await seed_market(db_session, jane_org_id)
    await seed_marketing(db_session, jane_org_id, jane_user_id, book_ids)

    # If we got here without exceptions, the test passes
    assert True
