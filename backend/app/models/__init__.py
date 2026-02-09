"""SQLAlchemy model registry — import all models so Alembic can discover them."""
from app.modules.cover_design.models import Cover, ExtractedProduct, KnowledgeClip

__all__ = ["Cover", "ExtractedProduct", "KnowledgeClip"]
