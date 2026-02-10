"""Pydantic v2 schemas for the Marketing & Launch Command module."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.marketing import (
    ARCCampaignStatus,
    ARCRecipientStatus,
    EmailSendStatus,
    EmailSequenceStatus,
    EmailTemplateType,
    LaunchPhaseType,
    LaunchPlanStatus,
    PhaseTaskStatus,
    SocialPlatform,
    SocialPostStatus,
)


# ---------------------------------------------------------------------------
# Phase Task Schemas
# ---------------------------------------------------------------------------

class PhaseTaskBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: str | None = None
    status: PhaseTaskStatus = PhaseTaskStatus.PENDING
    due_date: datetime | None = None
    order_index: int = 0


class PhaseTaskCreate(PhaseTaskBase):
    pass


class PhaseTaskUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    status: PhaseTaskStatus | None = None
    due_date: datetime | None = None
    order_index: int | None = None


class PhaseTaskResponse(PhaseTaskBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    phase_id: UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Launch Phase Schemas
# ---------------------------------------------------------------------------

class LaunchPhaseBase(BaseModel):
    phase_type: LaunchPhaseType
    name: str = Field(..., max_length=300)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    order_index: int = 0


class LaunchPhaseCreate(LaunchPhaseBase):
    tasks: list[PhaseTaskCreate] = []


class LaunchPhaseUpdate(BaseModel):
    name: str | None = Field(None, max_length=300)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    order_index: int | None = None


class LaunchPhaseResponse(LaunchPhaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    launch_plan_id: UUID
    tasks: list[PhaseTaskResponse] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Launch Plan Schemas
# ---------------------------------------------------------------------------

class LaunchPlanBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: str | None = None
    launch_date: datetime | None = None
    genre: str | None = Field(None, max_length=200)
    target_audience: str | None = None
    budget: float | None = None
    goals: dict[str, Any] | None = None


class LaunchPlanCreate(LaunchPlanBase):
    book_id: UUID
    phases: list[LaunchPhaseCreate] = []


class LaunchPlanUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    status: LaunchPlanStatus | None = None
    launch_date: datetime | None = None
    genre: str | None = Field(None, max_length=200)
    target_audience: str | None = None
    budget: float | None = None
    goals: dict[str, Any] | None = None


class LaunchPlanResponse(LaunchPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID
    status: LaunchPlanStatus
    ai_metadata: dict[str, Any] | None = None
    created_by: UUID
    phases: list[LaunchPhaseResponse] = []
    created_at: datetime
    updated_at: datetime


class LaunchPlanSummary(BaseModel):
    """Lightweight launch plan for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID
    title: str
    status: LaunchPlanStatus
    launch_date: datetime | None = None
    genre: str | None = None
    created_at: datetime
    updated_at: datetime


class GenerateLaunchPlanRequest(BaseModel):
    """Request body for AI launch plan generation."""
    book_id: UUID
    book_title: str = Field(..., max_length=500)
    genre: str = Field(..., max_length=200)
    target_audience: str
    launch_date: datetime
    budget: float | None = None
    goals: list[str] = []
    additional_context: str | None = None


# ---------------------------------------------------------------------------
# Email Template Schemas
# ---------------------------------------------------------------------------

class EmailTemplateBase(BaseModel):
    template_type: EmailTemplateType = EmailTemplateType.CUSTOM
    subject: str = Field(..., max_length=1000)
    body_html: str | None = None
    body_text: str | None = None
    delay_days: int = 0
    delay_hours: int = 0
    order_index: int = 0
    personalization_fields: list[str] | None = None


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    template_type: EmailTemplateType | None = None
    subject: str | None = Field(None, max_length=1000)
    body_html: str | None = None
    body_text: str | None = None
    delay_days: int | None = None
    delay_hours: int | None = None
    order_index: int | None = None
    personalization_fields: list[str] | None = None


