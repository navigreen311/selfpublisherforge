# W08: Make Facebook Ads API Version Configurable

## Branch: `fix/w08-facebook-ads-version`

## Files YOU Own (only modify these):
- `backend/app/modules/advertising/facebook_ads.py`

## Task

Line ~47 has a hardcoded Facebook Graph API version:
```python
"https://graph.facebook.com/v18.0"
```

### Fix Required:

1. At the top of the file, add:
```python
import os

FACEBOOK_ADS_API_VERSION = os.environ.get("FACEBOOK_ADS_API_VERSION", "v18.0")
FACEBOOK_GRAPH_API_BASE = f"https://graph.facebook.com/{FACEBOOK_ADS_API_VERSION}"
```

2. Replace ALL hardcoded `https://graph.facebook.com/v18.0` references with `FACEBOOK_GRAPH_API_BASE`.

3. Search the file for any other hardcoded API versions (e.g., `v17.0`, `v19.0`) and fix similarly.

4. Check for any `except Exception: pass` or other silent error swallowing and fix with proper logging.

## Verification
```bash
cd backend && python -c "from app.modules.advertising.facebook_ads import FACEBOOK_GRAPH_API_BASE; print(FACEBOOK_GRAPH_API_BASE)"
cd backend && grep -n "graph.facebook.com/v" app/modules/advertising/facebook_ads.py
```
