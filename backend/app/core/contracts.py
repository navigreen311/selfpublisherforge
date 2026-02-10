"""API contracts that all modules must follow.

Local copy of shared/contracts/api.py so the backend can run without the
root-level ``shared`` package on sys.path.
"""

from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = []
    request_id: str


class SuccessResponse(BaseModel, Generic[T]):
    data: T


class PaginatedRequest(BaseModel):
    cursor: str | None = None
    limit: int = 20
    sort_by: str | None = None
    sort_dir: str = "desc"


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None
