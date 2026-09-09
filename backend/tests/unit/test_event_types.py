"""Unit tests for app.core.event_types -- event enum, BaseEvent, and EventPublisher.

Validates that EventType covers all expected domains, BaseEvent serializes
correctly, and EventPublisher raises NotImplementedError as an abstract interface.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.core.event_types import BaseEvent, EventPublisher, EventType

# ---------------------------------------------------------------------------
# EventType enum
# ---------------------------------------------------------------------------


class TestEventType:
    """EventType is a str enum whose values use dot-notation domain prefixes."""

    # -- Auth events --

    def test_user_registered(self):
        assert EventType.USER_REGISTERED == "user.registered"
        assert EventType.USER_REGISTERED.value == "user.registered"

    def test_user_login(self):
        assert EventType.USER_LOGIN == "user.login"

    def test_user_logout(self):
        assert EventType.USER_LOGOUT == "user.logout"

    # -- Project events --

    def test_project_created(self):
        assert EventType.PROJECT_CREATED == "project.created"

    def test_project_updated(self):
        assert EventType.PROJECT_UPDATED == "project.updated"

    def test_book_created(self):
        assert EventType.BOOK_CREATED == "book.created"

    def test_book_status_changed(self):
        assert EventType.BOOK_STATUS_CHANGED == "book.status_changed"

    # -- AI events --

    def test_ai_generation_started(self):
        assert EventType.AI_GENERATION_STARTED == "ai.generation.started"

    def test_ai_generation_completed(self):
        assert EventType.AI_GENERATION_COMPLETED == "ai.generation.completed"

    def test_ai_generation_failed(self):
        assert EventType.AI_GENERATION_FAILED == "ai.generation.failed"

    # -- Publishing events --

    def test_book_validated(self):
        assert EventType.BOOK_VALIDATED == "publishing.validated"

    def test_book_uploaded(self):
        assert EventType.BOOK_UPLOADED == "publishing.uploaded"

    def test_listing_synced(self):
        assert EventType.LISTING_SYNCED == "publishing.listing_synced"

    # -- Marketing events --

    def test_campaign_created(self):
        assert EventType.CAMPAIGN_CREATED == "marketing.campaign.created"

    def test_campaign_updated(self):
        assert EventType.CAMPAIGN_UPDATED == "marketing.campaign.updated"

    # -- Agent events --

    def test_agent_task_started(self):
        assert EventType.AGENT_TASK_STARTED == "agent.task.started"

    def test_agent_task_completed(self):
        assert EventType.AGENT_TASK_COMPLETED == "agent.task.completed"

    def test_agent_task_failed(self):
        assert EventType.AGENT_TASK_FAILED == "agent.task.failed"

    def test_agent_budget_alert(self):
        assert EventType.AGENT_BUDGET_ALERT == "agent.budget.alert"

    # -- Analytics events --

    def test_metric_recorded(self):
        assert EventType.METRIC_RECORDED == "analytics.metric"

    def test_report_generated(self):
        assert EventType.REPORT_GENERATED == "analytics.report.generated"

    # -- Aggregate checks --

    def test_total_event_count(self):
        """Guard against accidental additions/removals."""
        assert len(EventType) == 21

    def test_all_values_are_strings(self):
        for member in EventType:
            assert isinstance(member.value, str)

    def test_is_str_enum(self):
        """EventType members can be used directly as strings."""
        assert isinstance(EventType.USER_LOGIN, str)
        assert EventType.USER_LOGIN == "user.login"

    def test_lookup_by_value(self):
        assert EventType("user.registered") is EventType.USER_REGISTERED
        assert EventType("ai.generation.failed") is EventType.AI_GENERATION_FAILED

    def test_lookup_invalid_value_raises(self):
        with pytest.raises(ValueError):
            EventType("nonexistent.event")

    def test_all_values_contain_dot(self):
        """All event type values follow domain.action dot-notation."""
        for member in EventType:
            assert "." in member.value, f"{member.name} value missing dot separator"

    def test_unique_values(self):
        values = [m.value for m in EventType]
        assert len(values) == len(set(values)), "Duplicate event type values found"

    def test_auth_domain_events(self):
        auth_events = [m for m in EventType if m.value.startswith("user.")]
        assert len(auth_events) == 3

    def test_ai_domain_events(self):
        ai_events = [m for m in EventType if m.value.startswith("ai.")]
        assert len(ai_events) == 3

    def test_agent_domain_events(self):
        agent_events = [m for m in EventType if m.value.startswith("agent.")]
        assert len(agent_events) == 4

    def test_publishing_domain_events(self):
        pub_events = [m for m in EventType if m.value.startswith("publishing.")]
        assert len(pub_events) == 3

    def test_marketing_domain_events(self):
        mkt_events = [m for m in EventType if m.value.startswith("marketing.")]
        assert len(mkt_events) == 2

    def test_analytics_domain_events(self):
        analytics_events = [m for m in EventType if m.value.startswith("analytics.")]
        assert len(analytics_events) == 2


# ---------------------------------------------------------------------------
# BaseEvent
# ---------------------------------------------------------------------------

_ORG_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
_ACTOR_ID = UUID("11111111-2222-3333-4444-555555555555")
_TIMESTAMP = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)


class TestBaseEvent:
    """BaseEvent is the envelope for all domain events."""

    def test_minimal_creation(self):
        event = BaseEvent(
            event_type=EventType.USER_REGISTERED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
        )
        assert event.event_type is EventType.USER_REGISTERED
        assert event.org_id == _ORG_ID
        assert event.actor_id == _ACTOR_ID
        assert event.timestamp == _TIMESTAMP
        assert event.actor_type == "user"
        assert event.data == {}

    def test_custom_actor_type(self):
        event = BaseEvent(
            event_type=EventType.AGENT_TASK_STARTED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            actor_type="agent",
            timestamp=_TIMESTAMP,
        )
        assert event.actor_type == "agent"

    def test_system_actor_type(self):
        event = BaseEvent(
            event_type=EventType.METRIC_RECORDED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            actor_type="system",
            timestamp=_TIMESTAMP,
        )
        assert event.actor_type == "system"

    def test_with_data_payload(self):
        data = {"book_id": str(uuid4()), "status": "published"}
        event = BaseEvent(
            event_type=EventType.BOOK_STATUS_CHANGED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
            data=data,
        )
        assert event.data == data
        assert event.data["status"] == "published"

    def test_with_nested_data(self):
        data = {
            "generation": {
                "model": "claude-sonnet-4-5-20250929",
                "tokens": 1500,
                "cost_usd": 0.03,
            },
            "tags": ["fiction", "sci-fi"],
        }
        event = BaseEvent(
            event_type=EventType.AI_GENERATION_COMPLETED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
            data=data,
        )
        assert event.data["generation"]["model"] == "claude-sonnet-4-5-20250929"
        assert event.data["tags"] == ["fiction", "sci-fi"]

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            BaseEvent()  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            BaseEvent(event_type=EventType.USER_LOGIN)  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            BaseEvent(
                event_type=EventType.USER_LOGIN,
                org_id=_ORG_ID,
            )  # type: ignore[call-arg]

    def test_invalid_event_type_raises(self):
        with pytest.raises(ValidationError):
            BaseEvent(
                event_type="not.a.valid.event",
                org_id=_ORG_ID,
                actor_id=_ACTOR_ID,
                timestamp=_TIMESTAMP,
            )

    def test_invalid_uuid_raises(self):
        with pytest.raises(ValidationError):
            BaseEvent(
                event_type=EventType.USER_LOGIN,
                org_id="not-a-uuid",
                actor_id=_ACTOR_ID,
                timestamp=_TIMESTAMP,
            )

    def test_serialization_to_dict(self):
        event = BaseEvent(
            event_type=EventType.PROJECT_CREATED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
            data={"project_name": "My Book"},
        )
        d = event.model_dump()
        assert d["event_type"] == EventType.PROJECT_CREATED
        assert d["org_id"] == _ORG_ID
        assert d["actor_id"] == _ACTOR_ID
        assert d["actor_type"] == "user"
        assert d["data"] == {"project_name": "My Book"}

    def test_serialization_to_json(self):
        event = BaseEvent(
            event_type=EventType.CAMPAIGN_CREATED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
            data={"budget": 500},
        )
        raw = event.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["event_type"] == "marketing.campaign.created"
        assert parsed["data"]["budget"] == 500

    def test_json_round_trip(self):
        event = BaseEvent(
            event_type=EventType.BOOK_UPLOADED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
            data={"platform": "kdp", "asin": "B0EXAMPLE"},
        )
        raw = event.model_dump_json()
        restored = BaseEvent.model_validate_json(raw)
        assert restored.event_type is EventType.BOOK_UPLOADED
        assert restored.org_id == _ORG_ID
        assert restored.actor_id == _ACTOR_ID
        assert restored.data["asin"] == "B0EXAMPLE"

    def test_event_type_value_in_json(self):
        """When serialized to JSON the event_type should be the string value."""
        event = BaseEvent(
            event_type=EventType.AI_GENERATION_STARTED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
        )
        raw = event.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["event_type"] == "ai.generation.started"

    def test_uuid_fields_are_uuid_type(self):
        event = BaseEvent(
            event_type=EventType.USER_REGISTERED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
        )
        assert isinstance(event.org_id, UUID)
        assert isinstance(event.actor_id, UUID)

    def test_accepts_uuid_strings(self):
        """Pydantic should coerce valid UUID strings."""
        event = BaseEvent(
            event_type=EventType.USER_LOGIN,
            org_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            actor_id="11111111-2222-3333-4444-555555555555",
            timestamp=_TIMESTAMP,
        )
        assert event.org_id == _ORG_ID
        assert event.actor_id == _ACTOR_ID

    def test_each_event_type_accepted(self):
        """Every EventType member can be used to create a BaseEvent."""
        for et in EventType:
            event = BaseEvent(
                event_type=et,
                org_id=_ORG_ID,
                actor_id=_ACTOR_ID,
                timestamp=_TIMESTAMP,
            )
            assert event.event_type is et


# ---------------------------------------------------------------------------
# EventPublisher
# ---------------------------------------------------------------------------


class TestEventPublisher:
    """EventPublisher is an abstract interface (raises NotImplementedError)."""

    @pytest.mark.asyncio
    async def test_publish_raises_not_implemented(self):
        publisher = EventPublisher()
        event = BaseEvent(
            event_type=EventType.USER_REGISTERED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
        )
        with pytest.raises(NotImplementedError):
            await publisher.publish(event)

    @pytest.mark.asyncio
    async def test_subclass_can_override_publish(self):
        """A concrete implementation should be able to override publish."""
        published_events: list[BaseEvent] = []

        class InMemoryPublisher(EventPublisher):
            async def publish(self, event: BaseEvent) -> None:
                published_events.append(event)

        publisher = InMemoryPublisher()
        event = BaseEvent(
            event_type=EventType.BOOK_CREATED,
            org_id=_ORG_ID,
            actor_id=_ACTOR_ID,
            timestamp=_TIMESTAMP,
            data={"title": "Test Book"},
        )
        await publisher.publish(event)
        assert len(published_events) == 1
        assert published_events[0].data["title"] == "Test Book"

    @pytest.mark.asyncio
    async def test_subclass_publish_multiple_events(self):
        published: list[BaseEvent] = []

        class InMemoryPublisher(EventPublisher):
            async def publish(self, event: BaseEvent) -> None:
                published.append(event)

        publisher = InMemoryPublisher()
        event_types = [
            EventType.USER_REGISTERED,
            EventType.PROJECT_CREATED,
            EventType.BOOK_CREATED,
        ]
        for et in event_types:
            await publisher.publish(
                BaseEvent(
                    event_type=et,
                    org_id=_ORG_ID,
                    actor_id=_ACTOR_ID,
                    timestamp=_TIMESTAMP,
                )
            )
        assert len(published) == 3
        assert [e.event_type for e in published] == event_types

    def test_publisher_is_instantiable(self):
        """The base class can be instantiated (it is not truly abstract)."""
        publisher = EventPublisher()
        assert publisher is not None
