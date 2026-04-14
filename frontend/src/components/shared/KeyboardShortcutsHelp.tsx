"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface Shortcut {
  keys: string[];
  description: string;
}

const shortcuts: Shortcut[] = [
  { keys: ["Ctrl", "K"], description: "Open command palette" },
  { keys: ["Ctrl", "N"], description: "New project" },
  { keys: ["Ctrl", "S"], description: "Save current work" },
  { keys: ["Ctrl", "Z"], description: "Undo" },
  { keys: ["Ctrl", "Y"], description: "Redo" },
  { keys: ["/"], description: "Focus search bar" },
  { keys: ["Esc"], description: "Close modals, panels, command palette" },
  { keys: ["?"], description: "Show keyboard shortcuts help panel" },
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function KeyboardShortcutsHelp({ open, onOpenChange }: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
        </DialogHeader>
        <div className="space-y-2">
          {shortcuts.map((s) => (
            <div
              key={s.description}
              className="flex items-center justify-between text-sm py-1.5 border-b last:border-b-0"
            >
              <span className="text-muted-foreground">{s.description}</span>
              <div className="flex gap-1">
                {s.keys.map((k) => (
                  <kbd
                    key={k}
                    className="border rounded px-1.5 py-0.5 text-xs bg-muted font-mono"
                  >
                    {k}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          On Mac, use Cmd instead of Ctrl.
        </p>
      </DialogContent>
    </Dialog>
  );
}
