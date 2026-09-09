"""Unit tests for agent marketplace templates."""

import pytest

from app.modules.agent_system.templates import (
    get_template,
    list_templates,
    validate_template,
)
from app.modules.agent_system.templates.backlist_analyzer import TEMPLATE as BACKLIST_ANALYZER_TEMPLATE
from app.modules.agent_system.templates.competitor_tracker import TEMPLATE as COMPETITOR_TRACKER_TEMPLATE
from app.modules.agent_system.templates.cover_designer import TEMPLATE as COVER_DESIGNER_TEMPLATE
from app.modules.agent_system.templates.keyword_scout import TEMPLATE as KEYWORD_SCOUT_TEMPLATE
from app.modules.agent_system.templates.launch_planner import TEMPLATE as LAUNCH_PLANNER_TEMPLATE
from app.modules.agent_system.templates.price_optimizer import TEMPLATE as PRICE_OPTIMIZER_TEMPLATE
from app.modules.agent_system.templates.research_agent import TEMPLATE as RESEARCH_TEMPLATE
from app.modules.agent_system.templates.review_monitor import TEMPLATE as REVIEW_MONITOR_TEMPLATE
from app.modules.agent_system.templates.social_content import TEMPLATE as SOCIAL_CONTENT_TEMPLATE
from app.modules.agent_system.templates.writing_coach import TEMPLATE as WRITING_COACH_TEMPLATE


class TestTemplateRegistry:
    """Tests for template registry functions."""

    def test_list_all_templates(self):
        """Test listing all templates returns 10 templates."""
        templates = list_templates()
        assert len(templates) == 10
        assert all(isinstance(t, dict) for t in templates)

    def test_list_templates_by_category_research(self):
        """Test filtering templates by research category."""
        templates = list_templates(category="research")
        assert len(templates) == 3
        slugs = {t["slug"] for t in templates}
        assert slugs == {"market-research", "keyword-scout", "competitor-tracker"}

    def test_list_templates_by_category_marketing(self):
        """Test filtering templates by marketing category."""
        templates = list_templates(category="marketing")
        assert len(templates) == 4
        slugs = {t["slug"] for t in templates}
        assert slugs == {
            "cover-design-assistant",
            "price-optimizer",
            "launch-planner",
            "social-content-agent",
        }

    def test_list_templates_by_category_writing(self):
        """Test filtering templates by writing category."""
        templates = list_templates(category="writing")
        assert len(templates) == 1
        assert templates[0]["slug"] == "writing-coach"

    def test_list_templates_by_category_automation(self):
        """Test filtering templates by automation category."""
        templates = list_templates(category="automation")
        assert len(templates) == 2
        slugs = {t["slug"] for t in templates}
        assert slugs == {"review-monitor", "backlist-analyzer"}

    def test_list_templates_by_tier_pro(self):
        """Test filtering templates by pro tier."""
        templates = list_templates(tier="pro")
        assert len(templates) == 10  # All templates are pro tier

    def test_list_templates_by_category_and_tier(self):
        """Test filtering by both category and tier."""
        templates = list_templates(category="research", tier="pro")
        assert len(templates) == 3

    def test_list_templates_empty_category(self):
        """Test filtering by non-existent category returns empty list."""
        templates = list_templates(category="nonexistent")
        assert len(templates) == 0

    def test_get_template_by_slug(self):
        """Test getting a specific template by slug."""
        template = get_template("market-research")
        assert template is not None
        assert template["name"] == "Market Research Agent"
        assert template["slug"] == "market-research"

    def test_get_template_not_found(self):
        """Test getting a non-existent template returns None."""
        template = get_template("nonexistent")
        assert template is None


