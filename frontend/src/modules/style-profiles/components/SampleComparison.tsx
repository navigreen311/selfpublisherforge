"use client";

import { useState } from "react";
import { Plus, Upload, FileText, Trash2 } from "lucide-react";

interface SampleComparisonProps {
  onAddSamples: (texts: string[]) => void;
  isSubmitting?: boolean;
}

export function SampleComparison({ onAddSamples, isSubmitting = false }: SampleComparisonProps) {
  const [textInput, setTextInput] = useState("");
  const [sampleTexts, setSampleTexts] = useState<string[]>([]);

  const handleAddText = () => {
    if (textInput.trim()) {
      setSampleTexts((prev) => [...prev, textInput.trim()]);
      setTextInput("");
    }
  };

  const handleRemoveText = (index: number) => {
    setSampleTexts((prev) => prev.filter((_, i) => i !== index));
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      if (text) {
        setSampleTexts((prev) => [...prev, text]);
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleSubmit = () => {
    const allTexts = textInput.trim()
      ? [...sampleTexts, textInput.trim()]
      : sampleTexts;
    if (allTexts.length > 0) {
      onAddSamples(allTexts);
      setSampleTexts([]);
      setTextInput("");
    }
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Writing Samples</h3>

      {/* Add new sample */}
      <div className="border rounded-lg bg-card p-4 space-y-3">
        <h4 className="text-sm font-medium">Add New Sample</h4>
        <textarea
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Paste a writing sample here (at least a few paragraphs)..."
          rows={6}
          className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleAddText}
            disabled={!textInput.trim()}
            className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add to List
          </button>
          <label className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-accent cursor-pointer">
            <Upload className="h-4 w-4" aria-hidden="true" />
            Upload File
            <input
              type="file"
              accept=".txt,.md"
              onChange={handleFileUpload}
              className="hidden"
              aria-label="Upload text file"
            />
          </label>
        </div>
      </div>

      {/* Queued samples */}
      {sampleTexts.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">
              Queued Samples ({sampleTexts.length})
            </h4>
          </div>
          <div className="space-y-2">
            {sampleTexts.map((text, idx) => (
              <div
                key={idx}
                className="border rounded-lg p-3 bg-card flex items-start justify-between gap-3"
              >
                <div className="flex items-start gap-2 flex-1 min-w-0">
                  <FileText className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" aria-hidden="true" />
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {text.substring(0, 200)}
                    {text.length > 200 ? "..." : ""}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveText(idx)}
                  aria-label={`Remove sample ${idx + 1}`}
                  className="text-destructive hover:text-destructive/80 shrink-0 p-1"
                >
                  <Trash2 className="h-4 w-4" aria-hidden="true" />
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Analyzing..." : "Analyze Samples"}
            </button>
          </div>
        </div>
      )}

      {sampleTexts.length === 0 && !textInput && (
        <div className="border rounded-lg bg-muted/30 p-6 text-center">
          <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm text-muted-foreground">
            No samples queued. Add writing samples above to refine your style profile.
          </p>
        </div>
      )}
    </div>
  );
}
