# VF12: SSML Generator Service

## Task
Create the intelligent SSML generator that converts plain manuscript text into SSML-annotated text for natural narration, using Claude API for text analysis.

## Files to Create

### `backend/app/services/voiceforge/ssml_generator.py`

Uses Claude API (via the project's existing LLM orchestration) to analyze text and add SSML tags.

**SSML enhancements:**
1. Paragraph breaks — `<break time="500ms"/>` between paragraphs
2. Chapter transitions — `<break time="1500ms"/>` with tone shift
3. Dialogue detection — quoted speech → character voice switching
4. Emphasis — contextual emphasis detection
5. Pronunciation — apply custom dictionary entries via `<phoneme>`
6. Numbers & dates — convert to spoken form
7. Abbreviations — expand ("Dr." → "Doctor")
8. Pace variation — slow for drama, fast for action
9. Emotional tone — prosody hints for emotional passages
10. Lists — pauses between items
11. Headings — stronger break + pitch change

Implement fully:

```python
"""Intelligent SSML Generator using Claude for text analysis."""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class DialogueSegment:
    character: str
    text: str
    emotion: str | None = None
    start_index: int = 0
    end_index: int = 0

@dataclass
class EmotionSegment:
    text: str
    emotion: str
    intensity: float = 0.5
    start_index: int = 0
    end_index: int = 0

@dataclass
class SSMLResult:
    original_text: str
    ssml_text: str
    dialogue_segments: list[DialogueSegment] = field(default_factory=list)
    emotion_segments: list[EmotionSegment] = field(default_factory=list)

class SSMLGenerator:
    async def generate_ssml(self, text: str, project_config: dict | None = None, pronunciation_dict: dict | None = None) -> SSMLResult:
        """Convert plain text to SSML using Claude analysis."""
        ...

    async def detect_dialogue(self, text: str) -> list[DialogueSegment]:
        """Detect dialogue segments with character attribution."""
        ...

    async def detect_emotions(self, text: str) -> list[EmotionSegment]:
        """Detect emotional tone of text passages."""
        ...

    def expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations to spoken form."""
        ...

    def apply_pronunciation_dict(self, ssml: str, dictionary: dict) -> str:
        """Apply custom pronunciation entries as SSML phoneme tags."""
        ...

    def validate_ssml(self, ssml_text: str) -> dict:
        """Validate SSML syntax."""
        ...
```

Use Claude via `app.modules.llm_orchestration.orchestrator` (the existing LLM routing layer) for text analysis. Fall back to regex-based detection if LLM is unavailable.

## Key Implementation Details
- Claude prompt should analyze text and return JSON with dialogue segments, emotions, emphasis words, and pace suggestions
- The SSML output must be valid XML — escape special characters
- Include fallback regex patterns for basic dialogue detection ("quoted text" she said)
- Numbers like "2024" should become `<say-as interpret-as="date">2024</say-as>` or spoken form
- Abbreviation dictionary should be extensible
