from pydantic import BaseModel
from typing import TypeVar, Generic
from uuid import UUID

T = TypeVar("T")

class CursorParams(BaseModel):
    cursor: str | None = None
    limit: int = 20

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None
