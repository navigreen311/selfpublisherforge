"""FastAPI router for Marketing & Launch Command module.

Provides endpoints for:
- Launch plan generation and management
- Email sequence CRUD and sending
- Social media content generation and calendar
- ARC campaign management
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.marketing.arc_manager import ARCManager
from app.modules.marketing.email_builder import EmailBuilder
from app.modules.marketing.launch_planner import LaunchPlanner
from app.modules.marketing.schemas import (
    ARCCampaignCreate,
    ARCCampaignResponse,
    ARCCampaignSummary,
    ARCCampaignUpdate,
    EmailSequenceCreate,
    EmailSequenceResponse,
    EmailSequenceSummary,
    EmailSequenceUpdate,
    GenerateLaunchPlanRequest,
    GenerateSocialContentRequest,
    LaunchPlanCreate,
    LaunchPlanResponse,
    LaunchPlanSummary,
    LaunchPlanUpdate,
    SendARCRequest,
    SocialCalendarResponse,
    SocialPostResponse,
    TriggerEmailSendRequest,
)
from app.modules.marketing.service import MarketingService
from app.modules.marketing.social_generator import SocialContentGenerator
from app.core.contracts import PaginatedResponse, SuccessResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Launch Plan Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/launch-plan/generate",
    response_model=SuccessResponse[LaunchPlanResponse],
    status_code=status.HTTP_201_CREATED,
    summary="AI-generate a launch plan",
    description="AI-generate a book launch plan with milestones, channels, and budget allocation.",
)
async def generate_launch_plan(
    request: GenerateLaunchPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    planner = LaunchPlanner()
    plan_data = await planner.generate_plan(request)

    service = MarketingService(db)
    plan = await service.save_generated_plan(
        org_id=current_user["org_id"],
        user_id=current_user["user_id"],
        plan_data=plan_data,
        ai_metadata={"generator": "template", "request": request.model_dump(mode="json")},
    )

    return {"data": plan}


@router.get(
    "/launch-plans",
    response_model=PaginatedResponse[LaunchPlanSummary],
    summary="List launch plans",
    description="List launch plans with optional status filter and pagination.",
)
async def list_launch_plans(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    from app.models.marketing import LaunchPlanStatus

    plan_status = None
    if status_filter:
        try:
            plan_status = LaunchPlanStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    service = MarketingService(db)
    plans, total = await service.list_launch_plans(
        org_id=current_user["org_id"],
        status=plan_status,
        limit=limit,
        offset=offset,
    )

    return {
        "items": plans,
        "total_count": total,
        "has_more": (offset + limit) < total,
    }


@router.get(
    "/launch-plans/{plan_id}",
    response_model=SuccessResponse[LaunchPlanResponse],
    summary="Get launch plan detail",
    description="Get full launch plan details including milestones and tasks.",
)
async def get_launch_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    service = MarketingService(db)
    plan = await service.get_launch_plan(plan_id, current_user["org_id"])
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Launch plan not found",
        )
    return {"data": plan}


@router.patch(
    "/launch-plans/{plan_id}",
    response_model=SuccessResponse[LaunchPlanResponse],
    summary="Update launch plan",
    description="Update launch plan status, milestones, or settings.",
)
async def update_launch_plan(
    plan_id: uuid.UUID,
    data: LaunchPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    service = MarketingService(db)
    plan = await service.update_launch_plan(plan_id, current_user["org_id"], data)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Launch plan not found",
        )
    return {"data": plan}


# ---------------------------------------------------------------------------
# Email Sequence Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/email-sequences",
    response_model=SuccessResponse[EmailSequenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create email sequence",
    description="Create a new email marketing sequence with subject lines and body content.",
)
async def create_email_sequence(
    data: EmailSequenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    service = MarketingService(db)
    sequence = await service.create_email_sequence(current_user["org_id"], current_user["user_id"], data)
    return {"data": sequence}


@router.get(
    "/email-sequences",
    response_model=PaginatedResponse[EmailSequenceSummary],
    summary="List email sequences",
    description="List email sequences with optional status filter and pagination.",
)
async def list_email_sequences(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    from app.models.marketing import EmailSequenceStatus

    seq_status = None
    if status_filter:
        try:
            seq_status = EmailSequenceStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    service = MarketingService(db)
    sequences, total = await service.list_email_sequences(
        org_id=current_user["org_id"],
        status=seq_status,
        limit=limit,
        offset=offset,
    )

    return {
        "items": sequences,
        "total_count": total,
        "has_more": (offset + limit) < total,
    }


@router.patch(
    "/email-sequences/{sequence_id}",
    response_model=SuccessResponse[EmailSequenceResponse],
    summary="Update email sequence",
    description="Update an email sequence's content, schedule, or status.",
)
async def update_email_sequence(
    sequence_id: uuid.UUID,
    data: EmailSequenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    service = MarketingService(db)
    sequence = await service.update_email_sequence(sequence_id, current_user["org_id"], data)
    if not sequence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email sequence not found",
        )
    return {"data": sequence}


@router.post(
    "/email-sequences/{sequence_id}/send",
    response_model=SuccessResponse[EmailSequenceResponse],
    summary="Trigger email sequence send",
    description="Trigger sending an email sequence to specified recipients.",
)
async def trigger_email_send(
    sequence_id: uuid.UUID,
    data: TriggerEmailSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    service = MarketingService(db)
    sequence = await service.trigger_email_send(
        sequence_id=sequence_id,
        org_id=current_user["org_id"],
        recipient_emails=data.recipient_emails,
        personalization=data.personalization,
        schedule_at=data.schedule_at,
    )
    if not sequence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email sequence not found",
        )
    return {"data": sequence}


# ---------------------------------------------------------------------------
# Social Media Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/social/generate",
    response_model=SuccessResponse[list[SocialPostResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Generate social media content",
    description="AI-generate social media posts for multiple platforms from book data.",
)
async def generate_social_content(
    request: GenerateSocialContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    generator = SocialContentGenerator()
    posts_data = await generator.generate_content(request)

    service = MarketingService(db)
    posts = await service.create_social_posts_batch(
        org_id=current_user["org_id"],
        user_id=current_user["user_id"],
        posts_data=posts_data,
        ai_metadata={"generator": "template", "request": request.model_dump(mode="json")},
    )

    return {"data": posts}


@router.get(
    "/social/calendar",
    response_model=SocialCalendarResponse,
    summary="Get social media calendar",
    description="Get scheduled social media posts filtered by date range and platform.",
)
async def get_social_calendar(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    platform: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    from app.models.marketing import SocialPlatform

    social_platform = None
    if platform:
        try:
            social_platform = SocialPlatform(platform)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}",
            )

    service = MarketingService(db)
    calendar_data = await service.get_social_calendar(
        org_id=current_user["org_id"],
        start_date=start_date,
        end_date=end_date,
        platform=social_platform,
    )

    return calendar_data


# ---------------------------------------------------------------------------
# ARC Campaign Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/arc",
    response_model=SuccessResponse[ARCCampaignResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create ARC campaign",
    description="Create an Advanced Reader Copy campaign for pre-launch review gathering.",
)
async def create_arc_campaign(
    data: ARCCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    service = MarketingService(db)
    campaign = await service.create_arc_campaign(current_user["org_id"], current_user["user_id"], data)
    return {"data": campaign}


@router.get(
    "/arc",
    response_model=PaginatedResponse[ARCCampaignSummary],
    summary="List ARC campaigns",
    description="List ARC campaigns with optional status filter and pagination.",
)
async def list_arc_campaigns(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    from app.models.marketing import ARCCampaignStatus

    arc_status = None
    if status_filter:
        try:
            arc_status = ARCCampaignStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    service = MarketingService(db)
    campaigns, total = await service.list_arc_campaigns(
        org_id=current_user["org_id"],
        status=arc_status,
        limit=limit,
        offset=offset,
    )

    return {
        "items": campaigns,
        "total_count": total,
        "has_more": (offset + limit) < total,
    }


@router.post(
    "/arc/{campaign_id}/send",
    response_model=SuccessResponse[ARCCampaignResponse],
    summary="Send ARC copies to recipients",
    description="Send ARC copies to selected recipients with an optional custom message.",
)
async def send_arc_copies(
    campaign_id: uuid.UUID,
    data: SendARCRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    service = MarketingService(db)
    campaign = await service.send_arc_copies(
        campaign_id=campaign_id,
        org_id=current_user["org_id"],
        recipient_ids=data.recipient_ids,
        custom_message=data.custom_message,
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ARC campaign not found",
        )
    return {"data": campaign}
