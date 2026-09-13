"""Load test configuration for Locust.

Defines load profiles, environment settings, and test parameters.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

# Environment configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"

# Test user credentials
TEST_USER_EMAIL = os.getenv("LOAD_TEST_USER_EMAIL", "loadtest@example.com")
TEST_USER_PASSWORD = os.getenv("LOAD_TEST_USER_PASSWORD", "LoadTest123!")

# Load profiles
LoadProfileName = Literal["smoke", "normal", "stress", "spike", "soak"]


@dataclass
class LoadProfile:
    """Configuration for a load testing profile."""

    users: int
    spawn_rate: int
    duration: str  # e.g., "1m", "5m", "1h"
    description: str


LOAD_PROFILES: dict[LoadProfileName, LoadProfile] = {
    "smoke": LoadProfile(
        users=5,
        spawn_rate=1,
        duration="1m",
        description="Minimal load test to verify basic functionality",
    ),
    "normal": LoadProfile(
        users=50,
        spawn_rate=5,
        duration="5m",
        description="Normal operational load with typical traffic patterns",
    ),
    "stress": LoadProfile(
        users=200,
        spawn_rate=20,
        duration="10m",
        description="Stress test to find performance limits",
    ),
    "spike": LoadProfile(
        users=500,
        spawn_rate=100,
        duration="2m",
        description="Sudden traffic spike to test elasticity",
    ),
    "soak": LoadProfile(
        users=100,
        spawn_rate=10,
        duration="30m",
        description="Extended duration test to find memory leaks and stability issues",
    ),
}

# User distribution (weights for locust user selection)
# These should sum to 100 for clarity
USER_WEIGHTS = {
    "reader": 60,  # 60% of traffic - read-heavy users
    "writer": 30,  # 30% of traffic - content creators
    "power": 10,  # 10% of traffic - full workflow users
}

# Wait times (seconds) between requests for different user types
WAIT_TIMES = {
    "reader": {"min": 1, "max": 3},  # Quick browsing
    "writer": {"min": 2, "max": 5},  # Thoughtful content creation
    "power": {"min": 1, "max": 2},  # Busy power users
}

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# Token refresh threshold (seconds before expiry)
TOKEN_REFRESH_THRESHOLD = 60


def get_active_profile() -> LoadProfile:
    """Get the active load profile from environment variable."""
    profile_name = os.getenv("LOAD_PROFILE", "smoke")
    if profile_name not in LOAD_PROFILES:
        raise ValueError(f"Invalid LOAD_PROFILE: {profile_name}. " f"Valid options: {', '.join(LOAD_PROFILES.keys())}")
    return LOAD_PROFILES[profile_name]  # type: ignore


def get_full_url(path: str) -> str:
    """Construct full URL from path."""
    if path.startswith("http"):
        return path
    path = path.lstrip("/")
    return f"{BACKEND_URL}{API_PREFIX}/{path}"
