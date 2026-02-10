"""Shared test configuration and fixtures."""

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
