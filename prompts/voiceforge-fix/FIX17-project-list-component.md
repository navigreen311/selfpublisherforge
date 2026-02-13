# FIX17: AudiobookProjectList Component

## Task
Create a reusable project list component with filtering and sorting.

## File to Create: `frontend/src/modules/audiobook/components/AudiobookProjectList.tsx`

Build a component that displays audiobook projects in a grid with:
- Filter bar: status dropdown (all, draft, generating, reviewing, complete), search by title
- Sort: by date (newest/oldest), by progress, by title
- Grid of project cards (responsive: 1 col mobile, 2 col tablet, 3 col desktop)
- Each card shows: title, status badge, progress bar, chapter count, duration, cost
- Click card → navigate to `/audiobook-studio/{id}`
- Empty state when no projects match filters
- Loading skeletons while fetching

```tsx
interface AudiobookProjectListProps {
  onCreateNew: () => void;
}
```

Use: `useAudiobookProjects` hook, shadcn/ui components (Card, Badge, Select, Input, Button), lucide-react icons, Tailwind CSS.

## Conventions
- "use client" directive
- Follow existing component patterns in the audiobook/components/ directory
- Import types from "@/modules/audiobook/types"
