"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

// ─── Constants ───────────────────────────────────────────────────────────────

const IS_DEVELOPMENT = process.env.NODE_ENV === "development";

const REPORT_ISSUE_URL =
  "https://github.com/selfpublisherforge/selfpublisherforge/issues/new?template=bug_report.md";

// ─── Error Reporting ─────────────────────────────────────────────────────────

/**
 * Centralized error reporting function.
 * In development, logs to console. In production, dispatches to an
 * external error-tracking service.
 */
function reportError(error: Error, errorInfo: React.ErrorInfo): void {
  if (IS_DEVELOPMENT) {
    // eslint-disable-next-line no-console
    console.error("[ErrorBoundary] Caught error:", error);
    // eslint-disable-next-line no-console
    console.error("[ErrorBoundary] Component stack:", errorInfo.componentStack);
  } else {
    // TODO: Integrate production error reporting service (Sentry, DataDog, etc.)
    // Example Sentry integration:
    //   Sentry.captureException(error, {
    //     contexts: { react: { componentStack: errorInfo.componentStack } },
    //   });
    //
    // Example DataDog integration:
    //   datadogRum.addError(error, {
    //     componentStack: errorInfo.componentStack,
    //   });
  }
}

// ─── Types ───────────────────────────────────────────────────────────────────

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

// ─── ErrorBoundaryInner (class component) ────────────────────────────────────

/**
 * Inner class component that implements the actual error boundary logic.
 * Wrapped by the outer `ErrorBoundary` function component to enable
 * hook-based navigation reset.
 */
class ErrorBoundaryInner extends React.Component<
  ErrorBoundaryProps & { resetKey: string },
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps & { resetKey: string }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    reportError(error, errorInfo);
  }

  componentDidUpdate(
    prevProps: ErrorBoundaryProps & { resetKey: string }
  ): void {
    // Reset error state when the route changes (resetKey is derived from pathname)
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false, error: null });
    }
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const errorMessage =
        this.state.error?.message || "An unexpected error occurred.";

      return (
        <div
          className="flex items-center justify-center min-h-[40vh] p-6"
          role="alert"
          aria-label="Application error"
        >
          <Card className="w-full max-w-md">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center gap-4">
                <div className="rounded-full bg-destructive/10 p-3">
                  <AlertTriangle
                    className="h-8 w-8 text-destructive"
                    aria-hidden="true"
                  />
                </div>

                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">
                    Something went wrong
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {errorMessage}
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-center gap-2">
                  <Button
                    onClick={this.handleReset}
                    variant="outline"
                    aria-label="Try again to recover from the error"
                  >
                    Try again
                  </Button>

                  <Button variant="ghost" size="sm" asChild>
                    <a
                      href={REPORT_ISSUE_URL}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label="Report this issue on GitHub"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="mr-1.5 h-4 w-4"
                        aria-hidden="true"
                      >
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                      </svg>
                      Report this issue
                    </a>
                  </Button>
                </div>

                {IS_DEVELOPMENT && this.state.error && (
                  <details className="w-full text-left mt-2">
                    <summary className="cursor-pointer text-xs font-medium text-muted-foreground">
                      Error details (dev only)
                    </summary>
                    <pre className="mt-2 p-3 bg-muted rounded text-xs overflow-auto max-h-40 whitespace-pre-wrap break-words">
                      {this.state.error.stack || this.state.error.message}
                    </pre>
                  </details>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// ─── Hooks ───────────────────────────────────────────────────────────────────

/**
 * Safely calls `usePathname()` from Next.js. Returns a fallback value when
 * the navigation context is unavailable (e.g., in test environments).
 */
function useSafePathname(): string {
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    return usePathname() ?? "/";
  } catch {
    return "/";
  }
}

// ─── ErrorBoundary (public wrapper) ──────────────────────────────────────────

/**
 * Public error boundary component that automatically resets on route changes.
 * Uses `usePathname()` from Next.js to detect navigation events and clear
 * the error state when the user navigates to a different page.
 */
export function ErrorBoundary({ children, fallback }: ErrorBoundaryProps) {
  const pathname = useSafePathname();

  return (
    <ErrorBoundaryInner resetKey={pathname} fallback={fallback}>
      {children}
    </ErrorBoundaryInner>
  );
}
