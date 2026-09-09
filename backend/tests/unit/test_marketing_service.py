"""Unit tests for the Marketing service layer.

Covers launch plans, email sequences, social posts, and ARC campaigns.

All tests use mocked AsyncSession -- no real DB.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.marketing import (
    ARCCampaignStatus,
    ARCRecipientStatus,
    EmailSequenceStatus,
    LaunchPlanStatus,
    SocialPlatform,
    SocialPostStatus,
)
from app.modules.marketing.schemas import (
    ARCCampaignCreate,
    ARCRecipientCreate,
    EmailSequenceCreate,
    EmailSequenceUpdate,
    EmailTemplateCreate,
    LaunchPlanCreate,
    LaunchPlanUpdate,
    LaunchPhaseCreate,
    SocialPostCreate,
    PhaseTaskCreate,
)
from app.modules.marketing.service import MarketingService


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def book_id():
    return uuid.uuid4()


@pytest.fixture
def mock_db():
    """Return an AsyncMock simulating an AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    """Return a MarketingService instance with mocked DB."""
    return MarketingService(mock_db)


# ===========================================================================
# Tests: Launch Plans
# ===========================================================================

class TestCreateLaunchPlan:
    """Tests for MarketingService.create_launch_plan."""

    @pytest.mark.asyncio
    async def test_creates_launch_plan_with_phases_and_tasks(
        self,
        service,
        org_id,
        user_id,
        book_id,
    ):
        """create_launch_plan should create launch plan with phases and tasks."""
        # Mock the get_launch_plan call at the end
        mock_plan = MagicMock(
            id=uuid.uuid4(),
            title="Book Launch 2025",
            status=LaunchPlanStatus.DRAFT,
            phases=[],
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_plan
        service.db.execute.return_value = mock_result

        data = LaunchPlanCreate(
            book_id=book_id,
            title="Book Launch 2025",
            description="Full launch campaign",
            launch_date=datetime(2025, 6, 1, tzinfo=UTC),
            genre="thriller",
            target_audience="Adult readers",
            budget=5000.00,
            goals=["Sell 1000 copies in first month"],
            phases=[
                LaunchPhaseCreate(
                    phase_type="pre_launch",
                    name="Pre-Launch",
                    description="Build hype",
                    start_date=datetime(2025, 5, 1, tzinfo=UTC),
                    end_date=datetime(2025, 5, 31, tzinfo=UTC),
                    order_index=1,
                    tasks=[
                        PhaseTaskCreate(
                            title="Build ARC team",
                            description="Recruit 50 ARC readers",
                            status="pending",
                            due_date=datetime(2025, 5, 15, tzinfo=UTC),
                            order_index=1,
                        ),
                    ],
                ),
            ],
        )

        result = await service.create_launch_plan(org_id, user_id, data)

        assert result.title == "Book Launch 2025"
        assert service.db.add.call_count >= 2  # plan + phase + task


class TestGetLaunchPlan:
    """Tests for MarketingService.get_launch_plan."""

    @pytest.mark.asyncio
    async def test_returns_launch_plan_with_phases(
        self,
        service,
        org_id,
    ):
        """get_launch_plan should return plan with all phases and tasks."""
        plan_id = uuid.uuid4()
        plan = MagicMock(
            id=plan_id,
            org_id=org_id,
            title="Test Plan",
            deleted_at=None,
            phases=[],
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = plan
        service.db.execute.return_value = mock_result

        result = await service.get_launch_plan(plan_id, org_id)

        assert result is not None
        assert result.id == plan_id


class TestListLaunchPlans:
    """Tests for MarketingService.list_launch_plans."""

    @pytest.mark.asyncio
    async def test_returns_paginated_launch_plans(
        self,
        service,
        org_id,
    ):
        """list_launch_plans should return paginated list of plans."""
        plan1 = MagicMock(id=uuid.uuid4())
        plan2 = MagicMock(id=uuid.uuid4())

        mock_count = MagicMock()
        mock_count.scalar.return_value = 2

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [plan1, plan2]

        service.db.execute.side_effect = [mock_count, mock_result]

        plans, total = await service.list_launch_plans(org_id, limit=20)

        assert len(plans) == 2
        assert total == 2


class TestUpdateLaunchPlan:
    """Tests for MarketingService.update_launch_plan."""

    @pytest.mark.asyncio
    async def test_updates_launch_plan_fields(
        self,
        service,
        org_id,
    ):
        """update_launch_plan should update plan fields."""
        plan_id = uuid.uuid4()
        plan = MagicMock(
            id=plan_id,
            org_id=org_id,
            title="Original Title",
            deleted_at=None,
            phases=[],
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = plan
        service.db.execute.return_value = mock_result

        update_data = LaunchPlanUpdate(
            title="Updated Title",
            status=LaunchPlanStatus.ACTIVE,
        )

        result = await service.update_launch_plan(plan_id, org_id, update_data)

        assert plan.title == "Updated Title"
        assert plan.status == LaunchPlanStatus.ACTIVE


# ===========================================================================
# Tests: Email Sequences
# ===========================================================================

class TestCreateEmailSequence:
    """Tests for MarketingService.create_email_sequence."""

    @pytest.mark.asyncio
    async def test_creates_email_sequence_with_templates(
        self,
        service,
        org_id,
        user_id,
    ):
        """create_email_sequence should create sequence with email templates."""
        # Mock the get_email_sequence call at the end
        mock_sequence = MagicMock(
            id=uuid.uuid4(),
            name="Welcome Series",
            status=EmailSequenceStatus.DRAFT,
            emails=[],
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sequence
        service.db.execute.return_value = mock_result

        data = EmailSequenceCreate(
            name="Welcome Series",
            description="Onboard new readers",
            trigger_event="signup",
            settings={"send_time": "10:00"},
            emails=[
                EmailTemplateCreate(
                    template_type="welcome",
                    subject="Welcome!",
                    body_html="<p>Welcome to our community!</p>",
                    body_text="Welcome to our community!",
                    delay_days=0,
                    delay_hours=0,
                    order_index=1,
                    personalization_fields={"name": "{{name}}"},
                ),
            ],
        )

        result = await service.create_email_sequence(org_id, user_id, data)

        assert result.name == "Welcome Series"
        assert service.db.add.call_count >= 2  # sequence + template


class TestListEmailSequences:
    """Tests for MarketingService.list_email_sequences."""

    @pytest.mark.asyncio
    async def test_returns_paginated_email_sequences(
        self,
        service,
        org_id,
    ):
        """list_email_sequences should return paginated sequences."""
        seq1 = MagicMock(id=uuid.uuid4(), emails=[])
        seq2 = MagicMock(id=uuid.uuid4(), emails=[])

        mock_count = MagicMock()
        mock_count.scalar.return_value = 2

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [seq1, seq2]

        service.db.execute.side_effect = [mock_count, mock_result]

        sequences, total = await service.list_email_sequences(org_id, limit=20)

        assert len(sequences) == 2
        assert total == 2


class TestTriggerEmailSend:
    """Tests for MarketingService.trigger_email_send."""

    @pytest.mark.asyncio
    async def test_triggers_email_sequence_send(
        self,
        service,
        org_id,
    ):
        """trigger_email_send should mark sequence as active and schedule emails."""
        sequence_id = uuid.uuid4()
        template = MagicMock(send_status="draft", scheduled_at=None)
        sequence = MagicMock(
            id=sequence_id,
            org_id=org_id,
            status=EmailSequenceStatus.DRAFT,
            recipient_count=0,
            emails=[template],
            deleted_at=None,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sequence
        service.db.execute.return_value = mock_result

        result = await service.trigger_email_send(
            sequence_id,
            org_id,
            recipient_emails=["user1@example.com", "user2@example.com"],
        )

        assert sequence.status == EmailSequenceStatus.ACTIVE
        assert sequence.recipient_count == 2
        assert template.send_status == "scheduled"


# ===========================================================================
# Tests: Social Posts
# ===========================================================================

class TestCreateSocialPost:
    """Tests for MarketingService.create_social_post."""

    @pytest.mark.asyncio
    async def test_creates_social_post(
        self,
        service,
        org_id,
        user_id,
    ):
        """create_social_post should create a social media post."""
        data = SocialPostCreate(
            platform=SocialPlatform.INSTAGRAM,
            content="Check out my new book! #thriller #mustread",
            media_urls=["https://example.com/cover.jpg"],
            hashtags=["thriller", "mustread"],
            scheduled_at=datetime(2025, 6, 1, 12, 0, tzinfo=UTC),
        )

        result = await service.create_social_post(org_id, user_id, data)

        service.db.add.assert_called_once()
        service.db.flush.assert_awaited_once()


class TestCreateSocialPostsBatch:
    """Tests for MarketingService.create_social_posts_batch."""

    @pytest.mark.asyncio
    async def test_creates_multiple_social_posts(
        self,
        service,
        org_id,
        user_id,
    ):
        """create_social_posts_batch should create multiple posts."""
        posts_data = [
            SocialPostCreate(
                platform=SocialPlatform.INSTAGRAM,
                content="Post 1",
                scheduled_at=datetime(2025, 6, 1, tzinfo=UTC),
            ),
            SocialPostCreate(
                platform=SocialPlatform.FACEBOOK,
                content="Post 2",
                scheduled_at=datetime(2025, 6, 2, tzinfo=UTC),
            ),
        ]

        result = await service.create_social_posts_batch(
            org_id,
            user_id,
            posts_data,
        )

        assert len(result) == 2
        assert service.db.add.call_count == 2


class TestGetSocialCalendar:
    """Tests for MarketingService.get_social_calendar."""

    @pytest.mark.asyncio
    async def test_returns_social_calendar_with_stats(
        self,
        service,
        org_id,
    ):
        """get_social_calendar should return posts and aggregated stats."""
        post1 = MagicMock(
            id=uuid.uuid4(),
            platform=SocialPlatform.INSTAGRAM,
            status=SocialPostStatus.SCHEDULED,
        )
        post2 = MagicMock(
            id=uuid.uuid4(),
            platform=SocialPlatform.FACEBOOK,
            status=SocialPostStatus.PUBLISHED,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [post1, post2]
        service.db.execute.return_value = mock_result

        result = await service.get_social_calendar(org_id)

        assert len(result["posts"]) == 2
        assert result["total_scheduled"] == 1
        assert result["total_published"] == 1
        assert "instagram" in result["platforms"]
        assert "facebook" in result["platforms"]


# ===========================================================================
# Tests: ARC Campaigns
# ===========================================================================

class TestCreateARCCampaign:
    """Tests for MarketingService.create_arc_campaign."""

    @pytest.mark.asyncio
    async def test_creates_arc_campaign_with_recipients(
        self,
        service,
        org_id,
        user_id,
        book_id,
    ):
        """create_arc_campaign should create campaign with recipients."""
        # Mock the get_arc_campaign call at the end
        mock_campaign = MagicMock(
            id=uuid.uuid4(),
            name="ARC Campaign 2025",
            status=ARCCampaignStatus.DRAFT,
            total_copies=2,
            recipients=[],
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_campaign
        service.db.execute.return_value = mock_result

        data = ARCCampaignCreate(
            book_id=book_id,
            name="ARC Campaign 2025",
            description="Send ARCs to reviewers",
            book_file_url="https://example.com/book.pdf",
            cover_letter="Please read and review my book!",
            deadline=datetime(2025, 5, 31, tzinfo=UTC),
            recipients=[
                ARCRecipientCreate(
                    name="Reviewer 1",
                    email="reviewer1@example.com",
                    notes="Top reviewer",
                ),
                ARCRecipientCreate(
                    name="Reviewer 2",
                    email="reviewer2@example.com",
                ),
            ],
        )

        result = await service.create_arc_campaign(org_id, user_id, data)

        assert result.name == "ARC Campaign 2025"
        assert result.total_copies == 2
        assert service.db.add.call_count >= 3  # campaign + 2 recipients


class TestListARCCampaigns:
    """Tests for MarketingService.list_arc_campaigns."""

    @pytest.mark.asyncio
    async def test_returns_paginated_arc_campaigns(
        self,
        service,
        org_id,
    ):
        """list_arc_campaigns should return paginated campaigns."""
        campaign1 = MagicMock(id=uuid.uuid4(), recipients=[])
        campaign2 = MagicMock(id=uuid.uuid4(), recipients=[])

        mock_count = MagicMock()
        mock_count.scalar.return_value = 2

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [campaign1, campaign2]

        service.db.execute.side_effect = [mock_count, mock_result]

        campaigns, total = await service.list_arc_campaigns(org_id, limit=20)

        assert len(campaigns) == 2
        assert total == 2


class TestSendARCCopies:
    """Tests for MarketingService.send_arc_copies."""

    @pytest.mark.asyncio
    async def test_sends_arc_copies_to_recipients(
        self,
        service,
        org_id,
    ):
        """send_arc_copies should mark recipients as sent."""
        campaign_id = uuid.uuid4()
        recipient1 = MagicMock(
            id=uuid.uuid4(),
            status=ARCRecipientStatus.PENDING,
            sent_at=None,
        )
        recipient2 = MagicMock(
            id=uuid.uuid4(),
            status=ARCRecipientStatus.PENDING,
            sent_at=None,
        )

        campaign = MagicMock(
            id=campaign_id,
            org_id=org_id,
            status=ARCCampaignStatus.DRAFT,
            total_copies=2,
            sent_copies=0,
            recipients=[recipient1, recipient2],
            deleted_at=None,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = campaign
        service.db.execute.return_value = mock_result

        result = await service.send_arc_copies(campaign_id, org_id)

        assert campaign.status == ARCCampaignStatus.COMPLETED
        assert campaign.sent_copies == 2
        assert recipient1.status == ARCRecipientStatus.SENT
        assert recipient2.status == ARCRecipientStatus.SENT
