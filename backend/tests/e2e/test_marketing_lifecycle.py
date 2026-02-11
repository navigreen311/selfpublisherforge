"""End-to-end tests for the marketing campaign lifecycle.

This test exercises a complete marketing campaign journey through the HTTP API:
- Creating a launch plan
- Setting up an ARC campaign
- Creating email sequences
- Generating social media content
- Creating advertising campaigns
- Tracking campaign performance

Tests use the async HTTPX client and in-memory SQLite fixtures from ``conftest.py``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.project import Book, BookFormat, BookStatus, Project, ProjectType

settings = get_settings()
AUTH_PREFIX = f"{settings.API_V1_PREFIX}/auth"
MARKETING_PREFIX = f"{settings.API_V1_PREFIX}/marketing"
ADVERTISING_PREFIX = f"{settings.API_V1_PREFIX}/ads"

VALID_PASSWORD = "StrongP@ss1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register(
    client: AsyncClient,
    email: str = "marketing-e2e@test.com",
    password: str = VALID_PASSWORD,
    name: str = "Marketing E2E Tester",
    org_name: str = "Marketing E2E Org",
) -> dict:
    """Register a user and return the full response JSON."""
    resp = await client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "email": email,
            "password": password,
            "name": name,
            "org_name": org_name,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(
    client: AsyncClient,
    email: str,
    password: str = VALID_PASSWORD,
) -> dict:
    """Login and return the response JSON (containing tokens)."""
    resp = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _auth_header(access_token: str) -> dict[str, str]:
    """Build an ``Authorization: Bearer <token>`` header dict."""
    return {"Authorization": f"Bearer {access_token}"}


async def _register_and_get_token(
    client: AsyncClient,
    email: str,
) -> tuple[str, str, str]:
    """Register, login, and return ``(access_token, org_id, user_id)``."""
    reg_data = await _register(client, email=email)
    org_id = reg_data["user"]["org_id"]
    user_id = reg_data["user"]["id"]
    login_data = await _login(client, email=email)
    access_token = login_data["tokens"]["access_token"]
    return access_token, org_id, user_id


async def _create_project_and_book(
    db: AsyncSession,
    org_id: str,
    title: str = "Test Marketing Book",
) -> tuple[uuid.UUID, uuid.UUID]:
    """Insert a Project + Book directly into the DB and return their IDs."""
    project_id = uuid.uuid4()
    project = Project(
        id=project_id,
        org_id=uuid.UUID(org_id),
        title=f"{title} Project",
        type=ProjectType.BOOK,
    )
    db.add(project)
    await db.flush()

    book_id = uuid.uuid4()
    book = Book(
        id=book_id,
        project_id=project_id,
        title=title,
        format=BookFormat.EBOOK,
        status=BookStatus.DRAFT,
    )
    db.add(book)
    await db.flush()
    return project_id, book_id


# ---------------------------------------------------------------------------
# E2E: Complete Marketing Campaign Lifecycle
# ---------------------------------------------------------------------------

class TestMarketingCampaignLifecycle:
    """Full flow: create launch plan, ARC campaign, email sequences, social posts, and ad campaigns."""

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.AmazonAdsClient")
    async def test_full_marketing_lifecycle(
        self, mock_amazon_cls, client: AsyncClient, db_session: AsyncSession
    ):
        """Complete marketing campaign lifecycle test covering all major components."""
        # Mock Amazon Ads client to avoid external dependencies
        mock_amazon = AsyncMock()
        mock_amazon.create_campaign.return_value = {
            "external_campaign_id": "amz-camp-123",
            "status": "draft",
            "created": True,
        }
        mock_amazon_cls.return_value = mock_amazon

        # ── Step 1: Register + login -> get token ──
        email = "marketing-lifecycle-1@test.com"
        token, org_id, user_id = await _register_and_get_token(client, email)

        # ── Step 2: Create a book project (via DB -- no project API exists) ──
        _project_id, book_id = await _create_project_and_book(
            db_session, org_id, title="The Marketing Chronicles"
        )

        # ── Step 3: Generate a launch plan via AI ──
        launch_date = datetime.now(timezone.utc) + timedelta(days=60)
        launch_plan_resp = await client.post(
            f"{MARKETING_PREFIX}/launch-plan/generate",
            json={
                "book_id": str(book_id),
                "book_title": "The Marketing Chronicles",
                "genre": "fantasy",
                "target_audience": "Young adult fantasy readers ages 16-25",
                "launch_date": launch_date.isoformat(),
                "budget": 5000.0,
                "goals": ["Build buzz on social media", "Get 50 ARC reviews", "Run targeted ads"],
                "additional_context": "First book in a trilogy, debut author",
            },
            headers=_auth_header(token),
        )
        assert launch_plan_resp.status_code == 201, launch_plan_resp.text
        launch_plan_data = launch_plan_resp.json()
        assert "data" in launch_plan_data
        launch_plan = launch_plan_data["data"]
        plan_id = uuid.UUID(launch_plan["id"])
        assert launch_plan["title"] is not None
        assert launch_plan["status"] == "draft"
        assert launch_plan["book_id"] == str(book_id)

        # ── Step 4: Create an ARC campaign ──
        arc_deadline = datetime.now(timezone.utc) + timedelta(days=45)
        arc_campaign_resp = await client.post(
            f"{MARKETING_PREFIX}/arc",
            json={
                "name": "Pre-Launch ARC Campaign",
                "description": "Send advanced copies to reviewers before launch",
                "book_id": str(book_id),
                "launch_plan_id": str(plan_id),
                "deadline": arc_deadline.isoformat(),
                "cover_letter": "Thank you for reviewing my debut novel!",
                "recipients": [
                    {
                        "name": "Reviewer Alice",
                        "email": "alice@bookreviewers.com",
                        "notes": "Fantasy specialist",
                    },
                    {
                        "name": "Reviewer Bob",
                        "email": "bob@readersunite.com",
                        "notes": "YA expert",
                    },
                ],
            },
            headers=_auth_header(token),
        )
        assert arc_campaign_resp.status_code == 201, arc_campaign_resp.text
        arc_data = arc_campaign_resp.json()
        assert "data" in arc_data
        arc_campaign = arc_data["data"]
        arc_id = uuid.UUID(arc_campaign["id"])
        assert arc_campaign["name"] == "Pre-Launch ARC Campaign"
        assert arc_campaign["status"] == "draft"
        assert arc_campaign["total_copies"] == 2
        assert len(arc_campaign["recipients"]) == 2

        # ── Step 5: Create an email sequence ──
        email_seq_resp = await client.post(
            f"{MARKETING_PREFIX}/email-sequences",
            json={
                "name": "Launch Week Email Sequence",
                "description": "Email campaign for launch week",
                "launch_plan_id": str(plan_id),
                "trigger_event": "launch_week",
                "emails": [
                    {
                        "template_type": "custom",
                        "subject": "Cover Reveal: The Marketing Chronicles is Coming!",
                        "body_text": "I'm excited to reveal the cover of my debut fantasy novel!",
                        "delay_days": 0,
                        "order_index": 0,
                    },
                    {
                        "template_type": "custom",
                        "subject": "Launch Day: The Marketing Chronicles is Live!",
                        "body_text": "The wait is over! The Marketing Chronicles is now available.",
                        "delay_days": 7,
                        "order_index": 1,
                    },
                    {
                        "template_type": "custom",
                        "subject": "Early Reviews Are In!",
                        "body_text": "Check out what readers are saying about The Marketing Chronicles.",
                        "delay_days": 14,
                        "order_index": 2,
                    },
                ],
            },
            headers=_auth_header(token),
        )
        assert email_seq_resp.status_code == 201, email_seq_resp.text
        email_seq_data = email_seq_resp.json()
        assert "data" in email_seq_data
        email_seq = email_seq_data["data"]
        email_seq_id = uuid.UUID(email_seq["id"])
        assert email_seq["name"] == "Launch Week Email Sequence"
        assert email_seq["status"] == "draft"
        assert len(email_seq["emails"]) == 3

        # ── Step 6: Generate social media content ──
        social_content_resp = await client.post(
            f"{MARKETING_PREFIX}/social/generate",
            json={
                "book_title": "The Marketing Chronicles",
                "genre": "fantasy",
                "target_audience": "Young adult fantasy readers",
                "book_description": "A thrilling fantasy adventure about a young marketer who discovers magic in data.",
                "platforms": ["twitter", "facebook", "instagram"],
                "tone": "enthusiastic",
                "num_posts_per_platform": 2,
                "launch_plan_id": str(plan_id),
            },
            headers=_auth_header(token),
        )
        assert social_content_resp.status_code == 201, social_content_resp.text
        social_data = social_content_resp.json()
        assert "data" in social_data
        social_posts = social_data["data"]
        assert len(social_posts) >= 6  # 2 posts per platform × 3 platforms
        assert all(post["status"] == "draft" for post in social_posts)

        # ── Step 7: Create an advertising campaign ──
        ad_campaign_resp = await client.post(
            f"{ADVERTISING_PREFIX}/campaigns",
            json={
                "name": "Launch Week Amazon Ads",
                "platform": "amazon",
                "campaign_type": "sponsored_products",
                "book_id": str(book_id),
                "daily_budget": 25.0,
                "total_budget": 500.0,
                "bid_strategy": "manual",
                "target_acos": 30.0,
                "targeting_keywords": [
                    "young adult fantasy",
                    "fantasy books",
                    "epic fantasy",
                    "fantasy adventure",
                ],
                "negative_keywords": ["romance", "horror"],
            },
            headers=_auth_header(token),
        )
        assert ad_campaign_resp.status_code == 201, ad_campaign_resp.text
        ad_campaign = ad_campaign_resp.json()
        ad_campaign_id = uuid.UUID(ad_campaign["id"])
        assert ad_campaign["name"] == "Launch Week Amazon Ads"
        assert ad_campaign["platform"] == "amazon"
        assert ad_campaign["daily_budget"] == 25.0
        assert ad_campaign["status"] == "draft"
        assert len(ad_campaign["targeting_keywords"]) == 4

        # ── Step 8: Check launch plan detail ──
        plan_detail_resp = await client.get(
            f"{MARKETING_PREFIX}/launch-plans/{plan_id}",
            headers=_auth_header(token),
        )
        assert plan_detail_resp.status_code == 200
        plan_detail_data = plan_detail_resp.json()
        assert "data" in plan_detail_data
        plan_detail = plan_detail_data["data"]
        assert plan_detail["id"] == str(plan_id)
        assert plan_detail["book_id"] == str(book_id)

        # ── Step 9: List all components to verify they were created ──
        # List ARC campaigns
        arc_list_resp = await client.get(
            f"{MARKETING_PREFIX}/arc",
            headers=_auth_header(token),
        )
        assert arc_list_resp.status_code == 200
        arc_list_data = arc_list_resp.json()
        assert arc_list_data["total_count"] >= 1
        assert any(arc["id"] == str(arc_id) for arc in arc_list_data["items"])

        # List email sequences
        email_list_resp = await client.get(
            f"{MARKETING_PREFIX}/email-sequences",
            headers=_auth_header(token),
        )
        assert email_list_resp.status_code == 200
        email_list_data = email_list_resp.json()
        assert email_list_data["total_count"] >= 1
        assert any(seq["id"] == str(email_seq_id) for seq in email_list_data["items"])

        # List ad campaigns
        ad_list_resp = await client.get(
            f"{ADVERTISING_PREFIX}/campaigns",
            headers=_auth_header(token),
        )
        assert ad_list_resp.status_code == 200
        ad_list_data = ad_list_resp.json()
        assert ad_list_data["total_count"] >= 1
        assert any(camp["id"] == str(ad_campaign_id) for camp in ad_list_data["items"])

        # ── Step 10: Get campaign performance (should be empty initially) ──
        perf_resp = await client.get(
            f"{ADVERTISING_PREFIX}/campaigns/{ad_campaign_id}/performance",
            headers=_auth_header(token),
        )
        assert perf_resp.status_code == 200
        perf_data = perf_resp.json()
        assert isinstance(perf_data, list)
        # Initially, performance data should be empty or have zero metrics
        assert len(perf_data) == 0 or all(p["spend"] == 0.0 for p in perf_data)

    @pytest.mark.asyncio
    async def test_social_calendar_view(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test social media calendar aggregation across platforms."""
        email = "social-calendar@test.com"
        token, org_id, user_id = await _register_and_get_token(client, email)

        # Create a book
        _project_id, book_id = await _create_project_and_book(
            db_session, org_id, title="Social Media Book"
        )

        # Generate social media content
        social_resp = await client.post(
            f"{MARKETING_PREFIX}/social/generate",
            json={
                "book_title": "Social Media Book",
                "genre": "contemporary",
                "target_audience": "Social media enthusiasts",
                "book_description": "A book about mastering social media marketing.",
                "platforms": ["twitter", "facebook"],
                "tone": "professional",
                "num_posts_per_platform": 3,
            },
            headers=_auth_header(token),
        )
        assert social_resp.status_code == 201

        # Get social calendar
        calendar_resp = await client.get(
            f"{MARKETING_PREFIX}/social/calendar",
            headers=_auth_header(token),
        )
        assert calendar_resp.status_code == 200
        calendar_data = calendar_resp.json()
        assert "posts" in calendar_data
        assert "total_scheduled" in calendar_data
        assert "total_published" in calendar_data
        assert "total_draft" in calendar_data
        assert "platforms" in calendar_data
        assert len(calendar_data["posts"]) >= 6

    @pytest.mark.asyncio
    async def test_arc_campaign_send_flow(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test sending ARC copies to specific recipients."""
        email = "arc-send@test.com"
        token, org_id, user_id = await _register_and_get_token(client, email)

        # Create a book
        _project_id, book_id = await _create_project_and_book(
            db_session, org_id, title="ARC Test Book"
        )

        # Create ARC campaign
        arc_resp = await client.post(
            f"{MARKETING_PREFIX}/arc",
            json={
                "name": "ARC Send Test",
                "book_id": str(book_id),
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "recipients": [
                    {"name": "Tester 1", "email": "test1@example.com"},
                    {"name": "Tester 2", "email": "test2@example.com"},
                ],
            },
            headers=_auth_header(token),
        )
        assert arc_resp.status_code == 201
        arc_data = arc_resp.json()["data"]
        arc_id = arc_data["id"]
        recipient_ids = [r["id"] for r in arc_data["recipients"]]

        # Send ARC copies to first recipient only
        send_resp = await client.post(
            f"{MARKETING_PREFIX}/arc/{arc_id}/send",
            json={
                "recipient_ids": [recipient_ids[0]],
                "custom_message": "Thank you for being an early reviewer!",
            },
            headers=_auth_header(token),
        )
        assert send_resp.status_code == 200
        send_data = send_resp.json()
        assert "data" in send_data

    @pytest.mark.asyncio
    async def test_email_sequence_trigger(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test triggering an email sequence send."""
        email = "email-trigger@test.com"
        token, org_id, user_id = await _register_and_get_token(client, email)

        # Create a book
        _project_id, book_id = await _create_project_and_book(
            db_session, org_id, title="Email Test Book"
        )

        # Create email sequence
        seq_resp = await client.post(
            f"{MARKETING_PREFIX}/email-sequences",
            json={
                "name": "Test Sequence",
                "emails": [
                    {
                        "subject": "Test Email",
                        "body_text": "Hello subscriber!",
                        "delay_days": 0,
                    }
                ],
            },
            headers=_auth_header(token),
        )
        assert seq_resp.status_code == 201
        seq_id = seq_resp.json()["data"]["id"]

        # Trigger email send
        send_resp = await client.post(
            f"{MARKETING_PREFIX}/email-sequences/{seq_id}/send",
            json={
                "recipient_emails": ["subscriber1@example.com", "subscriber2@example.com"],
                "personalization": {"author_name": "John Doe"},
            },
            headers=_auth_header(token),
        )
        assert send_resp.status_code == 200
        send_data = send_resp.json()
        assert "data" in send_data

    @pytest.mark.asyncio
    @patch("app.modules.advertising.service.AmazonAdsClient")
    async def test_ad_campaign_update(
        self, mock_amazon_cls, client: AsyncClient, db_session: AsyncSession
    ):
        """Test updating an advertising campaign's budget and status."""
        # Mock Amazon Ads client
        mock_amazon = AsyncMock()
        mock_amazon.create_campaign.return_value = {
            "external_campaign_id": "amz-camp-update-123",
            "status": "draft",
            "created": True,
        }
        mock_amazon.update_campaign.return_value = {
            "external_campaign_id": "amz-camp-update-123",
            "status": "active",
            "updated": True,
        }
        mock_amazon_cls.return_value = mock_amazon

        email = "ad-update@test.com"
        token, org_id, user_id = await _register_and_get_token(client, email)

        # Create a book
        _project_id, book_id = await _create_project_and_book(
            db_session, org_id, title="Ad Update Book"
        )

        # Create ad campaign
        create_resp = await client.post(
            f"{ADVERTISING_PREFIX}/campaigns",
            json={
                "name": "Test Ad Campaign",
                "platform": "amazon",
                "campaign_type": "sponsored_products",
                "book_id": str(book_id),
                "daily_budget": 10.0,
                "bid_strategy": "manual",
                "targeting_keywords": ["test"],
            },
            headers=_auth_header(token),
        )
        assert create_resp.status_code == 201
        campaign_id = create_resp.json()["id"]

        # Update campaign
        update_resp = await client.patch(
            f"{ADVERTISING_PREFIX}/campaigns/{campaign_id}",
            json={
                "daily_budget": 20.0,
                "status": "active",
                "targeting_keywords": ["test", "new keyword"],
            },
            headers=_auth_header(token),
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["daily_budget"] == 20.0
        assert updated["status"] == "active"
        assert "new keyword" in updated["targeting_keywords"]
