"""Shared test configuration and fixtures."""
import sys
from pathlib import Path

import pytest

# Add project root to sys.path so 'shared' package can be imported
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


@pytest.fixture(autouse=True)
def _env_setup(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_spf")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/14")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/13")
