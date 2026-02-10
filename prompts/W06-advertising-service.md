# W06: Fix Advertising Service — Silent Exception, Bid Reference

## Branch: `fix/w06-advertising-service`

## Files YOU Own (only modify these):
- `backend/app/modules/advertising/service.py`

## Task

### Fix 1: Silent exception swallowing (line ~112)

There is an `except Exception: pass` inside a campaign processing loop. This silently drops errors.

```python
# BEFORE (bad):
except Exception:
    pass

# AFTER (good):
except Exception:
    logger.exception("Failed to process campaign %s", campaign_id_or_relevant_var)
    continue  # Continue processing remaining campaigns
```

Add `import logging` and `logger = logging.getLogger(__name__)` if not already present.

### Fix 2: Hardcoded bid amount (line ~199)

Find the hardcoded `0.75` bid amount and replace with:
```python
DEFAULT_BID_AMOUNT = float(os.environ.get("DEFAULT_BID_AMOUNT", "0.75"))
```

Add `import os` if not present. Then use `DEFAULT_BID_AMOUNT` instead of the literal.

### Fix 3: Check for other `except: pass` or `except Exception: pass` patterns
Search the entire file. Any silent swallows should get `logger.exception(...)` or at minimum `logger.warning(...)`.

## Verification
```bash
cd backend && python -c "from app.modules.advertising.service import *; print('imports OK')"
cd backend && grep -n "except.*pass" app/modules/advertising/service.py || echo "No silent exceptions remaining"
```
