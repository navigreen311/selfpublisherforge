# W01: Add Missing Configuration Settings to backend/app/config.py

## Branch: `fix/w01-config-settings`

## Files YOU Own (only modify these):
- `backend/app/config.py`

## Task

Add the following missing configuration settings to the `Settings` class in `backend/app/config.py`. Read the file first to understand the existing pattern, then add these settings in logical sections:

### 1. Frontend URL (used by billing redirects)
```python
FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")
```

### 2. Chrome Extension ID
```python
CHROME_EXTENSION_ID: str = os.environ.get("CHROME_EXTENSION_ID", "")
```

### 3. Default Ad Bid Amount
```python
DEFAULT_BID_AMOUNT: float = float(os.environ.get("DEFAULT_BID_AMOUNT", "0.75"))
```

### 4. Facebook Ads API Version
```python
FACEBOOK_ADS_API_VERSION: str = os.environ.get("FACEBOOK_ADS_API_VERSION", "v18.0")
```

### 5. Market Intelligence Scoring Thresholds
```python
# Market intelligence scoring midpoints (sigmoid scaling)
MI_DEMAND_MIDPOINT: int = int(os.environ.get("MI_DEMAND_MIDPOINT", "5000"))
MI_COMPETITION_MIDPOINT: int = int(os.environ.get("MI_COMPETITION_MIDPOINT", "50000"))
MI_OPPORTUNITY_MIDPOINT: int = int(os.environ.get("MI_OPPORTUNITY_MIDPOINT", "500"))
```

### 6. AI Writing Word Count Multiplier
```python
AI_WORD_COUNT_MULTIPLIER: float = float(os.environ.get("AI_WORD_COUNT_MULTIPLIER", "0.5"))
```

Place these in appropriate sections within the existing Settings class. Follow the existing code style exactly (uppercase names, os.environ.get pattern).

Also update `backend/.env.example` to document each new variable in the appropriate section with a comment explaining its purpose.

## Verification
```bash
cd backend && python -c "from app.config import settings; print(settings.FRONTEND_URL)"
```
