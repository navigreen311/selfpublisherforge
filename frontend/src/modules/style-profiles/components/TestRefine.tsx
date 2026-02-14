"use client";

import { useState } from "react";
import { Sparkles, CheckCircle2, AlertCircle } from "lucide-react";
import type { ConformityCheckResult } from "../types";

interface TestRefineProps {
  onCheck: (text: string) => Promise<ConformityCheckResult>;
  onGenerate: (prompt: string, maxWords?: number) => Promise<{ generated_text: string }>;
  isChecking?: boolean;
  isGenerating?: boolean;
  profileReady?: boolean;
}

function getScoreColor(score: number) {
  if (score >= 80) return "text-green-600";
  if (score >= 60) return "text-yellow-600";
  return "text-red-600";
}

function getScoreLabel(score: number) {
  if (score >= 80) return "Excellent Match";
  if (score >= 60) return "Good Match";
  if (score >= 40) return "Fair Match";
  return "Poor Match";
}

export function TestRefine({
  onCheck,
  onGenerate,
  isChecking = false,
  isGenerating = false,
  profileReady = false,
}: TestRefineProps) {
  const [checkText, setCheckText] = useState("");
  const [checkResult, setCheckResult] = useState<ConformityCheckResult | null>(null);
  const [generatePrompt, setGeneratePrompt] = useState("");
  const [generatedText, setGeneratedText] = useState("");

  const handleCheck = async () => {
    if (!checkText.trim()) return;
    const result = await onCheck(checkText);
    setCheckResult(result);
  };

  const handleGenerate = async () => {
    if (!generatePrompt.trim()) return;
    const result = await onGenerate(generatePrompt, 300);
    setGeneratedText(result.generated_text);
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Test & Refine</h3>

      {/* Conformity Checker */}
      <div className="border rounded-lg bg-card p-6 space-y-4">
        <div>
          <h4 className="text-sm font-semibold mb-1">Conformity Checker</h4>
          <p className="text-sm text-muted-foreground">
            Check how well a text matches this style profile.
          </p>
        </div>

        <div>
          <label htmlFor="conformity-text" className="block text-sm font-medium mb-2">
            Text to Check
          </label>
          <textarea
            id="conformity-text"
            value={checkText}
            onChange={(e) => setCheckText(e.target.value)}
            placeholder="Paste text to check against this style profile..."
            rows={6}
            className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        <button
          onClick={handleCheck}
          disabled={!checkText.trim() || isChecking || !profileReady}
          className="px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isChecking ? "Checking..." : "Check Conformity"}
        </button>

        {!profileReady && (
          <p className="text-xs text-muted-foreground">
            Profile must be in &ldquo;ready&rdquo; status to run conformity checks.
          </p>
        )}

        {/* Results */}
        {checkResult && (
          <div className="space-y-4 pt-2">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <h5 className="text-sm font-medium mb-1">Overall Match Score</h5>
                <div className="flex items-baseline gap-2">
                  <span className={`text-3xl font-bold ${getScoreColor(checkResult.overall_score)}`}>
                    {Math.round(checkResult.overall_score)}%
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {getScoreLabel(checkResult.overall_score)}
                  </span>
                </div>
              </div>
              {checkResult.overall_score >= 70 ? (
                <CheckCircle2 className="h-8 w-8 text-green-600" aria-hidden="true" />
              ) : (
                <AlertCircle className="h-8 w-8 text-yellow-600" aria-hidden="true" />
              )}
            </div>

            <div className="border rounded-lg p-4 bg-muted/30">
              <h5 className="text-sm font-medium mb-3">Detailed Breakdown</h5>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[
                  { label: "Vocabulary", value: checkResult.vocabulary_score },
                  { label: "Sentence", value: checkResult.sentence_score },
                  { label: "Paragraph", value: checkResult.paragraph_score },
                  { label: "Rhetorical", value: checkResult.rhetorical_score },
                  { label: "Dialogue", value: checkResult.dialogue_score },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="text-xs text-muted-foreground mb-1">{item.label}</div>
                    <div className={`text-lg font-semibold ${getScoreColor(item.value)}`}>
                      {Math.round(item.value)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {checkResult.feedback && checkResult.feedback.length > 0 && (
              <div className="border rounded-lg p-4">
                <h5 className="text-sm font-medium mb-2">Suggestions for Improvement</h5>
                <ul className="space-y-1">
                  {checkResult.feedback.map((item, idx) => (
                    <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-primary mt-0.5">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Generate Sample */}
      <div className="border rounded-lg bg-card p-6 space-y-4">
        <div>
          <h4 className="text-sm font-semibold mb-1">Generate Sample Text</h4>
          <p className="text-sm text-muted-foreground">
            Generate text that matches this style profile.
          </p>
        </div>

        <div>
          <label htmlFor="generate-prompt" className="block text-sm font-medium mb-2">
            Prompt
          </label>
          <input
            id="generate-prompt"
            type="text"
            value={generatePrompt}
            onChange={(e) => setGeneratePrompt(e.target.value)}
            placeholder="Describe what you want generated in this style..."
            className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={!generatePrompt.trim() || isGenerating || !profileReady}
          className="flex items-center gap-2 px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          {isGenerating ? "Generating..." : "Generate"}
        </button>

        {!profileReady && (
          <p className="text-xs text-muted-foreground">
            Profile must be in &ldquo;ready&rdquo; status to generate samples.
          </p>
        )}

        {generatedText && (
          <div className="border rounded-lg p-4 bg-muted/30">
            <h5 className="text-sm font-medium mb-2">Generated Text</h5>
            <p className="text-sm whitespace-pre-wrap">{generatedText}</p>
          </div>
        )}
      </div>
    </div>
  );
}
