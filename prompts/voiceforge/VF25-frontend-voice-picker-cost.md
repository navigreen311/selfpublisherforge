# VF25: Frontend — VoicePicker & CostEstimator Components

## Task
Create VoicePicker and CostEstimator React components.

## Files to Create

### `frontend/src/modules/audiobook/components/VoicePicker.tsx`

Voice selection grid:
- Grid of voice cards (3-4 columns)
- Each card shows: name, gender icon, accent, provider badge (Self-Hosted/Premium), cost indicator ($/$$/$$$), play sample button
- Filter bar: gender (all/male/female/neutral), accent dropdown, provider toggle, price tier
- Search input for voice name
- "Clone My Voice" button → opens modal with file upload (accept audio files, min 3 minutes)
- Preview: text input + "Preview" button → plays sample
- Currently selected voice has highlight border
- onClick selects voice and calls onSelect callback

```tsx
interface VoicePickerProps {
  selectedVoiceId?: string;
  onSelect: (voiceId: string) => void;
  voices: Voice[];
  isLoading: boolean;
}

export function VoicePicker({ selectedVoiceId, onSelect, voices, isLoading }: VoicePickerProps) {
  const [filter, setFilter] = useState({ gender: 'all', accent: 'all', provider: 'all' });
  const [search, setSearch] = useState('');
  const [previewText, setPreviewText] = useState('The quick brown fox jumps over the lazy dog.');
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);

  // Filter logic
  // Render grid
  // Play preview audio
  // Clone voice modal
}
```

### `frontend/src/modules/audiobook/components/CostEstimator.tsx`

Real-time cost calculator:
- Auto-pull total word count from project/manuscript
- Show estimated duration: `word_count / 150` words per minute
- Provider cost comparison table:
  | Provider | Cost/Min | Total Est. | Quality |
  | Coqui XTTS | $0.001 | $X.XX | Good |
  | ElevenLabs | $0.030 | $X.XX | Premium |
- Per-chapter cost breakdown (expandable)
- Budget cap input: set max budget, show warning when exceeded
- Comparison callout: "AI narration: $XX vs Professional narrator: $2,000-5,000+"
- Visual: horizontal bar chart comparing provider costs

```tsx
interface CostEstimatorProps {
  projectId: string;
  totalWordCount: number;
  chapters: { chapter_number: number; word_count: number; cost_usd: number }[];
}

export function CostEstimator({ projectId, totalWordCount, chapters }: CostEstimatorProps) {
  const estimatedMinutes = totalWordCount / 150;
  const providers = [
    { name: 'Coqui XTTS (Self-Hosted)', rate: 0.001, quality: 'Good', tier: '$' },
    { name: 'ElevenLabs (Premium)', rate: 0.03, quality: 'Premium', tier: '$$$' },
    { name: 'Piper (Fast Preview)', rate: 0.0001, quality: 'Basic', tier: '¢' },
  ];
  // Render cost table, per-chapter breakdown, budget input, comparison
}
```

### `frontend/src/modules/audiobook/components/index.ts`
Export all audiobook components.
