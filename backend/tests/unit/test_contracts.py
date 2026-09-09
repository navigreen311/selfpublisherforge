"""Unit tests for app.core.contracts -- API response/request contracts.

Validates that SuccessResponse, PaginatedResponse, ErrorResponse, and related
models serialize correctly and enforce their schemas.
"""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel, ValidationError

from app.core.contracts import (
    ErrorDetail,
    ErrorResponse,
    PaginatedRequest,
    PaginatedResponse,
    SuccessResponse,
)

# ---------------------------------------------------------------------------
# Helpers -- small domain models used as generic type arguments
# ---------------------------------------------------------------------------

class _UserOut(BaseModel):
    id: int
    name: str


class _BookOut(BaseModel):
    isbn: str
    title: str
    price: float


# ===================================================================
# SuccessResponse
# ===================================================================

class TestSuccessResponse:
    """SuccessResponse[T] wraps arbitrary data in a ``data`` field."""

    def test_with_string_data(self):
        resp = SuccessResponse[str](data="hello")
        assert resp.data == "hello"

    def test_with_int_data(self):
        resp = SuccessResponse[int](data=42)
        assert resp.data == 42

    def test_with_float_data(self):
        resp = SuccessResponse[float](data=3.14)
        assert resp.data == 3.14

    def test_with_bool_data(self):
        resp = SuccessResponse[bool](data=True)
        assert resp.data is True

    def test_with_none_data(self):
        resp = SuccessResponse[None](data=None)
        assert resp.data is None

    def test_with_list_data(self):
        resp = SuccessResponse[list[int]](data=[1, 2, 3])
        assert resp.data == [1, 2, 3]

    def test_with_dict_data(self):
        payload = {"key": "value", "nested": {"a": 1}}
        resp = SuccessResponse[dict](data=payload)
        assert resp.data == payload

    def test_with_pydantic_model(self):
        user = _UserOut(id=1, name="Alice")
        resp = SuccessResponse[_UserOut](data=user)
        assert resp.data.id == 1
        assert resp.data.name == "Alice"

    def test_serialization_to_dict(self):
        resp = SuccessResponse[str](data="test")
        d = resp.model_dump()
        assert d == {"data": "test"}

    def test_serialization_to_json(self):
        resp = SuccessResponse[int](data=99)
        raw = resp.model_dump_json()
        parsed = json.loads(raw)
        assert parsed == {"data": 99}

    def test_nested_model_serialization(self):
        book = _BookOut(isbn="978-0-13-468599-1", title="Clean Code", price=29.99)
        resp = SuccessResponse[_BookOut](data=book)
        d = resp.model_dump()
        assert d["data"]["isbn"] == "978-0-13-468599-1"
        assert d["data"]["title"] == "Clean Code"
        assert d["data"]["price"] == 29.99

    def test_missing_data_raises(self):
        with pytest.raises(ValidationError):
            SuccessResponse[str]()  # type: ignore[call-arg]


# ===================================================================
# ErrorDetail
# ===================================================================

class TestErrorDetail:
    """ErrorDetail carries per-field validation info."""

    def test_with_field(self):
        detail = ErrorDetail(field="email", message="invalid format")
        assert detail.field == "email"
        assert detail.message == "invalid format"

    def test_field_defaults_to_none(self):
        detail = ErrorDetail(message="something went wrong")
        assert detail.field is None
        assert detail.message == "something went wrong"

    def test_missing_message_raises(self):
        with pytest.raises(ValidationError):
            ErrorDetail()  # type: ignore[call-arg]

    def test_serialization(self):
        detail = ErrorDetail(field="name", message="required")
        d = detail.model_dump()
        assert d == {"field": "name", "message": "required"}


# ===================================================================
# ErrorResponse
# ===================================================================

class TestErrorResponse:
    """ErrorResponse carries a top-level error code, message, and optional details."""

    def test_minimal_error(self):
        err = ErrorResponse(
            code="NOT_FOUND",
            message="Resource not found",
            request_id="req-001",
        )
        assert err.code == "NOT_FOUND"
        assert err.message == "Resource not found"
        assert err.details == []
        assert err.request_id == "req-001"

    def test_with_details(self):
        details = [
            ErrorDetail(field="email", message="invalid"),
            ErrorDetail(field="name", message="too short"),
        ]
        err = ErrorResponse(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details,
            request_id="req-002",
        )
        assert len(err.details) == 2
        assert err.details[0].field == "email"
        assert err.details[1].message == "too short"

    def test_with_empty_details_list(self):
        err = ErrorResponse(
            code="SERVER_ERROR",
            message="Internal error",
            details=[],
            request_id="req-003",
        )
        assert err.details == []

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            ErrorResponse(code="ERR")  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            ErrorResponse(message="msg")  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            ErrorResponse(code="ERR", message="msg")  # type: ignore[call-arg]

    def test_serialization(self):
        err = ErrorResponse(
            code="BAD_REQUEST",
            message="Invalid input",
            details=[ErrorDetail(field="age", message="must be positive")],
            request_id="req-004",
        )
        d = err.model_dump()
        assert d["code"] == "BAD_REQUEST"
        assert d["request_id"] == "req-004"
        assert len(d["details"]) == 1
        assert d["details"][0]["field"] == "age"

    def test_json_round_trip(self):
        err = ErrorResponse(
            code="CONFLICT",
            message="Duplicate entry",
            request_id="req-005",
        )
        raw = err.model_dump_json()
        restored = ErrorResponse.model_validate_json(raw)
        assert restored.code == err.code
        assert restored.message == err.message
        assert restored.request_id == err.request_id


