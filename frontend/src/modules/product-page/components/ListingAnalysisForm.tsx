"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Loader2, Search, Clock, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAnalyzeListingMutation, useListingAnalyses } from "../hooks";
import type { ListingAnalysisResult } from "../types";
import { formatDistanceToNow } from "date-fns";

interface ListingAnalysisFormProps {
  onAnalysisComplete?: (result: ListingAnalysisResult) => void;
  className?: string;
}

export function ListingAnalysisForm({ onAnalysisComplete, className }: ListingAnalysisFormProps) {
  const [asinInput, setAsinInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const analyzeMutation = useAnalyzeListingMutation();
  const { data: recentAnalyses, isLoading: isLoadingRecent } = useListingAnalyses();

  const validateAsin = (value: string): boolean => {
    return /^[A-Z0-9]{10}$/i.test(value);
  };

  const handleAnalyze = () => {
    setValidationError(null);

    if (!asinInput && !urlInput) {
      setValidationError("Please enter an ASIN or Amazon URL.");
      return;
    }

    if (asinInput && !validateAsin(asinInput)) {
      setValidationError("ASIN must be exactly 10 alphanumeric characters.");
      return;
    }

    analyzeMutation.mutate(
      {
        asin: asinInput ? asinInput.toUpperCase() : undefined,
        url: !asinInput && urlInput ? urlInput : undefined,
      },
      {
        onSuccess: (result) => {
          onAnalysisComplete?.(result);
        },
      }
    );
  };

  const handleSelectRecent = (analysis: ListingAnalysisResult) => {
    onAnalysisComplete?.(analysis);
  };

  return (
    <div className={cn("space-y-6", className)}>
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Analyze Amazon Listing</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="asin-input">ASIN</Label>
              <Input
                id="asin-input"
                type="text"
                value={asinInput}
                onChange={(e) => {
                  setAsinInput(e.target.value);
                  setValidationError(null);
                }}
                placeholder="e.g. B0XXXXXXXXX"
                maxLength={10}
              />
              <p className="text-xs text-muted-foreground">
                10-character alphanumeric Amazon identifier
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="url-input">Or Amazon URL</Label>
              <Input
                id="url-input"
                type="url"
                value={urlInput}
                onChange={(e) => {
                  setUrlInput(e.target.value);
                  setValidationError(null);
                }}
                placeholder="https://amazon.com/dp/..."
              />
              <p className="text-xs text-muted-foreground">
                Full Amazon product page URL
              </p>
            </div>
          </div>

          {validationError && (
            <Alert variant="destructive">
              <AlertDescription>{validationError}</AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleAnalyze}
            disabled={(!asinInput && !urlInput) || analyzeMutation.isPending}
          >
            {analyzeMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing listing...
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Analyze Listing
              </>
            )}
          </Button>

          {analyzeMutation.isError && (
            <Alert variant="destructive">
              <AlertDescription>
                Failed to analyze listing. Please check your ASIN or URL and try again.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Recent analyses */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Recent Analyses
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingRecent ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : recentAnalyses && recentAnalyses.length > 0 ? (
            <div className="space-y-2">
              {recentAnalyses.slice(0, 5).map((analysis) => (
                <button
                  key={analysis.id}
                  onClick={() => handleSelectRecent(analysis)}
                  className="w-full flex items-center justify-between rounded-md border px-3 py-2 text-sm hover:bg-accent transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold",
                        analysis.overall_score >= 80
                          ? "bg-green-100 text-green-700"
                          : analysis.overall_score >= 60
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-red-100 text-red-700"
                      )}
                    >
                      {Math.round(analysis.overall_score)}
                    </div>
                    <span className="font-medium">{analysis.id.slice(0, 8)}...</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <span className="text-xs">
                      {formatDistanceToNow(new Date(analysis.created_at), { addSuffix: true })}
                    </span>
                    <ExternalLink className="h-3 w-3" />
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              No previous analyses found. Analyze your first listing above.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
