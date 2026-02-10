"""Shared test configuration for the publishing operations tests."""

import pytest


@pytest.fixture(autouse=True)
def anyio_backend():
    return "asyncio"
