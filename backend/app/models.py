"""Barrel import for all SQLAlchemy models.

Importing this module ensures that every model is registered with
``Base.metadata`` so that ``create_all`` / ``drop_all`` can discover
all tables.
"""

from app.modules.advertising.models import *  # noqa: F401,F403
from app.modules.agent_system.models import *  # noqa: F401,F403
from app.modules.analytics.models import *  # noqa: F401,F403
from app.modules.competitor_finder.models import *  # noqa: F401,F403
from app.modules.cover_design.models import *  # noqa: F401,F403
from app.modules.knowledge_vault.models import *  # noqa: F401,F403
from app.modules.notifications.models import *  # noqa: F401,F403
from app.modules.pricing_automation.models import *  # noqa: F401,F403
from app.modules.product_page_lab.models import *  # noqa: F401,F403
from app.modules.production_pipeline.models import *  # noqa: F401,F403
from app.modules.review_intelligence.models import *  # noqa: F401,F403
