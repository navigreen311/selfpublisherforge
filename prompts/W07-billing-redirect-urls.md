# W07: Fix Hardcoded Billing Redirect URLs

## Branch: `fix/w07-billing-redirect-urls`

## Files YOU Own (only modify these):
- `backend/app/billing/schemas.py`

## Task

Lines ~90, ~94, and ~110 have hardcoded `http://localhost:3000/settings/billing...` URLs used as Stripe checkout redirect URLs.

### Fix Required:

1. At the top of the file, read the frontend URL from environment:
```python
import os
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
```

2. Replace all hardcoded `http://localhost:3000` references with `FRONTEND_URL`:

```python
# BEFORE:
success_url = "http://localhost:3000/settings/billing?success=true"
cancel_url = "http://localhost:3000/settings/billing?canceled=true"
return_url = "http://localhost:3000/settings/billing"

# AFTER:
success_url = f"{FRONTEND_URL}/settings/billing?success=true"
cancel_url = f"{FRONTEND_URL}/settings/billing?canceled=true"
return_url = f"{FRONTEND_URL}/settings/billing"
```

3. Search the entire file for any other `localhost` references and fix them the same way.

## Verification
```bash
cd backend && python -c "from app.billing.schemas import *; print('imports OK')"
cd backend && grep -n "localhost" app/billing/schemas.py || echo "No hardcoded localhost remaining"
```
