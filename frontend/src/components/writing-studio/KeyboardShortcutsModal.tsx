"use client";

import { useTranslations } from "@/hooks/use-translations";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface KeyboardShortcutsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ShortcutItem {
  keys: string;
  labelKey: string;
}

interface ShortcutGroup {
  titleKey: string;
  shortcuts: ShortcutItem[];
}

const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    titleKey: "shortcuts.formatting",
    shortcuts: [
      { keys: "Ctrl + B", labelKey: "shortcuts.bold" },
      { keys: "Ctrl + I", labelKey: "shortcuts.italic" },
      { keys: "Ctrl + U", labelKey: "shortcuts.underline" },
      { keys: "Ctrl + K", labelKey: "shortcuts.insertLink" },
      { keys: "Ctrl + 1", labelKey: "shortcuts.heading1" },
      { keys: "Ctrl + 2", labelKey: "shortcuts.heading2" },
      { keys: "Ctrl + 3", labelKey: "shortcuts.heading3" },
      { keys: "Ctrl + Shift + 8", labelKey: "shortcuts.bulletList" },
      { keys: "Ctrl + Shift + 9", labelKey: "shortcuts.numberedList" },
    ],
  },
  {
    titleKey: "shortcuts.editor",
    shortcuts: [
      { keys: "Ctrl + Z", labelKey: "shortcuts.undo" },
      { keys: "Ctrl + Shift + Z", labelKey: "shortcuts.redo" },
      { keys: "Ctrl + S", labelKey: "shortcuts.save" },
      { keys: "Ctrl + F", labelKey: "shortcuts.find" },
      { keys: "Ctrl + H", labelKey: "shortcuts.findReplace" },
    ],
  },
  {
    titleKey: "shortcuts.panels",
    shortcuts: [
      { keys: "Ctrl + Shift + A", labelKey: "shortcuts.toggleAI" },
      { keys: "Ctrl + Shift + C", labelKey: "shortcuts.toggleChapters" },
      { keys: "F11", labelKey: "shortcuts.focusMode" },
      { keys: "Ctrl + Enter", labelKey: "shortcuts.aiContinue" },
    ],
  },
];

export function KeyboardShortcutsModal({
  open,
  onOpenChange,
}: KeyboardShortcutsModalProps) {
  const t = useTranslations("writing");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("shortcuts.title")}</DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-2">
          {SHORTCUT_GROUPS.map((group) => (
            <div key={group.titleKey}>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                {t(group.titleKey)}
              </h4>
              <div className="space-y-2">
                {group.shortcuts.map((shortcut) => (
                  <div
                    key={shortcut.keys}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="text-foreground">
                      {t(shortcut.labelKey)}
                    </span>
                    <kbd className="inline-flex items-center gap-1 rounded border bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
                      {shortcut.keys}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
