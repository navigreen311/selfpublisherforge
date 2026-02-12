# FIX27: Unit Tests for SSMLGenerator & DictationRefiner

## Task
Create unit tests for the SSMLGenerator and DictationRefiner services.

## File to Create: `backend/tests/voiceforge/test_ssml_dictation.py`

### Tests for SSMLGenerator (`backend/app/services/voiceforge/ssml_generator.py`)
Read the source file first, then test:

1. `test_ssml_generator_init` — Can be instantiated
2. `test_detect_dialogue` — Detects quoted dialogue with character attribution
3. `test_detect_emotions` — Detects emotional tone in passages
4. `test_expand_abbreviations` — Expands "Dr." to "Doctor", "St." to "Street", etc.
5. `test_validate_ssml_valid` — Validates well-formed SSML
6. `test_validate_ssml_invalid` — Rejects malformed SSML
7. `test_apply_pronunciation_dict` — Applies custom pronunciation rules
8. `test_generate_ssml_basic` — Generates basic SSML from plain text

### Tests for DictationRefiner (`backend/app/services/voiceforge/dictation_refiner.py`)
Read the source file first, then test:

1. `test_dictation_refiner_init` — Can be instantiated
2. `test_restore_punctuation` — Adds periods, commas to unpunctuated text
3. `test_remove_fillers` — Removes "um", "uh", "like", "you know"
4. `test_structure_paragraphs` — Groups sentences into paragraphs
5. `test_diff_highlight` — Produces correct diff between original and refined
6. `test_refine_transcript_full` — Full pipeline: filler removal + punctuation + structure

### Test Data
```python
DIALOGUE_TEXT = '''
"I can't believe it," Sarah whispered.
John replied, "Neither can I."
"What do we do now?" she asked.
'''

UNPUNCTUATED_TEXT = "the quick brown fox jumps over the lazy dog it was a sunny day"

FILLER_TEXT = "so um I was thinking you know that maybe we should uh go to the store like tomorrow"
```

## Conventions
- Use pytest
- Mock LLM calls (Claude API) for SSML generation
- Test with realistic text samples
