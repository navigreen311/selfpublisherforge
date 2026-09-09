"""Celery tasks for async agent execution and workflow step execution.

These tasks run outside the HTTP request/response cycle, allowing
long-running LLM calls and multi-step workflows to proceed asynchronously.

Time limit strategy
-------------------
Each task declares explicit ``soft_time_limit`` and ``time_limit`` values
(in seconds) based on expected workload:
  - Quick   (notifications, status updates):   soft=60,   hard=120
  - Medium  (API calls, data sync):            soft=300,  hard=600
  - Long    (bulk imports, report generation):  soft=1800, hard=3600
  - V. Long (full analytics aggregation):       soft=3300, hard=3600
Global defaults in config.py are 3300/3600 but per-task limits take precedence.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC
from typing import Any

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session
from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="agent_system.execute_task",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
    soft_time_limit=1800,
    time_limit=3600,
)
def execute_agent_task(self, task_id: str, user_role: str = "viewer") -> dict[str, Any]:
    """Execute an agent task asynchronously.

    Args:
        task_id: UUID string of the AgentTask to execute.
        user_role: Role of the user who created the task.

    Returns:
        Dict with task_id, status, and optional error.
    """
    return _run_async(_execute_agent_task_async(task_id, user_role))


async def _execute_agent_task_async(task_id: str, user_role: str) -> dict[str, Any]:
    from sqlalchemy import select

    from app.modules.agent_system.executor import TaskExecutor
    from app.modules.agent_system.models import AgentTask, TaskStatus

    async with async_session() as db:
        try:
            result = await db.execute(select(AgentTask).where(AgentTask.id == uuid.UUID(task_id)))
            task = result.scalar_one_or_none()

            if task is None:
                return {"task_id": task_id, "status": "not_found", "error": "Task not found"}

            if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
                return {
                    "task_id": task_id,
                    "status": task.status.value,
                    "error": f"Task is not in executable state: {task.status.value}",
                }

            executor = TaskExecutor(db)
            task = await executor.execute(task, user_role=user_role)

            await db.commit()

            return {
                "task_id": task_id,
                "status": task.status.value,
                "tokens_used": task.tokens_used,
                "cost_usd": task.cost_usd,
                "quality_score": task.quality_score,
            }

        except SQLAlchemyError as exc:
            await db.rollback()
            logger.error("Database error executing agent task %s: %s", task_id, exc, exc_info=True)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(exc),
            }
        except (ValueError, TypeError) as exc:
            await db.rollback()
            logger.error("Validation error executing agent task %s: %s", task_id, exc, exc_info=True)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(exc),
            }
        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning("Agent task %s hit soft time limit, cleaning up", task_id)
            raise
        except Exception as exc:
            await db.rollback()
            logger.error("Unexpected error executing agent task %s: %s", task_id, exc, exc_info=True)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(exc),
            }


@celery_app.task(
    name="agent_system.execute_workflow",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=1800,
    time_limit=3600,
)
def execute_agent_workflow(
    self,
    workflow_id: str,
    user_role: str = "viewer",
) -> dict[str, Any]:
    """Execute a workflow asynchronously.

    Args:
        workflow_id: UUID string of the AgentWorkflow to execute.
        user_role: Role of the user who created the workflow.

    Returns:
        Dict with workflow_id, status, and optional error.
    """
    return _run_async(_execute_agent_workflow_async(workflow_id, user_role))


async def _execute_agent_workflow_async(
    workflow_id: str,
    user_role: str,
) -> dict[str, Any]:
    from sqlalchemy import select

    from app.modules.agent_system.models import AgentWorkflow, WorkflowStatus
    from app.modules.agent_system.workflow_engine import WorkflowEngine

    async with async_session() as db:
        try:
            result = await db.execute(select(AgentWorkflow).where(AgentWorkflow.id == uuid.UUID(workflow_id)))
            workflow = result.scalar_one_or_none()

            if workflow is None:
                return {
                    "workflow_id": workflow_id,
                    "status": "not_found",
                    "error": "Workflow not found",
                }

            engine = WorkflowEngine(db)

            if workflow.status == WorkflowStatus.DRAFT:
                workflow = await engine.start_workflow(workflow, user_role=user_role)
            elif workflow.status in (WorkflowStatus.RUNNING, WorkflowStatus.PAUSED):
                workflow = await engine.resume_workflow(workflow, user_role=user_role)
            else:
                return {
                    "workflow_id": workflow_id,
                    "status": workflow.status.value,
                    "error": f"Workflow cannot be executed in state: {workflow.status.value}",
                }

            await db.commit()

            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "current_step": workflow.current_step_index,
                "total_steps": len(workflow.steps or []),
            }

        except SQLAlchemyError as exc:
            await db.rollback()
            logger.error("Database error executing workflow %s: %s", workflow_id, exc, exc_info=True)
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(exc),
            }
        except (ValueError, TypeError) as exc:
            await db.rollback()
            logger.error("Validation error executing workflow %s: %s", workflow_id, exc, exc_info=True)
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(exc),
            }
        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning("Workflow %s hit soft time limit, cleaning up", workflow_id)
            raise
        except Exception as exc:
            await db.rollback()
            logger.error("Unexpected error executing workflow %s: %s", workflow_id, exc, exc_info=True)
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(exc),
            }


@celery_app.task(
    name="agent_system.reset_daily_budgets",
    bind=True,
    soft_time_limit=60,
    time_limit=120,
)
def reset_daily_budgets(self) -> dict[str, Any]:
    """Periodic task to reset daily budget counters.

    Intended to be scheduled via Celery Beat (e.g., daily at midnight UTC).
    """
    return _run_async(_reset_daily_budgets_async())


async def _reset_daily_budgets_async() -> dict[str, Any]:
    from datetime import datetime

    from sqlalchemy import update

    from app.modules.agent_system.models import AgentBudget

    async with async_session() as db:
        try:
            result = await db.execute(
                update(AgentBudget).values(
                    tokens_used_today=0,
                    usd_used_today=0.0,
                    last_reset_daily=datetime.now(UTC),
                )
            )
            await db.commit()
            return {"reset": True, "count": result.rowcount}
        except SQLAlchemyError as exc:
            await db.rollback()
            logger.error("Database error resetting daily budgets: %s", exc, exc_info=True)
            return {"reset": False, "error": str(exc)}


@celery_app.task(
    name="agent_system.reset_monthly_budgets",
    bind=True,
    soft_time_limit=60,
    time_limit=120,
)
def reset_monthly_budgets(self) -> dict[str, Any]:
    """Periodic task to reset monthly budget counters.

    Intended to be scheduled via Celery Beat (e.g., 1st of each month).
    """
    return _run_async(_reset_monthly_budgets_async())


async def _reset_monthly_budgets_async() -> dict[str, Any]:
    from datetime import datetime

    from sqlalchemy import update

    from app.modules.agent_system.models import AgentBudget

    async with async_session() as db:
        try:
            result = await db.execute(
                update(AgentBudget).values(
                    usd_used_this_month=0.0,
                    last_reset_monthly=datetime.now(UTC),
                )
            )
            await db.commit()
            return {"reset": True, "count": result.rowcount}
        except SQLAlchemyError as exc:
            await db.rollback()
            logger.error("Database error resetting monthly budgets: %s", exc, exc_info=True)
            return {"reset": False, "error": str(exc)}
