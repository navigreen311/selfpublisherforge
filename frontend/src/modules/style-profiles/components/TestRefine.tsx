"use client";

import { useState } from "react";
import { RotateCw, SlidersHorizontal, Sparkles, CheckCircle2, AlertCircle } from "lucide-react";
import { useGenerateSample, useConformityCheck } from "../hooks";
import type { ConformityCheckResult } from "../types";

interface TestRefineProps {
  profileId: string;
}

type LengthOption = "short" | "medium" | "long";

const LENGTH_WORDS: Record<LengthOption, number> = {
  short: 100,
  medium: 300,
  long: 600,
};

const LENGTH_LABELS: Record<LengthOption, string> = {
  short: "Short (100 words)",
  medium: "Medium (300 words)",
  long: "Long (600 words)",
};

export function TestRefine({ profileId }: TestRefineProps) {
  const [topic, setTopic] = useState("");
  const [length, setLength] = useState<LengthOption>("medium");
  const [generatedText, setGeneratedText] = useState("");
  const [conformityResult, setConformityResult] = useState<ConformityCheckResult | null>(null);

  // Fine-tune sliders
  const [formality, setFormality] = useState(50);
  const [warmth, setWarmth] = useState(50);
  const [sentenceLength, setSentenceLength] = useState(50);
  const [complexity, setComplexity] = useState(50);

  const generateSample = useGenerateSample(profileId);
  const conformityCheck = useConformityCheck(profileId);

  const isGenerating = generateSample.isPending;
  const isChecking = conformityCheck.isPending;

  const handleGenerate = () => {
    if (!topic.trim()) return;

    setConformityResult(null);
    generateSample.mutate(
      { prompt: topic, max_words: LENGTH_WORDS[length] },
      {
        onSuccess: (response) => {
          setGeneratedText(response.generated_text);
          // Auto-run conformity check on the generated text
          conformityCheck.mutate(
            { text: response.generated_text },
            {
              onSuccess: (result) => {
                setConformityResult(result);
              },
            }
          );
        },
      }
    );
  };

  const handleRegenerate = () => {
    handleGenerate();
  };

  const handleApplyAdjustments = () => {
    console.log("Fine-tune adjustments:", {
      formality,
      warmth,
      sentenceLength,
      complexity,
    });
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return "Excellent Match";
    if (score >= 60) return "Good Match";
    if (score >= 40) return "Fair Match";
    return "Poor Match";
  };

  return (
    <div className="space-y-6">
      {/* Topic Input */}
      <div className="border rounded-lg bg-card p-6">
        <h3 className="text-lg font-semibold mb-2">Test Your Style Profile</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Give AI a topic and see how it writes in this style
        </p>

        <div className="space-y-4">
          <div>
            <label htmlFor="test-topic" className="block text-sm font-medium mb-2">
              Topic
            </label>
            <textarea
              id="test-topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. A rainy evening in a small coastal town..."
              rows={3}
              className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {/* Length Toggle */}
          <div>
            <span className="block text-sm font-medium mb-2">Length</span>
            <div className="flex gap-4">
              {(Object.keys(LENGTH_LABELS) as LengthOption[]).map((option) => (
                <label key={option} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="length"
                    value={option}
                    checked={length === option}
                    onChange={() => setLength(option)}
                    className="accent-primary"
                  />
                  <span className="text-sm">{LENGTH_LABELS[option]}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!topic.trim() || isGenerating}
            className="inline-flex items-center gap-2 px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            {isGenerating ? "Generating..." : "Generate"}
          </button>
        </div>
      </div>

      {/* Generated Text Output */}
      {generatedText && (
        <div className="border rounded-lg bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Generated Text</h3>
            {conformityResult && (
              <div className="flex items-center gap-2">
                {conformityResult.overall_score >= 70 ? (
                  <CheckCircle2 className="h-5 w-5 text-green-600" aria-hidden="true" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-yellow-600" aria-hidden="true" />
                )}
                <span className="text-sm font-medium">Style Match:</span>
                <span className={`text-lg font-bold ${getScoreColor(conformityResult.overall_score)}`}>
                  {Math.round(conformityResult.overall_score)}%
                </span>
                <span className="text-xs text-muted-foreground">
                  {getScoreLabel(conformityResult.overall_score)}
                </span>
              </div>
            )}
            {isChecking && (
              <span className="text-sm text-muted-foreground">Scoring...</span>
            )}
          </div>

          <div className="border rounded-lg p-4 bg-muted/30 text-sm leading-relaxed whitespace-pre-wrap mb-4">
            {generatedText}
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleRegenerate}
              disabled={isGenerating}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border hover:bg-muted/50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RotateCw className="h-4 w-4" aria-hidden="true" />
              Regenerate
            </button>
            <button
              onClick={() => {
                const section = document.getElementById("fine-tune-section");
                section?.scrollIntoView({ behavior: "smooth" });
              }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border hover:bg-muted/50"
            >
              <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
              Adjust Profile
            </button>
          </div>
        </div>
      )}

      {/* Fine-Tune Section */}
      <div id="fine-tune-section" className="border rounded-lg bg-card p-6">
        <h3 className="text-lg font-semibold mb-2">Fine-Tune Style</h3>
        <p className="text-sm text-muted-foreground mb-6">
          Adjust style parameters to refine the generated output.
        </p>

        <div className="space-y-5">
          {/* Formality Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="slider-formality" className="text-sm font-medium">
                Formality
              </label>
              <span className="text-sm text-muted-foreground">{formality}</span>
            </div>
            <input
              id="slider-formality"
              type="range"
              min={0}
              max={100}
              value={formality}
              onChange={(e) => setFormality(Number(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Casual</span>
              <span>Formal</span>
            </div>
          </div>

          {/* Warmth Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="slider-warmth" className="text-sm font-medium">
                Warmth
              </label>
              <span className="text-sm text-muted-foreground">{warmth}</span>
            </div>
            <input
              id="slider-warmth"
              type="range"
              min={0}
              max={100}
              value={warmth}
              onChange={(e) => setWarmth(Number(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Detached</span>
              <span>Warm</span>
            </div>
          </div>

          {/* Sentence Length Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="slider-sentence-length" className="text-sm font-medium">
                Sentence Length
              </label>
              <span className="text-sm text-muted-foreground">{sentenceLength}</span>
            </div>
            <input
              id="slider-sentence-length"
              type="range"
              min={0}
              max={100}
              value={sentenceLength}
              onChange={(e) => setSentenceLength(Number(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Short</span>
              <span>Long</span>
            </div>
          </div>

          {/* Complexity Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="slider-complexity" className="text-sm font-medium">
                Complexity
              </label>
              <span className="text-sm text-muted-foreground">{complexity}</span>
            </div>
            <input
              id="slider-complexity"
              type="range"
              min={0}
              max={100}
              value={complexity}
              onChange={(e) => setComplexity(Number(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Simple</span>
              <span>Complex</span>
            </div>
          </div>
        </div>

        <button
          onClick={handleApplyAdjustments}
          className="mt-6 inline-flex items-center gap-2 px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
          Apply Adjustments
        </button>
      </div>
    </div>
  );
}
