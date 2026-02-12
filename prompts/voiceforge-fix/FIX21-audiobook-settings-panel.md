# FIX21: AudiobookSettingsPanel Component

## Task
Create a settings/configuration panel for audiobook projects.

## File to Create: `frontend/src/modules/audiobook/components/AudiobookSettingsPanel.tsx`

Build a settings panel with sections:

**Audio Output Settings:**
- Output format selector (MP3, M4B, FLAC, WAV)
- Sample rate (44100Hz, 48000Hz)
- Bit rate (128, 192, 256, 320 kbps)
- Channels (Mono recommended for ACX, Stereo)

**Target Platform:**
- Platform selector (ACX, Findaway Voices, Generic)
- Auto-configure settings based on platform (ACX = MP3/44100/192/Mono)

**Narration Style:**
- Pacing: speed slider (0.8x - 1.2x, default 1.0)
- Pause between paragraphs (0.5s - 3s)
- Pause between chapters (1s - 5s)
- Emphasis level (subtle, moderate, dramatic)

**Save button** → calls `useUpdateAudiobookProject` mutation

```tsx
interface AudiobookSettingsPanelProps {
  projectId: string;
  currentSettings: {
    output_format: string;
    sample_rate: number;
    bit_rate: number;
    channels: number;
    target_platform: string;
    narration_style: Record<string, unknown> | null;
  };
  onSave: () => void;
}
```

Use: shadcn/ui Card, Label, Select, Slider, Switch, Button, Separator.

## Conventions
- "use client" directive
- Follow existing component patterns
