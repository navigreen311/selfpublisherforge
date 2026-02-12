"use client";

import { useState, useMemo } from "react";
import {
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  DollarSign,
  Clock,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChapterCost {
  chapter_number: number;
  word_count: number;
  cost_usd: number;
}

interface Provider {
  name: string;
  rate: number;
  quality: string;
  tier: string;
}

export interface CostEstimatorProps {
  projectId: string;
  totalWordCount: number;
  chapters: ChapterCost[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WORDS_PER_MINUTE = 150;
const PROFESSIONAL_NARRATOR_LOW = 2000;
const PROFESSIONAL_NARRATOR_HIGH = 5000;

const PROVIDERS: Provider[] = [
  { name: "Coqui XTTS (Self-Hosted)", rate: 0.001, quality: "Good", tier: "$" },
  { name: "ElevenLabs (Premium)", rate: 0.03, quality: "Premium", tier: "$$$" },
  { name: "Piper (Fast Preview)", rate: 0.0001, quality: "Basic", tier: "\u00A2" },
];

const qualityColors: Record<string, string> = {
  Basic: "bg-gray-100 text-gray-800",
  Good: "bg-blue-100 text-blue-800",
  Premium: "bg-purple-100 text-purple-800",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCurrency(amount: number): string {
  return amount < 0.01 && amount > 0
    ? `$${amount.toFixed(4)}`
    : `$${amount.toFixed(2)}`;
}

function formatDuration(minutes: number): string {
  const hrs = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  if (hrs === 0) return `${mins}m`;
  return `${hrs}h ${mins}m`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CostEstimator({
  projectId,
  totalWordCount,
  chapters,
}: CostEstimatorProps) {
  const [budgetCap, setBudgetCap] = useState<string>("");
  const [chaptersExpanded, setChaptersExpanded] = useState(false);

  const estimatedMinutes = totalWordCount / WORDS_PER_MINUTE;

  const providerCosts = useMemo(
    () =>
      PROVIDERS.map((p) => ({
        ...p,
        totalCost: estimatedMinutes * p.rate,
      })),
    [estimatedMinutes]
  );

  const maxCost = Math.max(...providerCosts.map((p) => p.totalCost));
  const budgetValue = budgetCap ? parseFloat(budgetCap) : null;
  const isBudgetExceeded =
    budgetValue !== null &&
    !isNaN(budgetValue) &&
    providerCosts.some((p) => p.totalCost > budgetValue);

  return (
    <div className="space-y-6">
      {/* Overview cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="border rounded-lg p-4 bg-card space-y-1">
          <div className="flex items-center gap-2 text-muted-foreground">
            <BarChart3 className="h-4 w-4" />
            <span className="text-xs font-medium">Total Words</span>
          </div>
          <p className="text-2xl font-bold">{totalWordCount.toLocaleString()}</p>
        </div>

        <div className="border rounded-lg p-4 bg-card space-y-1">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span className="text-xs font-medium">Est. Duration</span>
          </div>
          <p className="text-2xl font-bold">{formatDuration(estimatedMinutes)}</p>
          <p className="text-xs text-muted-foreground">
            ~{WORDS_PER_MINUTE} words/min
          </p>
        </div>

        <div className="border rounded-lg p-4 bg-card space-y-1">
          <div className="flex items-center gap-2 text-muted-foreground">
            <DollarSign className="h-4 w-4" />
            <span className="text-xs font-medium">Chapters</span>
          </div>
          <p className="text-2xl font-bold">{chapters.length}</p>
        </div>
      </div>

      {/* Provider comparison table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="p-4 border-b bg-muted/30">
          <h3 className="font-semibold text-sm">Provider Cost Comparison</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/10">
                <th className="text-left p-3 font-medium">Provider</th>
                <th className="text-right p-3 font-medium">Cost/Min</th>
                <th className="text-right p-3 font-medium">Total Est.</th>
                <th className="text-center p-3 font-medium">Quality</th>
              </tr>
            </thead>
            <tbody>
              {providerCosts.map((provider) => {
                const overBudget =
                  budgetValue !== null &&
                  !isNaN(budgetValue) &&
                  provider.totalCost > budgetValue;

                return (
                  <tr
                    key={provider.name}
                    className={cn(
                      "border-b last:border-b-0",
                      overBudget && "bg-destructive/5"
                    )}
                  >
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <span>{provider.name}</span>
                        <Badge variant="outline" className="text-[10px] px-1.5">
                          {provider.tier}
                        </Badge>
                      </div>
                    </td>
                    <td className="p-3 text-right font-mono text-xs">
                      {formatCurrency(provider.rate)}
                    </td>
                    <td className="p-3 text-right font-mono font-semibold">
                      <span className={cn(overBudget && "text-destructive")}>
                        {formatCurrency(provider.totalCost)}
                      </span>
                      {overBudget && (
                        <AlertTriangle className="inline h-3.5 w-3.5 ml-1 text-destructive" />
                      )}
                    </td>
                    <td className="p-3 text-center">
                      <span
                        className={cn(
                          "text-[10px] px-2 py-0.5 rounded-full font-medium",
                          qualityColors[provider.quality] ?? "bg-gray-100 text-gray-800"
                        )}
                      >
                        {provider.quality}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cost bar chart */}
      <div className="border rounded-lg p-4 space-y-3">
        <h3 className="font-semibold text-sm">Visual Comparison</h3>
        <div className="space-y-2">
          {providerCosts.map((provider) => {
            const pct = maxCost > 0 ? (provider.totalCost / maxCost) * 100 : 0;
            return (
              <div key={provider.name} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="truncate">{provider.name}</span>
                  <span className="font-mono font-medium">
                    {formatCurrency(provider.totalCost)}
                  </span>
                </div>
                <div className="h-3 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all"
                    style={{ width: `${Math.max(pct, 1)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Per-chapter breakdown */}
      <div className="border rounded-lg overflow-hidden">
        <button
          onClick={() => setChaptersExpanded((prev) => !prev)}
          className="w-full flex items-center justify-between p-4 bg-muted/30 hover:bg-muted/50 transition-colors"
        >
          <h3 className="font-semibold text-sm">Per-Chapter Breakdown</h3>
          {chaptersExpanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
        {chaptersExpanded && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/10">
                  <th className="text-left p-3 font-medium">Chapter</th>
                  <th className="text-right p-3 font-medium">Words</th>
                  <th className="text-right p-3 font-medium">Duration</th>
                  <th className="text-right p-3 font-medium">Cost (Est.)</th>
                </tr>
              </thead>
              <tbody>
                {chapters.map((ch) => {
                  const chMins = ch.word_count / WORDS_PER_MINUTE;
                  return (
                    <tr key={ch.chapter_number} className="border-b last:border-b-0">
                      <td className="p-3">Chapter {ch.chapter_number}</td>
                      <td className="p-3 text-right font-mono text-xs">
                        {ch.word_count.toLocaleString()}
                      </td>
                      <td className="p-3 text-right font-mono text-xs">
                        {formatDuration(chMins)}
                      </td>
                      <td className="p-3 text-right font-mono text-xs">
                        {formatCurrency(ch.cost_usd)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Budget cap */}
      <div className="border rounded-lg p-4 space-y-3">
        <h3 className="font-semibold text-sm">Budget Cap</h3>
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-xs">
            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="number"
              min="0"
              step="0.01"
              value={budgetCap}
              onChange={(e) => setBudgetCap(e.target.value)}
              placeholder="Set max budget"
              className="w-full border rounded-lg pl-9 pr-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              aria-label="Budget cap in USD"
            />
          </div>
          {isBudgetExceeded && (
            <div className="flex items-center gap-1.5 text-destructive text-sm">
              <AlertTriangle className="h-4 w-4" />
              <span>Budget exceeded by some providers</span>
            </div>
          )}
        </div>
      </div>

      {/* Comparison callout */}
      <div className="border rounded-lg p-4 bg-primary/5 space-y-2">
        <h3 className="font-semibold text-sm">Cost Comparison</h3>
        <p className="text-sm text-muted-foreground">
          AI narration:{" "}
          <span className="font-semibold text-foreground">
            {formatCurrency(providerCosts[0]?.totalCost ?? 0)}
            {" \u2013 "}
            {formatCurrency(providerCosts[1]?.totalCost ?? 0)}
          </span>
          {" vs "}
          Professional narrator:{" "}
          <span className="font-semibold text-foreground">
            ${PROFESSIONAL_NARRATOR_LOW.toLocaleString()} &ndash; $
            {PROFESSIONAL_NARRATOR_HIGH.toLocaleString()}+
          </span>
        </p>
        <p className="text-xs text-muted-foreground">
          Save up to{" "}
          <span className="font-semibold text-green-600">
            {Math.round(
              ((PROFESSIONAL_NARRATOR_LOW - (providerCosts[0]?.totalCost ?? 0)) /
                PROFESSIONAL_NARRATOR_LOW) *
                100
            )}
            %
          </span>{" "}
          with AI-powered narration.
        </p>
      </div>
    </div>
  );
}
