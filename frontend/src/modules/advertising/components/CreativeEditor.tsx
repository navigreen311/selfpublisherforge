"use client";

import { useState } from "react";
import { useGenerateCreatives, useCreatives } from "../hooks";
import type { GeneratedCreative, AdCreative } from "../hooks";
import { toast } from "sonner";

interface CreativeEditorProps {
  campaignId?: string;
  bookId?: string;
}

export function CreativeEditor({ campaignId, bookId }: CreativeEditorProps) {
  const { data: existingCreatives, isLoading } = useCreatives(campaignId);
  const generateCreatives = useGenerateCreatives();

  const [showGenerator, setShowGenerator] = useState(false);
  const [generatedResults, setGeneratedResults] = useState<GeneratedCreative[]>([]);
  const [formData, setFormData] = useState({
    book_title: "",
    book_description: "",
    genre: "",
    target_audience: "",
    tone: "professional",
    num_variations: 3,
    platform: "amazon" as "amazon" | "facebook",
  });

  const handleGenerate = async () => {
    if (!formData.book_title || !formData.book_description) {
      toast.error("Book title and description are required");
      return;
    }

    try {
      const result = await generateCreatives.mutateAsync({
        ...formData,
        book_id: bookId,
      } as any);
      setGeneratedResults(result.variations);
      toast.success(`Generated ${result.variations.length} creative variations`);
    } catch {
      toast.error("Failed to generate creatives");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Ad Creatives</h3>
        <button
          onClick={() => setShowGenerator(!showGenerator)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90"
        >
          {showGenerator ? "Hide Generator" : "Generate New"}
        </button>
      </div>

      {/* AI Generator Form */}
      {showGenerator && (
        <div className="border rounded-lg p-5 bg-muted/10 space-y-4">
          <h4 className="font-medium">AI Creative Generator</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Book Title *</label>
              <input
                type="text"
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={formData.book_title}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, book_title: e.target.value }))
                }
                placeholder="Enter book title"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Genre</label>
              <input
                type="text"
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={formData.genre}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, genre: e.target.value }))
                }
                placeholder="e.g., Fantasy, Romance"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Book Description *</label>
              <textarea
                className="w-full border rounded-lg px-3 py-2 text-sm"
                rows={3}
                value={formData.book_description}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    book_description: e.target.value,
                  }))
                }
                placeholder="Enter book description or blurb"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Target Audience</label>
              <input
                type="text"
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={formData.target_audience}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    target_audience: e.target.value,
                  }))
                }
                placeholder="e.g., Fantasy readers 18-45"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Platform</label>
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={formData.platform}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    platform: e.target.value as "amazon" | "facebook",
                  }))
                }
              >
                <option value="amazon">Amazon Ads</option>
                <option value="facebook">Facebook Ads</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Tone</label>
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={formData.tone}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, tone: e.target.value }))
                }
              >
                <option value="professional">Professional</option>
                <option value="exciting">Exciting</option>
                <option value="emotional">Emotional</option>
                <option value="humorous">Humorous</option>
                <option value="mysterious">Mysterious</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Variations</label>
              <input
                type="number"
                min={1}
                max={10}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={formData.num_variations}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    num_variations: parseInt(e.target.value) || 3,
                  }))
                }
              />
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generateCreatives.isPending}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90 disabled:opacity-50"
          >
            {generateCreatives.isPending ? "Generating..." : "Generate Creatives"}
          </button>

          {/* Generated Results */}
          {generatedResults.length > 0 && (
            <div className="mt-4 space-y-3">
              <h4 className="font-medium text-sm">Generated Variations</h4>
              {generatedResults.map((creative, index) => (
                <div
                  key={index}
                  className="border rounded-lg p-4 bg-background space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      Variation {index + 1}
                    </span>
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">
                      {creative.call_to_action}
                    </span>
                  </div>
                  <h5 className="font-semibold">{creative.headline}</h5>
                  <p className="text-sm text-muted-foreground">
                    {creative.body_text}
                  </p>
                  {creative.reasoning && (
                    <p className="text-xs text-muted-foreground italic">
                      Strategy: {creative.reasoning}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Existing Creatives */}
      {isLoading ? (
        <div className="animate-pulse space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-24 bg-muted rounded" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {(existingCreatives || []).map((creative) => (
            <CreativeCard key={creative.id} creative={creative} />
          ))}
          {(existingCreatives || []).length === 0 && !showGenerator && (
            <p className="text-center text-muted-foreground py-8">
              No creatives yet. Click &quot;Generate New&quot; to create AI-powered ad copy.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function CreativeCard({ creative }: { creative: AdCreative }) {
  const statusStyles: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    draft: "bg-gray-100 text-gray-800",
    paused: "bg-yellow-100 text-yellow-800",
    rejected: "bg-red-100 text-red-800",
  };

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-semibold">{creative.headline}</h4>
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            statusStyles[creative.status] || statusStyles.draft
          }`}
        >
          {creative.status}
        </span>
      </div>
      <p className="text-sm text-muted-foreground mb-3">{creative.body_text}</p>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span>CTA: {creative.call_to_action}</span>
        <span>{creative.impressions.toLocaleString()} impr.</span>
        <span>{creative.clicks} clicks</span>
        <span>CTR: {creative.ctr.toFixed(2)}%</span>
        <span>{creative.conversions} conversions</span>
      </div>
    </div>
  );
}
