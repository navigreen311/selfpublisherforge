# W09: Fix Analytics Service Bare Excepts + Metrics Thresholds

## Branch: `fix/w09-analytics-fixes`

## Files YOU Own (only modify these):
- `backend/app/modules/analytics/service.py`
- `backend/app/modules/analytics/metrics.py`

## Task

### Fix 1: service.py — Bare `except ValueError: pass` blocks (lines ~164, ~277)

Two locations silently swallow ValueError when parsing timezone info.

```python
# BEFORE:
except ValueError:
    pass

# AFTER:
except ValueError:
    logger.warning("Failed to parse timezone value, using default UTC")
```

Add `import logging` and `logger = logging.getLogger(__name__)` if not present.

### Fix 2: metrics.py — Hardcoded change thresholds (lines ~49, ~51)

The value `0.5` is used as a change detection threshold. Make it configurable:

```python
import os

CHANGE_THRESHOLD = float(os.environ.get("ANALYTICS_CHANGE_THRESHOLD", "0.5"))
```

Replace the hardcoded `0.5` threshold values with `CHANGE_THRESHOLD`.

### Fix 3: metrics.py — Verify expenses calculation
The previous audit noted `total_expenses=Decimal("0.00")` was a placeholder. Check if this was already fixed to query real CampaignPerformance data. If it's still hardcoded to 0, add a comment noting it depends on advertising module data.

## Verification
```bash
cd backend && python -c "from app.modules.analytics import service, metrics; print('imports OK')"
cd backend && grep -n "except.*pass" app/modules/analytics/service.py || echo "No silent exceptions"
```
