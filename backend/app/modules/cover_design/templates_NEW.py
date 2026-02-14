"""Built-in cover templates organised by genre.

Each template includes dimension specs, font recommendations, and layout guidance
for common self-publishing platforms. Templates now include Fabric.js editor_state
for direct visual editing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.modules.cover_design.schemas import CoverDimensions, CoverGenre, CoverPlatform
