"""Conftest for voiceforge tests — stubs broken model imports."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

# The app.models.__init__ tries to import Agent from app.models.agent, which
# doesn't exist (the re-exports were removed). Stub the models package before
# any voiceforge service import triggers the cascade.
if "app.models" not in sys.modules:
    _models_mock = MagicMock()
    sys.modules.setdefault("app.models", _models_mock)
    sys.modules.setdefault("app.models.agent", _models_mock)
    sys.modules.setdefault("app.models.audiobook", _models_mock)
