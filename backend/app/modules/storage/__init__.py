"""Storage module — S3/R2-compatible file storage for manuscripts, covers, exports, and media."""

from app.modules.storage.router import router

__all__ = ["router"]
