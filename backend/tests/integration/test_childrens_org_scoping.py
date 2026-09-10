"""Cross-tenant isolation for the children's-book page/character surface.

Only ChildrensBook carries org_id; its pages and characters do not. The lookup
helpers filtered on ``ChildrensBookPage.org_id``, an attribute that does not
exist, so every page and character read raised AttributeError rather than
scoping. These tests pin the replacement — a sub-select over the org's books —
shut, so the surface cannot come back unscoped once it works.
"""

import uuid

import pytest

from app.core.exceptions import NotFoundError
from app.modules.specialty.childrens import service
from app.modules.specialty.models.childrens import (
    ChildrensBook,
    ChildrensBookCharacter,
    ChildrensBookPage,
)


async def _seed(db, org_id):
    book = ChildrensBook(
        id=uuid.uuid4(),
        org_id=org_id,
        title="Org Book",
        author="A. Author",
        age_range="preschool",
        page_count=24,
        trim_size="8.5x8.5",
        illustration_style="watercolor",
        color_palette="bright",
        story_mode="ai_generated",
        fear_intensity="none",
        status="draft",
    )
    page = ChildrensBookPage(
        id=uuid.uuid4(),
        book_id=book.id,
        page_number=1,
        page_type="story",
        layout="image_top_text_bottom",
        text_content="Once upon a time",
    )
    character = ChildrensBookCharacter(
        id=uuid.uuid4(),
        book_id=book.id,
        name="Bramble",
    )
    db.add_all([book, page, character])
    await db.commit()
    return book, page, character


@pytest.mark.asyncio
async def test_page_lookup_is_scoped_to_the_owning_org(db_session):
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    book, page, _ = await _seed(db_session, org_a)

    found = await service._get_page_or_404(db_session, org_a, book.id, page.id)
    assert found.id == page.id

    with pytest.raises(NotFoundError):
        await service._get_page_or_404(db_session, org_b, book.id, page.id)


@pytest.mark.asyncio
async def test_character_lookup_is_scoped_to_the_owning_org(db_session):
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    book, _, character = await _seed(db_session, org_a)

    found = await service._get_character_or_404(db_session, org_a, book.id, character.id)
    assert found.id == character.id

    with pytest.raises(NotFoundError):
        await service._get_character_or_404(db_session, org_b, book.id, character.id)


@pytest.mark.asyncio
async def test_listing_pages_from_another_org_is_a_404(db_session):
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    book, _, _ = await _seed(db_session, org_a)

    assert len(await service.list_pages(db_session, org_a, book.id)) == 1

    # The book itself is org-scoped, so the listing never gets as far as the
    # pages for a caller in another org.
    with pytest.raises(NotFoundError):
        await service.list_pages(db_session, org_b, book.id)


@pytest.mark.asyncio
async def test_page_serializer_matches_the_published_field_names(db_session):
    """The wire shape must stay the one PageResponse and the client agree on."""
    org_id = uuid.uuid4()
    book, page, _ = await _seed(db_session, org_id)

    (payload,) = await service.list_pages(db_session, org_id, book.id)

    assert payload["text_size"] == page.text_size
    assert payload["illustration_url"] == page.illustration_url
    # Names the serializer used to invent, which exist on neither the model nor
    # the response schema nor the frontend's types.
    for invented in ("image_url", "thumbnail_url", "font_size", "dpi"):
        assert invented not in payload


@pytest.mark.asyncio
async def test_character_serializer_matches_the_published_field_names(db_session):
    org_id = uuid.uuid4()
    book, _, character = await _seed(db_session, org_id)

    (payload,) = await service.list_characters(db_session, org_id, book.id)

    assert payload["name"] == character.name
    assert payload["species"] == character.species
    assert payload["setting_continuity_rules"] == {}
    assert payload["time_of_day_rules"] == {}
    for invented in ("species_type", "setting_continuity", "metadata"):
        assert invented not in payload
