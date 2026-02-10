"use client";

import React from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    if (process.env.NODE_ENV === "development") {
      console.error("ErrorBoundary caught:", error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex items-center justify-center min-h-[40vh] p-6">
          <Card className="w-full max-w-md">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center gap-4">
                <div className="rounded-full bg-destructive/10 p-3">
                  <AlertTriangle className="h-8 w-8 text-destructive" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">Something went wrong</h3>
                  <p className="text-sm text-muted-foreground">
                    {this.state.error?.message || "An unexpected error occurred."}
                  </p>
                </div>
                <Button
                  onClick={() => this.setState({ hasError: false, error: null })}
                  variant="outline"
                >
                  Try again
                </Button>
                {process.env.NODE_ENV === "development" && this.state.error?.message && (
                  <pre className="mt-4 p-3 bg-muted rounded text-xs overflow-auto max-h-40">
                    {this.state.error.message}
                  </pre>
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
