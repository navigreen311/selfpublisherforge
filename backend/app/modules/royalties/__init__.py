"""Royalty tracking module.

Tracks distributor-level royalty entries imported from KDP, IngramSpark,
and Draft2Digital CSV reports. Exposes dashboard aggregations, monthly
statements, CSV import, manual entry, and CSV/PDF export.
"""

from app.modules.royalties.router import router

__all__ = ["router"]
