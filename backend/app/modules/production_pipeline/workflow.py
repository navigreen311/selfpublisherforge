"""Workflow engine: task dependency resolution, status transitions, deadline alerts."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime

from app.modules.production_pipeline.models import (
    PipelineStatus,
    PipelineTask,
    TaskStatus,
)

# ── Valid status transitions ──────────────────────────────────────────────

PIPELINE_TRANSITIONS: dict[PipelineStatus, set[PipelineStatus]] = {
    PipelineStatus.DRAFT: {PipelineStatus.ACTIVE, PipelineStatus.CANCELLED},
    PipelineStatus.ACTIVE: {
        PipelineStatus.PAUSED,
        PipelineStatus.COMPLETED,
        PipelineStatus.CANCELLED,
    },
    PipelineStatus.PAUSED: {PipelineStatus.ACTIVE, PipelineStatus.CANCELLED},
    PipelineStatus.COMPLETED: set(),
    PipelineStatus.CANCELLED: set(),
}

TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.BLOCKED: {TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}


class WorkflowError(Exception):
    """Raised when a workflow rule is violated."""

    pass


# ── Status transition validation ──────────────────────────────────────────


def validate_pipeline_transition(
    current: PipelineStatus, target: PipelineStatus
) -> None:
    """Raise WorkflowError if the pipeline transition is invalid."""
    if target not in PIPELINE_TRANSITIONS.get(current, set()):
        raise WorkflowError(
            f"Cannot transition pipeline from '{current.value}' to '{target.value}'."
        )


def validate_task_transition(current: TaskStatus, target: TaskStatus) -> None:
    """Raise WorkflowError if the task transition is invalid."""
    if target not in TASK_TRANSITIONS.get(current, set()):
        raise WorkflowError(
            f"Cannot transition task from '{current.value}' to '{target.value}'."
        )


# ── Dependency resolution ─────────────────────────────────────────────────


def build_dependency_graph(
    tasks: list[PipelineTask],
) -> tuple[dict[str, list[str]], dict[str, int]]:
    """Build adjacency list and in-degree map from tasks.

    Returns (adjacency, in_degree) where keys are task IDs as strings.
    """
    adjacency: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = {}

    task_ids = {str(t.id) for t in tasks}

    for t in tasks:
        tid = str(t.id)
        in_degree.setdefault(tid, 0)
        for dep_id in t.depends_on or []:
            if dep_id in task_ids:
                adjacency[dep_id].append(tid)
                in_degree[tid] = in_degree.get(tid, 0) + 1

    return dict(adjacency), in_degree


def topological_sort(tasks: list[PipelineTask]) -> list[str]:
    """Return task IDs in topological (execution) order.

    Raises WorkflowError if a cycle is detected.
    """
    adjacency, in_degree = build_dependency_graph(tasks)
    queue: deque[str] = deque()

    for tid, deg in in_degree.items():
        if deg == 0:
            queue.append(tid)

    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbour in adjacency.get(node, []):
            in_degree[neighbour] -= 1
            if in_degree[neighbour] == 0:
                queue.append(neighbour)

    if len(order) != len(in_degree):
        raise WorkflowError("Cycle detected in task dependencies.")

    return order


def detect_cycle(tasks: list[PipelineTask]) -> bool:
    """Return True if there is a cycle in the dependency graph."""
    try:
        topological_sort(tasks)
        return False
    except WorkflowError:
        return True


def get_ready_tasks(tasks: list[PipelineTask]) -> list[PipelineTask]:
    """Return tasks that are unblocked (all dependencies completed)."""
    completed = {
        str(t.id) for t in tasks if t.status == TaskStatus.COMPLETED
    }
    ready: list[PipelineTask] = []
    for t in tasks:
        if t.status not in (TaskStatus.PENDING, TaskStatus.BLOCKED):
            continue
        deps = t.depends_on or []
        if all(d in completed for d in deps):
            ready.append(t)
    return ready


def compute_blocked_tasks(tasks: list[PipelineTask]) -> list[PipelineTask]:
    """Return tasks that should be marked BLOCKED because deps are unmet."""
    completed = {
        str(t.id) for t in tasks if t.status == TaskStatus.COMPLETED
    }
    cancelled = {
        str(t.id) for t in tasks if t.status == TaskStatus.CANCELLED
    }
    blocked: list[PipelineTask] = []
    for t in tasks:
        if t.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            continue
        deps = t.depends_on or []
        if not deps:
            continue
        # blocked if any dep is not completed and not cancelled
        unmet = [d for d in deps if d not in completed and d not in cancelled]
        if unmet:
            blocked.append(t)
    return blocked


# ── Critical path ─────────────────────────────────────────────────────────


def compute_critical_path(tasks: list[PipelineTask]) -> list[str]:
    """Compute critical path through the task dependency graph.

    Uses longest-path through a DAG (topological order + dynamic programming).
    Weight of each task = 1 (uniform).
    Returns list of task IDs on the critical path.
    """
    if not tasks:
        return []

    order = topological_sort(tasks)
    task_map = {str(t.id): t for t in tasks}

    # Build reverse adjacency for traceback
    adjacency: dict[str, list[str]] = defaultdict(list)
    for t in tasks:
        for dep_id in t.depends_on or []:
            if dep_id in task_map:
                adjacency[dep_id].append(str(t.id))

    # dp[node] = length of longest path ending at node
    dp: dict[str, int] = {}
    predecessor: dict[str, str | None] = {}

    for node in order:
        dp[node] = 1
        predecessor[node] = None
        t = task_map[node]
        for dep_id in t.depends_on or []:
            if dep_id in dp and dp[dep_id] + 1 > dp[node]:
                dp[node] = dp[dep_id] + 1
                predecessor[node] = dep_id

    # Find the end of the critical path
    if not dp:
        return []
    end_node = max(dp, key=lambda k: dp[k])

    # Trace back
    path: list[str] = []
    current: str | None = end_node
    while current is not None:
        path.append(current)
        current = predecessor[current]
    path.reverse()
    return path


# ── Deadline helpers ──────────────────────────────────────────────────────


def get_overdue_tasks(
    tasks: list[PipelineTask], now: datetime | None = None
) -> list[PipelineTask]:
    """Return tasks that are past their due date and not completed/cancelled."""
    now = now or datetime.now(UTC)
    overdue: list[PipelineTask] = []
    for t in tasks:
        if t.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            continue
        if t.due_date and t.due_date < now:
            overdue.append(t)
    return overdue


def get_upcoming_deadlines(
    tasks: list[PipelineTask],
    within_hours: int = 48,
    now: datetime | None = None,
) -> list[PipelineTask]:
    """Return tasks due within the given window that are not completed."""
    from datetime import timedelta

    now = now or datetime.now(UTC)
    cutoff = now + timedelta(hours=within_hours)
    upcoming: list[PipelineTask] = []
    for t in tasks:
        if t.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            continue
        if t.due_date and now <= t.due_date <= cutoff:
            upcoming.append(t)
    return upcoming


def compute_task_progress(task: PipelineTask) -> float:
    """Return a 0.0 – 1.0 progress value for a task based on its status."""
    progress_map = {
        TaskStatus.PENDING: 0.0,
        TaskStatus.BLOCKED: 0.0,
        TaskStatus.IN_PROGRESS: 0.5,
        TaskStatus.COMPLETED: 1.0,
        TaskStatus.CANCELLED: 0.0,
    }
    return progress_map.get(task.status, 0.0)
