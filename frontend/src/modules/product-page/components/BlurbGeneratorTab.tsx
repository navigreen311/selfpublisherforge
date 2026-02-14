"use client";

import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useGenerateBlurbMutation } from "../hooks";
import { BlurbVersionCard } from "./BlurbVersionCard";
import type { BlurbVersion } from "../types";

interface BlurbGeneratorTabProps {
  className?: string;
}

const TONE_OPTIONS = [
  { value: "warm", label: "Warm" },
  { value: "professional", label: "Professional" },
  { value: "casual", label: "Casual" },
  { value: "urgent", label: "Urgent" },
  { value: "inspirational", label: "Inspirational" },
];

const VERSION_LABELS = ["Version A", "Version B", "Version C"];

export function BlurbGeneratorTab({ className }: BlurbGeneratorTabProps) {
  const [sellingPoints, setSellingPoints] = useState("");
  const [targetReader, setTargetReader] = useState("");
  const [tone, setTone] = useState("warm");
  const [currentBlurb, setCurrentBlurb] = useState("");

  const generateMutation = useGenerateBlurbMutation();

  const handleGenerate = () => {
    if (!sellingPoints.trim()) return;

    generateMutation.mutate({
      current_blurb: currentBlurb || sellingPoints,
      genre: "other",
      target_audience: targetReader || undefined,
      tone,
      num_variants: 3,
      keywords: sellingPoints
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    });
  };

  const handleUseVersion = (content: string) => {
    setCurrentBlurb(content);
  };

  return (
    <div className={className}>
      <div className="space-y-6">
        {/* Input section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              AI Blurb Generator
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="selling-points">
                Key Selling Points / Book Summary
              </Label>
              <Textarea
                id="selling-points"
                value={sellingPoints}
                onChange={(e) => setSellingPoints(e.target.value)}
                rows={4}
                placeholder="Describe your book's main selling points, themes, or premise..."
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="target-reader">Target Reader</Label>
                <Input
                  id="target-reader"
                  value={targetReader}
                  onChange={(e) => setTargetReader(e.target.value)}
                  placeholder="e.g., Women 25-45 who love romance"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tone-select">Tone</Label>
                <select
                  id="tone-select"
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  {TONE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="current-blurb">
                Current Blurb (optional -- for improvement)
              </Label>
              <Textarea
                id="current-blurb"
                value={currentBlurb}
                onChange={(e) => setCurrentBlurb(e.target.value)}
                rows={3}
                placeholder="Paste your existing blurb here to improve it..."
              />
            </div>

            <Button
              onClick={handleGenerate}
              disabled={!sellingPoints.trim() || generateMutation.isPending}
            >
              {generateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating 3 Versions...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate 3 Versions
                </>
              )}
            </Button>

            {generateMutation.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  Failed to generate blurb versions. Please try again.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        {generateMutation.data && generateMutation.data.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Generated Versions</h3>
            <div className="grid gap-4 md:grid-cols-3">
              {generateMutation.data.map((version: BlurbVersion, i: number) => (
                <BlurbVersionCard
                  key={i}
                  version={version}
                  label={VERSION_LABELS[i] ?? `Version ${i + 1}`}
                  onUse={handleUseVersion}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
