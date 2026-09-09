"""Task execution logic for AI Agent System.

Handles task execution simulation, progress tracking, and SSE streaming.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_system.models import Agent, AgentTask, TaskStatus

logger = logging.getLogger(__name__)


# Agent-specific execution steps configuration
AGENT_STEPS = {
    "research": [
        {"name": "Analyzing market trends", "duration": 2.0},
        {"name": "Gathering competitor data", "duration": 2.5},
        {"name": "Identifying keywords", "duration": 1.5},
        {"name": "Compiling insights", "duration": 2.0},
        {"name": "Generating report", "duration": 1.5},
    ],
    "writing_assistant": [
        {"name": "Understanding context", "duration": 1.5},
        {"name": "Drafting content", "duration": 3.0},
        {"name": "Refining narrative", "duration": 2.0},
        {"name": "Final polish", "duration": 1.5},
    ],
    "editor": [
        {"name": "Scanning document", "duration": 1.0},
        {"name": "Checking grammar and style", "duration": 2.5},
        {"name": "Analyzing consistency", "duration": 2.0},
        {"name": "Preparing suggestions", "duration": 1.5},
    ],
    "marketing_copy": [
        {"name": "Analyzing target audience", "duration": 1.5},
        {"name": "Crafting compelling copy", "duration": 2.5},
        {"name": "Optimizing for engagement", "duration": 1.5},
    ],
}


async def execute_task(
    db: AsyncSession,
    task: AgentTask,
    agent: Agent,
) -> dict[str, Any]:
    """Execute a task and simulate step-by-step progress.

    Args:
        db: Database session
        task: The task to execute
        agent: The agent executing the task

    Returns:
        Dictionary with execution results
    """
    start_time = datetime.now(UTC)

    # Update task status to running
    task.status = TaskStatus.RUNNING
    task.started_at = start_time
    await db.commit()

    # Get steps for this agent type
    agent_type = agent.agent_type.value
    steps_config = AGENT_STEPS.get(agent_type, AGENT_STEPS["research"])

    # Initialize steps
    steps = [
        {
            "name": step["name"],
            "status": "pending",
            "output": None,
        }
        for step in steps_config
    ]

    total_steps = len(steps)
    tokens_per_step = 100
    cost_per_1k_tokens = 0.003

    # Execute each step
    for i, step_config in enumerate(steps_config):
        # Update step to running
        steps[i]["status"] = "running"

        # Simulate processing
        await asyncio.sleep(step_config["duration"])

        # Mark step as complete with output
        steps[i]["status"] = "complete"
        steps[i]["output"] = f"Completed: {step_config['name']}"

    # Calculate final metrics
    total_tokens = tokens_per_step * total_steps
    total_cost = (total_tokens / 1000) * cost_per_1k_tokens
    execution_time = int((datetime.now(UTC) - start_time).total_seconds())

    # Generate output based on agent type
    output = _generate_task_output(agent_type, task)

    # Update task with results
    task.status = TaskStatus.AWAITING_APPROVAL
    task.completed_at = datetime.now(UTC)
    task.output_data = {
        "output": output,
        "steps": steps,
    }
    task.tokens_used = total_tokens
    task.cost_usd = total_cost
    await db.commit()
    await db.refresh(task)

    return {
        "task_id": task.id,
        "status": task.status.value,
        "progress": 100,
        "steps": steps,
        "output": output,
        "tokens_used": total_tokens,
        "cost": total_cost,
        "execution_time_seconds": execution_time,
    }


async def stream_task_execution(
    db: AsyncSession,
    task_id: uuid.UUID,
) -> AsyncGenerator[str, None]:
    """Stream task execution progress via Server-Sent Events.

    Args:
        db: Database session
        task_id: ID of the task to stream

    Yields:
        SSE-formatted event strings
    """
    # Get task
    result = await db.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
        return

    # Get agent
    result = await db.execute(select(Agent).where(Agent.id == task.agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        yield f"data: {json.dumps({'error': 'Agent not found'})}\n\n"
        return

    # Get steps for this agent type
    agent_type = agent.agent_type.value
    steps_config = AGENT_STEPS.get(agent_type, AGENT_STEPS["research"])

    total_steps = len(steps_config)

    # Send initial event
    yield f"data: {json.dumps({'event': 'started', 'progress': 0})}\n\n"

    # Execute and stream each step
    for i, step_config in enumerate(steps_config):
        # Send step start event
        progress = int((i / total_steps) * 100)
        yield f"data: {json.dumps({'event': 'step_start', 'step': step_config['name'], 'progress': progress})}\n\n"

        # Simulate processing
        await asyncio.sleep(step_config["duration"])

        # Send step complete event
        yield f"data: {json.dumps({'event': 'step_complete', 'step': step_config['name']})}\n\n"

    # Generate final output
    output = _generate_task_output(agent_type, task)

    # Send completion event
    yield f"data: {json.dumps({'event': 'completed', 'progress': 100, 'output': output})}\n\n"


async def stop_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    org_id: uuid.UUID,
) -> AgentTask | None:
    """Stop a running task.

    Args:
        db: Database session
        task_id: ID of the task to stop
        org_id: Organization ID for security check

    Returns:
        The updated task or None if not found
    """
    result = await db.execute(
        select(AgentTask).where(
            AgentTask.id == task_id,
            AgentTask.org_id == org_id,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        return None

    # Only stop if task is running or pending
    if task.status in (TaskStatus.RUNNING, TaskStatus.PENDING):
        task.status = TaskStatus.CANCELLED
        task.error_message = "Task stopped by user"
        task.completed_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(task)

    return task


def _generate_task_output(agent_type: str, task: AgentTask) -> str:
    """Generate simulated output based on agent type and task.

    Args:
        agent_type: Type of agent (research, writing_assistant, etc.)
        task: The task being executed

    Returns:
        Simulated task output as a string
    """
    instructions = ""
    if task.input_data and "instructions" in task.input_data:
        instructions = task.input_data["instructions"]

    outputs = {
        "research": f"""# Market Research Report

