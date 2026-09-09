"""Power user behavior - full workflow pattern.

PowerUser represents 10% of traffic:
- Executes complete publishing workflows
- Creates projects from concept to publication
- Uses advanced features across all modules
- High engagement with platform capabilities

Wait time: 1-2 seconds between requests (busy power users)
"""
from __future__ import annotations

import random
import uuid

from locust import SequentialTaskSet, between, task

from ..config import WAIT_TIMES
from . import AuthenticatedUser

wait_config = WAIT_TIMES["power"]


class PublishingWorkflow(SequentialTaskSet):
    """Sequential workflow for a complete publishing pipeline."""

    project_id: str | None = None
    book_id: str | None = None
    manuscript_id: str | None = None

    @task
    def create_project(self) -> None:
        """Step 1: Create a new project."""
        project_data = {
            "title": f"Load Test Project {uuid.uuid4()}",
            "description": "Created during load testing",
            "status": "planning",
        }

        response = self.user.api_post(
            "production/projects",
            json=project_data,
            name="POST /production/projects",
        )

        if response.status_code == 201:
            project = response.json()
            self.project_id = project.get("id")

    @task
    def research_market(self) -> None:
        """Step 2: Research market opportunities."""
        # Search for categories
        self.user.api_get(
            "market/categories",
            params={"limit": 20},
            name="GET /market/categories",
        )

        # Check market trends
        self.user.api_get(
            "analytics/trends",
            params={"period": "monthly"},
            name="GET /analytics/trends",
        )

        # Find competitors
        self.user.api_get(
            "competitor/search",
            params={"query": "test book", "limit": 10},
            name="GET /competitor/search",
        )

    @task
    def create_book(self) -> None:
        """Step 3: Create a book."""
        book_data = {
            "title": f"Test Book {uuid.uuid4()}",
            "subtitle": "A load testing book",
            "author": "Load Test Author",
            "genre": random.choice(["fiction", "non-fiction", "mystery", "romance"]),
            "target_word_count": 75000,
            "status": "draft",
        }

        if self.project_id:
            book_data["project_id"] = self.project_id

        response = self.user.api_post(
            "portfolio/books",
            json=book_data,
            name="POST /portfolio/books",
        )

        if response.status_code == 201:
            book = response.json()
            self.book_id = book.get("id")

    @task
    def create_manuscript_chapters(self) -> None:
        """Step 4: Create manuscript with chapters."""
        if not self.book_id:
            return

        # Create multiple chapters
        for i in range(3):
            chapter_data = {
                "title": f"Chapter {i + 1}",
                "content": f"Test content for chapter {i + 1}. {uuid.uuid4()}",
                "order_index": i,
                "status": "draft",
            }

            self.user.api_post(
                f"ai-writing/books/{self.book_id}/manuscript/chapters",
                json=chapter_data,
                name="POST /ai-writing/books/:id/manuscript/chapters",
            )

    @task
    def validate_content(self) -> None:
        """Step 5: Validate the content."""
        if not self.book_id:
            return

        # Run KDP validation
        self.user.api_post(
            f"kdp-validation/books/{self.book_id}/validate",
            json={},
            name="POST /kdp-validation/books/:id/validate",
        )

        # Check readability
        self.user.api_get(
            f"ai-writing/books/{self.book_id}/manuscript/readability-score",
            name="GET /ai-writing/books/:id/manuscript/readability-score",
        )

    @task
    def create_marketing_plan(self) -> None:
        """Step 6: Create a marketing plan."""
        if not self.book_id:
            return

        marketing_data = {
            "book_id": self.book_id,
            "strategy": "launch",
            "budget": random.randint(100, 1000),
            "duration_days": 30,
        }

        self.user.api_post(
            "marketing/plans",
            json=marketing_data,
            name="POST /marketing/plans",
        )

    @task
    def setup_advertising(self) -> None:
        """Step 7: Set up advertising campaigns."""
        if not self.book_id:
            return

        campaign_data = {
            "book_id": self.book_id,
            "name": f"Launch Campaign {uuid.uuid4()}",
            "platform": random.choice(["amazon", "facebook"]),
            "daily_budget": random.uniform(10.0, 50.0),
            "status": "draft",
        }

        self.user.api_post(
            "advertising/campaigns",
            json=campaign_data,
            name="POST /advertising/campaigns",
        )

    @task
    def view_analytics(self) -> None:
        """Step 8: Review analytics and metrics."""
        # Dashboard overview
        self.user.api_get(
            "analytics/dashboard",
            name="GET /analytics/dashboard",
        )

        # Portfolio metrics
        self.user.api_get(
            "analytics/portfolio",
            name="GET /analytics/portfolio",
        )

        # Revenue data
        self.user.api_get(
            "analytics/revenue",
            params={"period": "monthly"},
            name="GET /analytics/revenue",
        )

    @task
    def complete_workflow(self) -> None:
        """Final step: Mark as completed and exit workflow."""
        # This ends the sequential workflow and the user will start over
        self.interrupt()


