"use client";

import { cn } from "@/lib/utils";

interface SkipLinkProps {
  href?: string;
  children?: React.ReactNode;
  className?: string;
}

/**
 * SkipLink component for keyboard navigation accessibility
 *
 * Provides a "Skip to main content" link that:
 * - Is visually hidden until focused via keyboard (Tab key)
 * - Allows keyboard users to bypass repetitive navigation
 * - Meets WCAG 2.1 AA criterion 2.4.1 (Bypass Blocks)
 *
 * @example
 * ```tsx
 * <SkipLink href="#main-content">Skip to main content</SkipLink>
 * ```
 */
export function SkipLink({
  href = "#main-content",
  children = "Skip to main content",
  className,
}: SkipLinkProps) {
  return (
    <a
      href={href}
      className={cn(
        // Visually hidden by default
        "sr-only",
        // Visible when focused (Tab key)
        "focus:not-sr-only focus:absolute focus:z-50",
        "focus:top-4 focus:left-4",
        "focus:px-4 focus:py-2",
        "focus:bg-primary focus:text-primary-foreground",
        "focus:rounded-md focus:shadow-lg",
        "focus:ring-2 focus:ring-ring focus:ring-offset-2",
        "focus:outline-none",
        "transition-all duration-200",
        className
      )}
    >
      {children}
    </a>
  );
}
