"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  Loader2,
  LayoutGrid,
  Copy,
  Check,
  Image as ImageIcon,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useGenerateAPlusPlan, useAPlusPlans } from "../hooks";
import type { APlusModule, APlusPlanResponse } from "../types";
import { formatDistanceToNow } from "date-fns";

interface APlusContentTabProps {
  className?: string;
}

function ModuleCard({
  module,
  index,
}: {
  module: APlusModule;
  index: number;
}) {
  const [copiedPrompt, setCopiedPrompt] = useState(false);

  const handleCopyImagePrompt = async () => {
    const prompt = `Create an A+ Content image for "${module.title}" module. Type: ${module.type}. Dimensions: ${module.image_spec.width}x${module.image_spec.height}px. Content theme: ${module.content}`;
    try {
      await navigator.clipboard.writeText(prompt);
      setCopiedPrompt(true);
      setTimeout(() => setCopiedPrompt(false), 2000);
    } catch {
      // ignore
    }
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
              {index + 1}
            </div>
            <div>
              <CardTitle className="text-sm">{module.title}</CardTitle>
              <Badge variant="secondary" className="mt-1 text-xs">
                {module.type.replace(/_/g, " ")}
              </Badge>
            </div>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <ImageIcon className="h-3 w-3" />
            {module.image_spec.width} x {module.image_spec.height}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Description */}
        <p className="text-sm text-muted-foreground">{module.content}</p>

        {/* AI Copy */}
        {module.ai_copy && (
          <div className="rounded-md bg-muted p-3">
            <p className="text-xs font-medium text-muted-foreground mb-1">AI-Generated Copy:</p>
            <p className="text-sm">{module.ai_copy}</p>
          </div>
        )}

        {/* Image spec & action */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            Image: {module.image_spec.width}px x {module.image_spec.height}px
          </span>
          <Button variant="outline" size="sm" onClick={handleCopyImagePrompt}>
            {copiedPrompt ? (
              <>
                <Check className="mr-1.5 h-3 w-3" />
                Copied
              </>
            ) : (
              <>
                <Copy className="mr-1.5 h-3 w-3" />
                Generate Image Prompt
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function APlusContentTab({ className }: APlusContentTabProps) {
  const [title, setTitle] = useState("");
  const [genre, setGenre] = useState("");

  const generateMutation = useGenerateAPlusPlan();
  const { data: pastPlans, isLoading: isLoadingPlans } = useAPlusPlans();

  const handleGenerate = () => {
    if (!title.trim()) return;

    generateMutation.mutate({
      title: title.trim(),
      genre: genre.trim() || "general",
    });
  };

  const activePlan = generateMutation.data;

  return (
    <div className={cn("space-y-6", className)}>
      {/* Input section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <LayoutGrid className="h-5 w-5" />
            A+ Content Planner
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Generate an AI-powered A+ Content plan with module layouts, copy, and image
            specifications for your Amazon product page.
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="aplus-title">Book Title</Label>
              <Input
                id="aplus-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Your book title"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="aplus-genre">Genre</Label>
              <Input
                id="aplus-genre"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                placeholder="e.g., Romance, Self-Help"
              />
            </div>
          </div>

          <Button onClick={handleGenerate} disabled={!title.trim() || generateMutation.isPending}>
            {generateMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating A+ Plan...
              </>
            ) : (
              <>
                <LayoutGrid className="mr-2 h-4 w-4" />
                Generate A+ Plan
              </>
            )}
          </Button>

          {generateMutation.isError && (
            <Alert variant="destructive">
              <AlertDescription>
                Failed to generate A+ content plan. Please try again.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Generated plan results */}
      {activePlan && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">
              A+ Content Plan
            </h3>
            <Badge variant="secondary" className="text-xs">
              {activePlan.status}
            </Badge>
          </div>

          <div className="space-y-4">
            {activePlan.modules.map((mod: APlusModule, i: number) => (
              <ModuleCard key={i} module={mod} index={i} />
            ))}
          </div>

          {activePlan.modules.length === 0 && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No modules generated. Try again with more details.
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Past plans */}
      {!activePlan && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Previous A+ Plans</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingPlans ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : pastPlans && pastPlans.length > 0 ? (
              <div className="space-y-2">
                {pastPlans.slice(0, 5).map((plan: APlusPlanResponse) => (
                  <div
                    key={plan.id}
                    className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary" className="text-xs">
                        {plan.modules.length} modules
                      </Badge>
                      <span className="text-muted-foreground">{plan.id.slice(0, 8)}...</span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(plan.created_at), { addSuffix: true })}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                No previous A+ plans. Generate your first plan above.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
