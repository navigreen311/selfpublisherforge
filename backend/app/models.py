"""Barrel import for all SQLAlchemy models.

Importing this module ensures that every model is registered with
``Base.metadata`` so that ``create_all`` / ``drop_all`` can discover
all tables.
"""

from app.modules.advertising.models import *
from app.modules.agent_system.models import *
from app.modules.analytics.models import *
from app.modules.competitor_finder.models import *
from app.modules.cover_design.models import *
from app.modules.knowledge_vault.models import *
from app.modules.notifications.models import *
from app.modules.pricing_automation.models import *
from app.modules.product_page_lab.models import *
from app.modules.production_pipeline.models import *
from app.modules.review_intelligence.models import *
