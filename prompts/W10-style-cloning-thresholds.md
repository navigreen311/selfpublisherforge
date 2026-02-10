# W10: Fix Style Cloning Hardcoded Thresholds

## Branch: `fix/w10-style-cloning-thresholds`

## Files YOU Own (only modify these):
- `backend/app/modules/style_cloning/profile_generator.py`
- `backend/app/modules/style_cloning/features.py`

## Task

### Fix 1: profile_generator.py — Hardcoded thresholds (lines ~140, ~171)

The values `0.5` are used as intensity and ratio thresholds.

1. Add at top of file:
```python
import os

INTENSITY_THRESHOLD = float(os.environ.get("STYLE_INTENSITY_THRESHOLD", "0.5"))
RATIO_THRESHOLD = float(os.environ.get("STYLE_RATIO_THRESHOLD", "0.5"))
```

2. Replace the hardcoded `0.5` values with the appropriate constant. Read the context to determine which constant applies to which location.

### Fix 2: features.py — Review placeholder comment (line ~44)

Line 44 has: `_CONTENT_POS_PREFIXES = frozenset()  # placeholder; we rely on heuristics below`

This is documented as intentional (the frozenset IS empty by design, heuristics are used instead). Add a clearer comment:
```python
# Empty by design: feature extraction uses heuristic analysis rather than POS prefix matching
_CONTENT_POS_PREFIXES: frozenset[str] = frozenset()
```

### Fix 3: profile_generator.py — Review placeholder (line ~64)

Line 64 has a "placeholder — populated below" comment. If the value IS populated later in the code, update the comment to clarify the flow. If it's actually never populated, that's a bug to fix.

## Verification
```bash
cd backend && python -c "from app.modules.style_cloning import profile_generator, features; print('imports OK')"
```
