# FIX18: NewProjectDialog Component

## Task
Create a dialog for creating new audiobook projects.

## File to Create: `frontend/src/modules/audiobook/components/NewProjectDialog.tsx`

Build a dialog/modal with:
- Book selector: dropdown of user's books (use existing book hooks if available, or a simple text input for book_id)
- Title field (optional, auto-fills from book title)
- Target platform dropdown: ACX, Findaway Voices, Generic
- Output format dropdown: MP3, M4B, FLAC, WAV
- Audio settings: sample rate (44100/48000), bit rate (128/192/256/320), channels (Mono/Stereo)
- "Create Project" button → calls `useCreateAudiobookProject` mutation
- Loading state while creating
- Success → redirect to `/audiobook-studio/{new_id}`
- Error toast on failure

```tsx
interface NewProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}
```

Use: shadcn/ui Dialog, Label, Input, Select, Button, sonner toast.

## Conventions
- "use client" directive
- Follow existing dialog patterns in the codebase
