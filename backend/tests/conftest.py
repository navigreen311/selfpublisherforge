"""Shared fixtures for backend tests."""

import pytest


@pytest.fixture
def sample_simple_text():
    """Simple, easy-to-read text for testing."""
    return (
        "The cat sat on the mat. The dog ran in the park. "
        "Birds fly in the sky. Fish swim in the sea."
    )


@pytest.fixture
def sample_complex_text():
    """Complex academic text for testing."""
    return (
        "The multifaceted philosophical underpinnings of contemporary "
        "epistemological discourse necessitate a comprehensive understanding "
        "of interdisciplinary methodological frameworks. Furthermore, the "
        "juxtaposition of theoretical paradigms illuminates the fundamental "
        "characteristics of postmodern intellectual inquiry."
    )
