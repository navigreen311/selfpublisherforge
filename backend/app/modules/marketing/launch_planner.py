"""AI-powered launch plan generation.

Generates comprehensive book launch plans with three phases:
- Pre-Launch (4 weeks before launch)
- Launch Week
- Post-Launch (2 weeks after)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from app.config import get_settings
from app.models.marketing import LaunchPhaseType, PhaseTaskStatus
from app.modules.marketing.schemas import (
    GenerateLaunchPlanRequest,
    LaunchPhaseCreate,
    LaunchPlanCreate,
    PhaseTaskCreate,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Pre-built task templates by phase
# ---------------------------------------------------------------------------

PRE_LAUNCH_TASKS = [
    {
        "title": "Set up author website / landing page",
        "description": "Create or update your author website with a dedicated page for the upcoming book launch.",
        "offset_days": -28,
    },
    {
        "title": "Build or update email subscriber list",
        "description": "Grow your email list through lead magnets, social media, and existing contacts.",
        "offset_days": -28,
    },
    {
        "title": "Create book cover reveal campaign",
        "description": "Plan and schedule a cover reveal across social media platforms.",
        "offset_days": -21,
    },
    {
        "title": "Set up pre-order on Amazon KDP",
        "description": "Configure pre-order listing with metadata, description, and categories.",
        "offset_days": -21,
    },
    {
        "title": "Send ARC copies to reviewers",
        "description": "Distribute advance review copies to your ARC team and book bloggers.",
        "offset_days": -14,
    },
    {
        "title": "Schedule social media content calendar",
        "description": "Create and schedule 4 weeks of social media content across all platforms.",
        "offset_days": -14,
    },
    {
        "title": "Prepare launch-day email sequence",
        "description": "Draft the launch-day email with buy links, bonuses, and call to action.",
        "offset_days": -7,
    },
    {
        "title": "Reach out to podcast hosts / bloggers for interviews",
        "description": "Pitch guest appearances and interviews to boost visibility.",
        "offset_days": -7,
    },
    {
        "title": "Final review of book metadata and keywords",
        "description": "Double-check title, subtitle, categories, keywords for discoverability.",
        "offset_days": -3,
    },
]

LAUNCH_WEEK_TASKS = [
    {
        "title": "Publish the book (go live)",
        "description": "Make the book available for purchase on all platforms.",
        "offset_days": 0,
    },
    {
        "title": "Send launch announcement email",
        "description": "Email your entire list with the launch announcement and buy links.",
        "offset_days": 0,
    },
    {
        "title": "Post launch announcement on all social media",
        "description": "Publish coordinated launch posts on Twitter, Facebook, Instagram.",
        "offset_days": 0,
    },
    {
        "title": "Engage with early readers and reviews",
        "description": "Respond to early reviews, share on social media, thank ARC reviewers.",
        "offset_days": 1,
    },
    {
        "title": "Run promotional pricing or giveaway",
        "description": "Consider a limited-time discount or free giveaway to boost initial sales rank.",
        "offset_days": 2,
    },
    {
        "title": "Monitor sales rank and adjust strategy",
        "description": "Track Amazon rank, sales, and reviews. Adjust ad spend and promotion.",
        "offset_days": 3,
    },
    {
        "title": "Send follow-up email with bonus content",
        "description": "Email readers with bonus content, character art, or behind-the-scenes.",
        "offset_days": 5,
    },
]

POST_LAUNCH_TASKS = [
    {
        "title": "Request reviews from readers",
        "description": "Send review request emails to purchasers and ARC recipients.",
        "offset_days": 7,
    },
    {
        "title": "Analyze launch performance metrics",
        "description": "Review sales data, email open rates, social engagement, ad ROI.",
        "offset_days": 8,
    },
    {
        "title": "Set up ongoing advertising campaigns",
        "description": "Configure Amazon Ads, Facebook Ads, or BookBub ads for sustained visibility.",
        "offset_days": 10,
    },
    {
        "title": "Plan next content / sequel announcement",
        "description": "Tease upcoming work to maintain reader engagement and momentum.",
        "offset_days": 12,
    },
    {
        "title": "Update book listing based on feedback",
        "description": "Refine description, keywords, or categories based on reader feedback and data.",
        "offset_days": 14,
    },
]


def _build_tasks_from_template(
    tasks_template: list[dict[str, Any]],
    launch_date: datetime,
) -> list[PhaseTaskCreate]:
    """Build PhaseTaskCreate list from a template with date offsets."""
    tasks = []
    for idx, tmpl in enumerate(tasks_template):
        due = launch_date + timedelta(days=tmpl["offset_days"])
        tasks.append(
            PhaseTaskCreate(
                title=tmpl["title"],
                description=tmpl["description"],
                status=PhaseTaskStatus.PENDING,
                due_date=due,
                order_index=idx,
            )
        )
    return tasks


class LaunchPlanner:
    """Generates comprehensive book launch plans using AI or templates."""

    async def generate_plan(
        self,
        request: GenerateLaunchPlanRequest,
    ) -> LaunchPlanCreate:
        """Generate a complete launch plan.

        Uses template-based generation with genre/audience customization.
        Can be extended to call an LLM for fully customized plans.
        """
        launch_date = request.launch_date

        # Build phases
        pre_launch_start = launch_date - timedelta(weeks=4)
        pre_launch_end = launch_date - timedelta(days=1)
        launch_start = launch_date
        launch_end = launch_date + timedelta(days=6)
        post_launch_start = launch_date + timedelta(days=7)
        post_launch_end = launch_date + timedelta(days=21)

        pre_launch_phase = LaunchPhaseCreate(
            phase_type=LaunchPhaseType.PRE_LAUNCH,
            name="Pre-Launch Phase (4 Weeks)",
            description=f"Build anticipation and prepare for the launch of '{request.book_title}'.",
            start_date=pre_launch_start,
            end_date=pre_launch_end,
            order_index=0,
            tasks=_build_tasks_from_template(PRE_LAUNCH_TASKS, launch_date),
        )

        launch_week_phase = LaunchPhaseCreate(
            phase_type=LaunchPhaseType.LAUNCH_WEEK,
            name="Launch Week",
            description=f"Execute the launch of '{request.book_title}' with maximum impact.",
            start_date=launch_start,
            end_date=launch_end,
            order_index=1,
            tasks=_build_tasks_from_template(LAUNCH_WEEK_TASKS, launch_date),
        )

        post_launch_phase = LaunchPhaseCreate(
            phase_type=LaunchPhaseType.POST_LAUNCH,
            name="Post-Launch Phase (2 Weeks)",
            description="Sustain momentum and capitalize on launch energy.",
            start_date=post_launch_start,
            end_date=post_launch_end,
            order_index=2,
            tasks=_build_tasks_from_template(POST_LAUNCH_TASKS, launch_date),
        )

        plan = LaunchPlanCreate(
            book_id=request.book_id,
            title=f"Launch Plan: {request.book_title}",
            description=(
                f"Comprehensive launch plan for '{request.book_title}' "
                f"({request.genre}) targeting {request.target_audience}."
            ),
            launch_date=launch_date,
            genre=request.genre,
            target_audience=request.target_audience,
            budget=request.budget,
            goals={"user_goals": request.goals} if request.goals else None,
            phases=[pre_launch_phase, launch_week_phase, post_launch_phase],
        )

        return plan

    async def generate_plan_with_ai(
        self,
        request: GenerateLaunchPlanRequest,
    ) -> LaunchPlanCreate:
        """Generate a launch plan using an LLM for fully customized content.

        Falls back to template-based generation if the LLM call fails.
        """
        try:
            return await self._call_llm_for_plan(request)
        except (OSError, ValueError, KeyError, RuntimeError, TypeError) as exc:
            logger.warning(
                "LLM-based plan generation failed (%s: %s), falling back to template",
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            return await self.generate_plan(request)

    async def _call_llm_for_plan(
        self,
        request: GenerateLaunchPlanRequest,
    ) -> LaunchPlanCreate:
        """Call the LLM to generate a customized launch plan.

        ASSUMPTION: anthropic SDK is configured and available.
        This method builds a prompt and parses the structured response.
        """
        prompt = self._build_plan_prompt(request)

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = await client.messages.create(
                model=settings.DEFAULT_LLM_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            content = message.content[0].text
            plan_data = json.loads(content)
            return self._parse_llm_response(request, plan_data)

        except ImportError:
            logger.warning("anthropic package not available, using template fallback")
            return await self.generate_plan(request)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return await self.generate_plan(request)

    def _build_plan_prompt(self, request: GenerateLaunchPlanRequest) -> str:
        """Build a detailed prompt for the LLM."""
        goals_text = ", ".join(request.goals) if request.goals else "maximize sales and reviews"
        budget_text = f"${request.budget}" if request.budget else "flexible"

        return f"""You are a book marketing expert. Generate a detailed launch plan for the following book:

