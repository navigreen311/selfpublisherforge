"""Pen Name Management module."""
from app.modules.pen_names.router import router
from app.modules.pen_names.service import PenNameService

__all__ = ["router", "PenNameService"]
