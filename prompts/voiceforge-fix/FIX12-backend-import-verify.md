# FIX12: Backend Import Verification Script

## Task
Create a Python script that verifies all VoiceForge module imports resolve correctly.

## File to Create: `backend/tests/test_voiceforge_imports.py`

### Implementation

```python
"""Verify all VoiceForge module imports resolve without errors."""
import importlib
import pytest

VOICEFORGE_MODULES = [
    # Models
    "app.models.audiobook",
    "app.models.dictation",
    # Schemas
    "app.modules.audiobook.schemas",
    "app.modules.audiobook.schemas_generation",
    "app.modules.audiobook.schemas_extended",
    "app.modules.dictation.schemas",
    # Routers
    "app.modules.audiobook.router",
    "app.modules.audiobook.router_crud",
    "app.modules.audiobook.router_generation",
    "app.modules.audiobook.router_voices",
    "app.modules.audiobook.router_mastering",
    "app.modules.audiobook.router_export",
    "app.modules.dictation.router",
    # Services
    "app.modules.audiobook.service",
    "app.modules.audiobook.service_crud",
    "app.modules.audiobook.service_generation",
    "app.modules.audiobook.service_voices",
    "app.modules.audiobook.service_mastering",
    "app.modules.audiobook.service_export",
    "app.modules.dictation.service",
    # VoiceForge services
    "app.services.voiceforge",
    "app.services.voiceforge.tts_engine",
    "app.services.voiceforge.asr_engine",
    "app.services.voiceforge.audio_processor",
    "app.services.voiceforge.voice_manager",
    "app.services.voiceforge.provider_router",
    "app.services.voiceforge.ssml_generator",
    "app.services.voiceforge.dictation_refiner",
    # WebSockets
    "app.modules.audiobook.websocket",
    "app.modules.dictation.websocket",
    # Celery tasks
    "app.tasks.audiobook_tasks",
    "app.tasks.mastering_tasks",
]


@pytest.mark.parametrize("module_path", VOICEFORGE_MODULES)
def test_import(module_path: str):
    """Each VoiceForge module should import without errors."""
    try:
        importlib.import_module(module_path)
    except ImportError as e:
        pytest.fail(f"Failed to import {module_path}: {e}")
```

Also run: `python -c "import ast; [ast.parse(open(f).read()) for f in __import__('glob').glob('backend/app/modules/audiobook/*.py')]"` to syntax-check all files.

## Conventions
- Use pytest parametrize for clean test output
- Don't fix issues, just report them
