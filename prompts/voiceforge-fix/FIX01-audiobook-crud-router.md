# FIX01: Audiobook Project CRUD Router

## Task
Create the missing audiobook project CRUD API endpoints.

## File to Create: `backend/app/modules/audiobook/router_crud.py`

### Patterns to Follow
- Look at `backend/app/modules/audiobook/router.py` for import conventions
- Use `APIRouter()`, `Depends(get_current_user)`, `Depends(get_db)`, `AsyncSession`
- Use `from app.core.dependencies import get_current_user`
- Use `from app.database import get_db`
- Async endpoints, org_id tenant scoping from `current_user["org_id"]`

### Endpoints to Implement

```python
router = APIRouter()

# POST / — Create audiobook project from a book
@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreateRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    # body has: book_id, title (optional), narrator_voice_id (optional), output_format, target_platform
    return await service_crud.create_project(db, current_user["org_id"], body)

# GET / — List audiobook projects (paginated)
@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    return await service_crud.list_projects(db, current_user["org_id"], page, per_page, status)

# GET /{project_id} — Get project with chapters
@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await service_crud.get_project(db, project_id, current_user["org_id"])
    if not result:
        raise HTTPException(404, "Project not found")
    return result

# PATCH /{project_id} — Update project settings
@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, body: ProjectUpdateRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await service_crud.update_project(db, project_id, current_user["org_id"], body)
    if not result:
        raise HTTPException(404, "Project not found")
    return result

# DELETE /{project_id} — Soft delete project
@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    deleted = await service_crud.delete_project(db, project_id, current_user["org_id"])
    if not deleted:
        raise HTTPException(404, "Project not found")
```

### Import schemas from `schemas_extended.py` (created by FIX09)
Use these schema names: `ProjectCreateRequest`, `ProjectUpdateRequest`, `ProjectResponse`, `ProjectDetailResponse`, `ProjectListResponse`

Import service as: `from app.modules.audiobook import service_crud`

## Conventions
- Read existing router.py first to match style exactly
- All endpoints must be async
- Use UUID type for IDs
- Proper HTTP status codes and error messages