class EmailTemplateResponse(EmailTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence_id: UUID
    send_status: EmailSendStatus
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Email Sequence Schemas
# ---------------------------------------------------------------------------

class EmailSequenceBase(BaseModel):
    name: str = Field(..., max_length=500)
    description: str | None = None
    trigger_event: str | None = Field(None, max_length=200)
    settings: dict[str, Any] | None = None


class EmailSequenceCreate(EmailSequenceBase):
    launch_plan_id: UUID | None = None
    emails: list[EmailTemplateCreate] = []


class EmailSequenceUpdate(BaseModel):
    name: str | None = Field(None, max_length=500)
    description: str | None = None
    status: EmailSequenceStatus | None = None
    trigger_event: str | None = Field(None, max_length=200)
    settings: dict[str, Any] | None = None


class EmailSequenceResponse(EmailSequenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    launch_plan_id: UUID | None = None
    status: EmailSequenceStatus
    recipient_count: int
    sent_count: int
    open_rate: float | None = None
    click_rate: float | None = None
    created_by: UUID
    emails: list[EmailTemplateResponse] = []
    created_at: datetime
    updated_at: datetime


class EmailSequenceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    status: EmailSequenceStatus
    recipient_count: int
    sent_count: int
    created_at: datetime
    updated_at: datetime


class TriggerEmailSendRequest(BaseModel):
    """Request to trigger sending an email sequence."""
    recipient_emails: list[str] = Field(..., min_length=1)
    personalization: dict[str, str] | None = None
    schedule_at: datetime | None = None


# ---------------------------------------------------------------------------
# Social Post Schemas
# ---------------------------------------------------------------------------

class SocialPostBase(BaseModel):
    platform: SocialPlatform
    content: str
    media_urls: list[str] | None = None
    hashtags: list[str] | None = None
    scheduled_at: datetime | None = None


class SocialPostCreate(SocialPostBase):
    launch_plan_id: UUID | None = None


class SocialPostUpdate(BaseModel):
    content: str | None = None
    media_urls: list[str] | None = None
    hashtags: list[str] | None = None
    scheduled_at: datetime | None = None
    status: SocialPostStatus | None = None


class SocialPostResponse(SocialPostBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    launch_plan_id: UUID | None = None
    status: SocialPostStatus
    published_at: datetime | None = None
    engagement_metrics: dict[str, Any] | None = None
    ai_metadata: dict[str, Any] | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class GenerateSocialContentRequest(BaseModel):
    """Request body for AI social media content generation."""
    book_title: str = Field(..., max_length=500)
    genre: str = Field(..., max_length=200)
    target_audience: str
    book_description: str
    platforms: list[SocialPlatform] = [
        SocialPlatform.TWITTER,
        SocialPlatform.FACEBOOK,
        SocialPlatform.INSTAGRAM,
    ]
    tone: str = "professional"
    num_posts_per_platform: int = Field(3, ge=1, le=10)
    launch_plan_id: UUID | None = None


class SocialCalendarResponse(BaseModel):
    """Aggregated view of scheduled social posts for a calendar."""
    posts: list[SocialPostResponse]
    total_scheduled: int
    total_published: int
    total_draft: int
    platforms: dict[str, int]  # platform -> count


# ---------------------------------------------------------------------------
# ARC Recipient Schemas
# ---------------------------------------------------------------------------

class ARCRecipientBase(BaseModel):
    name: str = Field(..., max_length=300)
    email: str = Field(..., max_length=500)
    notes: str | None = None


class ARCRecipientCreate(ARCRecipientBase):
    pass


class ARCRecipientResponse(ARCRecipientBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID
    status: ARCRecipientStatus
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    review_url: str | None = None
    review_received_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# ARC Campaign Schemas
# ---------------------------------------------------------------------------

class ARCCampaignBase(BaseModel):
    name: str = Field(..., max_length=500)
    description: str | None = None
    book_file_url: str | None = None
    cover_letter: str | None = None
    deadline: datetime | None = None


class ARCCampaignCreate(ARCCampaignBase):
    book_id: UUID
    launch_plan_id: UUID | None = None
    recipients: list[ARCRecipientCreate] = []


class ARCCampaignUpdate(BaseModel):
    name: str | None = Field(None, max_length=500)
    description: str | None = None
    status: ARCCampaignStatus | None = None
    book_file_url: str | None = None
    cover_letter: str | None = None
    deadline: datetime | None = None


class ARCCampaignResponse(ARCCampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID
    launch_plan_id: UUID | None = None
    status: ARCCampaignStatus
    total_copies: int
    sent_copies: int
    reviews_received: int
    settings: dict[str, Any] | None = None
    created_by: UUID
    recipients: list[ARCRecipientResponse] = []
    created_at: datetime
    updated_at: datetime


class ARCCampaignSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    book_id: UUID
    name: str
    status: ARCCampaignStatus
    total_copies: int
    sent_copies: int
    reviews_received: int
    deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SendARCRequest(BaseModel):
    """Request to send ARC copies to recipients."""
    recipient_ids: list[UUID] | None = None  # None means send to all pending
    custom_message: str | None = None
