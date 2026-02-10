"""File validation utilities -- MIME types, size limits, and content-based malware scanning."""

from __future__ import annotations

import logging
import os
import re

from app.core.exceptions import AppException
from app.modules.storage.schemas import AssetType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ENABLE_MALWARE_SCAN: bool = os.environ.get("ENABLE_MALWARE_SCAN", "true").lower() in (
    "true",
    "1",
    "yes",
)

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
# Magic-byte signatures for MIME-type verification
# ---------------------------------------------------------------------------

# Maps MIME types to a list of accepted magic-byte prefixes.
# Each entry is a tuple of (offset, expected_bytes).
_MAGIC_SIGNATURES: dict[str, list[tuple[int, bytes]]] = {
    "image/jpeg": [(0, b"\xff\xd8\xff")],
    "image/png": [(0, b"\x89PNG")],  # 89 50 4E 47
    "image/tiff": [
        (0, b"II\x2a\x00"),   # little-endian TIFF
        (0, b"MM\x00\x2a"),   # big-endian TIFF
    ],
    "application/pdf": [(0, b"%PDF")],
    "application/zip": [(0, b"PK\x03\x04")],
    # DOCX and EPUB are ZIP-based, so they share the PK signature
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        (0, b"PK\x03\x04"),
    ],
    "application/epub+zip": [(0, b"PK\x03\x04")],
    "application/rtf": [(0, b"{\\rtf")],
    "text/rtf": [(0, b"{\\rtf")],
}

# MIME types that are allowed to contain text/scripts (no binary header check)
_TEXT_MIME_TYPES: set[str] = {
    "text/plain",
    "image/svg+xml",
}

# ---------------------------------------------------------------------------
# Dangerous binary signatures
# ---------------------------------------------------------------------------

_PE_HEADER = b"MZ"        # Windows PE executable
_ELF_HEADER = b"\x7fELF"  # Linux ELF executable
_SHEBANG = b"#!"          # Script shebang

# MIME types for which a shebang is acceptable
_SCRIPT_MIME_TYPES: set[str] = {
    "text/plain",
}

# ---------------------------------------------------------------------------
# Suspicious PDF patterns
# ---------------------------------------------------------------------------

