# W11: Fix Competitor Finder + Market Scoring Thresholds

## Branch: `fix/w11-competitor-scoring-thresholds`

## Files YOU Own (only modify these):
- `backend/app/modules/competitor_finder/gap_detector.py`
- `backend/app/modules/market_intelligence/scoring.py`

## Task

### Fix 1: gap_detector.py — Hardcoded thresholds (lines ~108, ~129, ~135)

The value `0.5` is used for price and frequency thresholds in gap detection.

1. Add at top:
```python
import os

GAP_PRICE_THRESHOLD = float(os.environ.get("GAP_PRICE_THRESHOLD", "0.5"))
GAP_FREQUENCY_THRESHOLD = float(os.environ.get("GAP_FREQUENCY_THRESHOLD", "0.5"))
```

2. Replace hardcoded `0.5` values with the appropriate constant based on context.

3. Check for any `return []` that should have logging/warnings. Add logging for empty returns that indicate data issues (not normal empty results).

### Fix 2: scoring.py — Sigmoid scaling midpoints (lines ~89, ~96, ~115)

Values `5000`, `50000`, `500` are used as sigmoid scaling midpoints.

1. Add at top:
```python
import os

DEMAND_MIDPOINT = int(os.environ.get("MI_DEMAND_MIDPOINT", "5000"))
COMPETITION_MIDPOINT = int(os.environ.get("MI_COMPETITION_MIDPOINT", "50000"))
OPPORTUNITY_MIDPOINT = int(os.environ.get("MI_OPPORTUNITY_MIDPOINT", "500"))
```

2. Replace the hardcoded values with the constants.

## Verification
```bash
cd backend && python -c "from app.modules.competitor_finder.gap_detector import *; from app.modules.market_intelligence.scoring import *; print('imports OK')"
```
