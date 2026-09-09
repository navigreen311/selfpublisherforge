"use client";

import { useState } from "react";
import { CheckCircle2, AlertCircle } from "lucide-react";
import type { ConformityCheckResult } from "../types";

interface ConformityCheckerProps {
  onCheck: (text: string) => Promise<ConformityCheckResult>;
  isChecking?: boolean;
}

export function ConformityChecker({ onCheck, isChecking = false }: ConformityCheckerProps) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<ConformityCheckResult | null>(null);

  const handleCheck = async () => {
    if (!text.trim()) return;
    const conformityResult = await onCheck(text);
    setResult(conformityResult);
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
    <div className="border rounded-lg bg-card p-6">
      <h3 className="text-lg font-semibold mb-4">Conformity Checker</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Check how well a text matches this style profile&apos;s voice.
      </p>

      <div className="space-y-4">
        <div>
          <label htmlFor="conformity-text" className="block text-sm font-medium mb-2">
            Text to Check
          </label>
          <textarea
            id="conformity-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste text to check against this style profile..."
            rows={6}
            className="w-full border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        <button
          onClick={handleCheck}
          disabled={!text.trim() || isChecking}
          className="px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isChecking ? "Checking..." : "Check Conformity"}
        </button>

        {/* Results */}
        {result && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <h4 className="text-sm font-medium mb-1">Overall Match Score</h4>
                <div className="flex items-baseline gap-2">
                  <span className={`text-3xl font-bold ${getScoreColor(result.overall_score)}`}>
                    {Math.round(result.overall_score)}%
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {getScoreLabel(result.overall_score)}
                  </span>
                </div>
              </div>
              {result.overall_score >= 70 ? (
                <CheckCircle2 className="h-8 w-8 text-green-600" aria-hidden="true" />
              ) : (
                <AlertCircle className="h-8 w-8 text-yellow-600" aria-hidden="true" />
              )}
            </div>

            {/* Detailed scores */}
            <div className="border rounded-lg p-4 bg-muted/30">
              <h5 className="text-sm font-medium mb-3">Detailed Breakdown</h5>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Vocabulary</div>
                  <div className={`text-lg font-semibold ${getScoreColor(result.vocabulary_score)}`}>
                    {Math.round(result.vocabulary_score)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Sentence</div>
                  <div className={`text-lg font-semibold ${getScoreColor(result.sentence_score)}`}>
                    {Math.round(result.sentence_score)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Paragraph</div>
                  <div className={`text-lg font-semibold ${getScoreColor(result.paragraph_score)}`}>
                    {Math.round(result.paragraph_score)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Rhetorical</div>
                  <div className={`text-lg font-semibold ${getScoreColor(result.rhetorical_score)}`}>
                    {Math.round(result.rhetorical_score)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Dialogue</div>
                  <div className={`text-lg font-semibold ${getScoreColor(result.dialogue_score)}`}>
                    {Math.round(result.dialogue_score)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Feedback */}
            {result.feedback && result.feedback.length > 0 && (
              <div className="border rounded-lg p-4">
                <h5 className="text-sm font-medium mb-2">Suggestions for Improvement</h5>
                <ul className="space-y-1">
                  {result.feedback.map((item, idx) => (
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
    </div>
  );
}
