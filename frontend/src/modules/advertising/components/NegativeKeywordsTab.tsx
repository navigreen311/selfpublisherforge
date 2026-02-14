"use client";

import { useState } from "react";
import { useUpdateCampaign } from "../hooks";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { X, Plus } from "lucide-react";
import { toast } from "sonner";

interface NegativeKeywordsTabProps {
  campaignId: string;
  negativeKeywords: string[];
}

export function NegativeKeywordsTab({
  campaignId,
  negativeKeywords,
}: NegativeKeywordsTabProps) {
  const updateCampaign = useUpdateCampaign(campaignId);
  const [inputValue, setInputValue] = useState("");

  const handleAdd = async () => {
    const newKeywords = inputValue
      .split(/[,\n]+/)
      .map((kw) => kw.trim().toLowerCase())
      .filter((kw) => kw.length > 0);

    if (newKeywords.length === 0) {
      toast.error("Please enter at least one keyword");
      return;
    }

    // Deduplicate against existing keywords
    const existingSet = new Set(negativeKeywords.map((k) => k.toLowerCase()));
    const uniqueNew = newKeywords.filter((kw) => !existingSet.has(kw));

    if (uniqueNew.length === 0) {
      toast.info("All keywords already exist in the negative list");
      return;
    }

    try {
      await updateCampaign.mutateAsync({
        negative_keywords: [...negativeKeywords, ...uniqueNew],
      });
      toast.success(`Added ${uniqueNew.length} negative keyword(s)`);
      setInputValue("");
    } catch {
      toast.error("Failed to add negative keywords");
    }
  };

  const handleRemove = async (keyword: string) => {
    const updated = negativeKeywords.filter(
      (kw) => kw.toLowerCase() !== keyword.toLowerCase()
    );
    try {
      await updateCampaign.mutateAsync({ negative_keywords: updated });
      toast.success(`Removed "${keyword}" from negative keywords`);
    } catch {
      toast.error("Failed to remove negative keyword");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">
          Negative Keywords ({negativeKeywords.length})
        </h3>
        <p className="text-sm text-muted-foreground mt-1">
          Prevent your ads from showing for these search terms. This helps reduce
          wasted spend on irrelevant clicks.
        </p>
      </div>

      {/* Add negative keywords form */}
      <div className="border rounded-lg p-4 space-y-3">
        <label className="text-sm font-medium">Add Negative Keywords</label>
        <Textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Enter keywords separated by commas or new lines...&#10;Example: free, used, cheap"
          rows={3}
          className="resize-none"
        />
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Separate multiple keywords with commas or new lines
          </p>
          <Button
            size="sm"
            onClick={handleAdd}
            disabled={updateCampaign.isPending || !inputValue.trim()}
          >
            <Plus className="h-4 w-4 mr-1" />
            {updateCampaign.isPending ? "Adding..." : "Add"}
          </Button>
        </div>
      </div>

      {/* Existing negative keywords */}
      <div>
        {negativeKeywords.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {negativeKeywords.map((keyword, index) => (
              <Badge
                key={`${keyword}-${index}`}
                variant="secondary"
                className="pl-3 pr-1 py-1.5 text-sm flex items-center gap-1 bg-red-50 text-red-800 border-red-200 hover:bg-red-100"
              >
                {keyword}
                <button
                  onClick={() => handleRemove(keyword)}
                  disabled={updateCampaign.isPending}
                  className="ml-1 rounded-full p-0.5 hover:bg-red-200 transition-colors disabled:opacity-50"
                  title={`Remove "${keyword}"`}
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        ) : (
          <div className="border rounded-lg p-8 text-center text-muted-foreground">
            No negative keywords added yet. Add keywords above to prevent your
            ads from showing for irrelevant searches.
          </div>
        )}
      </div>
    </div>
  );
}
