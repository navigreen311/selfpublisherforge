"""Reader user behavior - read-heavy traffic pattern.

ReaderUser represents 60% of traffic:
- Browses projects and books
- Views analytics dashboards
- Searches market categories
- Minimal write operations

Wait time: 1-3 seconds between requests
"""
from __future__ import annotations

import random

from locust import task, between

from . import AuthenticatedUser
from ..config import WAIT_TIMES

wait_config = WAIT_TIMES["reader"]


class ReaderUser(AuthenticatedUser):
    """Read-heavy user pattern - browsing and viewing content."""

    wait_time = between(wait_config["min"], wait_config["max"])
    weight = 60  # 60% of total traffic

    @task(10)
    def view_analytics_dashboard(self) -> None:
        """View the main analytics dashboard."""
        self.api_get("analytics/dashboard", name="GET /analytics/dashboard")

    @task(8)
    def list_projects(self) -> None:
        """List all projects."""
        response = self.api_get("production/projects", name="GET /production/projects")

        # If we got projects, randomly view one in detail
        if response.status_code == 200:
            data = response.json()
            projects = data.get("items", [])
            if projects:
                project = random.choice(projects)
                project_id = project.get("id")
                if project_id:
                    self.api_get(
                        f"production/projects/{project_id}",
                        name="GET /production/projects/:id",
                    )

    @task(7)
    def browse_books(self) -> None:
        """Browse books in portfolio."""
        response = self.api_get("portfolio/books", name="GET /portfolio/books")

        # If we got books, randomly view one
        if response.status_code == 200:
            data = response.json()
            books = data.get("items", [])
            if books:
                book = random.choice(books)
                book_id = book.get("id")
                if book_id:
                    self.api_get(
                        f"portfolio/books/{book_id}",
                        name="GET /portfolio/books/:id",
                    )

    @task(6)
    def view_market_categories(self) -> None:
        """Browse market intelligence categories."""
        self.api_get(
            "market/categories",
            params={"limit": 20},
            name="GET /market/categories",
        )

    @task(5)
    def view_portfolio_metrics(self) -> None:
        """View portfolio economics metrics."""
        self.api_get("analytics/portfolio", name="GET /analytics/portfolio")

    @task(5)
    def view_revenue_data(self) -> None:
        """View revenue analytics."""
        self.api_get(
            "analytics/revenue",
            params={"period": "monthly"},
            name="GET /analytics/revenue",
        )

    @task(4)
    def search_knowledge_vault(self) -> None:
        """Search the knowledge vault."""
        search_queries = [
            "marketing",
            "amazon",
            "kdp",
            "publishing",
            "cover design",
            "pricing",
            "categories",
            "keywords",
        ]
        query = random.choice(search_queries)
        self.api_get(
            "knowledge/search",
            params={"query": query, "limit": 10},
            name="GET /knowledge/search",
        )

    @task(3)
    def view_notifications(self) -> None:
        """Check notifications."""
        self.api_get("notifications", name="GET /notifications")

    @task(3)
    def view_trends(self) -> None:
        """View analytics trends."""
        self.api_get(
            "analytics/trends",
            params={"period": "weekly"},
            name="GET /analytics/trends",
        )

    @task(2)
    def view_marketing_campaigns(self) -> None:
        """View marketing campaigns."""
        response = self.api_get("marketing/campaigns", name="GET /marketing/campaigns")

        # Optionally view a campaign in detail
        if response.status_code == 200:
            data = response.json()
            campaigns = data.get("items", [])
            if campaigns and random.random() < 0.3:  # 30% chance to drill down
                campaign = random.choice(campaigns)
                campaign_id = campaign.get("id")
                if campaign_id:
                    self.api_get(
                        f"marketing/campaigns/{campaign_id}",
                        name="GET /marketing/campaigns/:id",
                    )

    @task(2)
    def view_reviews(self) -> None:
        """View review intelligence."""
        self.api_get("reviews", params={"limit": 20}, name="GET /reviews")

    @task(1)
    def view_user_profile(self) -> None:
        """View own user profile."""
        self.api_get("users/me", name="GET /users/me")

    @task(1)
    def view_advertising_campaigns(self) -> None:
        """View advertising campaigns."""
        self.api_get("advertising/campaigns", name="GET /advertising/campaigns")
