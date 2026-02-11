"""Task executor for the Agent System.

Receives a task, checks permissions, checks budget, executes via LLM
orchestrator, quality checks the result, and records the outcome.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

AGENT_QUALITY_WEIGHT = float(os.environ.get("AGENT_QUALITY_WEIGHT", "0.5"))
AGENT_SPEED_WEIGHT = float(os.environ.get("AGENT_SPEED_WEIGHT", "0.25"))
AGENT_COST_WEIGHT = float(os.environ.get("AGENT_COST_WEIGHT", "0.25"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_system.models import (
    Agent,
    AgentTask,
    AgentType,
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
from app.modules.llm_orchestration.orchestrator import (
    GenerationOptions,
    GenerationResult,
    LLMOrchestrator,
)
from app.modules.llm_orchestration.router_config import (
    ModelRouter,
    ProviderName,
    TaskType,
)
from app.modules.llm_orchestration.cost_tracker import CostTracker
from app.modules.llm_orchestration.cache import SemanticCache
from app.modules.llm_orchestration.quality import QualityAssurance
from app.modules.llm_orchestration.providers.anthropic import AnthropicProvider
from app.modules.llm_orchestration.providers.base import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

# Mapping from AgentType to the orchestrator's TaskType so that the model
# router picks an appropriate model chain for each kind of agent work.
_AGENT_TYPE_TO_TASK_TYPE: dict[AgentType, TaskType] = {
    AgentType.RESEARCH: TaskType.MARKET_ANALYSIS,
    AgentType.WRITING_ASSISTANT: TaskType.LONG_FORM_WRITING,
    AgentType.EDITOR: TaskType.QUICK_EDITS_GRAMMAR,
    AgentType.MARKETING_COPY: TaskType.BLURB_AD_COPY,
}


def _get_orchestrator() -> LLMOrchestrator:
    """Build an LLMOrchestrator wired to the Anthropic provider.

    A fresh instance is created per call to avoid stale state. The
    underlying Anthropic SDK client manages its own connection pool.
    """
    anthropic_provider = AnthropicProvider()
    orchestrator = LLMOrchestrator(
        providers={ProviderName.ANTHROPIC: anthropic_provider},
        router=ModelRouter(),
        cache=SemanticCache(),
        cost_tracker=CostTracker(),
        quality=QualityAssurance(),
    )
    return orchestrator


# ---------------------------------------------------------------------------
# LLM execution via the orchestration layer
# ---------------------------------------------------------------------------

async def _call_llm(
    model_id: str,
    system_prompt: str | None,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    *,
    agent_type: AgentType | None = None,
) -> dict[str, Any]:
    """Execute an LLM request through the orchestration layer.

    Routes through the full LLMOrchestrator pipeline (model routing,
    caching, cost tracking, quality assurance) when the agent type maps
    to a known TaskType. Falls back to a direct provider call when the
    orchestrator route is unavailable.

    Returns a dict with keys: text, tokens_used, cost_usd, model.
    """
    # Attempt orchestrated generation when we can resolve a TaskType
    task_type: TaskType | None = None
    if agent_type is not None:
        task_type = _AGENT_TYPE_TO_TASK_TYPE.get(agent_type)

    if task_type is not None:
        try:
            orchestrator = _get_orchestrator()
            options = GenerationOptions(
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                skip_cache=False,
                skip_quality_check=False,
            )

            result: GenerationResult = await orchestrator.generate(
                task_type=task_type.value,
                prompt=user_prompt,
                options=options,
            )

            if result.succeeded:
                return {
                    "text": result.content,
                    "tokens_used": result.total_tokens,
                    "cost_usd": result.cost_usd,
                    "model": result.model_id or model_id,
                }

            # Orchestrator exhausted all models -- fall through to direct call
            logger.warning(
                "Orchestrated generation failed (error=%s), falling back to direct provider call",
                result.metadata.get("error", "unknown"),
            )
        except (RuntimeError, ConnectionError, TimeoutError) as e:
            logger.exception("Orchestrator raised an unexpected error; falling back to direct provider call")

    # Direct provider call as fallback (or when no TaskType mapping exists)
    try:
        provider = AnthropicProvider()
        request = LLMRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        response: LLMResponse = await provider.generate(request)

        if response.succeeded:
            cost_usd = response.total_tokens * 0.000003  # conservative fallback estimate
            return {
                "text": response.content,
                "tokens_used": response.total_tokens,
                "cost_usd": cost_usd,
                "model": response.model_id or model_id,
            }

        raise RuntimeError(
            f"LLM provider returned an error: {response.metadata.get('error', response.finish_reason)}"
        )
    except Exception as exc:
        logger.exception("Direct LLM provider call failed")
        raise RuntimeError(f"LLM execution failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Quality evaluation via heuristics
# ---------------------------------------------------------------------------

async def _compute_quality_score(
    output_text: str,
    *,
    expected_min_words: int = 50,
    keywords: list[str] | None = None,
) -> float:
    """Evaluate the quality of LLM output using deterministic heuristics.

    Scoring dimensions (each contributes to the final 0.0-1.0 score):
      - Length adequacy:   is the output long enough relative to expectations?
      - Sentence structure: does it contain well-formed sentences?
      - Vocabulary richness: type-token ratio as a proxy for coherence.
      - Formatting signals:  presence of paragraphs, lists, or headings.
      - Keyword relevance:   overlap with expected keywords (when provided).

    Returns a float between 0.0 and 1.0.
    """
    if not output_text or not output_text.strip():
        return 0.0

    text = output_text.strip()
    words = re.findall(r"[a-zA-Z']+", text)
    word_count = len(words)

    if word_count < 5:
        return 0.05

    # --- 1. Length adequacy (0.0 - 1.0), weight 0.30 ---
    # Ramp linearly up to the expected minimum, then cap at 1.0 for
    # outputs up to 4x the minimum (very long isn't necessarily better).
    if word_count >= expected_min_words:
        length_score = 1.0
    else:
        length_score = word_count / expected_min_words
    # Slight penalty for extremely short outputs even relative to minimum
    if word_count < 20:
        length_score *= 0.6

    # --- 2. Sentence structure (0.0 - 1.0), weight 0.25 ---
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_count = len(sentences)
    if sentence_count == 0:
        structure_score = 0.1
    else:
        avg_sentence_len = word_count / sentence_count
        # Ideal average sentence length is 10-25 words
        if 10 <= avg_sentence_len <= 25:
            structure_score = 1.0
        elif 5 <= avg_sentence_len < 10 or 25 < avg_sentence_len <= 40:
            structure_score = 0.7
        else:
            structure_score = 0.4

    # --- 3. Vocabulary richness / coherence (0.0 - 1.0), weight 0.20 ---
    unique_words = set(w.lower() for w in words)
    if word_count > 0:
        ttr = len(unique_words) / word_count  # type-token ratio
    else:
        ttr = 0.0
    # A TTR between 0.3 and 0.8 is typical for well-written prose
    if 0.3 <= ttr <= 0.8:
        vocab_score = 1.0
    elif 0.2 <= ttr < 0.3 or 0.8 < ttr <= 0.95:
        vocab_score = 0.7
    else:
        vocab_score = 0.4

    # --- 4. Formatting signals (0.0 - 1.0), weight 0.10 ---
    formatting_score = AGENT_QUALITY_WEIGHT  # baseline
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) > 1:
        formatting_score += 0.2  # multi-paragraph structure
    if re.search(r'(?m)^[-*]\s', text):
        formatting_score += 0.15  # bullet/list items
    if re.search(r'(?m)^#{1,6}\s', text):
        formatting_score += 0.15  # markdown headings
    formatting_score = min(formatting_score, 1.0)

    # --- 5. Keyword relevance (0.0 - 1.0), weight 0.15 ---
    if keywords:
        text_lower = text.lower()
        matched = sum(1 for kw in keywords if kw.lower() in text_lower)
        keyword_score = matched / len(keywords) if keywords else AGENT_COST_WEIGHT
    else:
        # No keywords supplied -- assume neutral (full marks)
        keyword_score = 1.0

    # --- Weighted combination ---
    score = (
        0.30 * length_score
        + AGENT_SPEED_WEIGHT * structure_score
        + 0.20 * vocab_score
        + 0.10 * formatting_score
        + 0.15 * keyword_score
    )

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, round(score, 4)))


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
                agent_type=agent.agent_type,
            )

            # 5. Record output
            task.output_data = {
                "text": llm_result["text"],
                "model": llm_result["model"],
            }
            task.tokens_used = llm_result["tokens_used"]
            task.cost_usd = llm_result["cost_usd"]

            # 6. Quality check
            # Extract keywords from the task title and input data for relevance scoring.
            quality_keywords: list[str] = []
            if task.title:
                quality_keywords.extend(
                    w for w in task.title.split() if len(w) > 3
                )
            if task.input_data:
                kw_field = task.input_data.get("keywords")
                if isinstance(kw_field, list):
                    quality_keywords.extend(kw_field)

            # Set expected minimum word count based on the agent's max_tokens
            # (rough heuristic: ~0.75 words per token for English prose).
            expected_min_words = max(30, int(agent.max_tokens * 0.1))

            quality = await _compute_quality_score(
                llm_result["text"],
                expected_min_words=expected_min_words,
                keywords=quality_keywords or None,
            )
            task.quality_score = quality

            try:
                threshold = (agent.config or {}).get("quality_threshold", 0.7)
                validate_quality(quality, threshold=threshold)
            except QualityBelowSLA:
                logger.warning(
                    "Task %s quality score %.2f below threshold %.2f — routing to approval",
                    task.id, quality, threshold,
                )
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
            logger.warning("Task %s failed: permission denied — %s", task.id, exc.message)
            task.status = TaskStatus.FAILED
            task.error_message = f"Permission denied: {exc.message}"
            task.completed_at = datetime.now(timezone.utc)
            await self._audit_failure(task, exc.message, ip_address)

        except BudgetExceeded as exc:
            logger.warning("Task %s failed: budget exceeded — %s", task.id, exc.message)
            task.status = TaskStatus.FAILED
            task.error_message = f"Budget exceeded: {exc.message}"
            task.completed_at = datetime.now(timezone.utc)
            await self._audit_failure(task, exc.message, ip_address)

        except (RuntimeError, ValueError, OSError) as exc:
            logger.error("Task %s failed with unexpected error: %s", task.id, exc, exc_info=True)
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
