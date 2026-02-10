"""Shared test configuration and fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend app is importable from tests
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
