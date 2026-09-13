"""Unit tests for the LaunchPlanner, EmailBuilder, and SocialContentGenerator."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.models.marketing import (
    EmailTemplateType,
    LaunchPhaseType,
    PhaseTaskStatus,
    SocialPlatform,
)
from app.modules.marketing.email_builder import EmailBuilder, _extract_personalization_fields
from app.modules.marketing.launch_planner import (
    LAUNCH_WEEK_TASKS,
    POST_LAUNCH_TASKS,
    PRE_LAUNCH_TASKS,
    LaunchPlanner,
    _build_tasks_from_template,
)
from app.modules.marketing.schemas import (
    GenerateLaunchPlanRequest,
    GenerateSocialContentRequest,
)
from app.modules.marketing.social_generator import SocialContentGenerator, _genre_to_hashtag

# ---------------------------------------------------------------------------
# LaunchPlanner Tests
# ---------------------------------------------------------------------------


class TestLaunchPlanner:
    """Tests for the AI launch plan generator."""

    @pytest.fixture
    def planner(self) -> LaunchPlanner:
        return LaunchPlanner()

    @pytest.fixture
    def gen_request(self) -> GenerateLaunchPlanRequest:
        return GenerateLaunchPlanRequest(
            book_id=uuid.uuid4(),
            book_title="The Great Adventure",
            genre="Fantasy",
            target_audience="Young adults ages 18-30 who enjoy epic fantasy",
            launch_date=datetime(2025, 6, 1, tzinfo=UTC),
            budget=500.0,
            goals=["1000 copies sold first month", "50 reviews"],
        )

    @pytest.mark.asyncio
    async def test_generate_plan_creates_three_phases(
        self, planner: LaunchPlanner, gen_request: GenerateLaunchPlanRequest
    ):
        plan = await planner.generate_plan(gen_request)

        assert plan.title == "Launch Plan: The Great Adventure"
        assert len(plan.phases) == 3
        assert plan.phases[0].phase_type == LaunchPhaseType.PRE_LAUNCH
        assert plan.phases[1].phase_type == LaunchPhaseType.LAUNCH_WEEK
        assert plan.phases[2].phase_type == LaunchPhaseType.POST_LAUNCH

    @pytest.mark.asyncio
    async def test_generate_plan_pre_launch_has_correct_tasks(
        self, planner: LaunchPlanner, gen_request: GenerateLaunchPlanRequest
    ):
        plan = await planner.generate_plan(gen_request)
        pre_launch = plan.phases[0]

        assert len(pre_launch.tasks) == len(PRE_LAUNCH_TASKS)
        for task in pre_launch.tasks:
            assert task.status == PhaseTaskStatus.PENDING
            assert task.due_date is not None

    @pytest.mark.asyncio
    async def test_generate_plan_launch_week_has_correct_tasks(
        self, planner: LaunchPlanner, gen_request: GenerateLaunchPlanRequest
    ):
        plan = await planner.generate_plan(gen_request)
        launch_week = plan.phases[1]

        assert len(launch_week.tasks) == len(LAUNCH_WEEK_TASKS)

    @pytest.mark.asyncio
    async def test_generate_plan_post_launch_has_correct_tasks(
        self, planner: LaunchPlanner, gen_request: GenerateLaunchPlanRequest
    ):
        plan = await planner.generate_plan(gen_request)
        post_launch = plan.phases[2]

        assert len(post_launch.tasks) == len(POST_LAUNCH_TASKS)

    @pytest.mark.asyncio
    async def test_generate_plan_dates_are_relative_to_launch(
        self, planner: LaunchPlanner, gen_request: GenerateLaunchPlanRequest
    ):
        plan = await planner.generate_plan(gen_request)
        launch_date = gen_request.launch_date

        # Pre-launch starts 4 weeks before
        pre_launch = plan.phases[0]
        assert pre_launch.start_date == launch_date - timedelta(weeks=4)

        # Launch week starts on launch day
        launch_week = plan.phases[1]
        assert launch_week.start_date == launch_date

        # Post-launch starts 7 days after
        post_launch = plan.phases[2]
        assert post_launch.start_date == launch_date + timedelta(days=7)

    @pytest.mark.asyncio
    async def test_generate_plan_includes_genre_and_audience(
        self, planner: LaunchPlanner, gen_request: GenerateLaunchPlanRequest
    ):
        plan = await planner.generate_plan(gen_request)

        assert plan.genre == "Fantasy"
        assert plan.target_audience == gen_request.target_audience
        assert plan.budget == 500.0

    @pytest.mark.asyncio
    async def test_generate_plan_with_no_budget(self, planner: LaunchPlanner):
        request = GenerateLaunchPlanRequest(
            book_id=uuid.uuid4(),
            book_title="Budget Free Book",
            genre="Non-Fiction",
            target_audience="General readers",
            launch_date=datetime(2025, 7, 1, tzinfo=UTC),
        )
        plan = await planner.generate_plan(request)

        assert plan.budget is None
        assert len(plan.phases) == 3

    @pytest.mark.asyncio
    async def test_generate_plan_with_ai_falls_back_to_template(
        self, planner: LaunchPlanner, gen_request: GenerateLaunchPlanRequest
    ):
        """AI generation should fall back to template when LLM is unavailable."""
        with patch.object(
            planner,
            "_call_llm_for_plan",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM unavailable"),
        ):
            plan = await planner.generate_plan_with_ai(gen_request)

        assert plan.title is not None
        assert len(plan.phases) == 3

    def test_build_tasks_from_template(self):
        launch_date = datetime(2025, 6, 1, tzinfo=UTC)
        tasks = _build_tasks_from_template(PRE_LAUNCH_TASKS, launch_date)

        assert len(tasks) == len(PRE_LAUNCH_TASKS)
        # First task should be 28 days before launch
        assert tasks[0].due_date == launch_date + timedelta(days=-28)
        assert tasks[0].order_index == 0

    def test_build_plan_prompt(self, planner: LaunchPlanner):
        request = GenerateLaunchPlanRequest(
            book_id=uuid.uuid4(),
            book_title="Test Book",
            genre="Romance",
            target_audience="Adult readers",
            launch_date=datetime(2025, 8, 1, tzinfo=UTC),
            goals=["Best seller"],
            additional_context="This is a debut novel",
        )
        prompt = planner._build_plan_prompt(request)

        assert "Test Book" in prompt
        assert "Romance" in prompt
        assert "Adult readers" in prompt
        assert "Best seller" in prompt
        assert "debut novel" in prompt


# ---------------------------------------------------------------------------
# EmailBuilder Tests
# ---------------------------------------------------------------------------


class TestEmailBuilder:
    """Tests for the email sequence builder."""

    @pytest.fixture
    def builder(self) -> EmailBuilder:
        return EmailBuilder()

    def test_build_launch_sequence_has_four_emails(self, builder: EmailBuilder):
        sequence = builder.build_launch_sequence(
            sequence_name="Test Launch",
            book_title="My Book",
            author_name="Jane Author",
            launch_date=datetime(2025, 6, 1, tzinfo=UTC),
        )

        assert sequence.name == "Test Launch"
        assert len(sequence.emails) == 4

    def test_build_launch_sequence_email_types(self, builder: EmailBuilder):
        sequence = builder.build_launch_sequence(
            sequence_name="Test Launch",
            book_title="My Book",
            author_name="Jane Author",
            launch_date=datetime(2025, 6, 1, tzinfo=UTC),
        )

        types = [e.template_type for e in sequence.emails]
        assert EmailTemplateType.WELCOME in types
        assert EmailTemplateType.LAUNCH_ANNOUNCEMENT in types
        assert EmailTemplateType.FOLLOW_UP in types
        assert EmailTemplateType.REVIEW_REQUEST in types

    def test_build_launch_sequence_has_delays(self, builder: EmailBuilder):
        sequence = builder.build_launch_sequence(
            sequence_name="Test",
            book_title="My Book",
            author_name="Jane",
            launch_date=datetime(2025, 6, 1, tzinfo=UTC),
        )

        delays = [e.delay_days for e in sequence.emails]
        # Welcome (0), Launch (7), Follow-up (12), Review request (21)
        assert delays == [0, 7, 12, 21]

    def test_build_launch_sequence_stores_settings(self, builder: EmailBuilder):
        sequence = builder.build_launch_sequence(
            sequence_name="Test",
            book_title="Great Book",
            author_name="Author",
            launch_date=datetime(2025, 6, 1, tzinfo=UTC),
            buy_link="https://amazon.com/dp/1234",
        )

        assert sequence.settings is not None
        assert sequence.settings["book_title"] == "Great Book"
        assert sequence.settings["buy_link"] == "https://amazon.com/dp/1234"

    def test_build_custom_sequence(self, builder: EmailBuilder):
        templates = [
            {
                "subject": "Hello",
                "body_html": "<p>Hi {name}</p>",
                "body_text": "Hi {name}",
                "delay_days": 0,
                "template_type": "custom",
            },
            {
                "subject": "Follow up",
                "body_html": "<p>Just checking in</p>",
                "delay_days": 3,
                "template_type": "custom",
            },
        ]

        sequence = builder.build_custom_sequence(
            name="Custom Sequence",
            templates=templates,
            description="A custom sequence",
            trigger_event="user.signup",
        )

        assert sequence.name == "Custom Sequence"
        assert len(sequence.emails) == 2
        assert sequence.trigger_event == "user.signup"

    def test_personalize_email(self):
        result = EmailBuilder.personalize_email(
            template_html="<p>Hi {reader_name}, check out {book_title}!</p>",
            template_text="Hi {reader_name}, check out {book_title}!",
            subject="{book_title} is here!",
            personalization={
                "reader_name": "Alice",
                "book_title": "The Great Novel",
            },
        )

        assert result["subject"] == "The Great Novel is here!"
        assert "Alice" in result["body_html"]
        assert "The Great Novel" in result["body_text"]

    def test_extract_personalization_fields(self):
        template = {
            "subject": "Hello {reader_name}",
            "body_html": "<p>{book_title} by {author_name}</p>",
            "body_text": "{book_title} by {author_name} for {reader_name}",
        }
        fields = _extract_personalization_fields(template)

        assert "reader_name" in fields
        assert "book_title" in fields
        assert "author_name" in fields


# ---------------------------------------------------------------------------
# SocialContentGenerator Tests
# ---------------------------------------------------------------------------


class TestSocialContentGenerator:
    """Tests for the social media content generator."""

    @pytest.fixture
    def generator(self) -> SocialContentGenerator:
        return SocialContentGenerator()

    @pytest.fixture
    def social_request(self) -> GenerateSocialContentRequest:
        return GenerateSocialContentRequest(
            book_title="The Great Adventure",
            genre="Fantasy",
            target_audience="Young adults",
            book_description="An epic tale of courage and discovery in a magical world.",
            platforms=[SocialPlatform.TWITTER, SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM],
            tone="exciting",
            num_posts_per_platform=3,
        )

    @pytest.mark.asyncio
    async def test_generate_content_creates_posts_for_each_platform(
        self, generator: SocialContentGenerator, social_request: GenerateSocialContentRequest
    ):
        posts = await generator.generate_content(social_request)

        platforms_found = {p.platform for p in posts}
        assert SocialPlatform.TWITTER in platforms_found
        assert SocialPlatform.FACEBOOK in platforms_found
        assert SocialPlatform.INSTAGRAM in platforms_found

    @pytest.mark.asyncio
    async def test_generate_content_respects_num_posts_per_platform(
        self, generator: SocialContentGenerator, social_request: GenerateSocialContentRequest
    ):
        posts = await generator.generate_content(social_request)

        twitter_posts = [p for p in posts if p.platform == SocialPlatform.TWITTER]
        assert len(twitter_posts) == 3

    @pytest.mark.asyncio
    async def test_twitter_posts_respect_character_limit(
        self, generator: SocialContentGenerator, social_request: GenerateSocialContentRequest
    ):
        posts = await generator.generate_content(social_request)

        twitter_posts = [p for p in posts if p.platform == SocialPlatform.TWITTER]
        for post in twitter_posts:
            assert len(post.content) <= 280

    @pytest.mark.asyncio
    async def test_posts_include_hashtags(
        self, generator: SocialContentGenerator, social_request: GenerateSocialContentRequest
    ):
        posts = await generator.generate_content(social_request)

        for post in posts:
            assert post.hashtags is not None
            assert len(post.hashtags) > 0

    @pytest.mark.asyncio
    async def test_generate_for_single_platform(self, generator: SocialContentGenerator):
        request = GenerateSocialContentRequest(
            book_title="Solo Platform Book",
            genre="Mystery",
            target_audience="Thriller fans",
            book_description="A gripping mystery that will keep you guessing.",
            platforms=[SocialPlatform.TWITTER],
            num_posts_per_platform=2,
        )
        posts = await generator.generate_content(request)

        assert all(p.platform == SocialPlatform.TWITTER for p in posts)
        assert len(posts) == 2

    @pytest.mark.asyncio
    async def test_generate_with_launch_plan_id(self, generator: SocialContentGenerator):
        plan_id = uuid.uuid4()
        request = GenerateSocialContentRequest(
            book_title="Linked Book",
            genre="Romance",
            target_audience="Romance readers",
            book_description="A heartwarming love story.",
            platforms=[SocialPlatform.FACEBOOK],
            num_posts_per_platform=1,
            launch_plan_id=plan_id,
        )
        posts = await generator.generate_content(request)

        assert len(posts) >= 1
        assert posts[0].launch_plan_id == plan_id

    def test_genre_to_hashtag(self):
        assert _genre_to_hashtag("Science Fiction") == "ScienceFiction"
        assert _genre_to_hashtag("Self-Help") == "SelfHelp"
        assert _genre_to_hashtag("Fantasy") == "Fantasy"

    @pytest.mark.asyncio
    async def test_generate_with_ai_falls_back_to_template(
        self, generator: SocialContentGenerator, social_request: GenerateSocialContentRequest
    ):
        with patch.object(
            generator,
            "_call_llm_for_content",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM unavailable"),
        ):
            posts = await generator.generate_content_with_ai(social_request)

        # Should fall back and still produce posts
        assert len(posts) > 0


# ---------------------------------------------------------------------------
# Task Template Tests
# ---------------------------------------------------------------------------


class TestTaskTemplates:
    """Tests for task template data integrity."""

    def test_pre_launch_tasks_have_negative_offsets(self):
        for task in PRE_LAUNCH_TASKS:
            assert task["offset_days"] < 0, f"Pre-launch task '{task['title']}' should have negative offset"

    def test_launch_week_tasks_have_non_negative_offsets(self):
        for task in LAUNCH_WEEK_TASKS:
            assert task["offset_days"] >= 0
            assert task["offset_days"] <= 6

    def test_post_launch_tasks_have_positive_offsets(self):
        for task in POST_LAUNCH_TASKS:
            assert task["offset_days"] > 0

    def test_all_tasks_have_required_fields(self):
        all_tasks = PRE_LAUNCH_TASKS + LAUNCH_WEEK_TASKS + POST_LAUNCH_TASKS
        for task in all_tasks:
            assert "title" in task
            assert "description" in task
            assert "offset_days" in task
            assert len(task["title"]) > 0
            assert len(task["description"]) > 0