class TestTemplateValidation:
    """Tests for template validation."""

    def test_validate_complete_template(self):
        """Test validating a complete, valid template."""
        assert validate_template(RESEARCH_TEMPLATE) is True

    def test_validate_missing_name(self):
        """Test validation fails for template missing name."""
        template = {"slug": "test", "description": "test"}
        with pytest.raises(ValueError, match="missing required field: name"):
            validate_template(template)

    def test_validate_missing_steps(self):
        """Test validation fails for template missing steps."""
        template = {
            "name": "Test",
            "slug": "test",
            "description": "test",
            "category": "test",
            "tier": "pro",
            "default_config": {},
            "triggers": [],
            "outputs": [],
        }
        with pytest.raises(ValueError, match="missing required field: steps"):
            validate_template(template)

    def test_validate_empty_steps(self):
        """Test validation fails for template with empty steps list."""
        template = {
            "name": "Test",
            "slug": "test",
            "description": "test",
            "category": "test",
            "tier": "pro",
            "default_config": {},
            "steps": [],
            "triggers": [],
            "outputs": [],
        }
        with pytest.raises(ValueError, match="must have at least one step"):
            validate_template(template)

    def test_validate_invalid_step_structure(self):
        """Test validation fails for steps without required fields."""
        template = {
            "name": "Test",
            "slug": "test",
            "description": "test",
            "category": "test",
            "tier": "pro",
            "default_config": {},
            "steps": [{"title": "Test"}],  # Missing description
            "triggers": [],
            "outputs": [],
        }
        with pytest.raises(ValueError, match="must have 'title' and 'description'"):
            validate_template(template)

    def test_validate_triggers_not_list(self):
        """Test validation fails for non-list triggers."""
        template = {
            "name": "Test",
            "slug": "test",
            "description": "test",
            "category": "test",
            "tier": "pro",
            "default_config": {},
            "steps": [{"title": "Test", "description": "Test"}],
            "triggers": "not a list",
            "outputs": [],
        }
        with pytest.raises(ValueError, match="Triggers must be a list"):
            validate_template(template)

    def test_validate_outputs_not_list(self):
        """Test validation fails for non-list outputs."""
        template = {
            "name": "Test",
            "slug": "test",
            "description": "test",
            "category": "test",
            "tier": "pro",
            "default_config": {},
            "steps": [{"title": "Test", "description": "Test"}],
            "triggers": [],
            "outputs": "not a list",
        }
        with pytest.raises(ValueError, match="Outputs must be a list"):
            validate_template(template)


class TestResearchAgentTemplate:
    """Tests for Market Research Agent template."""

    def test_research_agent_structure(self):
        """Test research agent has correct structure."""
        assert RESEARCH_TEMPLATE["name"] == "Market Research Agent"
        assert RESEARCH_TEMPLATE["slug"] == "market-research"
        assert RESEARCH_TEMPLATE["category"] == "research"
        assert RESEARCH_TEMPLATE["tier"] == "pro"
        assert len(RESEARCH_TEMPLATE["steps"]) == 4
        assert len(RESEARCH_TEMPLATE["triggers"]) == 3
        assert len(RESEARCH_TEMPLATE["outputs"]) == 3

    def test_research_agent_default_config(self):
        """Test research agent has valid default config."""
        config = RESEARCH_TEMPLATE["default_config"]
        assert config["max_budget_usd"] == 5.0
        assert config["model"] == "claude-sonnet-4-5-20250929"
        assert config["max_tokens"] == 8192
        assert config["temperature"] == 0.3

    def test_research_agent_steps(self):
        """Test research agent steps are well-defined."""
        steps = RESEARCH_TEMPLATE["steps"]
        assert steps[0]["title"] == "Analyze bestseller lists"
        assert "input_schema" in steps[0]
        assert "estimated_tokens" in steps[0]


class TestWritingCoachTemplate:
    """Tests for Writing Coach Agent template."""

    def test_writing_coach_structure(self):
        """Test writing coach has correct structure."""
        assert WRITING_COACH_TEMPLATE["name"] == "Writing Coach Agent"
        assert WRITING_COACH_TEMPLATE["slug"] == "writing-coach"
        assert WRITING_COACH_TEMPLATE["category"] == "writing"
        assert len(WRITING_COACH_TEMPLATE["steps"]) == 5

    def test_writing_coach_outputs(self):
        """Test writing coach has comprehensive outputs."""
        outputs = WRITING_COACH_TEMPLATE["outputs"]
        output_names = {o["name"] for o in outputs}
        assert "coaching_report" in output_names
        assert "writing_exercises" in output_names
        assert "progress_metrics" in output_names
        assert "style_profile" in output_names


class TestCoverDesignerTemplate:
    """Tests for Cover Design Assistant template."""

    def test_cover_designer_structure(self):
        """Test cover designer has correct structure."""
        assert COVER_DESIGNER_TEMPLATE["name"] == "Cover Design Assistant"
        assert COVER_DESIGNER_TEMPLATE["slug"] == "cover-design-assistant"
        assert COVER_DESIGNER_TEMPLATE["category"] == "marketing"
        assert len(COVER_DESIGNER_TEMPLATE["steps"]) == 4

    def test_cover_designer_outputs(self):
        """Test cover designer has design-specific outputs."""
        outputs = COVER_DESIGNER_TEMPLATE["outputs"]
        output_names = {o["name"] for o in outputs}
        assert "cover_concepts" in output_names
        assert "design_brief" in output_names
        assert "color_palette" in output_names
        assert "font_recommendations" in output_names


