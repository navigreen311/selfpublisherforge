# W05: Fix Amazon Ads — Bid Constants, Stub Warnings, Error Handling

## Branch: `fix/w05-amazon-ads-fixes`

## Files YOU Own (only modify these):
- `backend/app/modules/advertising/amazon_ads.py`

## Task

Multiple issues in this file need fixing.

### Fix 1: Replace hardcoded bid amount 0.75

The value `0.75` appears ~5 times as a default bid amount. Replace all occurrences with a module-level constant:

```python
# At the top of the file, after imports:
DEFAULT_BID_AMOUNT = float(os.environ.get("DEFAULT_BID_AMOUNT", "0.75"))
```

Then find-and-replace all hardcoded `0.75` bid values with `DEFAULT_BID_AMOUNT`. Be careful to only replace bid-related 0.75 values, not any other use of that number.

### Fix 2: Add warning logging for stub data returns

Add a module logger if not present:
```python
import logging
logger = logging.getLogger(__name__)
```

There are 6 methods that return stub/empty data when `self._is_configured` is False:
1. `add_keywords` — returns stub keyword list
2. `update_keyword_bids` — returns stub with "updated": False
3. `add_negative_keywords` — returns stub list
4. `get_campaign_report` — returns zeroed metrics dict
5. `get_keyword_report` — returns empty list
6. `get_search_term_report` — returns empty list

In each of these methods, before the stub return, add:
```python
logger.warning("Amazon Ads not configured — returning stub data for %s", "<method_name>")
```

### Fix 3: Check for any remaining `except Exception: pass` blocks
If found, replace with `except Exception: logger.exception("...")`.

## Verification
```bash
cd backend && python -c "from app.modules.advertising.amazon_ads import AmazonAdsClient, DEFAULT_BID_AMOUNT; print(f'Default bid: {DEFAULT_BID_AMOUNT}')"
cd backend && grep -n "0\.75" app/modules/advertising/amazon_ads.py || echo "No hardcoded 0.75 remaining"
```
