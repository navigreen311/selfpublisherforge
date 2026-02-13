"use client";

import { useState, useEffect, useCallback } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface FocusModeState {
  /** Whether focus mode is currently active */
  isFocusMode: boolean;
  /** Toggle focus mode on/off */
  toggleFocusMode: () => void;
  /** Explicitly enter focus mode */
  enterFocusMode: () => void;
  /** Explicitly exit focus mode */
  exitFocusMode: () => void;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Hook to manage distraction-free focus mode.
 *
 * Provides state and actions for entering/exiting focus mode.
 * Automatically listens for:
 * - **F11** to toggle focus mode
 * - **Escape** to exit focus mode (only when active)
 *
 * @returns `{ isFocusMode, toggleFocusMode, enterFocusMode, exitFocusMode }`
 *
 * @example
 * ```tsx
 * import { useFocusMode } from "@/hooks/use-focus-mode";
 * import { FocusMode } from "@/components/writing-studio/FocusMode";
 *
 * function WritingStudio() {
 *   const { isFocusMode, exitFocusMode } = useFocusMode();
 *
 *   return (
 *     <FocusMode isActive={isFocusMode} onExit={exitFocusMode} wordCount={1234}>
 *       <EditorContent editor={editor} />
 *     </FocusMode>
 *   );
 * }
 * ```
 */
export function useFocusMode(): FocusModeState {
  const [isFocusMode, setIsFocusMode] = useState(false);

  const toggleFocusMode = useCallback(() => {
    setIsFocusMode((prev) => !prev);
  }, []);

  const enterFocusMode = useCallback(() => {
    setIsFocusMode(true);
  }, []);

  const exitFocusMode = useCallback(() => {
    setIsFocusMode(false);
  }, []);

  // F11 to toggle focus mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "F11") {
        e.preventDefault();
        setIsFocusMode((prev) => !prev);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Escape to exit (only bound when focus mode is active)
  useEffect(() => {
    if (!isFocusMode) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setIsFocusMode(false);
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isFocusMode]);

  return {
    isFocusMode,
    toggleFocusMode,
    enterFocusMode,
    exitFocusMode,
  };
}
