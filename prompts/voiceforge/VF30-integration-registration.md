# VF30: Integration Registration, Pages & Documentation

## Task
Wire up all new modules into the main app, create frontend pages/routes, and update documentation.

## Files to Modify

### 1. `backend/app/main.py` — Register new routers

Add to `_register_routers()` function, in a new "VoiceForge" section after the existing Chrome Extension block:

```python
    # VoiceForge Integration
    from app.modules.audiobook.router import router as audiobook_router
    app.include_router(audiobook_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])

    from app.modules.audiobook.websocket import router as audiobook_ws_router
    app.include_router(audiobook_ws_router, prefix=f"{prefix}", tags=["audiobooks-ws"])

    from app.modules.dictation.router import router as dictation_router
    app.include_router(dictation_router, prefix=f"{prefix}/dictation", tags=["dictation"])

    from app.modules.dictation.websocket import router as dictation_ws_router
    app.include_router(dictation_ws_router, prefix=f"{prefix}", tags=["dictation-ws"])
```

### 2. `backend/app/core/openapi.py` — Add tag descriptions

Add tag descriptions for "audiobooks", "audiobooks-ws", "dictation", "dictation-ws" to the OpenAPI schema.

### 3. `shared/contracts/module_registry.py` — Register new modules

Add audiobook and dictation to the module registry if it exists:
- Module 34: audiobook — "AI Audiobook Production Studio" — Pro tier — /audiobooks
- Module 35: dictation — "Voice-Driven Writing (Dictation)" — Starter tier — /dictation

### 4. Frontend Pages

Create these Next.js App Router pages:

**`frontend/src/app/(dashboard)/audiobook-studio/page.tsx`**
```tsx
import { AudiobookStudio } from "@/modules/audiobook/components/AudiobookStudio";

export default function AudiobookStudioPage() {
  // Get project ID from search params or create new
  return <AudiobookStudio projectId={projectId} />;
}

export const metadata = {
  title: "Audiobook Studio | SelfPublisherForge",
  description: "AI-powered audiobook production studio",
};
```

**`frontend/src/app/(dashboard)/audiobook-studio/[id]/page.tsx`**
```tsx
// Dynamic route for specific audiobook project
```

### 5. Frontend Navigation

Update the sidebar/navigation component to include:
- "Audiobook Studio" link under Writing & Content section (with headphones icon)
- Add dictation toggle button to the Writing Studio editor toolbar

Look at:
- `frontend/src/components/layout/` for sidebar
- `frontend/src/modules/writing/components/editor.tsx` for editor toolbar

### 6. Update `README.md`

Add to the Features section:
```markdown
### Voice & Audio
- **AI Audiobook Production Studio** -- Full audiobook creation pipeline with multi-provider TTS (Coqui XTTS, ElevenLabs), SSML generation, ACX validation, chapter-by-chapter generation with real-time progress, voice cloning, and mastering/export for ACX, Findaway Voices, and more
- **Voice-Driven Writing** -- Real-time speech-to-text dictation in the Writing Studio using Faster-Whisper ASR, with automatic punctuation restoration, filler removal, and style refinement via the Style Cloning Engine
```

Add to Module Registry table:
| 34 | audiobook | Pro | `/audiobooks` | AI audiobook production with TTS |
| 35 | dictation | Starter | `/dictation` | Voice dictation for writing |

Add to Getting Started URLs table:
| Frontend - Audiobook Studio | http://localhost:3000/audiobook-studio |

Add VoiceForge env vars to the environment variables table.

Add to Docker Compose section: note about `--profile voiceforge` for TTS/ASR services.

### 7. Update `CHANGELOG.md`

Add under the latest version:
```markdown
### Added
- AI Audiobook Production Studio with multi-provider TTS (Coqui XTTS, ElevenLabs, Piper)
- Voice-Driven Writing with real-time ASR dictation in Writing Studio
- SSML generator for natural narration with dialogue detection and emotion tagging
- ACX technical validation and auto-fix pipeline
- Custom voice cloning (ElevenLabs and Coqui XTTS)
- Pronunciation dictionary for custom word handling
- Audiobook mastering pipeline with normalization, noise gate, and format conversion
- Cost estimator with provider comparison
- Real-time generation progress via WebSocket
- Voice command system for hands-free dictation control
- Dictation refinement pipeline with style matching
```

## Conventions
- Read each file before modifying
- Make minimal, targeted edits
- Don't break existing functionality
- Follow existing naming and organization patterns
