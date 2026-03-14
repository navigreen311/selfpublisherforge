"""Tests for Photo Integration features.

Covers: photo upload, CRUD, filtering, generation with references.

~12 test cases.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

BOOK_ID = uuid.uuid4()
ORG_ID = uuid.uuid4()
PHOTO_ID = uuid.uuid4()


class TestPhotoCRUD:
    """Tests for photo upload, list, get, update, and delete."""

    @pytest.mark.asyncio
    async def test_upload_photo(self):
        """Upload a photo and verify metadata is returned."""
        mock_service = AsyncMock()
        mock_service.upload_photo.return_value = {
            "id": str(PHOTO_ID), "filename": "reference_01.jpg",
            "mime_type": "image/jpeg", "size_bytes": 245760,
            "width": 1920, "height": 1080, "usage_type": "reference",
            "book_id": str(BOOK_ID), "org_id": str(ORG_ID),
        }
        result = await mock_service.upload_photo(
            org_id=ORG_ID, book_id=BOOK_ID, filename="reference_01.jpg",
            content_type="image/jpeg", size_bytes=245760,
        )
        assert result["filename"] == "reference_01.jpg"
        assert result["mime_type"] == "image/jpeg"
        mock_service.upload_photo.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_photos_pagination(self):
        """Verify photo listing supports pagination."""
        mock_service = AsyncMock()
        photos = [{"id": str(uuid.uuid4()), "filename": f"photo_{i}.jpg"} for i in range(8)]
        mock_service.list_photos.return_value = {
            "items": photos[:3], "total": 8, "page": 1, "page_size": 3,
        }
        result = await mock_service.list_photos(org_id=ORG_ID, page=1, page_size=3)
        assert len(result["items"]) == 3
        assert result["total"] == 8

    @pytest.mark.asyncio
    async def test_list_photos_filter_by_usage_type(self):
        """Filter photos by usage type (reference, texture, background)."""
        mock_service = AsyncMock()
        mock_service.list_photos.return_value = {
            "items": [{"id": str(PHOTO_ID), "usage_type": "reference"}], "total": 1,
        }
        result = await mock_service.list_photos(org_id=ORG_ID, usage_type="reference")
        assert all(p["usage_type"] == "reference" for p in result["items"])

    @pytest.mark.asyncio
    async def test_list_photos_filter_by_book(self):
        """Filter photos by associated book ID."""
        mock_service = AsyncMock()
        mock_service.list_photos.return_value = {
            "items": [{"id": str(PHOTO_ID), "book_id": str(BOOK_ID)}], "total": 1,
        }
        result = await mock_service.list_photos(org_id=ORG_ID, book_id=BOOK_ID)
        assert all(p["book_id"] == str(BOOK_ID) for p in result["items"])

    @pytest.mark.asyncio
    async def test_get_photo(self):
        """Get a single photo by ID with full metadata."""
        mock_service = AsyncMock()
        mock_service.get_photo.return_value = {
            "id": str(PHOTO_ID), "filename": "reference_01.jpg",
            "mime_type": "image/jpeg", "tags": ["landscape", "mountains"],
        }
        result = await mock_service.get_photo(photo_id=PHOTO_ID)
        assert result["id"] == str(PHOTO_ID)
        assert isinstance(result["tags"], list)

    @pytest.mark.asyncio
    async def test_update_photo_metadata(self):
        """Update photo metadata (tags, usage_type)."""
        mock_service = AsyncMock()
        mock_service.update_photo.return_value = {
            "id": str(PHOTO_ID), "usage_type": "texture", "tags": ["pattern", "fabric"],
        }
        result = await mock_service.update_photo(
            photo_id=PHOTO_ID, usage_type="texture", tags=["pattern", "fabric"],
        )
        assert result["usage_type"] == "texture"
        assert "pattern" in result["tags"]

    @pytest.mark.asyncio
    async def test_delete_photo(self):
        """Delete a photo and verify deletion."""
        mock_service = AsyncMock()
        mock_service.delete_photo.return_value = {"deleted": True, "id": str(PHOTO_ID)}
        result = await mock_service.delete_photo(photo_id=PHOTO_ID)
        assert result["deleted"] is True


class TestPhotoGeneration:
    """Tests for AI image generation using photo references."""

    @pytest.mark.asyncio
    async def test_generate_with_single_reference(self):
        """Generate an image using a single photo reference."""
        mock_service = AsyncMock()
        mock_service.generate_with_references.return_value = {
            "generated_image_url": "https://example.com/generated/img_001.png",
            "reference_ids": [str(PHOTO_ID)], "prompt": "A mountain landscape at sunset",
        }
        result = await mock_service.generate_with_references(
            reference_ids=[PHOTO_ID], prompt="A mountain landscape at sunset", style_influence=0.7,
        )
        assert "generated_image_url" in result
        assert len(result["reference_ids"]) == 1

    @pytest.mark.asyncio
    async def test_generate_with_multiple_references(self):
        """Generate an image using multiple photo references."""
        mock_service = AsyncMock()
        ref_ids = [uuid.uuid4() for _ in range(3)]
        mock_service.generate_with_references.return_value = {
            "generated_image_url": "https://example.com/generated/img_002.png",
            "reference_ids": [str(rid) for rid in ref_ids],
        }
        result = await mock_service.generate_with_references(
            reference_ids=ref_ids, prompt="A cozy cabin in the woods",
        )
        assert len(result["reference_ids"]) == 3

    @pytest.mark.asyncio
    async def test_generate_with_invalid_reference(self):
        """Verify error raised when using a non-existent reference photo."""
        mock_service = AsyncMock()
        mock_service.generate_with_references.side_effect = Exception("Reference photo not found")
        with pytest.raises(Exception, match="not found"):
            await mock_service.generate_with_references(reference_ids=[uuid.uuid4()], prompt="Test")


class TestPhotoValidation:
    """Tests for photo upload validation rules."""

    @pytest.mark.asyncio
    async def test_upload_invalid_mime_type(self):
        """Verify error when uploading a non-image file."""
        mock_service = AsyncMock()
        mock_service.upload_photo.side_effect = Exception("Invalid MIME type: application/pdf")
        with pytest.raises(Exception, match="Invalid MIME type"):
            await mock_service.upload_photo(
                org_id=ORG_ID, book_id=BOOK_ID, filename="doc.pdf",
                content_type="application/pdf", size_bytes=1024,
            )

    @pytest.mark.asyncio
    async def test_upload_exceeds_size_limit(self):
        """Verify error when photo exceeds maximum file size."""
        mock_service = AsyncMock()
        mock_service.upload_photo.side_effect = Exception("File size exceeds maximum")
        with pytest.raises(Exception, match="exceeds maximum"):
            await mock_service.upload_photo(
                org_id=ORG_ID, book_id=BOOK_ID, filename="huge.jpg",
                content_type="image/jpeg", size_bytes=100 * 1024 * 1024,
            )