_PDF_SUSPICIOUS_PATTERNS: list[re.Pattern[bytes]] = [
    re.compile(rb"/JavaScript\s", re.IGNORECASE),
    re.compile(rb"/JS\s", re.IGNORECASE),
    re.compile(rb"/Launch\s", re.IGNORECASE),
    re.compile(rb"/OpenAction\s.*?/URI\s", re.IGNORECASE | re.DOTALL),
    re.compile(rb"/AA\s", re.IGNORECASE),       # Additional Actions
    re.compile(rb"/RichMedia\s", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Office macro indicator
# ---------------------------------------------------------------------------

_MACRO_SIGNATURES: list[bytes] = [
    b"vbaProject",
    b"VBAProject",
    b"vbaproject",
]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def validate_file(
    *,
    file_name: str,
    content_type: str,
    size: int,
    asset_type: AssetType,
    data: bytes | None = None,
) -> None:
    """Validate MIME type and size; raise *AppException* on failure.

    Parameters
    ----------
    file_name:
        Original file name as provided by the client.
    content_type:
        Claimed MIME type.
    size:
        File size in bytes.
    asset_type:
        The logical asset category.
    data:
        Optional raw file bytes.  When provided, content-based malware
        scanning checks are performed (magic-byte verification, dangerous
        signature detection, macro scanning, etc.).
    """
    _validate_content_type(content_type, asset_type)
    _validate_size(size, asset_type)
    _scan_for_malware(file_name, content_type, data=data)


def scan_file(
    file_name: str,
    content_type: str,
    data: bytes,
) -> None:
    """Standalone entry point for content-based malware scanning.

    Use this when you already have the file bytes and want to run the full
    suite of heuristic checks without repeating MIME / size validation.

    Raises :class:`AppException` if any check fails.
    """
    _scan_for_malware(file_name, content_type, data=data)


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


def _scan_for_malware(
    file_name: str,
    content_type: str,
    *,
    data: bytes | None = None,
) -> None:
    """Run heuristic content-based malware and integrity checks.

    When *data* is ``None`` (i.e. file bytes are not yet available), only
    lightweight filename-based checks are performed.  When *data* is
    provided the full suite of checks runs:

    1. Magic-byte verification against claimed MIME type.
    2. Dangerous executable signature detection (PE / ELF / shebang).
    3. Embedded VBA macro detection in Office documents.
    4. Suspicious pattern detection in PDF files.
    5. Image header validation for JPEG and PNG.

    All checks are controlled by the ``ENABLE_MALWARE_SCAN`` environment
    variable (default ``True``).
    """
    if not ENABLE_MALWARE_SCAN:
        logger.debug("Malware scanning disabled via ENABLE_MALWARE_SCAN; skipping.")
        return

    # --- Filename-based checks (always available) --------------------------
    _check_dangerous_extension(file_name, content_type)

    if data is None:
        # No file content to inspect yet; remaining checks require bytes.
        return

    if len(data) == 0:
        # Empty files are technically valid but not useful; skip scanning.
        return

    # --- Content-based checks (require file bytes) -------------------------
    _check_magic_bytes(data, content_type, file_name)
    _check_dangerous_signatures(data, content_type, file_name)
    _check_office_macros(data, content_type, file_name)
    _check_pdf_suspicious_patterns(data, content_type, file_name)
    _check_image_headers(data, content_type, file_name)


# ---------------------------------------------------------------------------
# Individual scan routines
# ---------------------------------------------------------------------------

def _check_dangerous_extension(file_name: str, content_type: str) -> None:
    """Reject files whose extension suggests an executable regardless of MIME."""
    dangerous_extensions = {
        ".exe", ".dll", ".bat", ".cmd", ".com", ".scr", ".pif",
        ".msi", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh",
        ".ps1", ".sh", ".csh", ".bash",
    }
    lower_name = file_name.lower()
    for ext in dangerous_extensions:
        if lower_name.endswith(ext):
            raise AppException(
                status_code=400,
                code="DANGEROUS_FILE_TYPE",
                message=f"Files with the '{ext}' extension are not permitted.",
                details=[
                    {
                        "field": "file_name",
                        "file_name": file_name,
                        "reason": "dangerous_extension",
                    }
                ],
            )


def _check_magic_bytes(data: bytes, content_type: str, file_name: str) -> None:
    """Verify that the file's magic bytes match the claimed MIME type."""
    if content_type in _TEXT_MIME_TYPES:
        # Text formats and SVG don't have mandatory binary magic bytes.
        return

    signatures = _MAGIC_SIGNATURES.get(content_type)
    if signatures is None:
        # No known signature to check for this MIME type; skip.
        return

    for offset, expected in signatures:
        end = offset + len(expected)
        if len(data) >= end and data[offset:end] == expected:
            return  # At least one signature matched.

    raise AppException(
        status_code=400,
        code="MAGIC_BYTES_MISMATCH",
        message=(
            f"File content does not match the claimed type '{content_type}'. "
            f"The file header is invalid or the file may be corrupted."
        ),
        details=[
            {
                "field": "data",
                "file_name": file_name,
                "claimed_type": content_type,
                "reason": "magic_bytes_mismatch",
            }
        ],
    )


def _check_dangerous_signatures(
    data: bytes, content_type: str, file_name: str
) -> None:
    """Detect PE executables, ELF binaries, and unexpected shebangs."""
    # PE header check -- never acceptable for any allowed asset type
    if data[:2] == _PE_HEADER and len(data) > 64:
        # Confirm it looks like a real PE by checking for the PE\0\0 signature
        # at the offset indicated by the DOS header (bytes 60-63).
        pe_offset = int.from_bytes(data[60:64], byteorder="little")
        if len(data) > pe_offset + 4 and data[pe_offset : pe_offset + 4] == b"PE\x00\x00":
            raise AppException(
                status_code=400,
                code="DANGEROUS_FILE_CONTENT",
                message="File contains a Windows executable (PE) header and cannot be uploaded.",
                details=[
                    {
                        "field": "data",
                        "file_name": file_name,
                        "reason": "pe_executable_detected",
                    }
                ],
            )

    # ELF header check
    if data[:4] == _ELF_HEADER:
        raise AppException(
            status_code=400,
            code="DANGEROUS_FILE_CONTENT",
            message="File contains a Linux executable (ELF) header and cannot be uploaded.",
            details=[
                {
                    "field": "data",
                    "file_name": file_name,
                    "reason": "elf_executable_detected",
                }
            ],
        )

    # Shebang check -- only allowed in text/plain files
    if data[:2] == _SHEBANG and content_type not in _SCRIPT_MIME_TYPES:
        raise AppException(
            status_code=400,
            code="DANGEROUS_FILE_CONTENT",
            message=(
                "File starts with a script shebang (#!) but its content type "
                f"'{content_type}' does not permit script content."
            ),
            details=[
                {
                    "field": "data",
                    "file_name": file_name,
                    "reason": "unexpected_shebang",
                }
            ],
        )


def _check_office_macros(data: bytes, content_type: str, file_name: str) -> None:
    """Detect embedded VBA macros in Office documents (DOCX, etc.)."""
    office_types = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if content_type not in office_types:
        return

    for signature in _MACRO_SIGNATURES:
        if signature in data:
            raise AppException(
                status_code=400,
                code="MACRO_DETECTED",
                message=(
                    "The uploaded document contains embedded VBA macros, "
                    "which are not permitted for security reasons."
                ),
                details=[
                    {
                        "field": "data",
                        "file_name": file_name,
                        "reason": "vba_macro_detected",
                    }
                ],
            )


def _check_pdf_suspicious_patterns(
    data: bytes, content_type: str, file_name: str
) -> None:
    """Scan PDF files for JavaScript, auto-launch actions, and other red flags."""
    if content_type != "application/pdf":
        return

    for pattern in _PDF_SUSPICIOUS_PATTERNS:
        match = pattern.search(data)
        if match:
            matched_text = match.group(0)
            # Decode for the error message, replacing non-printable chars.
            readable = matched_text[:80].decode("ascii", errors="replace")
            raise AppException(
                status_code=400,
                code="SUSPICIOUS_PDF_CONTENT",
                message=(
                    "The uploaded PDF contains suspicious active content "
                    "(e.g. JavaScript or auto-launch actions) and cannot be accepted."
                ),
                details=[
                    {
                        "field": "data",
                        "file_name": file_name,
                        "reason": "suspicious_pdf_pattern",
                        "matched_pattern": readable,
                    }
                ],
            )


def _check_image_headers(data: bytes, content_type: str, file_name: str) -> None:
    """Validate that image files begin with proper format headers."""
    if content_type == "image/jpeg":
        # JPEG: must start with FF D8 FF
        if len(data) < 3 or data[:3] != b"\xff\xd8\xff":
            raise AppException(
                status_code=400,
                code="INVALID_IMAGE_HEADER",
                message="The file does not have a valid JPEG header (expected FF D8 FF).",
                details=[
                    {
                        "field": "data",
                        "file_name": file_name,
                        "reason": "invalid_jpeg_header",
                    }
                ],
            )

    elif content_type == "image/png":
        # PNG: must start with 89 50 4E 47 0D 0A 1A 0A (8-byte signature)
        png_sig = b"\x89PNG\r\n\x1a\n"
        if len(data) < 8 or data[:8] != png_sig:
            raise AppException(
                status_code=400,
                code="INVALID_IMAGE_HEADER",
                message="The file does not have a valid PNG header (expected 89504E47 signature).",
                details=[
                    {
                        "field": "data",
                        "file_name": file_name,
                        "reason": "invalid_png_header",
                    }
                ],
            )

    elif content_type == "image/tiff":
        # TIFF: II*\0 (little-endian) or MM\0* (big-endian)
        if len(data) < 4 or (data[:4] != b"II\x2a\x00" and data[:4] != b"MM\x00\x2a"):
            raise AppException(
                status_code=400,
                code="INVALID_IMAGE_HEADER",
                message="The file does not have a valid TIFF header.",
                details=[
                    {
                        "field": "data",
                        "file_name": file_name,
                        "reason": "invalid_tiff_header",
                    }
                ],
            )
