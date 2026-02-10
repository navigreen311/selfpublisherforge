# W12: Fix AI Writing + Agent Executor Configurable Thresholds

## Branch: `fix/w12-ai-writing-agent-thresholds`

## Files YOU Own (only modify these):
- `backend/app/modules/ai_writing/service.py`
- `backend/app/modules/agent_system/executor.py`

## Task

### Fix 1: ai_writing/service.py — Word count multiplier (line ~273)

The value `0.5` is used as a word count multiplier for AI generation.

1. Add at top:
```python
import os

WORD_COUNT_MULTIPLIER = float(os.environ.get("AI_WORD_COUNT_MULTIPLIER", "0.5"))
```

2. Replace the hardcoded `0.5` with `WORD_COUNT_MULTIPLIER`.

### Fix 2: agent_system/executor.py — Scoring weights (lines ~213, ~243, ~265)

Multiple hardcoded values (`0.0`, `0.5`, `0.25`) used as scoring weights.

1. Add at top:
```python
import os

AGENT_QUALITY_WEIGHT = float(os.environ.get("AGENT_QUALITY_WEIGHT", "0.5"))
AGENT_SPEED_WEIGHT = float(os.environ.get("AGENT_SPEED_WEIGHT", "0.25"))
AGENT_COST_WEIGHT = float(os.environ.get("AGENT_COST_WEIGHT", "0.25"))
```

2. Replace the hardcoded values with the constants. Read the context carefully to match each constant to the right location.

3. Also check executor.py for any `except Exception: pass` blocks. If found, add `logger.exception(...)`.

## Verification
```bash
cd backend && python -c "from app.modules.ai_writing.service import *; print('ai_writing OK')"
cd backend && python -c "from app.modules.agent_system.executor import *; print('executor OK')"
```
