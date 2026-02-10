"""Shared test configuration."""

import pytest


def pytest_configure(config):
    """Set the default asyncio mode to 'auto' for pytest-asyncio."""
    config.addinivalue_line("markers", "asyncio: mark test as async")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