## Executive Summary
Based on the analysis of current market trends and competitive landscape for: {instructions}

### Key Findings
- Market opportunity identified in niche segments
- Competitor analysis reveals gaps in content quality
- High-value keywords with moderate competition discovered

### Top Keywords
1. Primary keyword (Search Vol: 12,000/mo)
2. Long-tail variant (Search Vol: 3,500/mo)
3. Related topic (Search Vol: 8,200/mo)

### Recommendations
- Focus on underserved subcategories
- Emphasize unique value propositions
- Target secondary keywords for initial traction
""",
        "writing_assistant": f"""# Generated Content

{instructions}

## Draft Output
Lorem ipsum dolor sit amet, consectetur adipiscing elit. The narrative begins with our protagonist facing a critical decision. The tension builds as circumstances force their hand, leading to unexpected consequences that ripple through the story.

Character development shines through authentic dialogue and meaningful internal conflict. The pacing maintains reader engagement while allowing space for emotional resonance.

### Key Story Elements
- Strong opening hook
- Character-driven plot progression
- Thematic consistency
- Satisfying narrative arc

This draft provides a solid foundation for further refinement and expansion.
""",
        "editor": f"""# Editorial Review

## Document Analysis
Reviewed content: {instructions}

### Grammar & Style Issues Found: 12
- 5 instances of passive voice (consider active voice)
- 3 run-on sentences (suggest breaking up)
- 2 subject-verb agreement issues
- 2 punctuation improvements recommended

### Consistency Check
- Character names: Consistent ✓
- Timeline: 1 discrepancy noted (Chapter 3 vs Chapter 7)
- Tone: Generally consistent with minor variations

### Readability Score
- Grade Level: 8.5 (appropriate for target audience)
- Sentence complexity: Moderate
- Vocabulary diversity: Good

### Top Recommendations
1. Tighten opening paragraph for stronger hook
2. Reduce adjective overuse in descriptive passages
3. Strengthen dialogue attribution variety
""",
        "marketing_copy": f"""# Marketing Copy

## Campaign: {instructions}

### Book Blurb (150 words)
Discover a tale that will captivate your imagination and keep you turning pages late into the night. When [protagonist] faces [central conflict], they must make impossible choices that will determine not only their fate but the fate of everyone they love.

Perfect for fans of [comparable authors], this gripping story delivers:
- Unforgettable characters you'll root for
- Plot twists that will leave you breathless
- An emotional journey that stays with you

### Social Media Posts
**Twitter/X:**
"The kind of book you can't put down. Thrilling, emotional, unforgettable. ⭐⭐⭐⭐⭐"

**Instagram:**
Behind every page is a story waiting to change everything you thought you knew...

### Email Subject Lines
- "You won't believe what happens in Chapter 7..."
- "Readers are calling this 'unputdownable'"
- "The book everyone's talking about this month"
""",
    }

    return outputs.get(agent_type, f"Task completed: {instructions}")
