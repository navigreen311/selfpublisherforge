# FIX23: Keyboard Shortcuts Help Panel

## Task
Create a keyboard shortcuts reference panel for the audiobook module.

## File to Create: `frontend/src/modules/audiobook/components/KeyboardShortcutsHelp.tsx`

Build a slide-out panel or dialog showing all keyboard shortcuts:

**Playback Controls:**
- Space: Play/Pause
- Left Arrow: Rewind 5s
- Right Arrow: Forward 5s
- Shift+Left: Rewind 30s
- Shift+Right: Forward 30s
- [ : Slow down (0.1x)
- ] : Speed up (0.1x)
- 0-9: Jump to 0%-90% of chapter

**Chapter Navigation:**
- Ctrl+Up: Previous chapter
- Ctrl+Down: Next chapter
- Ctrl+Enter: Approve chapter

**SSML Editing:**
- Ctrl+B: Bold/emphasis
- Ctrl+P: Insert pause
- Ctrl+Shift+E: Toggle emotion tags

**General:**
- Ctrl+S: Save project
- Ctrl+G: Generate chapter audio
- Ctrl+M: Start mastering
- ?: Show this help panel

Display in a clean 2-column layout grouped by category. Include a "Press ? to toggle" footer.

```tsx
interface KeyboardShortcutsHelpProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}
```

Use: shadcn/ui Sheet, Badge, Separator.

## Conventions
- "use client" directive
- Follow existing component patterns
