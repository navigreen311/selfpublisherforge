"""FastAPI router for Children's Books CRUD endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty_books import service_childrens as svc
from app.modules.specialty_books.schemas_childrens import (
    CharacterCreate,
    CharacterResponse,
    CharacterUpdate,
    ChildrensBookCreate,
    ChildrensBookListResponse,
    ChildrensBookResponse,
    ChildrensBookUpdate,
    PageCreate,
    PageReorderRequest,
    PageResponse,
    PageUpdate,
)

router = APIRouter()


@router.get("/", response_model=ChildrensBookListResponse, summary="List children's books")
async def list_books(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * per_page
    return await svc.list_childrens_books(db, current_user["org_id"], skip, per_page)


@router.post(
    "/", response_model=ChildrensBookResponse, status_code=status.HTTP_201_CREATED, summary="Create children's book"
)
async def create_book(
    body: ChildrensBookCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await svc.create_childrens_book(db, current_user["org_id"], body.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.get("/{book_id}", response_model=ChildrensBookResponse, summary="Get children's book")
async def get_book(book_id: UUID, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await svc.get_childrens_book(db, book_id, current_user["org_id"])
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Children's book not found.")
    return result


@router.patch("/{book_id}", response_model=ChildrensBookResponse, summary="Update children's book")
async def update_book(
    book_id: UUID,
    body: ChildrensBookUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_childrens_book(db, book_id, current_user["org_id"], body.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Children's book not found.")
    return result


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete children's book")
async def delete_book(
    book_id: UUID, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    deleted = await svc.delete_childrens_book(db, book_id, current_user["org_id"])
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Children's book not found.")


@router.get("/{book_id}/pages", response_model=list[PageResponse], summary="List pages")
async def list_pages(book_id: UUID, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await svc.list_pages(db, book_id, current_user["org_id"])
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Children's book not found.")
    return result


@router.post(
    "/{book_id}/pages", response_model=PageResponse, status_code=status.HTTP_201_CREATED, summary="Create page"
)
async def create_page(
    book_id: UUID,
    body: PageCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.create_page(db, book_id, current_user["org_id"], body.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Children's book not found.")
    return result


@router.patch("/{book_id}/pages/{page_id}", response_model=PageResponse, summary="Update page")
async def update_page(
    book_id: UUID,
    page_id: UUID,
    body: PageUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_page(db, book_id, page_id, current_user["org_id"], body.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found.")
    return result


@router.delete("/{book_id}/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete page")
async def delete_page(
    book_id: UUID,
    page_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await svc.delete_page(db, book_id, page_id, current_user["org_id"])
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found.")


@router.post("/{book_id}/pages/reorder", response_model=list[PageResponse], summary="Reorder pages")
async def reorder_pages(
    book_id: UUID,
    body: PageReorderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.reorder_pages(db, book_id, current_user["org_id"], body.pages)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Children's book not found.")
    return result


@router.post("/{book_id}/pages/{page_id}/upload-image", response_model=PageResponse, summary="Upload page image")
async def upload_page_image(
    book_id: UUID,
    page_id: UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_url = f"/uploads/childrens-books/{book_id}/pages/{page_id}/{file.filename}"
    result = await svc.upload_page_image(db, book_id, page_id, current_user["org_id"], file_url)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found.")
    return result


@router.get("/{book_id}/characters", response_model=list[CharacterResponse], summary="List characters")
async def list_characters(
    book_id: UUID, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await svc.list_characters(db, book_id, current_user["org_id"])
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Children's book not found.")
    return result


@router.post(
    "/{book_id}/characters",
    response_model=CharacterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create character",
)
async def create_character(
    book_id: UUID,
    body: CharacterCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.create_character(db, book_id, current_user["org_id"], body.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Children's book not found.")
    return result


@router.get("/{book_id}/characters/{char_id}", response_model=CharacterResponse, summary="Get character")
async def get_character(
    book_id: UUID,
    char_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.get_character(db, book_id, char_id, current_user["org_id"])
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found.")
    return result


@router.patch("/{book_id}/characters/{char_id}", response_model=CharacterResponse, summary="Update character")
async def update_character(
    book_id: UUID,
    char_id: UUID,
    body: CharacterUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_character(
        db, book_id, char_id, current_user["org_id"], body.model_dump(exclude_unset=True)
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found.")
    return result


@router.delete("/{book_id}/characters/{char_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete character")
async def delete_character(
    book_id: UUID,
    char_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await svc.delete_character(db, book_id, char_id, current_user["org_id"])
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found.")
