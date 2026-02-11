"use client";

import { cn } from "@/lib/utils";

interface VisuallyHiddenProps {
  children: React.ReactNode;
  className?: string;
  /**
   * If true, the element will be announced to screen readers immediately
   * Equivalent to aria-live="assertive"
   */
  assertive?: boolean;
  /**
   * If true, the element will be announced to screen readers politely
   * Equivalent to aria-live="polite"
   */
  polite?: boolean;
}

/**
 * VisuallyHidden component for screen reader only content
 *
 * Provides content that:
 * - Is accessible to screen readers
 * - Is visually hidden from sighted users
 * - Maintains document flow and doesn't use display:none or visibility:hidden
 * - Meets WCAG 2.1 AA requirements for accessible labels and descriptions
 *
 * @example
 * ```tsx
 * <VisuallyHidden>Additional context for screen readers</VisuallyHidden>
 * <VisuallyHidden polite>Loading complete</VisuallyHidden>
 * ```
 */
export function VisuallyHidden({
  children,
  className,
  assertive = false,
  polite = false,
}: VisuallyHiddenProps) {
  const ariaLive = assertive ? "assertive" : polite ? "polite" : undefined;

  return (
    <span
      className={cn("sr-only", className)}
      aria-live={ariaLive}
      aria-atomic={ariaLive ? "true" : undefined}
    >
      {children}
    </span>
  );
}
