"use client";

import React from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

// ─── Constants ───────────────────────────────────────────────────────────────

const REPORT_ISSUE_URL =
  "https://github.com/selfpublisherforge/selfpublisherforge/issues/new?template=bug_report.md";

// ─── Types ───────────────────────────────────────────────────────────────────

interface AudiobookErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface AudiobookErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

// ─── Component ───────────────────────────────────────────────────────────────

/**
 * Error boundary scoped to the audiobook module.
 * Catches rendering errors in audiobook components, shows a user-friendly
 * message with retry / report actions, and logs error details to console.
 */
export class AudiobookErrorBoundary extends React.Component<
  AudiobookErrorBoundaryProps,
  AudiobookErrorBoundaryState
> {
  constructor(props: AudiobookErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): AudiobookErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error("[AudiobookErrorBoundary] Caught error:", error);
    if (errorInfo?.componentStack) {
      // eslint-disable-next-line no-console
      console.error(
        "[AudiobookErrorBoundary] Component stack:",
        errorInfo.componentStack
      );
    }
  }

  private handleRetry = (): void => {
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
          aria-label="Audiobook module error"
          data-testid="audiobook-error-boundary"
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
                    The audiobook studio encountered an error. You can try again
                    or report this issue if the problem persists.
                  </p>
                  <p className="text-xs text-muted-foreground/70 font-mono break-all">
                    {errorMessage}
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-center gap-2">
                  <Button
                    onClick={this.handleRetry}
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
                      Report Issue
                    </a>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