class PowerUser(AuthenticatedUser):
    """Power user pattern - executes complete workflows."""

    wait_time = between(wait_config["min"], wait_config["max"])
    weight = 10  # 10% of total traffic

    tasks = {PublishingWorkflow: 1}  # type: ignore

    @task(5)
    def manage_multiple_projects(self) -> None:
        """Manage existing projects across the platform."""
        # Get all projects
        response = self.api_get("production/projects", name="GET /production/projects")

        if response.status_code == 200:
            data = response.json()
            projects = data.get("items", [])

            if projects:
                # View a random project in detail
                project = random.choice(projects)
                project_id = project.get("id")
                if project_id:
                    self.api_get(
                        f"production/projects/{project_id}",
                        name="GET /production/projects/:id",
                    )

    @task(4)
    def review_portfolio_performance(self) -> None:
        """Deep dive into portfolio performance."""
        # Portfolio metrics
        self.api_get("analytics/portfolio", name="GET /analytics/portfolio")

        # Revenue breakdown
        self.api_get(
            "analytics/revenue",
            params={"period": "daily", "limit": 30},
            name="GET /analytics/revenue",
        )

        # Royalty records
        self.api_get("analytics/royalties", name="GET /analytics/royalties")

    @task(3)
    def optimize_advertising(self) -> None:
        """Optimize advertising campaigns."""
        # Get campaigns
        response = self.api_get("advertising/campaigns", name="GET /advertising/campaigns")

        if response.status_code == 200:
            data = response.json()
            campaigns = data.get("items", [])

            if campaigns:
                campaign = random.choice(campaigns)
                campaign_id = campaign.get("id")

                if campaign_id:
                    # View campaign performance
                    self.api_get(
                        f"advertising/campaigns/{campaign_id}",
                        name="GET /advertising/campaigns/:id",
                    )

                    # Update campaign settings
                    update_data = {
                        "daily_budget": random.uniform(10.0, 100.0),
                        "status": random.choice(["active", "paused"]),
                    }
                    self.api_put(
                        f"advertising/campaigns/{campaign_id}",
                        json=update_data,
                        name="PUT /advertising/campaigns/:id",
                    )

    @task(3)
    def use_ai_agents(self) -> None:
        """Interact with AI agent system."""
        # Get available agents
        self.api_get("agents", name="GET /agents")

        # Create an agent task
        task_data = {
            "agent_type": random.choice(["market_researcher", "content_optimizer"]),
            "instruction": "Analyze and provide recommendations",
            "context": {"test": True},
        }
        self.api_post("agents/tasks", json=task_data, name="POST /agents/tasks")

    @task(2)
    def manage_knowledge_vault(self) -> None:
        """Actively manage knowledge vault."""
        # Search for knowledge
        self.api_get(
            "knowledge/search",
            params={"query": "best practices", "limit": 20},
            name="GET /knowledge/search",
        )

        # Add new knowledge entry
        entry_data = {
            "title": f"Load Test Entry {uuid.uuid4()}",
            "content": "Test knowledge entry for load testing",
            "tags": ["test", "load-testing"],
            "category": "general",
        }
        self.api_post("knowledge", json=entry_data, name="POST /knowledge")

    @task(2)
    def review_competitive_intelligence(self) -> None:
        """Analyze competitive landscape."""
        # Search competitors
        self.api_get(
            "competitor/search",
            params={"query": "test", "limit": 10},
            name="GET /competitor/search",
        )

        # Get market categories
        self.api_get(
            "market/categories",
            params={"limit": 50},
            name="GET /market/categories",
        )

    @task(1)
    def use_advanced_features(self) -> None:
        """Use advanced platform features."""
        # Product page lab
        self.api_get("product-page-lab/experiments", name="GET /product-page-lab/experiments")

        # Style cloning
        self.api_get("style-cloning/styles", name="GET /style-cloning/styles")

        # Review intelligence
        self.api_get("reviews", params={"limit": 20}, name="GET /reviews")
