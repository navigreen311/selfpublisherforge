"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Copy, Check, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { BlurbVersion } from "../types";

interface BlurbVersionCardProps {
  version: BlurbVersion;
  label: string;
  onUse?: (content: string) => void;
  className?: string;
}

const STYLE_LABELS: Record<string, string> = {
  story_led: "Story-led",
  benefit_led: "Benefit-led",
  problem_solution: "Problem-Solution",
};

export function BlurbVersionCard({
  version,
  label,
  onUse,
  className,
}: BlurbVersionCardProps) {
  const [copied, setCopied] = useState(false);

  const scoreColor =
    version.score >= 80
      ? "bg-green-100 text-green-800"
      : version.score >= 60
        ? "bg-yellow-100 text-yellow-800"
        : "bg-red-100 text-red-800";

  const wordCount = version.plain_content.split(/\s+/).filter(Boolean).length;
  const styleName = STYLE_LABELS[version.style] ?? version.style.replace(/_/g, " ");

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(version.plain_content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: ignore if clipboard is not available
    }
  };

  return (
    <Card className={cn("flex flex-col", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">
            {label}{" "}
            <span className="font-normal text-muted-foreground">
              ({styleName})
            </span>
          </CardTitle>
          <Badge className={cn("text-xs font-bold", scoreColor)} variant="secondary">
            {Math.round(version.score)}/100
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        {/* Rendered content */}
        <div
          className="text-sm text-foreground leading-relaxed mb-3 flex-1 max-h-56 overflow-y-auto prose prose-sm"
          dangerouslySetInnerHTML={{ __html: version.html_content }}
        />

        {/* Word count */}
        <p className="text-xs text-muted-foreground mb-3">
          {wordCount} words
        </p>

        {/* Actions */}
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            {copied ? (
              <>
                <Check className="mr-1.5 h-3 w-3" />
                Copied
              </>
            ) : (
              <>
                <Copy className="mr-1.5 h-3 w-3" />
                Copy to Clipboard
              </>
            )}
          </Button>
          {onUse && (
            <Button size="sm" onClick={() => onUse(version.plain_content)}>
              <ArrowRight className="mr-1.5 h-3 w-3" />
              Use This Version
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