class TestPriceOptimizerTemplate:
    """Tests for Price Optimizer Agent template."""

    def test_price_optimizer_structure(self):
        """Test price optimizer has correct structure."""
        assert PRICE_OPTIMIZER_TEMPLATE["name"] == "Price Optimizer Agent"
        assert PRICE_OPTIMIZER_TEMPLATE["slug"] == "price-optimizer"
        assert PRICE_OPTIMIZER_TEMPLATE["category"] == "marketing"
        assert len(PRICE_OPTIMIZER_TEMPLATE["steps"]) == 4

    def test_price_optimizer_config(self):
        """Test price optimizer has optimization config."""
        config = PRICE_OPTIMIZER_TEMPLATE["default_config"]
        assert config["optimization_goal"] == "revenue"
        assert config["temperature"] == 0.2  # Low temp for analytical work


class TestReviewMonitorTemplate:
    """Tests for Review Monitor Agent template."""

    def test_review_monitor_structure(self):
        """Test review monitor has correct structure."""
        assert REVIEW_MONITOR_TEMPLATE["name"] == "Review Monitor Agent"
        assert REVIEW_MONITOR_TEMPLATE["slug"] == "review-monitor"
        assert REVIEW_MONITOR_TEMPLATE["category"] == "automation"
        assert len(REVIEW_MONITOR_TEMPLATE["steps"]) == 4

    def test_review_monitor_config(self):
        """Test review monitor has monitoring config."""
        config = REVIEW_MONITOR_TEMPLATE["default_config"]
        assert config["alert_threshold"] == 3.5
        assert config["check_interval_hours"] == 6

    def test_review_monitor_triggers(self):
        """Test review monitor has scheduled triggers."""
        triggers = REVIEW_MONITOR_TEMPLATE["triggers"]
        trigger_types = {t["type"] for t in triggers}
        assert "scheduled" in trigger_types


class TestKeywordScoutTemplate:
    """Tests for Keyword Scout Agent template."""

    def test_keyword_scout_structure(self):
        """Test keyword scout has correct structure."""
        assert KEYWORD_SCOUT_TEMPLATE["name"] == "Keyword Scout Agent"
        assert KEYWORD_SCOUT_TEMPLATE["slug"] == "keyword-scout"
        assert KEYWORD_SCOUT_TEMPLATE["category"] == "research"
        assert len(KEYWORD_SCOUT_TEMPLATE["steps"]) == 4

    def test_keyword_scout_outputs(self):
        """Test keyword scout has keyword-specific outputs."""
        outputs = KEYWORD_SCOUT_TEMPLATE["outputs"]
        output_names = {o["name"] for o in outputs}
        assert "keyword_scores" in output_names
        assert "metadata_recommendations" in output_names
        assert "competitor_keywords" in output_names


class TestLaunchPlannerTemplate:
    """Tests for Launch Planner Agent template."""

    def test_launch_planner_structure(self):
        """Test launch planner has correct structure."""
        assert LAUNCH_PLANNER_TEMPLATE["name"] == "Launch Planner Agent"
        assert LAUNCH_PLANNER_TEMPLATE["slug"] == "launch-planner"
        assert LAUNCH_PLANNER_TEMPLATE["category"] == "marketing"
        assert len(LAUNCH_PLANNER_TEMPLATE["steps"]) == 5

    def test_launch_planner_config(self):
        """Test launch planner has launch config."""
        config = LAUNCH_PLANNER_TEMPLATE["default_config"]
        assert config["launch_window_days"] == 30

    def test_launch_planner_outputs(self):
        """Test launch planner has comprehensive outputs."""
        outputs = LAUNCH_PLANNER_TEMPLATE["outputs"]
        output_names = {o["name"] for o in outputs}
        assert "launch_plan" in output_names
        assert "timeline" in output_names
        assert "checklist" in output_names
        assert "marketing_copy" in output_names
        assert "budget_allocation" in output_names


class TestCompetitorTrackerTemplate:
    """Tests for Competitor Tracker Agent template."""

    def test_competitor_tracker_structure(self):
        """Test competitor tracker has correct structure."""
        assert COMPETITOR_TRACKER_TEMPLATE["name"] == "Competitor Tracker Agent"
        assert COMPETITOR_TRACKER_TEMPLATE["slug"] == "competitor-tracker"
        assert COMPETITOR_TRACKER_TEMPLATE["category"] == "research"
        assert len(COMPETITOR_TRACKER_TEMPLATE["steps"]) == 4

    def test_competitor_tracker_config(self):
        """Test competitor tracker has monitoring config."""
        config = COMPETITOR_TRACKER_TEMPLATE["default_config"]
        assert config["check_interval_hours"] == 12
        assert config["max_competitors"] == 10


