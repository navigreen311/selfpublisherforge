# VF24: Frontend — AudiobookStudio Layout Component

## Task
Create the main AudiobookStudio page component with full-page layout.

## Context
- Use shadcn/ui components: Button, Card, Progress, Badge, Tabs, ScrollArea
- Use Tailwind CSS for layout
- Follow patterns in existing frontend modules (e.g., `frontend/src/modules/writing/components/editor.tsx`)

## Files to Create

### `frontend/src/modules/audiobook/components/AudiobookStudio.tsx`

Full-page layout with 4 panels:

**Top Bar:**
- Project title (editable)
- Overall progress bar: "X of Y chapters complete"
- Total duration display
- Estimated/actual cost display
- Action buttons: "Generate All", "Master & Export", "Validate ACX"
- Status badge (draft, generating, reviewing, etc.)

**Left Panel (Chapter List):**
- Scrollable list of chapters
- Each item shows: chapter number, title, status icon (pending=gray, generating=spinner, review=yellow, approved=green, failed=red)
- Duration per chapter
- Click to select and view in center panel
- Drag to reorder (optional)

**Center Panel (Content + Audio):**
- Top: Read-only manuscript text for selected chapter (with sentence highlighting during playback)
- Bottom: Waveform player (placeholder div for wavesurfer.js integration from VF26)
- "Generate Audio" button if chapter is pending
- "Regenerate" button if chapter has audio

**Right Panel (Settings):**
- Narrator voice selection (dropdown/card)
- Character voice mapping (for fiction — show detected characters with voice assignment)
- SSML editor toggle
- Quality metrics display (naturalness, clarity, pace)
- Pronunciation dictionary quick-add
- Output settings (format, platform, sample rate)

```tsx
"use client";

import React, { useState, useEffect } from "react";
import { useAudiobookProject, useAudiobookWebSocket } from "../hooks";
import { useAudiobookStudioStore } from "../store";
import type { AudiobookChapter, AudiobookWSEvent } from "../types";

// Use shadcn/ui components
// import { Button } from "@/components/ui/button";
// import { Card } from "@/components/ui/card";
// import { Badge } from "@/components/ui/badge";
// import { Progress } from "@/components/ui/progress";
// import { ScrollArea } from "@/components/ui/scroll-area";

interface AudiobookStudioProps {
  projectId: string;
}

export function AudiobookStudio({ projectId }: AudiobookStudioProps) {
  // Fetch project data
  // Connect WebSocket for real-time updates
  // Render 4-panel layout
  // Handle chapter selection, generation triggers, etc.
}

// Sub-components:
function ChapterList({ chapters, selectedId, onSelect, progress }) { ... }
function ChapterContent({ chapter }) { ... }
function SettingsPanel({ project, voices }) { ... }
function TopBar({ project, onGenerateAll, onMaster, onValidate }) { ... }
function BottomPlayer({ chapter, isPlaying, speed }) { ... }
```

Build a complete, functional component with proper state management. Use the hooks from VF23.

**Layout CSS (Tailwind):**
```
h-screen flex flex-col
  top-bar: h-16 border-b
  main: flex-1 flex overflow-hidden
    left: w-72 border-r overflow-y-auto
    center: flex-1 flex flex-col
      text: flex-1 overflow-y-auto p-6
      waveform: h-48 border-t
    right: w-80 border-l overflow-y-auto p-4
  bottom: h-16 border-t (audio controls)
```
