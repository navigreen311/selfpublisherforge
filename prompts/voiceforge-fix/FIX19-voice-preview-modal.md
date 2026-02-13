# FIX19: VoicePreviewModal Component

## Task
Create a modal for previewing and comparing TTS voices.

## File to Create: `frontend/src/modules/audiobook/components/VoicePreviewModal.tsx`

Build a modal with:
- Voice info header: name, provider badge, gender, accent, language
- Audio player: play/pause button with waveform visualization for the sample
- Custom text input: user can type text to preview with this voice
- "Generate Preview" button → calls voice preview API
- Compare section: play up to 3 voices side by side
- Quality score display (stars or percentage)
- Cost per minute display
- "Select Voice" button → calls onSelect callback

```tsx
interface VoicePreviewModalProps {
  voiceId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (voiceId: string) => void;
}
```

Use: shadcn/ui Dialog, Button, Input, Badge, Slider. Audio playback via HTML5 `<audio>` element.

## Conventions
- "use client" directive
- Follow existing component patterns
- Use `useVoicePreview` hook from hooks.ts if it exists
