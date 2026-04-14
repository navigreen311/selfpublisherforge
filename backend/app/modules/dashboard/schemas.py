"""Pydantic schemas for the dashboard aggregator endpoint."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DashboardStats(BaseModel):
    total_projects: int = 0
    in_progress: int = 0
    published: int = 0
    monthly_revenue: Decimal = Decimal("0")


class RevenuePoint(BaseModel):
    date: date
    amount: Decimal = Decimal("0")


class ActivePipelineItem(BaseModel):
    id: UUID
    title: str
    stage: str | None = None
    progress_pct: int = 0
    due_date: datetime | None = None


class RecentActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action: str
    description: str | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    created_at: datetime


class AIInsight(BaseModel):
    id: str
    type: str
    message: str
    action_url: str | None = None
    priority: str = "info"


class UpcomingDeadline(BaseModel):
    id: UUID
    title: str
    date: date
    source_type: str
    source_id: UUID


class DashboardResponse(BaseModel):
    stats: DashboardStats
    revenue_trend: list[RevenuePoint]
    active_pipelines: list[ActivePipelineItem]
    recent_activity: list[RecentActivityItem]
    ai_insights: list[AIInsight]
    upcoming_deadlines: list[UpcomingDeadline]
