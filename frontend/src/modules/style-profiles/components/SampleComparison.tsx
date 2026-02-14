"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useGenerateSample } from "../hooks";

interface SampleComparisonProps {
  profileId: string;
}

export function SampleComparison({ profileId }: SampleComparisonProps) {
  const [prompt, setPrompt] = useState("");
  const generateSample = useGenerateSample(profileId);

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    generateSample.mutate({ prompt: prompt.trim() });
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter a prompt to generate a styled sample..."
          className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          onKeyDown={(e) => {
            if (e.key === "Enter") handleGenerate();
          }}
        />
        <Button
          onClick={handleGenerate}
          disabled={!prompt.trim() || generateSample.isPending}
          size="sm"
        >
          {generateSample.isPending ? "Generating..." : "Generate"}
        </Button>
      </div>

      {generateSample.data && (
        <div className="space-y-3">
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1">Prompt</h5>
            <p className="text-sm italic">{generateSample.data.prompt}</p>
          </div>
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1">
              Generated Sample
            </h5>
            <div className="rounded-md border bg-muted/50 p-4">
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {generateSample.data.generated_text}
              </p>
            </div>
          </div>
        </div>
      )}

      {generateSample.isError && (
        <p className="text-sm text-destructive">
          Failed to generate sample. Please try again.
        </p>
      )}

      {!generateSample.data && !generateSample.isPending && (
        <p className="text-sm text-muted-foreground text-center py-4">
          Enter a prompt to see how your writing style would handle it.
        </p>
      )}
    </div>
  );
}
