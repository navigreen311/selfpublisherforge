"use client";

import { useState } from "react";
import { Upload, FileText } from "lucide-react";

interface TextIngestionProps {
  onSubmit: (texts: string[]) => void;
  isSubmitting?: boolean;
}

export function TextIngestion({ onSubmit, isSubmitting = false }: TextIngestionProps) {
  const [textInput, setTextInput] = useState("");
  const [sampleTexts, setSampleTexts] = useState<string[]>([]);

  const handleAddText = () => {
    if (textInput.trim()) {
      setSampleTexts([...sampleTexts, textInput.trim()]);
      setTextInput("");
    }
  };

  const handleRemoveText = (index: number) => {
    setSampleTexts(sampleTexts.filter((_, i) => i !== index));
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      if (text) {
        setSampleTexts([...sampleTexts, text]);
      }
    };
    reader.readAsText(file);
  };

  const handleSubmit = () => {
    const allTexts = textInput.trim()
      ? [...sampleTexts, textInput.trim()]
      : sampleTexts;
    if (allTexts.length > 0) {
      onSubmit(allTexts);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="text-input" className="block text-sm font-medium mb-2">
          Add Sample Text
        </label>
        <textarea
          id="text-input"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Paste a writing sample here (at least a few paragraphs)..."
          rows={8}
          className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        <div className="flex gap-2 mt-2">
          <button
            type="button"
            onClick={handleAddText}
            disabled={!textInput.trim()}
            className="px-4 py-2 text-sm border rounded-lg hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add to Samples
          </button>
          <label className="px-4 py-2 text-sm border rounded-lg hover:bg-accent cursor-pointer flex items-center gap-2">
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

      {/* Sample list */}
      {sampleTexts.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">
            Sample Texts ({sampleTexts.length})
          </h4>
          <div className="space-y-2">
            {sampleTexts.map((text, idx) => (
              <div
                key={idx}
                className="border rounded-lg p-3 bg-card flex items-start justify-between gap-2"
              >
                <div className="flex items-start gap-2 flex-1">
                  <FileText className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" aria-hidden="true" />
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {text.substring(0, 150)}...
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveText(idx)}
                  aria-label={`Remove sample ${idx + 1}`}
                  className="text-xs text-destructive hover:underline shrink-0"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Submit button */}
      <div className="flex justify-end pt-4 border-t">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={sampleTexts.length === 0 && !textInput.trim() || isSubmitting}
          className="px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Processing..." : "Analyze Samples"}
        </button>
      </div>
    </div>
  );
}
