"use client";

import { useCallback, useState } from "react";
import { cn } from "@/lib/utils";
import { useSSEGeneration, type GenerateRequest } from "../hooks";

interface AIPanelProps {
  bookId: string;
  projectId: string;
  selectedText?: string;
  onInsertText?: (text: string) => void;
  onReplaceSelection?: (text: string) => void;
  className?: string;
}

type ActionType =
  | "continue_writing"
  | "edit_selection"
  | "tone_adjustment"
  | "blurb"
  | "title_suggestions"
  | "chapter";

const TONE_OPTIONS = [
  "professional",
  "casual",
  "dramatic",
  "humorous",
  "dark",
  "literary",
  "conversational",
  "poetic",
];

/**
 * AI assistant panel for the writing studio.
 *
 * Provides controls for generating, continuing, editing selections,
 * and adjusting tone of manuscript text. Displays streamed AI output
 * in real time.
 */
export function AIPanel({
  bookId,
  projectId,
  selectedText,
  onInsertText,
  onReplaceSelection,
  className,
}: AIPanelProps) {
  const [instructions, setInstructions] = useState("");
  const [selectedTone, setSelectedTone] = useState("professional");
  const [activeAction, setActiveAction] = useState<ActionType | null>(null);

  const {
    content: generatedContent,
    isStreaming,
    error,
    qualityResults,
    startGeneration,
    stopGeneration,
  } = useSSEGeneration();

  const handleGenerate = useCallback(
    (actionType: ActionType) => {
      setActiveAction(actionType);
      const request: GenerateRequest = {
        generation_type: actionType,
        project_id: projectId,
        instructions: instructions || `Generate ${actionType.replace("_", " ")}`,
        context: {
          selected_text: selectedText || "",
          target_tone: selectedTone,
          genre: "",
        },
        model_preference: "auto",
        stream: true,
        quality_checks: ["readability", "word_count"],
      };
      startGeneration(request);
    },
    [instructions, projectId, selectedText, selectedTone, startGeneration]
  );

  const handleInsert = useCallback(() => {
    if (generatedContent) {
      onInsertText?.(generatedContent);
    }
  }, [generatedContent, onInsertText]);

  const handleReplace = useCallback(() => {
    if (generatedContent) {
      onReplaceSelection?.(generatedContent);
    }
  }, [generatedContent, onReplaceSelection]);

  return (
    <div
      className={cn(
        "flex flex-col h-full border-l bg-card w-80",
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b">
        <h3 className="text-sm font-semibold text-foreground">AI Assistant</h3>
        <p className="text-xs text-muted-foreground mt-0.5">
          Generate, continue, or edit your manuscript with AI
        </p>
      </div>

      {/* Instructions input */}
      <div className="px-4 py-3 border-b space-y-2">
        <label className="text-xs font-medium text-foreground">
          Instructions
        </label>
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="Describe what you want the AI to write or how to edit..."
          className="w-full h-20 text-sm rounded-md border p-2 resize-none bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        />

        {/* Tone selector */}
        <div>
          <label className="text-xs font-medium text-foreground">Tone</label>
          <select
            value={selectedTone}
            onChange={(e) => setSelectedTone(e.target.value)}
            className="w-full mt-1 text-sm rounded-md border p-1.5 bg-background text-foreground"
          >
            {TONE_OPTIONS.map((tone) => (
              <option key={tone} value={tone}>
                {tone.charAt(0).toUpperCase() + tone.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Action buttons */}
      <div className="px-4 py-3 border-b space-y-2">
        <p className="text-xs font-medium text-foreground mb-1">Actions</p>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleGenerate("continue_writing")}
            disabled={isStreaming}
            className="text-xs px-2 py-1.5 rounded border hover:bg-accent transition-colors disabled:opacity-50"
          >
            Continue Writing
          </button>
          <button
            onClick={() => handleGenerate("chapter")}
            disabled={isStreaming}
            className="text-xs px-2 py-1.5 rounded border hover:bg-accent transition-colors disabled:opacity-50"
          >
            Generate Chapter
          </button>
          <button
            onClick={() => handleGenerate("edit_selection")}
            disabled={isStreaming || !selectedText}
            className="text-xs px-2 py-1.5 rounded border hover:bg-accent transition-colors disabled:opacity-50"
          >
            Edit Selection
          </button>
          <button
            onClick={() => handleGenerate("tone_adjustment")}
            disabled={isStreaming || !selectedText}
            className="text-xs px-2 py-1.5 rounded border hover:bg-accent transition-colors disabled:opacity-50"
          >
            Adjust Tone
          </button>
          <button
            onClick={() => handleGenerate("blurb")}
            disabled={isStreaming}
            className="text-xs px-2 py-1.5 rounded border hover:bg-accent transition-colors disabled:opacity-50"
          >
            Write Blurb
          </button>
          <button
            onClick={() => handleGenerate("title_suggestions")}
            disabled={isStreaming}
            className="text-xs px-2 py-1.5 rounded border hover:bg-accent transition-colors disabled:opacity-50"
          >
            Suggest Titles
          </button>
        </div>

        {isStreaming && (
          <button
            onClick={stopGeneration}
            className="w-full text-xs px-2 py-1.5 rounded bg-red-500 text-white hover:bg-red-600 transition-colors"
          >
            Stop Generation
          </button>
        )}
      </div>

      {/* Selected text indicator */}
      {selectedText && (
        <div className="px-4 py-2 border-b bg-blue-50">
          <p className="text-xs text-blue-600 font-medium">Selected Text:</p>
          <p className="text-xs text-blue-800 truncate mt-0.5">
            {selectedText.length > 100
              ? selectedText.slice(0, 100) + "..."
              : selectedText}
          </p>
        </div>
      )}

      {/* Output area */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3 mb-3">
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}

        {(generatedContent || isStreaming) && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-medium text-foreground">
                {isStreaming ? "Generating..." : "Generated Content"}
              </p>
              {isStreaming && (
                <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              )}
            </div>
            <div className="rounded-md border bg-muted/30 p-3 text-sm whitespace-pre-wrap font-serif max-h-64 overflow-y-auto">
              {generatedContent || (
                <span className="text-muted-foreground">Waiting for AI...</span>
              )}
            </div>

            {/* Insert / replace buttons */}
            {!isStreaming && generatedContent && (
              <div className="flex gap-2 mt-2">
                <button
                  onClick={handleInsert}
                  className="flex-1 text-xs px-2 py-1.5 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  Insert at Cursor
                </button>
                {selectedText && (
                  <button
                    onClick={handleReplace}
                    className="flex-1 text-xs px-2 py-1.5 rounded bg-blue-500 text-white hover:bg-blue-600 transition-colors"
                  >
                    Replace Selection
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Quality results */}
        {qualityResults && !isStreaming && (
          <div className="mt-3 rounded-md border p-3">
            <p className="text-xs font-medium text-foreground mb-1">
              Quality Check
            </p>
            {Object.entries(qualityResults).map(([key, value]) => (
              <div key={key} className="text-xs text-muted-foreground">
                <span className="font-medium capitalize">
                  {key.replace("_", " ")}:
                </span>{" "}
                {typeof value === "object" ? JSON.stringify(value) : String(value)}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default AIPanel;
