"""Webhook event catalog.

Central registry of supported event types and their human-readable metadata.
Adding new event types here is the single source of truth consulted by both
the backend dispatch service and the frontend event picker UI.
"""
from __future__ import annotations

from typing import TypedDict


class EventSpec(TypedDict):
    type: str
    category: str
    description: str
    example_payload: dict


EVENT_CATALOG: list[EventSpec] = [
    # --- Books & Content ---
    {
        "type": "book.created",
        "category": "Books & Content",
        "description": "A new book is created",
        "example_payload": {
            "book_id": "uuid",
            "title": "string",
            "book_type": "cookbook",
            "status": "draft",
        },
    },
    {
        "type": "book.published",
        "category": "Books & Content",
        "description": "A book is published to a distributor",
        "example_payload": {
            "book_id": "uuid",
            "title": "string",
            "distributor": "kdp",
            "asin": "B0XXXXXXXX",
        },
    },
    {
        "type": "book.status_changed",
        "category": "Books & Content",
        "description": "Book status changes (draft -> in_progress, etc.)",
        "example_payload": {
            "book_id": "uuid",
            "old_status": "draft",
            "new_status": "in_progress",
        },
    },
    {
        "type": "book.exported",
        "category": "Books & Content",
        "description": "A book PDF/file is exported",
        "example_payload": {"book_id": "uuid", "format": "pdf", "url": "string"},
    },
    {
        "type": "book.deleted",
        "category": "Books & Content",
        "description": "A book is deleted",
        "example_payload": {"book_id": "uuid"},
    },
    # --- Reviews & Analytics ---
    {
        "type": "review.received",
        "category": "Reviews & Analytics",
        "description": "New review detected",
        "example_payload": {
            "book_id": "uuid",
            "rating": 5,
            "reviewer": "Jane S.",
        },
    },
    {
        "type": "review.negative",
        "category": "Reviews & Analytics",
        "description": "Negative review (<=2 stars)",
        "example_payload": {"book_id": "uuid", "rating": 2, "body": "string"},
    },
    {
        "type": "analytics.daily",
        "category": "Reviews & Analytics",
        "description": "Daily sales summary (midnight UTC)",
        "example_payload": {
            "date": "2026-04-13",
            "units": 42,
            "revenue_cents": 12345,
        },
    },
    {
        "type": "analytics.bsr_change",
        "category": "Reviews & Analytics",
        "description": "Significant BSR movement (>20%)",
        "example_payload": {
            "book_id": "uuid",
            "old_bsr": 10000,
            "new_bsr": 5000,
            "delta_pct": -50.0,
        },
    },
    # --- Pipeline & Tasks ---
    {
        "type": "pipeline.stage_changed",
        "category": "Pipeline & Tasks",
        "description": "Pipeline moves to new stage",
        "example_payload": {
            "pipeline_id": "uuid",
            "old_stage": "editing",
            "new_stage": "formatting",
        },
    },
    {
        "type": "pipeline.completed",
        "category": "Pipeline & Tasks",
        "description": "Pipeline reaches final stage",
        "example_payload": {"pipeline_id": "uuid"},
    },
    {
        "type": "task.completed",
        "category": "Pipeline & Tasks",
        "description": "A pipeline task is completed",
        "example_payload": {"task_id": "uuid", "pipeline_id": "uuid"},
    },
    {
        "type": "task.overdue",
        "category": "Pipeline & Tasks",
        "description": "A task passes its due date",
        "example_payload": {"task_id": "uuid", "due_date": "2026-04-01"},
    },
    # --- Generation & Export ---
    {
        "type": "generation.completed",
        "category": "Generation & Export",
        "description": "AI generation job finishes",
        "example_payload": {"job_id": "uuid", "kind": "chapter"},
    },
    {
        "type": "batch.completed",
        "category": "Generation & Export",
        "description": "Batch factory job completes",
        "example_payload": {"batch_id": "uuid", "count": 10},
    },
    {
        "type": "export.completed",
        "category": "Generation & Export",
        "description": "Export file is ready",
        "example_payload": {
            "export_id": "uuid",
            "book_id": "uuid",
            "format": "epub",
            "url": "string",
        },
    },
    # --- Pricing & Marketing ---
    {
        "type": "price.changed",
        "category": "Pricing & Marketing",
        "description": "Price change executed",
        "example_payload": {
            "book_id": "uuid",
            "old_price_cents": 999,
            "new_price_cents": 1299,
        },
    },
    {
        "type": "campaign.launched",
        "category": "Pricing & Marketing",
        "description": "Marketing campaign goes live",
        "example_payload": {"campaign_id": "uuid", "channel": "amazon_ads"},
    },
]

EVENT_TYPES: set[str] = {e["type"] for e in EVENT_CATALOG}


def is_valid_event(event_type: str) -> bool:
    return event_type in EVENT_TYPES
