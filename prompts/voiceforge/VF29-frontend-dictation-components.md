# VF29: Frontend — Dictation UI Components

## Task
Create all dictation UI components for the Writing Studio.

## Files to Create

### `frontend/src/modules/dictation/components/DictationToolbar.tsx`

Floating toolbar for the Writing Studio when dictation is active:
- Large microphone button: gray=inactive, red=recording (with pulse animation), yellow=paused
- Audio level meter (VU meter — simple horizontal bar that reacts to mic input)
- Recording duration timer (MM:SS format)
- Words per minute counter (live)
- Pause / Resume / Stop buttons
- Status text: "Listening...", "Processing...", "Paused", "Ready"
- Settings gear icon → popover with: language selector, microphone device selector, auto-refine toggle, voice commands on/off toggle
- "Refine" button (visible when auto-refine is off, triggers style refinement)
- Position: fixed bottom-center of editor, with slight shadow/elevation

```tsx
interface DictationToolbarProps {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  wpm: number;
  audioLevel: number; // 0-1
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onRefine: () => void;
  settings: DictationSettings;
  onSettingsChange: (settings: Partial<DictationSettings>) => void;
}
```

### `frontend/src/modules/dictation/components/DictationOverlay.tsx`

Overlay displayed in the manuscript editor during dictation:
- Partial transcript shown in gray italic text (at cursor position)
- Final transcript in normal weight (committed to editor)
- Low-confidence words underlined in orange with tooltip showing confidence %
- Click orange word → shows correction suggestions
- Voice command toast: brief animated badge showing "New Paragraph" etc. when command detected
- Word count increment animation (number ticks up)

```tsx
interface DictationOverlayProps {
  partialText: string;
  finalTexts: string[];
  lowConfidenceWords: { word: string; confidence: number; index: number }[];
  lastCommand?: { command: string; action: string };
  wordCount: number;
}
```

### `frontend/src/modules/dictation/components/RefinementDiff.tsx`

Side-by-side diff view after style refinement:
- Left panel: raw dictated text (scrollable)
- Right panel: style-refined text (scrollable, synced scroll)
- Inline diff highlighting: additions=green bg, removals=red bg/strikethrough, changes=yellow bg
- "Accept All" button → replaces raw with refined in editor
- "Accept Paragraph" → accepts individual paragraphs
- "Reject" → keeps original
- Click any refined sentence → revert that sentence to original
- Style match score badge: "87% style match" with color indicator (green >80%, yellow 60-80%, red <60%)

```tsx
interface RefinementDiffProps {
  rawText: string;
  refinedText: string;
  diff: DiffSegment[];
  styleMatchScore?: number;
  onAcceptAll: () => void;
  onAcceptParagraph: (index: number) => void;
  onReject: () => void;
  onRevertSentence: (sentenceIndex: number) => void;
}
```

### `frontend/src/modules/dictation/components/VoiceCommandPanel.tsx`

Slide-out panel showing available voice commands:
- Two sections: "Built-in Commands" and "Custom Commands"
- Each command shows: phrase (bold), action description, toggle on/off
- Built-in commands: new paragraph, new line, period, comma, question mark, delete that, undo, bold that, italic that, chapter break, stop dictation, read that back
- "Add Custom Command" button → inline form (phrase input + action dropdown)
- Delete button on custom commands
- Search/filter input

```tsx
interface VoiceCommandPanelProps {
  commands: DictationCommand[];
  onToggle: (id: string, active: boolean) => void;
  onAdd: (phrase: string, action: string) => void;
  onDelete: (id: string) => void;
  isOpen: boolean;
  onClose: () => void;
}
```

### `frontend/src/modules/dictation/components/index.ts`
Export all dictation components.

Build all components fully with Tailwind CSS and shadcn/ui (Button, Card, Badge, Switch, Input, Popover, Sheet, Slider, Select, ScrollArea). Include proper TypeScript types and accessibility attributes.
