"use client";

import Link from "next/link";
import { FileQuestion, Home, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";

/**
 * Dashboard 404 Not Found Page
 *
 * Shown when a user navigates to a non-existent route within the dashboard.
 * Provides helpful navigation options to get back on track.
 */
export default function DashboardNotFound() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center pb-4">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <FileQuestion className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
          </div>
        </CardHeader>
        <CardContent className="text-center space-y-2">
          <h1 className="text-3xl font-bold">404</h1>
          <h2 className="text-xl font-semibold">Page Not Found</h2>
          <p className="text-sm text-muted-foreground pt-2">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
        </CardContent>
        <CardFooter className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button variant="outline" asChild className="gap-2">
            <Link href="/dashboard">
              <Home className="h-4 w-4" />
              Go to Dashboard
            </Link>
          </Button>
          <Button variant="ghost" onClick={() => window.history.back()} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Go Back
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
