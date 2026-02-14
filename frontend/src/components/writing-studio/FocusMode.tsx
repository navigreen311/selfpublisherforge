"use client";

import {
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Re-export the hook for convenience
// ---------------------------------------------------------------------------

export { useFocusMode } from "@/hooks/use-focus-mode";
export type { FocusModeState } from "@/hooks/use-focus-mode";

// ---------------------------------------------------------------------------
// Focus Mode Overlay / Wrapper Component
// ---------------------------------------------------------------------------

interface FocusModeProps {
  /** Whether focus mode is active */
  isActive: boolean;
  /** Callback to exit focus mode */
  onExit: () => void;
  /** Current word count to show in minimal status */
  wordCount?: number;
  /** The editor content (children) */
  children: ReactNode;
  className?: string;
}

/**
 * Focus Mode wrapper component.
 *
 * When active, renders a full-screen distraction-free writing environment:
 * - Dark overlay background
 * - Centered content area (max-width 680px)
 * - Minimal "Exit Focus Mode" hint on mouse movement (fades after 3s)
 * - Optional word count display
 *
 * When inactive, renders children as-is (pass-through).
 *
 * @example
 * ```tsx
 * const { isFocusMode, exitFocusMode } = useFocusMode();
 *
 * <FocusMode isActive={isFocusMode} onExit={exitFocusMode} wordCount={1234}>
 *   <EditorContent editor={editor} />
 * </FocusMode>
 * ```
 */
export function FocusMode({
  isActive,
  onExit,
  wordCount,
  children,
  className,
}: FocusModeProps) {
  const [showExitHint, setShowExitHint] = useState(false);
  const hideTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---------------------------------------------------------------------------
  // Show "Exit Focus Mode" hint on mouse movement, fade after 3 seconds
  // ---------------------------------------------------------------------------
  const handleMouseMove = useCallback(() => {
    setShowExitHint(true);

    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current);
    }

    hideTimeoutRef.current = setTimeout(() => {
      setShowExitHint(false);
    }, 3000);
  }, []);

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
      }
    };
  }, []);

  // Reset hint visibility when entering/exiting focus mode
  useEffect(() => {
    if (isActive) {
      // Show hint briefly on enter
      setShowExitHint(true);
      hideTimeoutRef.current = setTimeout(() => {
        setShowExitHint(false);
      }, 3000);
    } else {
      setShowExitHint(false);
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
      }
    }
  }, [isActive]);

  // Prevent body scroll when in focus mode
  useEffect(() => {
    if (isActive) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isActive]);

  // ---------------------------------------------------------------------------
  // When not active, just pass through children
  // ---------------------------------------------------------------------------
  if (!isActive) {
    return <>{children}</>;
  }

  // ---------------------------------------------------------------------------
  // Active: full-screen distraction-free overlay
  // ---------------------------------------------------------------------------
  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex flex-col",
        "bg-black/60 backdrop-blur-sm",
        "transition-all duration-500 ease-in-out",
        "animate-in fade-in-0 duration-300",
        className
      )}
      onMouseMove={handleMouseMove}
    >
      {/* Exit hint — appears at top-right on mouse movement */}
      <div
        className={cn(
          "absolute top-4 right-6 z-[60] transition-opacity duration-500",
          showExitHint ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
      >
        <button
          type="button"
          onClick={onExit}
          className={cn(
            "text-xs text-white/60 hover:text-white/90 transition-colors",
            "bg-white/10 hover:bg-white/20 backdrop-blur-sm",
            "rounded-md px-3 py-1.5"
          )}
        >
          Exit Focus Mode
          <span className="ml-2 text-white/40">(Esc / F11)</span>
        </button>
      </div>

      {/* Minimal word count — bottom center */}
      {wordCount !== undefined && (
        <div
          className={cn(
            "absolute bottom-4 left-1/2 -translate-x-1/2 z-[60]",
            "transition-opacity duration-500",
            showExitHint ? "opacity-70" : "opacity-30"
          )}
        >
          <span className="text-xs text-white/60 tabular-nums">
            {wordCount.toLocaleString()} words
          </span>
        </div>
      )}

      {/* Centered writing area */}
      <div
        className={cn(
          "flex-1 flex items-start justify-center overflow-y-auto",
          "py-12 px-4"
        )}
      >
        <div className="w-full max-w-[680px] rounded-lg bg-background shadow-2xl">
          {children}
        </div>
      </div>
    </div>
  );
}