class TestSocialContentTemplate:
    """Tests for Social Content Agent template."""

    def test_social_content_structure(self):
        """Test social content agent has correct structure."""
        assert SOCIAL_CONTENT_TEMPLATE["name"] == "Social Content Agent"
        assert SOCIAL_CONTENT_TEMPLATE["slug"] == "social-content-agent"
        assert SOCIAL_CONTENT_TEMPLATE["category"] == "marketing"
        assert len(SOCIAL_CONTENT_TEMPLATE["steps"]) == 4

    def test_social_content_config(self):
        """Test social content agent has content config."""
        config = SOCIAL_CONTENT_TEMPLATE["default_config"]
        assert config["temperature"] == 0.8  # High temp for creative work
        assert config["content_days"] == 30
        assert config["posts_per_week"] == 5

    def test_social_content_outputs(self):
        """Test social content agent has social-specific outputs."""
        outputs = SOCIAL_CONTENT_TEMPLATE["outputs"]
        output_names = {o["name"] for o in outputs}
        assert "content_calendar" in output_names
        assert "social_posts" in output_names
        assert "hashtag_research" in output_names
        assert "brand_voice_guide" in output_names


class TestBacklistAnalyzerTemplate:
    """Tests for Backlist Analyzer Agent template."""

    def test_backlist_analyzer_structure(self):
        """Test backlist analyzer has correct structure."""
        assert BACKLIST_ANALYZER_TEMPLATE["name"] == "Backlist Analyzer Agent"
        assert BACKLIST_ANALYZER_TEMPLATE["slug"] == "backlist-analyzer"
        assert BACKLIST_ANALYZER_TEMPLATE["category"] == "automation"
        assert len(BACKLIST_ANALYZER_TEMPLATE["steps"]) == 5

    def test_backlist_analyzer_config(self):
        """Test backlist analyzer has analysis config."""
        config = BACKLIST_ANALYZER_TEMPLATE["default_config"]
        assert config["min_book_age_months"] == 6

    def test_backlist_analyzer_outputs(self):
        """Test backlist analyzer has optimization outputs."""
        outputs = BACKLIST_ANALYZER_TEMPLATE["outputs"]
        output_names = {o["name"] for o in outputs}
        assert "backlist_analysis" in output_names
        assert "opportunity_scores" in output_names
        assert "optimization_recommendations" in output_names
        assert "action_plan" in output_names
        assert "revenue_projections" in output_names


class TestTemplateConsistency:
    """Tests for consistency across all templates."""

    def test_all_templates_have_unique_slugs(self):
        """Test that all template slugs are unique."""
        templates = list_templates()
        slugs = [t["slug"] for t in templates]
        assert len(slugs) == len(set(slugs))

    def test_all_templates_have_unique_names(self):
        """Test that all template names are unique."""
        templates = list_templates()
        names = [t["name"] for t in templates]
        assert len(names) == len(set(names))

    def test_all_templates_have_valid_categories(self):
        """Test that all templates use valid categories."""
        valid_categories = {"research", "writing", "marketing", "automation"}
        templates = list_templates()
        for template in templates:
            assert template["category"] in valid_categories

    def test_all_templates_have_valid_tiers(self):
        """Test that all templates use valid tiers."""
        valid_tiers = {"free", "pro", "enterprise"}
        templates = list_templates()
        for template in templates:
            assert template["tier"] in valid_tiers

    def test_all_templates_have_default_config(self):
        """Test that all templates have default_config."""
        templates = list_templates()
        for template in templates:
            assert "default_config" in template
            assert isinstance(template["default_config"], dict)
            assert "max_budget_usd" in template["default_config"]
            assert "model" in template["default_config"]

    def test_all_templates_have_steps(self):
        """Test that all templates have at least one step."""
        templates = list_templates()
        for template in templates:
            assert "steps" in template
            assert isinstance(template["steps"], list)
            assert len(template["steps"]) > 0

    def test_all_templates_have_triggers(self):
        """Test that all templates have triggers."""
        templates = list_templates()
        for template in templates:
            assert "triggers" in template
            assert isinstance(template["triggers"], list)

    def test_all_templates_have_outputs(self):
        """Test that all templates have outputs."""
        templates = list_templates()
        for template in templates:
            assert "outputs" in template
            assert isinstance(template["outputs"], list)

    def test_all_templates_pass_validation(self):
        """Test that all templates pass validation."""
        templates = list_templates()
        for template in templates:
            assert validate_template(template) is True
