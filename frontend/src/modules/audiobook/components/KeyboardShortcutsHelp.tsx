"use client";

import { Keyboard } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface KeyboardShortcutsHelpProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface Shortcut {
  keys: string[];
  description: string;
}

interface ShortcutGroup {
  label: string;
  shortcuts: Shortcut[];
}

// ---------------------------------------------------------------------------
// Shortcut definitions
// ---------------------------------------------------------------------------

const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    label: "Playback Controls",
    shortcuts: [
      { keys: ["Space"], description: "Play / Pause" },
      { keys: ["\u2190"], description: "Rewind 5s" },
      { keys: ["\u2192"], description: "Forward 5s" },
      { keys: ["Shift", "\u2190"], description: "Rewind 30s" },
      { keys: ["Shift", "\u2192"], description: "Forward 30s" },
      { keys: ["["], description: "Slow down (0.1\u00D7)" },
      { keys: ["]"], description: "Speed up (0.1\u00D7)" },
      { keys: ["0\u20139"], description: "Jump to 0%\u201390% of chapter" },
    ],
  },
  {
    label: "Chapter Navigation",
    shortcuts: [
      { keys: ["Ctrl", "\u2191"], description: "Previous chapter" },
      { keys: ["Ctrl", "\u2193"], description: "Next chapter" },
      { keys: ["Ctrl", "Enter"], description: "Approve chapter" },
    ],
  },
  {
    label: "SSML Editing",
    shortcuts: [
      { keys: ["Ctrl", "B"], description: "Bold / emphasis" },
      { keys: ["Ctrl", "P"], description: "Insert pause" },
      { keys: ["Ctrl", "Shift", "E"], description: "Toggle emotion tags" },
    ],
  },
  {
    label: "General",
    shortcuts: [
      { keys: ["Ctrl", "S"], description: "Save project" },
      { keys: ["Ctrl", "G"], description: "Generate chapter audio" },
      { keys: ["Ctrl", "M"], description: "Start mastering" },
      { keys: ["?"], description: "Show this help panel" },
    ],
  },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KeyBadge({ children }: { children: React.ReactNode }) {
  return (
    <Badge
      variant="outline"
      className="px-1.5 py-0.5 text-[11px] font-mono font-medium bg-muted/50"
    >
      {children}
    </Badge>
  );
}

function ShortcutRow({ shortcut }: { shortcut: Shortcut }) {
  return (
    <div className="flex items-center justify-between gap-4 py-1.5">
      <span className="text-sm text-muted-foreground">
        {shortcut.description}
      </span>
      <div className="flex items-center gap-1 shrink-0">
        {shortcut.keys.map((key, i) => (
          <span key={i} className="flex items-center gap-1">
            {i > 0 && (
              <span className="text-[10px] text-muted-foreground">+</span>
            )}
            <KeyBadge>{key}</KeyBadge>
          </span>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function KeyboardShortcutsHelp({
  open,
  onOpenChange,
}: KeyboardShortcutsHelpProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex flex-col overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </SheetTitle>
          <SheetDescription>
            Quick reference for all available keyboard shortcuts in the
            audiobook studio.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 space-y-6 py-4">
          {SHORTCUT_GROUPS.map((group, groupIdx) => (
            <div key={group.label}>
              {groupIdx > 0 && <Separator className="mb-4" />}
              <h3 className="text-sm font-semibold mb-2">{group.label}</h3>
              <div className="space-y-0.5">
                {group.shortcuts.map((shortcut) => (
                  <ShortcutRow
                    key={shortcut.description}
                    shortcut={shortcut}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>

        <SheetFooter className="border-t pt-4">
          <p className="text-xs text-muted-foreground w-full text-center">
            Press <KeyBadge>?</KeyBadge> to toggle this panel
          </p>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
