"""Task executor for the Agent System.

Receives a task, checks permissions, checks budget, executes via LLM
orchestrator, quality checks the result, and records the outcome.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_system.models import (
    Agent,
    AgentTask,
    AuditAction,
    PermissionLevel,
    TaskStatus,
)
from app.modules.agent_system.governance import (
    BudgetExceeded,
    PermissionDenied,
    QualityBelowSLA,
    check_budget,
    check_permission,
    record_usage,
    requires_approval,
    validate_quality,
)
from app.modules.agent_system.audit import record_audit


# ---------------------------------------------------------------------------
# LLM Orchestration stub
# ---------------------------------------------------------------------------

async def _call_llm(
    model_id: str,
    system_prompt: str | None,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> dict[str, Any]:
    """Stub for the LLM orchestration layer.

    In production this would delegate to the llm_orchestration module.
    Returns a dict with keys: text, tokens_used, cost_usd, model.
    """
    # Placeholder – real implementation calls Anthropic / OpenAI via
    # the llm_orchestration module.
    estimated_tokens = min(max_tokens, len(user_prompt.split()) * 4)
    estimated_cost = estimated_tokens * 0.000003  # rough estimate

    return {
        "text": f"[LLM output for: {user_prompt[:80]}...]",
        "tokens_used": estimated_tokens,
        "cost_usd": estimated_cost,
        "model": model_id,
    }


async def _compute_quality_score(output_text: str) -> float:
    """Stub for quality evaluation.

    In production this could run a secondary LLM check, grammar check, etc.
    Returns a float 0.0-1.0.
    """
    # Placeholder – always returns a reasonable score
    if not output_text or len(output_text.strip()) < 10:
        return 0.3
    return 0.85


# ---------------------------------------------------------------------------
# Main executor
# ---------------------------------------------------------------------------

class TaskExecutor:
    """Orchestrates the end-to-end lifecycle of a single agent task."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute(
        self,
        task: AgentTask,
        *,
        user_role: str = "viewer",
        ip_address: str | None = None,
    ) -> AgentTask:
        """Execute a task through the full pipeline.

        1. Load agent
        2. Check permissions
        3. Check budget
        4. Run LLM
        5. Quality check
        6. Determine status (awaiting_approval vs completed)
        7. Record usage and audit
        """
        agent = await self._load_agent(task.agent_id)

        # Mark as running
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        await self.db.flush()

        await record_audit(
            self.db,
            org_id=task.org_id,
            action=AuditAction.TASK_STARTED,
            actor_id=task.created_by,
            actor_type="system",
            resource_type="agent_task",
            resource_id=task.id,
            details={"agent_id": str(task.agent_id)},
            ip_address=ip_address,
        )

        try:
            # 1. Permission check
            # Draft-only and suggest agents are allowed to execute but need
            # approval afterward, so only enforce execute_auto for autonomous
            # agents.
            if not requires_approval(agent):
                check_permission(agent, "execute_auto", user_role=user_role)
            else:
                check_permission(agent, "approve", user_role=user_role)

            # 2. Budget check
            estimated_tokens = agent.max_tokens
            estimated_cost = estimated_tokens * 0.000003
            await check_budget(self.db, agent, estimated_tokens, estimated_cost)

            # 3. Build prompt
            user_prompt = self._build_prompt(task)

            # 4. Call LLM
            llm_result = await _call_llm(
                model_id=agent.model_id,
                system_prompt=agent.system_prompt,
                user_prompt=user_prompt,
                max_tokens=agent.max_tokens,
                temperature=agent.temperature,
            )

            # 5. Record output
            task.output_data = {
                "text": llm_result["text"],
                "model": llm_result["model"],
            }
            task.tokens_used = llm_result["tokens_used"]
            task.cost_usd = llm_result["cost_usd"]

            # 6. Quality check
            quality = await _compute_quality_score(llm_result["text"])
            task.quality_score = quality

            try:
                threshold = (agent.config or {}).get("quality_threshold", 0.7)
                validate_quality(quality, threshold=threshold)
            except QualityBelowSLA:
                task.status = TaskStatus.AWAITING_APPROVAL
                task.output_data["quality_warning"] = (
                    f"Quality score {quality:.2f} below threshold {threshold:.2f}"
                )

            # 7. Determine final status
            if task.status != TaskStatus.AWAITING_APPROVAL:
                if requires_approval(agent):
                    task.status = TaskStatus.AWAITING_APPROVAL
                else:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now(timezone.utc)

            # 8. Record budget usage
            await record_usage(
                self.db,
                agent_id=agent.id,
                tokens_used=llm_result["tokens_used"],
                cost_usd=llm_result["cost_usd"],
            )

            # 9. Audit completion
            completion_action = (
                AuditAction.TASK_COMPLETED
                if task.status == TaskStatus.COMPLETED
                else AuditAction.TASK_STARTED  # still in progress (awaiting approval)
            )
            await record_audit(
                self.db,
                org_id=task.org_id,
                action=completion_action,
                actor_id=task.created_by,
                actor_type="system",
                resource_type="agent_task",
                resource_id=task.id,
                details={
                    "tokens_used": llm_result["tokens_used"],
                    "cost_usd": llm_result["cost_usd"],
                    "quality_score": quality,
                    "status": task.status.value,
                },
                ip_address=ip_address,
            )

        except PermissionDenied as exc:
            task.status = TaskStatus.FAILED
            task.error_message = f"Permission denied: {exc.message}"
            task.completed_at = datetime.now(timezone.utc)
            await self._audit_failure(task, exc.message, ip_address)

        except BudgetExceeded as exc:
            task.status = TaskStatus.FAILED
            task.error_message = f"Budget exceeded: {exc.message}"
            task.completed_at = datetime.now(timezone.utc)
            await self._audit_failure(task, exc.message, ip_address)

        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error_message = f"Execution error: {str(exc)}"
            task.completed_at = datetime.now(timezone.utc)
            await self._audit_failure(task, str(exc), ip_address)

        await self.db.flush()
        return task

    async def _load_agent(self, agent_id: uuid.UUID) -> Agent:
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            raise ValueError(f"Agent {agent_id} not found")
        return agent

    def _build_prompt(self, task: AgentTask) -> str:
        """Build the user prompt from task data."""
        parts = [task.title]
        if task.description:
            parts.append(task.description)
        if task.input_data:
            context = task.input_data.get("context", "")
            if context:
                parts.append(f"Context: {context}")
            instructions = task.input_data.get("instructions", "")
            if instructions:
                parts.append(f"Instructions: {instructions}")
        return "\n\n".join(parts)

    async def _audit_failure(
        self,
        task: AgentTask,
        error: str,
        ip_address: str | None,
    ) -> None:
        await record_audit(
            self.db,
            org_id=task.org_id,
            action=AuditAction.TASK_FAILED,
            actor_id=task.created_by,
            actor_type="system",
            resource_type="agent_task",
            resource_id=task.id,
            details={"error": error},
            ip_address=ip_address,
        )
