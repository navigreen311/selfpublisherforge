"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CommandPalette } from "@/components/shared/CommandPalette";
import { KeyboardShortcutsHelp } from "@/components/shared/KeyboardShortcutsHelp";

function isEditableTarget(t: EventTarget | null): boolean {
  if (!t || !(t instanceof HTMLElement)) return false;
  const tag = t.tagName;
  return (
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT" ||
    t.isContentEditable
  );
}

export function KeyboardShortcutsProvider() {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const router = useRouter();

  const handler = useCallback(
    (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;

      // Ctrl/Cmd+K - command palette (always)
      if (mod && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((o) => !o);
        return;
      }

      // Ctrl/Cmd+N - new project
      if (mod && e.key.toLowerCase() === "n") {
        e.preventDefault();
        router.push("/projects?new=1");
        return;
      }

      // Non-modifier keys should be ignored when typing
      if (isEditableTarget(e.target)) return;

      // "/" focus search
      if (e.key === "/" && !mod) {
        e.preventDefault();
        const search = document.querySelector<HTMLInputElement>(
          'input[aria-label^="Search"]'
        );
        search?.focus();
        return;
      }

      // "?" help
      if (e.key === "?" && !mod) {
        e.preventDefault();
        setHelpOpen((o) => !o);
        return;
      }
    },
    [router]
  );

  useEffect(() => {
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handler]);

  return (
    <>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
      <KeyboardShortcutsHelp open={helpOpen} onOpenChange={setHelpOpen} />
    </>
  );
}