Book Title: {request.book_title}
Genre: {request.genre}
Target Audience: {request.target_audience}
Launch Date: {request.launch_date.strftime("%Y-%m-%d")}
Budget: {budget_text}
Goals: {goals_text}
{f"Additional Context: {request.additional_context}" if request.additional_context else ""}

Create a structured launch plan with three phases:
1. Pre-Launch (4 weeks before launch) - 8-10 tasks
2. Launch Week - 6-8 tasks
3. Post-Launch (2 weeks after) - 5-7 tasks

For each task, provide:
- title: Short descriptive title
- description: Detailed instructions (2-3 sentences)
- offset_days: Number of days relative to launch date (negative for pre-launch)

Respond ONLY with valid JSON in this format:
{{
  "phases": [
    {{
      "phase_type": "pre_launch",
      "name": "Pre-Launch Phase",
      "description": "...",
      "tasks": [
        {{"title": "...", "description": "...", "offset_days": -28}}
      ]
    }}
  ]
}}"""

    def _parse_llm_response(
        self,
        request: GenerateLaunchPlanRequest,
        plan_data: dict[str, Any],
    ) -> LaunchPlanCreate:
        """Parse the LLM's JSON response into a LaunchPlanCreate."""
        launch_date = request.launch_date
        phases = []

        phase_type_map = {
            "pre_launch": LaunchPhaseType.PRE_LAUNCH,
            "launch_week": LaunchPhaseType.LAUNCH_WEEK,
            "post_launch": LaunchPhaseType.POST_LAUNCH,
        }

        for idx, phase_data in enumerate(plan_data.get("phases", [])):
            phase_type_str = phase_data.get("phase_type", "pre_launch")
            phase_type = phase_type_map.get(phase_type_str, LaunchPhaseType.PRE_LAUNCH)

            tasks = []
            for t_idx, task_data in enumerate(phase_data.get("tasks", [])):
                offset = task_data.get("offset_days", 0)
                tasks.append(
                    PhaseTaskCreate(
                        title=task_data["title"],
                        description=task_data.get("description"),
                        status=PhaseTaskStatus.PENDING,
                        due_date=launch_date + timedelta(days=offset),
                        order_index=t_idx,
                    )
                )

            # Calculate phase date ranges
            offsets = [t.get("offset_days", 0) for t in phase_data.get("tasks", [])]
            min_offset = min(offsets) if offsets else 0
            max_offset = max(offsets) if offsets else 0

            phases.append(
                LaunchPhaseCreate(
                    phase_type=phase_type,
                    name=phase_data.get("name", f"Phase {idx + 1}"),
                    description=phase_data.get("description"),
                    start_date=launch_date + timedelta(days=min_offset),
                    end_date=launch_date + timedelta(days=max_offset),
                    order_index=idx,
                    tasks=tasks,
                )
            )

        return LaunchPlanCreate(
            book_id=request.book_id,
            title=f"Launch Plan: {request.book_title}",
            description=(
                f"AI-generated launch plan for '{request.book_title}' "
                f"({request.genre}) targeting {request.target_audience}."
            ),
            launch_date=launch_date,
            genre=request.genre,
            target_audience=request.target_audience,
            budget=request.budget,
            goals={"user_goals": request.goals} if request.goals else None,
            phases=phases,
        )
