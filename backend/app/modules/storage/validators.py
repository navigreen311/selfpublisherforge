"""File validation utilities — MIME types, size limits, and malware-scan placeholder."""

from __future__ import annotations

from app.core.exceptions import AppException
from app.modules.storage.schemas import AssetType


# ---------------------------------------------------------------------------
# MIME-type whitelists per asset type
# ---------------------------------------------------------------------------

ALLOWED_MIME_TYPES: dict[AssetType, set[str]] = {
    AssetType.MANUSCRIPT: {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/epub+zip",   # .epub
        "application/pdf",        # .pdf
        "text/plain",             # .txt
        "application/rtf",        # .rtf
        "text/rtf",               # .rtf (alternative)
    },
    AssetType.IMAGE: {
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/svg+xml",
    },
    AssetType.COVER: {
        "image/jpeg",
        "image/png",
        "image/tiff",
    },
    AssetType.EXPORT: {
        "application/epub+zip",
        "application/pdf",
        "application/x-mobipocket-ebook",  # .mobi
    },
}

# ---------------------------------------------------------------------------
# Size limits per asset type (bytes)
# ---------------------------------------------------------------------------

MAX_FILE_SIZE: dict[AssetType, int] = {
    AssetType.MANUSCRIPT: 50 * 1024 * 1024,   # 50 MB
    AssetType.IMAGE: 20 * 1024 * 1024,         # 20 MB
    AssetType.COVER: 20 * 1024 * 1024,         # 20 MB
    AssetType.EXPORT: 100 * 1024 * 1024,       # 100 MB (generated files can be large)
}


# ---------------------------------------------------------------------------
# File-extension mapping (used for S3 key generation)
# ---------------------------------------------------------------------------

MIME_TO_EXTENSION: dict[str, str] = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/epub+zip": ".epub",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/rtf": ".rtf",
    "text/rtf": ".rtf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/tiff": ".tiff",
    "image/svg+xml": ".svg",
    "application/x-mobipocket-ebook": ".mobi",
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def validate_file(
    *,
    file_name: str,
    content_type: str,
    size: int,
    asset_type: AssetType,
) -> None:
    """Validate MIME type and size; raise *AppException* on failure."""

    _validate_content_type(content_type, asset_type)
    _validate_size(size, asset_type)
    _scan_for_malware(file_name, content_type)


# ---------------------------------------------------------------------------
# Internal validators
# ---------------------------------------------------------------------------

def _validate_content_type(content_type: str, asset_type: AssetType) -> None:
    allowed = ALLOWED_MIME_TYPES.get(asset_type, set())
    if content_type not in allowed:
        raise AppException(
            status_code=400,
            code="INVALID_CONTENT_TYPE",
            message=f"Content type '{content_type}' is not allowed for {asset_type.value} assets.",
            details=[
                {
                    "field": "content_type",
                    "allowed": sorted(allowed),
                }
            ],
        )


def _validate_size(size: int, asset_type: AssetType) -> None:
    max_size = MAX_FILE_SIZE.get(asset_type, 0)
    if size > max_size:
        mb_limit = max_size / (1024 * 1024)
        raise AppException(
            status_code=400,
            code="FILE_TOO_LARGE",
            message=f"File exceeds the {mb_limit:.0f} MB limit for {asset_type.value} assets.",
            details=[
                {
                    "field": "size",
                    "max_bytes": max_size,
                    "provided_bytes": size,
                }
            ],
        )


def _scan_for_malware(file_name: str, content_type: str) -> None:
    """Placeholder for future malware / antivirus integration.

    When a scanning service (e.g. ClamAV, VirusTotal) is available,
    hook into it here.  For now this is a no-op that always passes.
    """
    pass