# ===================================================================
# PaginatedRequest
# ===================================================================

class TestPaginatedRequest:
    """PaginatedRequest carries cursor-based pagination parameters."""

    def test_defaults(self):
        req = PaginatedRequest()
        assert req.cursor is None
        assert req.limit == 20
        assert req.sort_by is None
        assert req.sort_dir == "desc"

    def test_custom_values(self):
        req = PaginatedRequest(
            cursor="abc123",
            limit=50,
            sort_by="created_at",
            sort_dir="asc",
        )
        assert req.cursor == "abc123"
        assert req.limit == 50
        assert req.sort_by == "created_at"
        assert req.sort_dir == "asc"

    def test_partial_override(self):
        req = PaginatedRequest(limit=10)
        assert req.limit == 10
        assert req.cursor is None
        assert req.sort_dir == "desc"

    def test_serialization(self):
        req = PaginatedRequest(cursor="xyz", limit=5, sort_by="title", sort_dir="asc")
        d = req.model_dump()
        assert d == {
            "cursor": "xyz",
            "limit": 5,
            "sort_by": "title",
            "sort_dir": "asc",
        }


# ===================================================================
# PaginatedResponse
# ===================================================================

class TestPaginatedResponse:
    """PaginatedResponse[T] carries a page of items plus cursor metadata."""

    def test_empty_page(self):
        page = PaginatedResponse[str](items=[])
        assert page.items == []
        assert page.next_cursor is None
        assert page.has_more is False
        assert page.total_count is None

    def test_single_page(self):
        page = PaginatedResponse[int](
            items=[1, 2, 3],
            has_more=False,
            total_count=3,
        )
        assert page.items == [1, 2, 3]
        assert page.has_more is False
        assert page.total_count == 3

    def test_with_cursor(self):
        page = PaginatedResponse[str](
            items=["a", "b"],
            next_cursor="cursor-after-b",
            has_more=True,
            total_count=100,
        )
        assert page.next_cursor == "cursor-after-b"
        assert page.has_more is True
        assert page.total_count == 100

    def test_with_pydantic_models(self):
        books = [
            _BookOut(isbn="111", title="Book A", price=9.99),
            _BookOut(isbn="222", title="Book B", price=14.99),
        ]
        page = PaginatedResponse[_BookOut](
            items=books,
            has_more=True,
            next_cursor="after-222",
        )
        assert len(page.items) == 2
        assert page.items[0].title == "Book A"
        assert page.items[1].isbn == "222"

    def test_serialization(self):
        page = PaginatedResponse[int](
            items=[10, 20],
            next_cursor="c1",
            has_more=True,
            total_count=50,
        )
        d = page.model_dump()
        assert d == {
            "items": [10, 20],
            "next_cursor": "c1",
            "has_more": True,
            "total_count": 50,
        }

    def test_json_round_trip(self):
        page = PaginatedResponse[str](
            items=["x", "y", "z"],
            next_cursor="after-z",
            has_more=True,
            total_count=26,
        )
        raw = page.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["items"] == ["x", "y", "z"]
        assert parsed["next_cursor"] == "after-z"
        assert parsed["has_more"] is True
        assert parsed["total_count"] == 26

    def test_nested_model_serialization(self):
        users = [_UserOut(id=1, name="A"), _UserOut(id=2, name="B")]
        page = PaginatedResponse[_UserOut](items=users, total_count=2)
        d = page.model_dump()
        assert d["items"][0] == {"id": 1, "name": "A"}
        assert d["items"][1] == {"id": 2, "name": "B"}
        assert d["total_count"] == 2

    def test_missing_items_raises(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[str]()  # type: ignore[call-arg]

    def test_defaults_when_only_items_provided(self):
        page = PaginatedResponse[int](items=[42])
        assert page.next_cursor is None
        assert page.has_more is False
        assert page.total_count is None
