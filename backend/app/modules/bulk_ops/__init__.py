"""Bulk operations on books (Feature 6B).

Supports archive, delete, change_price, add_tags, export_metadata_csv.
"""
from app.modules.bulk_ops.router import router

__all__ = ["router"]
