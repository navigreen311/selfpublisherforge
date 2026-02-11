"""Workflow engine for multi-step agent workflows.

Handles step execution, conditional branching, error handling (stop / skip /
retry), and resume from paused state.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_system.audit import record_audit
from app.modules.agent_system.executor import TaskExecutor
from app.modules.agent_system.models import (
    AgentTask,
    AgentWorkflow,
    AuditAction,
    TaskPriority,
    TaskStatus,
    WorkflowStatus,
    WorkflowStepStatus,
)


class WorkflowEngine:
    """Drives multi-step workflows through their step sequence."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.executor = TaskExecutor(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start_workflow(
        self,
        workflow: AgentWorkflow,
        *,
        user_role: str = "viewer",
        ip_address: str | None = None,
    ) -> AgentWorkflow:
        """Start a workflow from the beginning."""
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now(UTC)
        workflow.current_step_index = 0
        await self.db.flush()

        await record_audit(
            self.db,
            org_id=workflow.org_id,
            action=AuditAction.WORKFLOW_STARTED,
            actor_id=workflow.created_by,
            actor_type="user",
            resource_type="agent_workflow",
            resource_id=workflow.id,
            details={"total_steps": len(workflow.steps)},
            ip_address=ip_address,
        )

        return await self._run_steps(workflow, user_role=user_role, ip_address=ip_address)

    async def resume_workflow(
        self,
        workflow: AgentWorkflow,
        *,
        user_role: str = "viewer",
        ip_address: str | None = None,
    ) -> AgentWorkflow:
        """Resume a paused or partially-completed workflow."""
        if workflow.status not in (WorkflowStatus.PAUSED, WorkflowStatus.RUNNING):
            raise ValueError(
                f"Cannot resume workflow in status '{workflow.status.value}'"
            )
        workflow.status = WorkflowStatus.RUNNING
        await self.db.flush()
        return await self._run_steps(workflow, user_role=user_role, ip_address=ip_address)

    # ------------------------------------------------------------------
    # Internal step runner
    # ------------------------------------------------------------------

    async def _run_steps(
        self,
        workflow: AgentWorkflow,
        *,
        user_role: str = "viewer",
        ip_address: str | None = None,
    ) -> AgentWorkflow:
        """Iterate through remaining steps and execute them."""
        steps = workflow.steps or []
        context = workflow.context or {}

        while workflow.current_step_index < len(steps):
            idx = workflow.current_step_index
            step_def = steps[idx]

            # Evaluate condition
            if not self._evaluate_condition(step_def.get("condition"), context):
                # Update step status to skipped
                step_def["status"] = WorkflowStepStatus.SKIPPED.value
                steps[idx] = step_def
                workflow.steps = steps  # trigger JSONB update
                workflow.current_step_index = idx + 1
                await self.db.flush()
                continue

            step_def["status"] = WorkflowStepStatus.RUNNING.value
            steps[idx] = step_def
            workflow.steps = steps
            await self.db.flush()

            # Create a task for this step
            task = AgentTask(
                org_id=workflow.org_id,
                agent_id=uuid.UUID(step_def["agent_id"]),
                workflow_id=workflow.id,
                workflow_step_index=idx,
                title=step_def.get("title", f"Workflow step {idx + 1}"),
                description=step_def.get("description"),
                priority=TaskPriority.MEDIUM,
                input_data=self._merge_step_input(step_def.get("input_data"), context),
                created_by=workflow.created_by,
            )
            self.db.add(task)
            await self.db.flush()
            await self.db.refresh(task)

            # Execute the task
            retries = 0
            max_retries = step_def.get("max_retries", 0)
            on_failure = step_def.get("on_failure", "stop")

            while True:
                task = await self.executor.execute(
                    task,
                    user_role=user_role,
                    ip_address=ip_address,
                )

                if task.status == TaskStatus.COMPLETED:
                    step_def["status"] = WorkflowStepStatus.COMPLETED.value
                    # Store output in workflow context
                    if task.output_data:
                        context[f"step_{idx}_output"] = task.output_data
                    break

                if task.status == TaskStatus.AWAITING_APPROVAL:
                    # Pause workflow until approval
                    step_def["status"] = WorkflowStepStatus.PENDING.value
                    steps[idx] = step_def
                    workflow.steps = steps
                    workflow.context = context
                    workflow.status = WorkflowStatus.PAUSED
                    await self.db.flush()
                    return workflow

                if task.status == TaskStatus.FAILED:
                    if retries < max_retries:
                        retries += 1
                        # Reset task for retry
                        task.status = TaskStatus.PENDING
                        task.error_message = None
                        task.started_at = None
                        task.completed_at = None
                        await self.db.flush()
                        continue

                    if on_failure == "skip":
                        step_def["status"] = WorkflowStepStatus.SKIPPED.value
                        step_def["error"] = task.error_message
                        break
                    # "stop" – fail the workflow
                    step_def["status"] = WorkflowStepStatus.FAILED.value
                    step_def["error"] = task.error_message
                    steps[idx] = step_def
                    workflow.steps = steps
                    workflow.context = context
                    workflow.status = WorkflowStatus.FAILED
                    workflow.error_message = (
                        f"Step {idx + 1} failed: {task.error_message}"
                    )
                    workflow.completed_at = datetime.now(UTC)
                    await self.db.flush()

                    await record_audit(
                        self.db,
                        org_id=workflow.org_id,
                        action=AuditAction.WORKFLOW_FAILED,
                        actor_id=workflow.created_by,
                        actor_type="system",
                        resource_type="agent_workflow",
                        resource_id=workflow.id,
                        details={"failed_step": idx, "error": task.error_message},
                        ip_address=ip_address,
                    )
                    return workflow
                # Unexpected status – treat as failure
                step_def["status"] = WorkflowStepStatus.FAILED.value
                break

            steps[idx] = step_def
            workflow.steps = steps
            workflow.context = context
            workflow.current_step_index = idx + 1
            await self.db.flush()

        # All steps completed
        workflow.status = WorkflowStatus.COMPLETED
        workflow.completed_at = datetime.now(UTC)
        await self.db.flush()

        await record_audit(
            self.db,
            org_id=workflow.org_id,
            action=AuditAction.WORKFLOW_COMPLETED,
            actor_id=workflow.created_by,
            actor_type="system",
            resource_type="agent_workflow",
            resource_id=workflow.id,
            details={"total_steps": len(steps)},
            ip_address=ip_address,
        )

        return workflow

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_condition(condition: str | None, context: dict[str, Any]) -> bool:
        """Evaluate a step condition against the workflow context.

        Supported simple expressions:
          - None / empty  -> True (always run)
          - "step_0_output.text" -> truthy check on context path
          - "!step_0_output.error" -> falsy check
        """
        if not condition:
            return True

        negate = False
        expr = condition.strip()
        if expr.startswith("!"):
            negate = True
            expr = expr[1:].strip()

        # Traverse dotted path
        parts = expr.split(".")
        value: Any = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break

        result = bool(value)
        return (not result) if negate else result

    @staticmethod
    def _merge_step_input(
        step_input: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge step-specific input with workflow context."""
        merged: dict[str, Any] = {}
        if step_input:
            merged.update(step_input)
        merged["workflow_context"] = context
        return merged
