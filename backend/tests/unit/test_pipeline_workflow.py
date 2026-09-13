"""Unit tests for the Production Pipeline workflow engine.

Tests dependency resolution, status transitions, cycle detection,
critical path computation, and deadline helpers.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.modules.production_pipeline.models import (
    PipelineStatus,
    PipelineTask,
    TaskStatus,
    TaskType,
)
from app.modules.production_pipeline.workflow import (
    PIPELINE_TRANSITIONS,
    TASK_TRANSITIONS,
    WorkflowError,
    build_dependency_graph,
    compute_blocked_tasks,
    compute_critical_path,
    compute_task_progress,
    detect_cycle,
    get_overdue_tasks,
    get_ready_tasks,
    get_upcoming_deadlines,
    topological_sort,
    validate_pipeline_transition,
    validate_task_transition,
)

# ── Helpers to create mock tasks ──────────────────────────────────────────


def _make_task(
    task_id: str | None = None,
    status: TaskStatus = TaskStatus.PENDING,
    depends_on: list[str] | None = None,
    due_date: datetime | None = None,
    completed_at: datetime | None = None,
    task_type: TaskType = TaskType.WRITING,
) -> MagicMock:
    """Create a mock PipelineTask with the required attributes."""
    mock = MagicMock(spec=PipelineTask)
    mock.id = uuid.UUID(task_id) if task_id else uuid.uuid4()
    mock.status = status
    mock.depends_on = depends_on or []
    mock.due_date = due_date
    mock.completed_at = completed_at
    mock.type = task_type
    mock.created_at = datetime.now(UTC)
    return mock


# ── Pipeline Status Transition Tests ──────────────────────────────────────


class TestPipelineTransitions:
    def test_draft_to_active_is_valid(self):
        validate_pipeline_transition(PipelineStatus.DRAFT, PipelineStatus.ACTIVE)

    def test_draft_to_cancelled_is_valid(self):
        validate_pipeline_transition(PipelineStatus.DRAFT, PipelineStatus.CANCELLED)

    def test_draft_to_completed_is_invalid(self):
        with pytest.raises(WorkflowError, match="Cannot transition pipeline"):
            validate_pipeline_transition(PipelineStatus.DRAFT, PipelineStatus.COMPLETED)

    def test_active_to_paused_is_valid(self):
        validate_pipeline_transition(PipelineStatus.ACTIVE, PipelineStatus.PAUSED)

    def test_active_to_completed_is_valid(self):
        validate_pipeline_transition(PipelineStatus.ACTIVE, PipelineStatus.COMPLETED)

    def test_paused_to_active_is_valid(self):
        validate_pipeline_transition(PipelineStatus.PAUSED, PipelineStatus.ACTIVE)

    def test_completed_to_active_is_invalid(self):
        with pytest.raises(WorkflowError):
            validate_pipeline_transition(PipelineStatus.COMPLETED, PipelineStatus.ACTIVE)

    def test_cancelled_is_terminal(self):
        with pytest.raises(WorkflowError):
            validate_pipeline_transition(PipelineStatus.CANCELLED, PipelineStatus.ACTIVE)

    def test_all_transitions_are_documented(self):
        """Ensure every PipelineStatus has an entry in PIPELINE_TRANSITIONS."""
        for status in PipelineStatus:
            assert status in PIPELINE_TRANSITIONS


# ── Task Status Transition Tests ──────────────────────────────────────────


class TestTaskTransitions:
    def test_pending_to_in_progress(self):
        validate_task_transition(TaskStatus.PENDING, TaskStatus.IN_PROGRESS)

    def test_pending_to_blocked(self):
        validate_task_transition(TaskStatus.PENDING, TaskStatus.BLOCKED)

    def test_in_progress_to_completed(self):
        validate_task_transition(TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED)

    def test_pending_to_completed_is_invalid(self):
        with pytest.raises(WorkflowError, match="Cannot transition task"):
            validate_task_transition(TaskStatus.PENDING, TaskStatus.COMPLETED)

    def test_completed_is_terminal(self):
        with pytest.raises(WorkflowError):
            validate_task_transition(TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS)

    def test_cancelled_is_terminal(self):
        with pytest.raises(WorkflowError):
            validate_task_transition(TaskStatus.CANCELLED, TaskStatus.PENDING)

    def test_blocked_to_in_progress(self):
        validate_task_transition(TaskStatus.BLOCKED, TaskStatus.IN_PROGRESS)

    def test_all_transitions_are_documented(self):
        for status in TaskStatus:
            assert status in TASK_TRANSITIONS


# ── Dependency Graph Tests ────────────────────────────────────────────────


class TestDependencyGraph:
    def test_empty_tasks(self):
        adj, in_deg = build_dependency_graph([])
        assert adj == {}
        assert in_deg == {}

    def test_single_task_no_deps(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        adj, in_deg = build_dependency_graph([t1])
        assert in_deg[str(t1.id)] == 0

    def test_linear_chain(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        t3 = _make_task(
            "00000000-0000-0000-0000-000000000003",
            depends_on=["00000000-0000-0000-0000-000000000002"],
        )
        adj, in_deg = build_dependency_graph([t1, t2, t3])
        assert in_deg[str(t1.id)] == 0
        assert in_deg[str(t2.id)] == 1
        assert in_deg[str(t3.id)] == 1

    def test_ignores_unknown_dependency(self):
        """Dependencies referencing non-existent task IDs are ignored."""
        t1 = _make_task(
            "00000000-0000-0000-0000-000000000001",
            depends_on=["00000000-0000-0000-0000-999999999999"],
        )
        adj, in_deg = build_dependency_graph([t1])
        assert in_deg[str(t1.id)] == 0


# ── Topological Sort Tests ────────────────────────────────────────────────


class TestTopologicalSort:
    def test_empty(self):
        assert topological_sort([]) == []

    def test_single_task(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        result = topological_sort([t1])
        assert result == [str(t1.id)]

    def test_linear_chain_order(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        t3 = _make_task(
            "00000000-0000-0000-0000-000000000003",
            depends_on=["00000000-0000-0000-0000-000000000002"],
        )
        result = topological_sort([t1, t2, t3])
        assert result.index(str(t1.id)) < result.index(str(t2.id))
        assert result.index(str(t2.id)) < result.index(str(t3.id))

    def test_diamond_dependency(self):
        """A -> B, A -> C, B -> D, C -> D."""
        a = _make_task("00000000-0000-0000-0000-00000000000a")
        b = _make_task(
            "00000000-0000-0000-0000-00000000000b",
            depends_on=["00000000-0000-0000-0000-00000000000a"],
        )
        c = _make_task(
            "00000000-0000-0000-0000-00000000000c",
            depends_on=["00000000-0000-0000-0000-00000000000a"],
        )
        d = _make_task(
            "00000000-0000-0000-0000-00000000000d",
            depends_on=[
                "00000000-0000-0000-0000-00000000000b",
                "00000000-0000-0000-0000-00000000000c",
            ],
        )
        result = topological_sort([a, b, c, d])
        assert result.index(str(a.id)) < result.index(str(b.id))
        assert result.index(str(a.id)) < result.index(str(c.id))
        assert result.index(str(b.id)) < result.index(str(d.id))
        assert result.index(str(c.id)) < result.index(str(d.id))

    def test_cycle_detection(self):
        t1 = _make_task(
            "00000000-0000-0000-0000-000000000001",
            depends_on=["00000000-0000-0000-0000-000000000002"],
        )
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        with pytest.raises(WorkflowError, match="Cycle detected"):
            topological_sort([t1, t2])


# ── Cycle Detection Tests ────────────────────────────────────────────────


class TestCycleDetection:
    def test_no_cycle(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        assert detect_cycle([t1, t2]) is False

    def test_with_cycle(self):
        t1 = _make_task(
            "00000000-0000-0000-0000-000000000001",
            depends_on=["00000000-0000-0000-0000-000000000002"],
        )
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        assert detect_cycle([t1, t2]) is True

    def test_three_node_cycle(self):
        t1 = _make_task(
            "00000000-0000-0000-0000-000000000001",
            depends_on=["00000000-0000-0000-0000-000000000003"],
        )
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        t3 = _make_task(
            "00000000-0000-0000-0000-000000000003",
            depends_on=["00000000-0000-0000-0000-000000000002"],
        )
        assert detect_cycle([t1, t2, t3]) is True


# ── Ready Tasks Tests ────────────────────────────────────────────────────


class TestReadyTasks:
    def test_task_with_no_deps_is_ready(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        ready = get_ready_tasks([t1])
        assert len(ready) == 1

    def test_task_with_completed_dep_is_ready(self):
        t1 = _make_task(
            "00000000-0000-0000-0000-000000000001",
            status=TaskStatus.COMPLETED,
        )
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        ready = get_ready_tasks([t1, t2])
        assert len(ready) == 1
        assert str(ready[0].id) == "00000000-0000-0000-0000-000000000002"

    def test_task_with_uncompleted_dep_is_not_ready(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        ready = get_ready_tasks([t1, t2])
        assert len(ready) == 1
        assert str(ready[0].id) == "00000000-0000-0000-0000-000000000001"

    def test_in_progress_task_is_not_in_ready(self):
        t1 = _make_task(
            "00000000-0000-0000-0000-000000000001",
            status=TaskStatus.IN_PROGRESS,
        )
        ready = get_ready_tasks([t1])
        assert len(ready) == 0

    def test_blocked_task_becomes_ready_when_deps_complete(self):
        t1 = _make_task(
            "00000000-0000-0000-0000-000000000001",
            status=TaskStatus.COMPLETED,
        )
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            status=TaskStatus.BLOCKED,
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        ready = get_ready_tasks([t1, t2])
        assert len(ready) == 1
        assert str(ready[0].id) == "00000000-0000-0000-0000-000000000002"


# ── Blocked Tasks Tests ──────────────────────────────────────────────────


class TestBlockedTasks:
    def test_task_with_pending_dep_is_blocked(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        blocked = compute_blocked_tasks([t1, t2])
        assert len(blocked) == 1
        assert str(blocked[0].id) == "00000000-0000-0000-0000-000000000002"

    def test_task_with_all_deps_completed_is_not_blocked(self):
        t1 = _make_task(
            "00000000-0000-0000-0000-000000000001",
            status=TaskStatus.COMPLETED,
        )
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        blocked = compute_blocked_tasks([t1, t2])
        assert len(blocked) == 0

    def test_no_deps_means_not_blocked(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        blocked = compute_blocked_tasks([t1])
        assert len(blocked) == 0


# ── Critical Path Tests ──────────────────────────────────────────────────


class TestCriticalPath:
    def test_empty_tasks(self):
        assert compute_critical_path([]) == []

    def test_single_task(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        path = compute_critical_path([t1])
        assert path == [str(t1.id)]

    def test_linear_chain(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        t2 = _make_task(
            "00000000-0000-0000-0000-000000000002",
            depends_on=["00000000-0000-0000-0000-000000000001"],
        )
        t3 = _make_task(
            "00000000-0000-0000-0000-000000000003",
            depends_on=["00000000-0000-0000-0000-000000000002"],
        )
        path = compute_critical_path([t1, t2, t3])
        assert len(path) == 3
        assert path[0] == str(t1.id)
        assert path[1] == str(t2.id)
        assert path[2] == str(t3.id)

    def test_parallel_branches_picks_longer(self):
        """
        A -> B -> C -> D (length 4)
        A -> E (length 2)
        Critical path should be A->B->C->D.
        """
        a = _make_task("00000000-0000-0000-0000-00000000000a")
        b = _make_task(
            "00000000-0000-0000-0000-00000000000b",
            depends_on=["00000000-0000-0000-0000-00000000000a"],
        )
        c = _make_task(
            "00000000-0000-0000-0000-00000000000c",
            depends_on=["00000000-0000-0000-0000-00000000000b"],
        )
        d = _make_task(
            "00000000-0000-0000-0000-00000000000d",
            depends_on=["00000000-0000-0000-0000-00000000000c"],
        )
        e = _make_task(
            "00000000-0000-0000-0000-00000000000e",
            depends_on=["00000000-0000-0000-0000-00000000000a"],
        )
        path = compute_critical_path([a, b, c, d, e])
        assert len(path) == 4
        assert path == [str(a.id), str(b.id), str(c.id), str(d.id)]


# ── Deadline Helper Tests ────────────────────────────────────────────────


class TestDeadlineHelpers:
    def test_overdue_tasks(self):
        now = datetime(2025, 6, 1, tzinfo=UTC)
        past = datetime(2025, 5, 15, tzinfo=UTC)
        future = datetime(2025, 7, 1, tzinfo=UTC)

        t1 = _make_task("00000000-0000-0000-0000-000000000001", due_date=past)
        t2 = _make_task("00000000-0000-0000-0000-000000000002", due_date=future)
        t3 = _make_task(
            "00000000-0000-0000-0000-000000000003",
            due_date=past,
            status=TaskStatus.COMPLETED,
        )

        overdue = get_overdue_tasks([t1, t2, t3], now=now)
        assert len(overdue) == 1
        assert str(overdue[0].id) == "00000000-0000-0000-0000-000000000001"

    def test_no_overdue_when_no_due_dates(self):
        t1 = _make_task("00000000-0000-0000-0000-000000000001")
        overdue = get_overdue_tasks([t1])
        assert len(overdue) == 0

    def test_upcoming_deadlines(self):
        now = datetime(2025, 6, 1, 12, 0, tzinfo=UTC)
        within = now + timedelta(hours=24)
        outside = now + timedelta(hours=72)

        t1 = _make_task("00000000-0000-0000-0000-000000000001", due_date=within)
        t2 = _make_task("00000000-0000-0000-0000-000000000002", due_date=outside)

        upcoming = get_upcoming_deadlines([t1, t2], within_hours=48, now=now)
        assert len(upcoming) == 1
        assert str(upcoming[0].id) == "00000000-0000-0000-0000-000000000001"

    def test_completed_tasks_not_in_upcoming(self):
        now = datetime(2025, 6, 1, 12, 0, tzinfo=UTC)
        within = now + timedelta(hours=24)
        t1 = _make_task(
            "00000000-0000-0000-0000-000000000001",
            due_date=within,
            status=TaskStatus.COMPLETED,
        )
        upcoming = get_upcoming_deadlines([t1], within_hours=48, now=now)
        assert len(upcoming) == 0


# ── Task Progress Tests ──────────────────────────────────────────────────


class TestTaskProgress:
    def test_pending_is_zero(self):
        t = _make_task(status=TaskStatus.PENDING)
        assert compute_task_progress(t) == 0.0

    def test_in_progress_is_half(self):
        t = _make_task(status=TaskStatus.IN_PROGRESS)
        assert compute_task_progress(t) == 0.5

    def test_completed_is_one(self):
        t = _make_task(status=TaskStatus.COMPLETED)
        assert compute_task_progress(t) == 1.0

    def test_blocked_is_zero(self):
        t = _make_task(status=TaskStatus.BLOCKED)
        assert compute_task_progress(t) == 0.0

    def test_cancelled_is_zero(self):
        t = _make_task(status=TaskStatus.CANCELLED)
        assert compute_task_progress(t) == 0.0
