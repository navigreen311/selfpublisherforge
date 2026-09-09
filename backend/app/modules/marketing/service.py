"""Core service for Marketing & Launch Command module.

Handles CRUD for launch plans, email sequences, social posts, and ARC campaigns.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.marketing import (
    ARCCampaign,
    ARCCampaignStatus,
    ARCRecipient,
    ARCRecipientStatus,
    EmailSequence,
    EmailSequenceStatus,
    EmailTemplate,
    LaunchPhase,
    LaunchPlan,
    LaunchPlanStatus,
    PhaseTask,
    SocialPlatform,
    SocialPost,
    SocialPostStatus,
)
from app.modules.marketing.schemas import (
    ARCCampaignCreate,
    EmailSequenceCreate,
    EmailSequenceUpdate,
    LaunchPlanCreate,
    LaunchPlanUpdate,
    SocialPostCreate,
)


class MarketingService:
    """Service for marketing and launch operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Launch Plans
    # ------------------------------------------------------------------

    async def create_launch_plan(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: LaunchPlanCreate,
    ) -> LaunchPlan:
        """Create a new launch plan with optional phases and tasks."""
        plan = LaunchPlan(
            org_id=org_id,
            book_id=data.book_id,
            title=data.title,
            description=data.description,
            launch_date=data.launch_date,
            genre=data.genre,
            target_audience=data.target_audience,
            budget=data.budget,
            goals=data.goals,
            created_by=user_id,
            status=LaunchPlanStatus.DRAFT,
        )
        self.db.add(plan)
        await self.db.flush()

        for phase_data in data.phases:
            phase = LaunchPhase(
                launch_plan_id=plan.id,
                phase_type=phase_data.phase_type,
                name=phase_data.name,
                description=phase_data.description,
                start_date=phase_data.start_date,
                end_date=phase_data.end_date,
                order_index=phase_data.order_index,
            )
            self.db.add(phase)
            await self.db.flush()

            for task_data in phase_data.tasks:
                task = PhaseTask(
                    phase_id=phase.id,
                    title=task_data.title,
                    description=task_data.description,
                    status=task_data.status,
                    due_date=task_data.due_date,
                    order_index=task_data.order_index,
                )
                self.db.add(task)

        await self.db.flush()
        return await self.get_launch_plan(plan.id, org_id)

    async def get_launch_plan(self, plan_id: uuid.UUID, org_id: uuid.UUID) -> LaunchPlan | None:
        """Get a launch plan with all phases and tasks."""
        stmt = (
            select(LaunchPlan)
            .options(selectinload(LaunchPlan.phases).selectinload(LaunchPhase.tasks))
            .where(
                and_(
                    LaunchPlan.id == plan_id,
                    LaunchPlan.org_id == org_id,
                    LaunchPlan.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_launch_plans(
        self,
        org_id: uuid.UUID,
        status: LaunchPlanStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[LaunchPlan], int]:
        """List launch plans with optional status filter."""
        base = select(LaunchPlan).where(
            and_(
                LaunchPlan.org_id == org_id,
                LaunchPlan.deleted_at.is_(None),
            )
        )
        if status:
            base = base.where(LaunchPlan.status == status)

        # Count
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Fetch
        stmt = base.order_by(LaunchPlan.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        plans = list(result.scalars().all())

        return plans, total

    async def update_launch_plan(
        self,
        plan_id: uuid.UUID,
        org_id: uuid.UUID,
        data: LaunchPlanUpdate,
    ) -> LaunchPlan | None:
        """Update an existing launch plan."""
        plan = await self.get_launch_plan(plan_id, org_id)
        if not plan:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)

        await self.db.flush()
        return await self.get_launch_plan(plan_id, org_id)

    async def save_generated_plan(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        plan_data: LaunchPlanCreate,
        ai_metadata: dict[str, Any] | None = None,
    ) -> LaunchPlan:
        """Save an AI-generated launch plan."""
        plan = await self.create_launch_plan(org_id, user_id, plan_data)
        if ai_metadata:
            plan.ai_metadata = ai_metadata
            await self.db.flush()
        return await self.get_launch_plan(plan.id, org_id)

    # ------------------------------------------------------------------
    # Email Sequences
    # ------------------------------------------------------------------

    async def create_email_sequence(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: EmailSequenceCreate,
    ) -> EmailSequence:
        """Create an email sequence with templates."""
        sequence = EmailSequence(
            org_id=org_id,
            launch_plan_id=data.launch_plan_id,
            name=data.name,
            description=data.description,
            trigger_event=data.trigger_event,
            settings=data.settings,
            created_by=user_id,
            status=EmailSequenceStatus.DRAFT,
        )
        self.db.add(sequence)
        await self.db.flush()

        for email_data in data.emails:
            template = EmailTemplate(
                sequence_id=sequence.id,
                template_type=email_data.template_type,
                subject=email_data.subject,
                body_html=email_data.body_html,
                body_text=email_data.body_text,
                delay_days=email_data.delay_days,
                delay_hours=email_data.delay_hours,
                order_index=email_data.order_index,
                personalization_fields=email_data.personalization_fields,
            )
            self.db.add(template)

        await self.db.flush()
        return await self.get_email_sequence(sequence.id, org_id)

    async def get_email_sequence(self, sequence_id: uuid.UUID, org_id: uuid.UUID) -> EmailSequence | None:
        """Get an email sequence with all templates."""
        stmt = (
            select(EmailSequence)
            .options(selectinload(EmailSequence.emails))
            .where(
                and_(
                    EmailSequence.id == sequence_id,
                    EmailSequence.org_id == org_id,
                    EmailSequence.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_email_sequences(
        self,
        org_id: uuid.UUID,
        status: EmailSequenceStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[EmailSequence], int]:
        """List email sequences."""
        base = select(EmailSequence).where(
            and_(
                EmailSequence.org_id == org_id,
                EmailSequence.deleted_at.is_(None),
            )
        )
        if status:
            base = base.where(EmailSequence.status == status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            base.options(selectinload(EmailSequence.emails))
            .order_by(EmailSequence.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        sequences = list(result.scalars().all())

        return sequences, total

    async def update_email_sequence(
        self,
        sequence_id: uuid.UUID,
        org_id: uuid.UUID,
        data: EmailSequenceUpdate,
    ) -> EmailSequence | None:
        """Update an email sequence."""
        sequence = await self.get_email_sequence(sequence_id, org_id)
        if not sequence:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sequence, field, value)

        await self.db.flush()
        return await self.get_email_sequence(sequence_id, org_id)

    async def trigger_email_send(
        self,
        sequence_id: uuid.UUID,
        org_id: uuid.UUID,
        recipient_emails: list[str],
        personalization: dict[str, str] | None = None,
        schedule_at: datetime | None = None,
    ) -> EmailSequence | None:
        """Trigger sending of an email sequence to specified recipients."""
        sequence = await self.get_email_sequence(sequence_id, org_id)
        if not sequence:
            return None

        sequence.status = EmailSequenceStatus.ACTIVE
        sequence.recipient_count = len(recipient_emails)

        # Mark templates as scheduled
        for template in sequence.emails:
            template.send_status = "scheduled"
            if schedule_at:
                template.scheduled_at = schedule_at

        await self.db.flush()
        return await self.get_email_sequence(sequence_id, org_id)

    # ------------------------------------------------------------------
    # Social Posts
    # ------------------------------------------------------------------

    async def create_social_post(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: SocialPostCreate,
    ) -> SocialPost:
        """Create a social media post."""
        post = SocialPost(
            org_id=org_id,
            launch_plan_id=data.launch_plan_id,
            platform=data.platform,
            content=data.content,
            media_urls=data.media_urls,
            hashtags=data.hashtags,
            scheduled_at=data.scheduled_at,
            status=SocialPostStatus.DRAFT,
            created_by=user_id,
        )
        self.db.add(post)
        await self.db.flush()
        return post

    async def create_social_posts_batch(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        posts_data: list[SocialPostCreate],
        ai_metadata: dict[str, Any] | None = None,
    ) -> list[SocialPost]:
        """Create multiple social media posts (e.g., from AI generation)."""
        posts = []
        for data in posts_data:
            post = SocialPost(
                org_id=org_id,
                launch_plan_id=data.launch_plan_id,
                platform=data.platform,
                content=data.content,
                media_urls=data.media_urls,
                hashtags=data.hashtags,
                scheduled_at=data.scheduled_at,
                status=SocialPostStatus.DRAFT,
                created_by=user_id,
                ai_metadata=ai_metadata,
            )
            self.db.add(post)
            posts.append(post)

        await self.db.flush()
        return posts

    async def get_social_calendar(
        self,
        org_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        platform: SocialPlatform | None = None,
    ) -> dict[str, Any]:
        """Get social media calendar with aggregated stats."""
        base = select(SocialPost).where(
            and_(
                SocialPost.org_id == org_id,
                SocialPost.deleted_at.is_(None),
            )
        )
        if start_date:
            base = base.where(SocialPost.scheduled_at >= start_date)
        if end_date:
            base = base.where(SocialPost.scheduled_at <= end_date)
        if platform:
            base = base.where(SocialPost.platform == platform)

        stmt = base.order_by(SocialPost.scheduled_at.asc())
        result = await self.db.execute(stmt)
        posts = list(result.scalars().all())

        # Aggregate stats
        total_scheduled = sum(1 for p in posts if p.status == SocialPostStatus.SCHEDULED)
        total_published = sum(1 for p in posts if p.status == SocialPostStatus.PUBLISHED)
        total_draft = sum(1 for p in posts if p.status == SocialPostStatus.DRAFT)

        platform_counts: dict[str, int] = {}
        for post in posts:
            platform_name = post.platform.value
            platform_counts[platform_name] = platform_counts.get(platform_name, 0) + 1

        return {
            "posts": posts,
            "total_scheduled": total_scheduled,
            "total_published": total_published,
            "total_draft": total_draft,
            "platforms": platform_counts,
        }

    # ------------------------------------------------------------------
    # ARC Campaigns
    # ------------------------------------------------------------------

    async def create_arc_campaign(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ARCCampaignCreate,
    ) -> ARCCampaign:
        """Create an ARC campaign with recipients."""
        campaign = ARCCampaign(
            org_id=org_id,
            book_id=data.book_id,
            launch_plan_id=data.launch_plan_id,
            name=data.name,
            description=data.description,
            book_file_url=data.book_file_url,
            cover_letter=data.cover_letter,
            deadline=data.deadline,
            status=ARCCampaignStatus.DRAFT,
            total_copies=len(data.recipients),
            created_by=user_id,
        )
        self.db.add(campaign)
        await self.db.flush()

        for recipient_data in data.recipients:
            recipient = ARCRecipient(
                campaign_id=campaign.id,
                name=recipient_data.name,
                email=recipient_data.email,
                notes=recipient_data.notes,
                status=ARCRecipientStatus.PENDING,
            )
            self.db.add(recipient)

        await self.db.flush()
        return await self.get_arc_campaign(campaign.id, org_id)

    async def get_arc_campaign(self, campaign_id: uuid.UUID, org_id: uuid.UUID) -> ARCCampaign | None:
        """Get an ARC campaign with all recipients."""
        stmt = (
            select(ARCCampaign)
            .options(selectinload(ARCCampaign.recipients))
            .where(
                and_(
                    ARCCampaign.id == campaign_id,
                    ARCCampaign.org_id == org_id,
                    ARCCampaign.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_arc_campaigns(
        self,
        org_id: uuid.UUID,
        status: ARCCampaignStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ARCCampaign], int]:
        """List ARC campaigns."""
        base = select(ARCCampaign).where(
            and_(
                ARCCampaign.org_id == org_id,
                ARCCampaign.deleted_at.is_(None),
            )
        )
        if status:
            base = base.where(ARCCampaign.status == status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            base.options(selectinload(ARCCampaign.recipients))
            .order_by(ARCCampaign.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        campaigns = list(result.scalars().all())

        return campaigns, total

    async def send_arc_copies(
        self,
        campaign_id: uuid.UUID,
        org_id: uuid.UUID,
        recipient_ids: list[uuid.UUID] | None = None,
        custom_message: str | None = None,
    ) -> ARCCampaign | None:
        """Mark ARC copies as sent to recipients."""
        campaign = await self.get_arc_campaign(campaign_id, org_id)
        if not campaign:
            return None

        campaign.status = ARCCampaignStatus.SENDING
        now = datetime.now(tz=UTC)

        sent_count = 0
        for recipient in campaign.recipients:
            if recipient_ids and recipient.id not in recipient_ids:
                continue
            if recipient.status == ARCRecipientStatus.PENDING:
                recipient.status = ARCRecipientStatus.SENT
                recipient.sent_at = now
                sent_count += 1

        campaign.sent_copies += sent_count

        if campaign.sent_copies >= campaign.total_copies:
            campaign.status = ARCCampaignStatus.COMPLETED
        else:
            campaign.status = ARCCampaignStatus.ACTIVE

        await self.db.flush()
        return await self.get_arc_campaign(campaign_id, org_id)
