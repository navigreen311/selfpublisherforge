# W03: Fix Chrome Extension ID Placeholder

## Branch: `fix/w03-extension-constants`

## Files YOU Own (only modify these):
- `backend/app/modules/chrome_extension/constants.py`

## Task

The file has a hardcoded `EXTENSION_ID` placeholder in the Chrome Web Store URL on line 8:
```python
"https://chromewebstore.google.com/detail/selfpublisherforge/EXTENSION_ID"
```

### Fix Required:

1. Import `os` at the top of the file
2. Read the extension ID from an environment variable
3. Construct the URL dynamically

```python
import os

CHROME_EXTENSION_ID = os.environ.get("CHROME_EXTENSION_ID", "")

CHROME_WEBSTORE_URL = (
    f"https://chromewebstore.google.com/detail/selfpublisherforge/{CHROME_EXTENSION_ID}"
    if CHROME_EXTENSION_ID
    else ""
)
```

4. Find any other references to the old hardcoded URL in this file and update them to use `CHROME_WEBSTORE_URL`.

5. If there's an `EXTENSION_UPDATE_URL` or similar, also make it dynamic using the same `CHROME_EXTENSION_ID`.

## Verification
```bash
cd backend && python -c "from app.modules.chrome_extension.constants import CHROME_EXTENSION_ID; print(f'ID: {CHROME_EXTENSION_ID!r}')"
```
