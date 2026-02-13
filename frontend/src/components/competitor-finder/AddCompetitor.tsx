"use client";

import { useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { useAddCompetitor } from "@/modules/competitors/hooks";
import type { AddCompetitorRequest } from "@/modules/competitors/hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Upload } from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Auto-detect the input type from the user's raw text. */
function detectInputType(value: string): AddCompetitorRequest["type"] {
  const trimmed = value.trim();
  if (trimmed.startsWith("B0") && trimmed.length === 10) return "asin";
  if (trimmed.toLowerCase().includes("amazon")) return "url";
  return "title";
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface AddCompetitorProps {
  trackedCount?: number;
  projectCount?: number;
}

export function AddCompetitor({
  trackedCount = 0,
  projectCount = 0,
}: AddCompetitorProps) {
  const t = useTranslations("competitors");
  const [inputValue, setInputValue] = useState("");
  const addMutation = useAddCompetitor();

  const handleAdd = () => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    addMutation.mutate(
      {
        identifier: trimmed,
        type: detectInputType(trimmed),
      },
      {
        onSuccess: () => setInputValue(""),
      },
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="space-y-3">
      {/* Input row */}
      <div className="flex items-center gap-2">
        <Input
          className="flex-1"
          placeholder={t("addPlaceholder")}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={addMutation.isPending}
        />
        <Button
          onClick={handleAdd}
          disabled={addMutation.isPending || !inputValue.trim()}
        >
          <Plus className="mr-2 h-4 w-4" />
          {addMutation.isPending ? t("adding") : t("add")}
        </Button>
      </div>

      {/* Status row */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {trackedCount > 0 || projectCount > 0
            ? t("tracking", {
                count: trackedCount,
                projects: projectCount,
              })
            : t("noTracking")}
        </p>

        <Button variant="outline" size="sm">
          <Upload className="mr-2 h-4 w-4" />
          {t("importFromProject")}
        </Button>
      </div>
    </div>
  );
}
