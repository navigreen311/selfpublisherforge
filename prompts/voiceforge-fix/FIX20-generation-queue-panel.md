# FIX20: GenerationQueuePanel Component

## Task
Create a panel showing the generation job queue and status.

## File to Create: `frontend/src/modules/audiobook/components/GenerationQueuePanel.tsx`

Build a panel/card that shows:
- Active generation jobs in a list
- Each job: chapter title, status (queued/processing/completed/failed), progress bar, provider
- Real-time updates via `useAudiobookWebSocket` hook
- Color-coded status: blue=queued, yellow=processing, green=completed, red=failed
- Cancel button for queued jobs
- Retry button for failed jobs
- Summary stats: X of Y chapters complete, estimated time remaining
- Auto-scroll to the active job
- Collapse/expand individual job details (timing, cost)

```tsx
interface GenerationQueuePanelProps {
  projectId: string;
  chapters: Array<{ id: string; chapter_number: number; chapter_title: string | null; status: string }>;
}
```

Use: shadcn/ui Card, Badge, Progress, Button, ScrollArea. lucide-react icons.

## Conventions
- "use client" directive
- Use the audiobook WebSocket hook for real-time updates
- Follow existing component patterns
