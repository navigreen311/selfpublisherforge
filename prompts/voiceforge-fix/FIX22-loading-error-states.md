# FIX22: Loading States & Error Boundaries for Audiobook Module

## Task
Create loading skeleton and error boundary components for the audiobook module.

## Files to Create

### 1. `frontend/src/modules/audiobook/components/AudiobookSkeleton.tsx`

Loading skeleton that matches the AudiobookStudio 4-panel layout:
- Left panel skeleton (chapter list): 8 rows of varying width
- Center panel skeleton (main content): large block with header
- Right panel skeleton (details): 4 sections
- Bottom bar skeleton: progress bar + buttons

```tsx
export function AudiobookStudioSkeleton() { ... }
export function ProjectListSkeleton() { ... }  // Grid of 6 card skeletons
export function ChapterListSkeleton() { ... }  // List of chapter row skeletons
```

### 2. `frontend/src/modules/audiobook/components/AudiobookErrorBoundary.tsx`

Error boundary component:
- Catches rendering errors in audiobook components
- Shows user-friendly error message with retry button
- Includes "Report Issue" link
- Logs error details to console

```tsx
interface AudiobookErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}
```

Use React's `ErrorBoundary` pattern (class component or react-error-boundary).

Use: shadcn/ui Card, Button, Skeleton. lucide-react AlertTriangle icon.

## Conventions
- "use client" directive
- Follow existing component patterns
