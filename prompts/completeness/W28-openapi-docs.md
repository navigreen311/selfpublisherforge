# W28: OpenAPI Documentation Completeness

## Files to modify
- All router files in `backend/app/modules/*/router.py` that have missing descriptions

## Task

### 1. Audit all routers

Read every router.py file across all modules. For each endpoint, verify it has:
- `summary` parameter (short title)
- `description` parameter or docstring (detailed explanation)
- `response_model` type hint
- Appropriate `status_code`
- `tags` for grouping in Swagger UI

### 2. Add missing documentation

For any endpoint missing documentation, add it. Example:

```python
@router.get(
    "/items",
    response_model=list[ItemResponse],
    summary="List all items",
    description="Returns a paginated list of items belonging to the authenticated user's organization.",
    tags=["items"],
)
```

### 3. Add response descriptions

For key endpoints, add response model descriptions:

```python
from fastapi import responses

@router.get(
    "/dashboard",
    response_model=DashboardData,
    summary="Get analytics dashboard",
    responses={
        200: {"description": "Dashboard data including KPIs, charts, and recent activity"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized for this organization"},
    },
)
```

### 4. Verify OpenAPI schema generation

Read `backend/app/main.py` to check the app title, description, version, and OpenAPI configuration. Ensure it's properly set:

```python
app = FastAPI(
    title="SelfPublisherForge API",
    description="AI-powered self-publishing platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
```

Focus on the modules that currently have the least documentation. Don't add excessive text — keep descriptions concise and useful.
