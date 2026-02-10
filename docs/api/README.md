# SelfPublisherForge API Documentation

This document describes how to explore, authenticate against, and export the SelfPublisherForge REST API.

## Interactive documentation

Once the backend is running (`uvicorn app.main:app` or `docker compose up`), two auto-generated documentation UIs are available:

| UI | URL | Notes |
|----|-----|-------|
| **Swagger UI** | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | Interactive "try it out" console with request builder |
| **ReDoc** | [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc) | Clean, read-only reference with a three-panel layout |

Both are generated automatically from the OpenAPI specification and always reflect the current state of the code.

## Authentication

Most endpoints require a **Bearer JWT** token.

### Obtaining a token

1. **Register** a new account:

   ```
   POST /api/v1/auth/register
   Content-Type: application/json

   {
     "email": "you@example.com",
     "password": "SecureP@ss1",
     "name": "Your Name",
     "org_name": "My Publishing Co"
   }
   ```

2. **Login** with existing credentials:

   ```
   POST /api/v1/auth/login
   Content-Type: application/json

   {
     "email": "you@example.com",
     "password": "SecureP@ss1"
   }
   ```

Both endpoints return a JSON body containing `tokens.access_token` and `tokens.refresh_token`.

### Using the token

Include the access token in the `Authorization` header of every subsequent request:

```
Authorization: Bearer <access_token>
```

In Swagger UI, click the **Authorize** button (lock icon) at the top of the page and paste your access token.

### Refreshing tokens

Access tokens expire after 15 minutes by default. Use the refresh token to obtain a new pair:

```
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

### MFA (optional)

If a user has multi-factor authentication enabled, the login response will include an `mfa_required` flag. Submit the TOTP code via the same login endpoint using the `mfa_code` field.

### OAuth

Google and GitHub OAuth flows are supported. Redirect the user to the authorization URL returned by:

- `GET /api/v1/auth/oauth/google`
- `GET /api/v1/auth/oauth/github`

The callback endpoints exchange the authorization code for JWT tokens.

## Endpoint groups

The API is organized into tiered modules. Each group is tagged in the OpenAPI spec for easy filtering in Swagger UI.

### Tier 0 -- Foundation

| Tag | Prefix | Description |
|-----|--------|-------------|
| `auth` | `/api/v1/auth` | Registration, login, logout, password reset, email verification, MFA, OAuth |
| `users` | `/api/v1` | User profile and organization management |
| `billing` | `/api/v1/billing` | Plans, Stripe checkout, subscriptions, invoices, usage |
| `storage` | `/api/v1/storage` | S3 pre-signed URLs and asset management |
| `notifications` | `/api/v1/notifications` | In-app and email notifications |
| `realtime` | (WebSocket) | Real-time event streaming |

### Tier 1-2 -- Data and Creation

| Tag | Prefix | Description |
|-----|--------|-------------|
| `llm` | `/api/v1/llm` | LLM orchestration, model selection, prompt execution |
| `market` | `/api/v1/market` | Category browsing, keyword research, niche analysis, competitor tracking, trends |
| `knowledge` | `/api/v1/knowledge` | Knowledge vault CRUD, search, import, tags, AI summaries |
| `writing` | `/api/v1` | AI content generation (SSE streaming), manuscript/chapter CRUD, outlines, readability |
| `style` | `/api/v1/style-profiles` | Author voice/style profiles for consistent AI writing |

### Tier 3 -- Production

| Tag | Prefix | Description |
|-----|--------|-------------|
| `pipelines` | `/api/v1/pipelines` | Manuscript production pipeline and stage tracking |
| `publishing` | `/api/v1/publishing` | Platform accounts, listing management, EPUB/PDF export, book metadata |
| `kdp-validation` | `/api/v1` | Amazon KDP compliance pre-flight checks |

### Tier 4 -- Optimization

| Tag | Prefix | Description |
|-----|--------|-------------|
| `product-page` | `/api/v1/product-page` | A/B testing for titles, descriptions, and keywords |
| `pricing` | `/api/v1` | Dynamic pricing recommendations and rules |
| `competitors` | `/api/v1/competitors` | Competitor discovery and tracking |

### Tier 5 -- Growth

| Tag | Prefix | Description |
|-----|--------|-------------|
| `marketing` | `/api/v1/marketing` | Launch plans, email sequences, social content, ARC campaigns |
| `advertising` | `/api/v1/ads` | Amazon Ads and Facebook Ads campaign management, bid optimization, creative generation |
| `reviews` | `/api/v1/reviews` | Review monitoring and analysis |
| `analytics` | `/api/v1/analytics` | Revenue dashboards, royalty imports, portfolio metrics, report generation, trends |

### Tier 6-8 -- Intelligence and Scale

| Tag | Prefix | Description |
|-----|--------|-------------|
| `agents` | `/api/v1/agents` | Autonomous AI agents with governance, budgets, and audit logs |
| `portfolio` | `/api/v1` | Cross-book financial modeling and ROI tracking |
| `audience` | `/api/v1` | Reader segmentation and engagement scoring |
| `seasonal` | `/api/v1` | Calendar-driven promotions and seasonal forecasts |
| `covers` | `/api/v1` | AI-assisted cover design |
| `chrome-extension` | `/api/v1` | Browser extension API for on-page market research |

## Exporting the OpenAPI spec

### As JSON (default)

The raw OpenAPI 3.x JSON document is served at:

```
GET http://localhost:8000/api/v1/openapi.json
```

Save it to a file with curl:

```bash
curl -s http://localhost:8000/api/v1/openapi.json -o openapi.json
```

### As YAML

FastAPI serves JSON natively. To convert to YAML, pipe through a converter:

```bash
# Using Python (PyYAML must be installed)
python -c "
import json, yaml, sys
with open('openapi.json') as f:
    data = json.load(f)
yaml.dump(data, sys.stdout, default_flow_style=False, sort_keys=False)
" > openapi.yaml
```

Or with `yq` if installed:

```bash
cat openapi.json | yq -y . > openapi.yaml
```

### Programmatic generation (without running the server)

You can generate the schema directly from the application factory:

```python
import json
from app.main import create_app

app = create_app()
schema = app.openapi()
with open("openapi.json", "w") as f:
    json.dump(schema, f, indent=2)
```

## Enabling the custom OpenAPI schema

A custom OpenAPI schema generator is provided at `backend/app/core/openapi.py`. It adds structured tag descriptions, a global Bearer JWT security scheme, and a detailed API overview.

To activate it, add the following to `main.py` inside `create_app()`, after the routers are registered:

```python
from app.core.openapi import custom_openapi_schema

def create_app() -> FastAPI:
    app = FastAPI(...)
    # ... middleware, error handlers, routers ...
    app.openapi = custom_openapi_schema(app)
    return app
```

No other changes are required. The custom schema is generated lazily on first request and cached for subsequent calls.

## Health check

A simple health endpoint is available without authentication:

```
GET /health
GET /api/v1/health
```

Response:

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```
