"use client";

import { useCallback, useEffect, useRef } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * Options for the `useFocusTrap` hook.
 */
export interface UseFocusTrapOptions {
  /**
   * Whether the focus trap is currently active.
   * When `true`, Tab / Shift+Tab cycles within the container.
   */
  active: boolean;

  /**
   * Optional callback invoked when the user presses the Escape key
   * while the trap is active. Typically used to close a modal.
   */
  onEscape?: () => void;

  /**
   * If `true`, the first focusable element inside the container will
   * receive focus automatically when the trap activates.
   * @default true
   */
  autoFocus?: boolean;

  /**
   * If `true`, focus is restored to the element that was focused before
   * the trap activated.
   * @default true
   */
  restoreFocus?: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** CSS selector that matches all natively-focusable and programmatically-focusable elements. */
const FOCUSABLE_SELECTOR = [
  'a[href]',
  'area[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  'details > summary',
  'audio[controls]',
  'video[controls]',
  '[contenteditable]:not([contenteditable="false"])',
].join(", ");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Query all focusable elements within a container, filtered to only those
 * that are visible (have layout dimensions).
 */
function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const elements = Array.from(
    container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
  );
  return elements.filter(
    (el) => !el.hasAttribute("disabled") && el.offsetParent !== null,
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Trap keyboard focus within a container element for accessibility.
 *
 * When active, Tab / Shift+Tab cycles through focusable descendants and
 * pressing Escape invokes the optional `onEscape` callback. On deactivation
 * focus is returned to the element that was focused before the trap engaged.
 *
 * A `MutationObserver` watches for DOM changes inside the container so the
 * list of focusable elements stays up to date with dynamic content.
 *
 * @param containerRef - React ref pointing to the container element.
 * @param options      - Configuration (see {@link UseFocusTrapOptions}).
 *
 * @example
 * ```tsx
 * const containerRef = useRef<HTMLDivElement>(null);
 * useFocusTrap(containerRef, {
 *   active: isOpen,
 *   onEscape: () => setIsOpen(false),
 * });
 *
 * return (
 *   <div ref={containerRef} role="dialog" aria-modal="true">
 *     <button>First</button>
 *     <button>Last</button>
 *   </div>
 * );
 * ```
 */
export function useFocusTrap(
  containerRef: React.RefObject<HTMLElement | null>,
  options: UseFocusTrapOptions,
): void {
  const { active, onEscape, autoFocus = true, restoreFocus = true } = options;

  // Track the element that held focus before the trap activated.
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Keep a mutable cache of focusable elements so the keydown handler always
  // works with the latest set without needing to re-attach the listener.
  const focusableElementsRef = useRef<HTMLElement[]>([]);

  // -------------------------------------------------------------------------
  // Refresh the cached list of focusable elements
  // -------------------------------------------------------------------------
  const refreshFocusableElements = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    focusableElementsRef.current = getFocusableElements(container);
  }, [containerRef]);

  // -------------------------------------------------------------------------
  // Keydown handler — trap Tab / Shift+Tab and handle Escape
  // -------------------------------------------------------------------------
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onEscape?.();
        return;
      }

      if (event.key !== "Tab") return;

      // Refresh in case DOM changed since last mutation event.
      refreshFocusableElements();

      const focusable = focusableElementsRef.current;
      if (focusable.length === 0) {
        // No focusable elements — prevent Tab from leaving the container.
        event.preventDefault();
        return;
      }

      const firstElement = focusable[0];
      const lastElement = focusable[focusable.length - 1];

      if (event.shiftKey) {
        // Shift+Tab: if focus is on the first element, wrap to the last.
        if (
          document.activeElement === firstElement ||
          !containerRef.current?.contains(document.activeElement)
        ) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab: if focus is on the last element, wrap to the first.
        if (
          document.activeElement === lastElement ||
          !containerRef.current?.contains(document.activeElement)
        ) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    },
    [containerRef, onEscape, refreshFocusableElements],
  );

  // -------------------------------------------------------------------------
  // Activate / deactivate the trap
  // -------------------------------------------------------------------------
  useEffect(() => {
    const container = containerRef.current;

    if (!active || !container) {
      return;
    }

    // Capture currently focused element so we can restore it later.
    previousFocusRef.current = document.activeElement as HTMLElement | null;

    // Build initial list of focusable elements.
    refreshFocusableElements();

    // Auto-focus the first focusable element inside the container.
    if (autoFocus) {
      // Use requestAnimationFrame to let the browser paint the container
      // before moving focus — necessary for transition-based modals.
      requestAnimationFrame(() => {
        const focusable = focusableElementsRef.current;
        if (focusable.length > 0) {
          focusable[0].focus();
        } else {
          // Fallback: make the container itself focusable.
          container.setAttribute("tabindex", "-1");
          container.focus();
        }
      });
    }

    // Listen for keydown on the document to intercept Tab before the
    // browser moves focus outside the container.
    document.addEventListener("keydown", handleKeyDown);

    // Observe the container for DOM mutations (dynamic content) so we
    // keep the focusable-element cache accurate.
    const observer = new MutationObserver(() => {
      refreshFocusableElements();
    });

    observer.observe(container, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["disabled", "tabindex", "href", "hidden", "style"],
    });

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      observer.disconnect();

      // Restore focus to the element that was focused before the trap.
      if (restoreFocus && previousFocusRef.current) {
        // Use setTimeout to let the closing animation finish before
        // restoring focus — avoids visual glitches.
        const elementToRestore = previousFocusRef.current;
        setTimeout(() => {
          if (elementToRestore && typeof elementToRestore.focus === "function") {
            elementToRestore.focus();
          }
        }, 0);
      }

      previousFocusRef.current = null;
    };
  }, [
    active,
    autoFocus,
    restoreFocus,
    containerRef,
    handleKeyDown,
    refreshFocusableElements,
  ]);
}
