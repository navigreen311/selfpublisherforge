"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

interface QueryErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface QueryErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * QueryErrorBoundary - React error boundary for catching errors in React Query hooks
 *
 * Wraps components that use React Query hooks and provides a user-friendly
 * error UI when queries fail. Includes retry functionality.
 */
export class QueryErrorBoundary extends Component<
  QueryErrorBoundaryProps,
  QueryErrorBoundaryState
> {
  constructor(props: QueryErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): QueryErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to console in development
    if (process.env.NODE_ENV === "development") {
      // eslint-disable-next-line no-console
      console.error("QueryErrorBoundary caught an error:", error, errorInfo);
    }
  }

  resetErrorBoundary = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.resetErrorBoundary);
      }

      // Default error UI
      return (
        <Card className="border-destructive/50">
          <CardHeader className="text-center">
            <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
              <AlertTriangle className="h-6 w-6 text-destructive" />
            </div>
            <CardTitle className="text-xl">Something went wrong</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-muted-foreground">
              {this.state.error.message || "An unexpected error occurred while loading this section."}
            </p>
            {process.env.NODE_ENV === "development" && (
              <details className="mt-4 text-left">
                <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                  Error details (dev mode)
                </summary>
                <pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">
                  {this.state.error.stack}
                </pre>
              </details>
            )}
          </CardContent>
          <CardFooter className="flex justify-center">
            <Button onClick={this.resetErrorBoundary} variant="outline" className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Try again
            </Button>
          </CardFooter>
        </Card>
      );
    }

    return this.props.children;
  }
}
