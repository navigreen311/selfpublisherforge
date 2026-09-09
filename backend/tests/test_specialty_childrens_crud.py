"""Tests for Children's Books CRUD API — 25 tests covering service layer."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.compiler import compiles


@compiles(ARRAY, "sqlite")
def _compile_sa_array_sqlite(element, compiler, **kw):
    return "TEXT"


from app.modules.specialty_books import service_childrens as svc

ORG_ID = uuid.uuid4()
OTHER_ORG_ID = uuid.uuid4()


async def _mk_book(db, org_id=ORG_ID, **kw):
    return await svc.create_childrens_book(db, org_id, {"title": "T", "author": "A", "age_range": "4-6", **kw})


async def _mk_page(db, book_id, n=1, org_id=ORG_ID):
    return await svc.create_page(db, book_id, org_id, {"page_number": n, "text_content": f"P{n}"})


async def _mk_char(db, book_id, name="Luna", org_id=ORG_ID):
    return await svc.create_character(db, book_id, org_id, {"name": name, "species": "cat"})


@pytest.mark.asyncio
async def test_list_books_empty(db_session: AsyncSession):
    r = await svc.list_childrens_books(db_session, ORG_ID)
    assert r["items"] == [] and r["total"] == 0


@pytest.mark.asyncio
async def test_create_book_valid(db_session: AsyncSession):
    b = await _mk_book(db_session, title="My Book")
    assert b.title == "My Book" and b.status == "draft" and b.id is not None


@pytest.mark.asyncio
async def test_create_book_invalid_age_range(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Invalid age_range"):
        await svc.create_childrens_book(db_session, ORG_ID, {"title": "X", "age_range": "99"})


@pytest.mark.asyncio
async def test_list_books_with_data(db_session: AsyncSession):
    await _mk_book(db_session, title="A")
    await _mk_book(db_session, title="B")
    r = await svc.list_childrens_books(db_session, ORG_ID)
    assert r["total"] == 2


@pytest.mark.asyncio
async def test_get_book_by_id(db_session: AsyncSession):
    b = await _mk_book(db_session)
    f = await svc.get_childrens_book(db_session, b.id, ORG_ID)
    assert f and f.id == b.id


@pytest.mark.asyncio
async def test_get_nonexistent_book(db_session: AsyncSession):
    assert await svc.get_childrens_book(db_session, uuid.uuid4(), ORG_ID) is None


@pytest.mark.asyncio
async def test_update_book_partial(db_session: AsyncSession):
    b = await _mk_book(db_session, title="Old")
    u = await svc.update_childrens_book(db_session, b.id, ORG_ID, {"title": "New"})
    assert u and u.title == "New" and u.age_range == "4-6"


@pytest.mark.asyncio
async def test_delete_book_soft(db_session: AsyncSession):
    b = await _mk_book(db_session)
    assert await svc.delete_childrens_book(db_session, b.id, ORG_ID) is True
    assert await svc.get_childrens_book(db_session, b.id, ORG_ID) is None


@pytest.mark.asyncio
async def test_delete_nonexistent_book(db_session: AsyncSession):
    assert await svc.delete_childrens_book(db_session, uuid.uuid4(), ORG_ID) is False


@pytest.mark.asyncio
async def test_create_page(db_session: AsyncSession):
    b = await _mk_book(db_session)
    p = await _mk_page(db_session, b.id)
    assert p and p.page_number == 1 and p.book_id == b.id


@pytest.mark.asyncio
async def test_list_pages_ordered(db_session: AsyncSession):
    b = await _mk_book(db_session)
    await _mk_page(db_session, b.id, 3)
    await _mk_page(db_session, b.id, 1)
    await _mk_page(db_session, b.id, 2)
    pages = await svc.list_pages(db_session, b.id, ORG_ID)
    assert [p.page_number for p in pages] == [1, 2, 3]


@pytest.mark.asyncio
async def test_update_page(db_session: AsyncSession):
    b = await _mk_book(db_session)
    p = await _mk_page(db_session, b.id)
    u = await svc.update_page(db_session, b.id, p.id, ORG_ID, {"text_content": "new"})
    assert u and u.text_content == "new"


@pytest.mark.asyncio
async def test_delete_page(db_session: AsyncSession):
    b = await _mk_book(db_session)
    p = await _mk_page(db_session, b.id)
    assert await svc.delete_page(db_session, b.id, p.id, ORG_ID) is True
    assert len(await svc.list_pages(db_session, b.id, ORG_ID)) == 0


@pytest.mark.asyncio
async def test_reorder_pages(db_session: AsyncSession):
    b = await _mk_book(db_session)
    p1 = await _mk_page(db_session, b.id, 1)
    p2 = await _mk_page(db_session, b.id, 2)
    p3 = await _mk_page(db_session, b.id, 3)
    r = await svc.reorder_pages(db_session, b.id, ORG_ID, [p3.id, p2.id, p1.id])
    assert r[0].id == p3.id and r[0].page_number == 1


@pytest.mark.asyncio
async def test_upload_page_image(db_session: AsyncSession):
    b = await _mk_book(db_session)
    p = await _mk_page(db_session, b.id)
    u = await svc.upload_page_image(db_session, b.id, p.id, ORG_ID, "/img.png")
    assert u and u.illustration_url == "/img.png"


@pytest.mark.asyncio
async def test_create_character(db_session: AsyncSession):
    b = await _mk_book(db_session)
    c = await _mk_char(db_session, b.id, "Whiskers")
    assert c and c.name == "Whiskers" and c.book_id == b.id


@pytest.mark.asyncio
async def test_list_characters(db_session: AsyncSession):
    b = await _mk_book(db_session)
    await _mk_char(db_session, b.id, "A")
    await _mk_char(db_session, b.id, "B")
    assert len(await svc.list_characters(db_session, b.id, ORG_ID)) == 2


@pytest.mark.asyncio
async def test_get_character(db_session: AsyncSession):
    b = await _mk_book(db_session)
    c = await _mk_char(db_session, b.id, "Bella")
    f = await svc.get_character(db_session, b.id, c.id, ORG_ID)
    assert f and f.name == "Bella"


@pytest.mark.asyncio
async def test_update_character(db_session: AsyncSession):
    b = await _mk_book(db_session)
    c = await _mk_char(db_session, b.id)
    u = await svc.update_character(db_session, b.id, c.id, ORG_ID, {"name": "Shadow"})
    assert u and u.name == "Shadow"


@pytest.mark.asyncio
async def test_delete_character(db_session: AsyncSession):
    b = await _mk_book(db_session)
    c = await _mk_char(db_session, b.id)
    assert await svc.delete_character(db_session, b.id, c.id, ORG_ID) is True
    assert len(await svc.list_characters(db_session, b.id, ORG_ID)) == 0


@pytest.mark.asyncio
async def test_org_isolation_get(db_session: AsyncSession):
    b = await _mk_book(db_session)
    assert await svc.get_childrens_book(db_session, b.id, OTHER_ORG_ID) is None


@pytest.mark.asyncio
async def test_org_isolation_update(db_session: AsyncSession):
    b = await _mk_book(db_session)
    assert await svc.update_childrens_book(db_session, b.id, OTHER_ORG_ID, {"title": "X"}) is None


@pytest.mark.asyncio
async def test_org_isolation_delete(db_session: AsyncSession):
    b = await _mk_book(db_session)
    assert await svc.delete_childrens_book(db_session, b.id, OTHER_ORG_ID) is False


@pytest.mark.asyncio
async def test_org_isolation_pages(db_session: AsyncSession):
    b = await _mk_book(db_session)
    await _mk_page(db_session, b.id)
    assert await svc.list_pages(db_session, b.id, OTHER_ORG_ID) is None


@pytest.mark.asyncio
async def test_org_isolation_characters(db_session: AsyncSession):
    b = await _mk_book(db_session)
    await _mk_char(db_session, b.id)
    assert await svc.list_characters(db_session, b.id, OTHER_ORG_ID) is None
