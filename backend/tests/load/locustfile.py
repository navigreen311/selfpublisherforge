"""Main Locust load testing file for SelfPublisherForge API.

This file orchestrates load testing with three user types:
- ReaderUser (60% weight): Read-heavy browsing and viewing
- WriterUser (30% weight): Content creation and editing
- PowerUser (10% weight): Complete publishing workflows

Usage:
    # Smoke test (5 users)
    LOAD_PROFILE=smoke locust -f locustfile.py --host=http://localhost:8000

    # Normal load (50 users)
    LOAD_PROFILE=normal locust -f locustfile.py --host=http://localhost:8000

    # Stress test (200 users)
    LOAD_PROFILE=stress locust -f locustfile.py --host=http://localhost:8000

    # Spike test (500 users)
    LOAD_PROFILE=spike locust -f locustfile.py --host=http://localhost:8000

    # Headless mode
    LOAD_PROFILE=normal locust -f locustfile.py --host=http://localhost:8000 \\
        --headless --users 50 --spawn-rate 5 --run-time 5m

Environment Variables:
    BACKEND_URL: Backend API URL (default: http://localhost:8000)
    LOAD_PROFILE: Load profile to use (smoke, normal, stress, spike, soak)
    LOAD_TEST_USER_EMAIL: Test user email (default: loadtest@example.com)
    LOAD_TEST_USER_PASSWORD: Test user password (default: LoadTest123!)

For distributed load testing, see docker-compose.load.yml
"""

from __future__ import annotations

import logging
import sys

from locust import events
from users.power_user import PowerUser

# Import user classes - Locust will automatically detect classes with weight attributes
from users.reader_user import ReaderUser
from users.writer_user import WriterUser

from config import BACKEND_URL, LOAD_PROFILES, get_active_profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Called when Locust initializes."""
    logger.info("=" * 70)
    logger.info("SelfPublisherForge Load Testing")
    logger.info("=" * 70)
    logger.info(f"Target: {BACKEND_URL}")
    logger.info(f"Host: {environment.host or 'Not set (use --host)'}")

    try:
        profile = get_active_profile()
        logger.info(f"Load Profile: {profile}")
        logger.info(f"  - Users: {profile.users}")
        logger.info(f"  - Spawn Rate: {profile.spawn_rate}/sec")
        logger.info(f"  - Duration: {profile.duration}")
        logger.info(f"  - Description: {profile.description}")
    except ValueError as e:
        logger.warning(f"Load profile error: {e}")
        logger.info("Available profiles:")
        for name, prof in LOAD_PROFILES.items():
            logger.info(f"  - {name}: {prof.users} users, {prof.description}")

    logger.info("")
    logger.info("User Distribution:")
    logger.info(f"  - ReaderUser: {ReaderUser.weight}% (read-heavy)")
    logger.info(f"  - WriterUser: {WriterUser.weight}% (content creation)")
    logger.info(f"  - PowerUser: {PowerUser.weight}% (full workflows)")
    logger.info("=" * 70)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    logger.info("🚀 Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    logger.info("✅ Load test completed")
    logger.info("")
    logger.info("Summary:")

    stats = environment.stats
    logger.info(f"  Total requests: {stats.total.num_requests}")
    logger.info(f"  Total failures: {stats.total.num_failures}")
    logger.info(f"  Failure rate: {stats.total.fail_ratio * 100:.2f}%")
    logger.info(f"  Median response time: {stats.total.median_response_time}ms")
    logger.info(f"  95th percentile: {stats.total.get_response_time_percentile(0.95)}ms")
    logger.info(f"  99th percentile: {stats.total.get_response_time_percentile(0.99)}ms")
    logger.info(f"  Avg response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"  RPS (avg): {stats.total.total_rps:.2f}")
    logger.info(f"  RPS (current): {stats.total.current_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called after each request."""
    if exception:
        logger.debug(f"❌ {request_type} {name} failed: {exception}")


@events.user_error.add_listener
def on_user_error(user_instance, exception, tb, **kwargs):
    """Called when a user task raises an exception."""
    logger.error(f"User error in {user_instance.__class__.__name__}: {exception}")


# Locust will automatically discover these user classes
__all__ = ["ReaderUser", "WriterUser", "PowerUser"]
