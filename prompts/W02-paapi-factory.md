# W02: Fix PA-API Factory in amazon_client.py

## Branch: `fix/w02-paapi-factory`

## Files YOU Own (only modify these):
- `backend/app/modules/market_intelligence/amazon_client.py`

## Task

The `get_amazon_client()` factory function at the bottom of the file silently falls through to `MockAmazonClient()` even when PA-API credentials ARE provided. The `if` block checking for credentials just has `pass`.

### Fix Required:

1. Add `import logging` at the top and create a module logger:
```python
logger = logging.getLogger(__name__)
```

2. Rewrite `get_amazon_client()`:
```python
def get_amazon_client() -> AmazonClientBase:
    """Return the Amazon client.

    When PA-API credentials are configured via environment variables,
    a live client would be returned. Until PA-API integration is implemented,
    falls back to the mock client for development and testing.
    """
    import os

    access_key = os.environ.get("AMAZON_PAAPI_ACCESS_KEY", "")
    secret_key = os.environ.get("AMAZON_PAAPI_SECRET_KEY", "")
    partner_tag = os.environ.get("AMAZON_PAAPI_PARTNER_TAG", "")

    if access_key and secret_key and partner_tag:
        logger.warning(
            "PA-API credentials provided but LiveAmazonClient is not yet implemented. "
            "Falling back to MockAmazonClient. Implement LiveAmazonClient to use real data."
        )

    logger.info("Using MockAmazonClient for market intelligence data")
    return MockAmazonClient()
```

The key change: instead of silently falling through with `pass`, it now **logs a warning** when credentials exist but the live client isn't implemented yet. This makes it obvious to operators why mock data is being returned.

## Verification
```bash
cd backend && python -c "from app.modules.market_intelligence.amazon_client import get_amazon_client; c = get_amazon_client(); print(type(c).__name__)"
```
