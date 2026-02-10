"use client";

import * as React from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

function OAuthCallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { handleOAuthCallback } = useAuth();
  const [error, setError] = React.useState("");
  const [isProcessing, setIsProcessing] = React.useState(true);
  const hasRun = React.useRef(false);

  React.useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const code = searchParams.get("code");
    const provider = searchParams.get("provider") || searchParams.get("state");

    if (!code) {
      setError("No authorization code received. Please try again.");
      setIsProcessing(false);
      return;
    }

    if (!provider) {
      setError("Could not determine the OAuth provider. Please try again.");
      setIsProcessing(false);
      return;
    }

    handleOAuthCallback(provider, code)
      .catch((err: unknown) => {
        const message =
          err instanceof Error
            ? err.message
            : "Authentication failed. Please try again.";
        setError(message);
        setIsProcessing(false);
      });
  }, [searchParams, handleOAuthCallback]);

  if (isProcessing && !error) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Signing you in</CardTitle>
          <CardDescription>
            Please wait while we complete authentication...
          </CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Authentication failed</CardTitle>
        <CardDescription>
          Something went wrong during sign in
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button
          className="w-full"
          onClick={() => router.push("/login")}
        >
          Back to login
        </Button>
      </CardContent>
    </Card>
  );
}

export default function OAuthCallbackPage() {
  return (
    <React.Suspense
      fallback={
        <Card className="w-full max-w-md">
          <CardContent className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </CardContent>
        </Card>
      }
    >
      <OAuthCallbackContent />
    </React.Suspense>
  );
}
