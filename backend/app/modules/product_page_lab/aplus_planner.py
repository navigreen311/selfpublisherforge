"""A+ content planner for the Product Page Conversion Lab.

Generates structured A+ content module plans for Amazon listings.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

# Default A+ module specifications
DEFAULT_MODULES = [
    {
        "module_type": "hero_banner",
        "title": "Hero Banner",
        "content": "A compelling hero image with a powerful tagline that captures the essence of your book. Use a high-quality lifestyle or thematic image.",
        "image_spec": {"width": 970, "height": 600},
        "ai_copy": "",
    },
    {
        "module_type": "comparison_chart",
        "title": "Comparison Chart",
        "content": "Compare your book's features against common reader expectations. Highlight what makes your book unique: length, depth, approach, bonuses.",
        "image_spec": {"width": 970, "height": 400},
        "ai_copy": "",
    },
    {
        "module_type": "feature_grid",
        "title": "3-Column Feature Grid",
        "content": "Showcase three key selling points with icons or images. Each column: 300x300 image + headline + short description.",
        "image_spec": {"width": 300, "height": 300},
        "ai_copy": "",
    },
    {
        "module_type": "author_story",
        "title": "Author Story",
        "content": "Share your author journey, credentials, or personal connection to the topic. Build trust and relatability with readers.",
        "image_spec": {"width": 970, "height": 600},
        "ai_copy": "",
    },
    {
        "module_type": "social_proof",
        "title": "Social Proof Banner",
        "content": "Feature reader testimonials, review quotes, awards, or media mentions. Use star ratings and pull quotes for visual impact.",
        "image_spec": {"width": 970, "height": 400},
        "ai_copy": "",
    },
]


def _generate_module_copy(module_type: str, book_title: str, genre: str) -> str:
    """Generate placeholder AI copy for each module type."""
    copy_templates = {
        "hero_banner": f'Discover "{book_title}" \u2014 a {genre} book that will transform how you think. This compelling read combines expert insights with practical strategies you can use today.',
        "comparison_chart": f"See how {book_title} compares: comprehensive coverage, actionable advice, real-world examples, and bonus resources included. Everything you need in one book.",
        "feature_grid": f"Why readers love {book_title}: Expert-backed content | Easy-to-follow format | Proven strategies that work. Start your journey today.",
        "author_story": f"After years of experience in {genre}, the author brings deep expertise and personal insight to {book_title}. This book represents a passion for helping readers succeed.",
        "social_proof": f'"One of the best {genre} books I\'ve read this year." \u2014 Early Reader Review. Join thousands of readers who have already discovered {book_title}.',
    }
    return copy_templates.get(module_type, f"Content for {module_type} module of {book_title}.")


async def generate_aplus_plan(
    db: AsyncSession,
    org_id: uuid.UUID,
    book_title: str = "",
    genre: str = "other",
    book_id: uuid.UUID | None = None,
) -> dict:
    """Generate an A+ content plan with 5 default modules.

    Returns a structured plan with module specs, suggested copy, and image dimensions.
    """
    modules = []
    for template in DEFAULT_MODULES:
        module = dict(template)
        module["ai_copy"] = _generate_module_copy(module["module_type"], book_title or "Your Book", genre)
        modules.append(module)

    # Persist to DB
    plan_id = None
    try:
        from app.modules.product_page_lab.models import APlusPlan

        plan = APlusPlan(
            org_id=org_id,
            book_id=book_id,
            modules=modules,
            status="draft",
        )
        db.add(plan)
        await db.flush()
        await db.refresh(plan)
        plan_id = str(plan.id)
    except Exception:
        pass  # Model may not exist yet

    return {
        "id": plan_id,
        "modules": modules,
        "status": "draft",
    }


async def get_aplus_plans(db: AsyncSession, org_id: uuid.UUID) -> list[dict]:
    """List all A+ plans for an organization."""
    try:
        from sqlalchemy import select

        from app.modules.product_page_lab.models import APlusPlan

        stmt = (
            select(APlusPlan)
            .where(
                APlusPlan.org_id == org_id,
                APlusPlan.deleted_at.is_(None),
            )
            .order_by(APlusPlan.created_at.desc())
        )
        result = await db.execute(stmt)
        plans = result.scalars().all()
        return [
            {
                "id": str(p.id),
                "book_id": str(p.book_id) if p.book_id else None,
                "modules": p.modules,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in plans
        ]
    except Exception:
        return []


async def get_aplus_plan(db: AsyncSession, plan_id: uuid.UUID, org_id: uuid.UUID) -> dict | None:
    """Get a single A+ plan by ID."""
    try:
        from sqlalchemy import select

        from app.modules.product_page_lab.models import APlusPlan

        stmt = select(APlusPlan).where(
            APlusPlan.id == plan_id,
            APlusPlan.org_id == org_id,
        )
        result = await db.execute(stmt)
        plan = result.scalar_one_or_none()
        if not plan:
            return None
        return {
            "id": str(plan.id),
            "book_id": str(plan.book_id) if plan.book_id else None,
            "modules": plan.modules,
            "status": plan.status,
            "created_at": plan.created_at.isoformat(),
        }
    except Exception:
        return None
