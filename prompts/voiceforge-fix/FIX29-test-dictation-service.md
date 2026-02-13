# FIX29: Unit Tests for Dictation Service

## Task
Create unit tests for the dictation module service functions.

## File to Create: `backend/tests/voiceforge/test_dictation_service.py`

### Tests for dictation service (`backend/app/modules/dictation/service.py`)
Read the source file first, then test:

1. `test_create_session` — Creates a dictation session
2. `test_get_session` — Returns session by ID with org scoping
3. `test_get_session_not_found` — Returns None for missing session
4. `test_list_sessions` — Returns paginated list for org
5. `test_update_session` — Updates session fields
6. `test_refine_session` — Calls DictationRefiner and saves result
7. `test_refine_text` — Refines arbitrary text (not tied to session)
8. `test_create_command` — Creates a custom voice command
9. `test_list_commands` — Lists built-in + custom commands
10. `test_delete_command` — Deletes a custom command
11. `test_get_settings` — Returns user's dictation settings
12. `test_update_settings` — Updates dictation settings

### Mock Setup
```python
@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db

@pytest.fixture
def mock_refiner():
    with patch("app.modules.dictation.service.DictationRefiner") as mock:
        refiner = mock.return_value
        refiner.refine_transcript = AsyncMock(return_value=MagicMock(
            refined_text="Refined text here.",
            diff=[],
            style_match_score=0.85,
        ))
        yield refiner
```

## Conventions
- Use pytest, pytest-asyncio
- Mock database and external services
- Test tenant isolation (org_id scoping)
