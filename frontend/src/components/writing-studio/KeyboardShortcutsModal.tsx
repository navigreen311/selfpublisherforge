"use client";

import { useTranslations } from "@/hooks/use-translations";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface KeyboardShortcutsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ShortcutItem {
  keys: string[];
  label: string;
  labelKey: string;
}

interface ShortcutGroup {
  title: string;
  titleKey: string;
  shortcuts: ShortcutItem[];
}

const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    title: "Formatting",
    titleKey: "shortcuts.formatting",
    shortcuts: [
      { keys: ["Ctrl", "B"], label: "Bold", labelKey: "shortcuts.bold" },
      { keys: ["Ctrl", "I"], label: "Italic", labelKey: "shortcuts.italic" },
      { keys: ["Ctrl", "U"], label: "Underline", labelKey: "shortcuts.underline" },
      { keys: ["Ctrl", "1"], label: "Heading 1", labelKey: "shortcuts.heading1" },
      { keys: ["Ctrl", "2"], label: "Heading 2", labelKey: "shortcuts.heading2" },
      { keys: ["Ctrl", "3"], label: "Heading 3", labelKey: "shortcuts.heading3" },
      { keys: ["Ctrl", "Shift", "8"], label: "Bullet list", labelKey: "shortcuts.bulletList" },
      { keys: ["Ctrl", "Shift", "9"], label: "Numbered list", labelKey: "shortcuts.numberedList" },
    ],
  },
  {
    title: "Navigation",
    titleKey: "shortcuts.navigation",
    shortcuts: [
      { keys: ["Ctrl", "F"], label: "Find", labelKey: "shortcuts.find" },
      { keys: ["Ctrl", "H"], label: "Find and Replace", labelKey: "shortcuts.findReplace" },
      { keys: ["Ctrl", "K"], label: "Insert link", labelKey: "shortcuts.insertLink" },
    ],
  },
  {
    title: "Editor",
    titleKey: "shortcuts.editor",
    shortcuts: [
      { keys: ["Ctrl", "S"], label: "Force save", labelKey: "shortcuts.save" },
      { keys: ["Ctrl", "Z"], label: "Undo", labelKey: "shortcuts.undo" },
      { keys: ["Ctrl", "Shift", "Z"], label: "Redo", labelKey: "shortcuts.redo" },
      { keys: ["Ctrl", "Enter"], label: "AI Continue", labelKey: "shortcuts.aiContinue" },
      { keys: ["Ctrl", "Shift", "A"], label: "Toggle AI panel", labelKey: "shortcuts.toggleAI" },
      { keys: ["Ctrl", "Shift", "C"], label: "Toggle Chapter panel", labelKey: "shortcuts.toggleChapters" },
      { keys: ["F11"], label: "Focus Mode", labelKey: "shortcuts.focusMode" },
    ],
  },
];

function KeyPill({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex items-center justify-center min-w-[28px] h-6 rounded-md border border-gray-200 bg-gray-100 dark:border-gray-700 dark:bg-gray-800 px-2 text-[11px] font-mono font-medium text-gray-600 dark:text-gray-300 shadow-sm">
      {children}
    </kbd>
  );
}

function ShortcutKeys({ keys }: { keys: string[] }) {
  return (
    <div className="flex items-center gap-1">
      {keys.map((key, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && (
            <span className="text-[10px] text-muted-foreground">+</span>
          )}
          <KeyPill>{key}</KeyPill>
        </span>
      ))}
    </div>
  );
}

export function KeyboardShortcutsModal({
  open,
  onOpenChange,
}: KeyboardShortcutsModalProps) {
  const t = useTranslations("writing");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("shortcuts.title")}</DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-2 max-h-[70vh] overflow-y-auto">
          {SHORTCUT_GROUPS.map((group) => (
            <div key={group.titleKey}>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 border-b pb-2">
                {t(group.titleKey)}
              </h4>
              <table className="w-full">
                <tbody>
                  {group.shortcuts.map((shortcut) => (
                    <tr
                      key={shortcut.labelKey}
                      className="group"
                    >
                      <td className="py-1.5 pr-4 w-[200px]">
                        <ShortcutKeys keys={shortcut.keys} />
                      </td>
                      <td className="py-1.5 text-sm text-foreground">
                        {t(shortcut.labelKey)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>

        <div className="flex justify-end pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
          >
            {t("shortcuts.close") || "Close"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
