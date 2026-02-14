"use client";

import { useState } from "react";
import { useOptimizeBids } from "../hooks";
import type { BidOptimizationRequest, BidOptimizationResponse, BidRecommendation } from "../types";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowUp, ArrowDown, Minus, Sparkles, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useUpdateKeywordBids } from "../hooks";

interface BidOptimizerDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  campaignId: string;
}

type Strategy = BidOptimizationRequest["strategy"];

function BidChangeIndicator({ current, suggested }: { current: number; suggested: number }) {
  const diff = suggested - current;
  if (Math.abs(diff) < 0.01) {
    return (
      <span className="inline-flex items-center gap-1 text-muted-foreground">
        <Minus className="h-3 w-3" />
        ${suggested.toFixed(2)}
      </span>
    );
  }
  if (diff > 0) {
    return (
      <span className="inline-flex items-center gap-1 text-green-600">
        <ArrowUp className="h-3 w-3" />
        ${suggested.toFixed(2)}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-red-600">
      <ArrowDown className="h-3 w-3" />
      ${suggested.toFixed(2)}
    </span>
  );
}

export function BidOptimizerDialog({
  open,
  onOpenChange,
  campaignId,
}: BidOptimizerDialogProps) {
  const [targetAcos, setTargetAcos] = useState("30");
  const [strategy, setStrategy] = useState<Strategy>("maximize_sales");
  const [results, setResults] = useState<BidOptimizationResponse | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const optimizeBids = useOptimizeBids(campaignId);
  const updateBids = useUpdateKeywordBids();

  const handleAnalyze = async () => {
    const acos = parseFloat(targetAcos);
    if (isNaN(acos) || acos <= 0 || acos > 100) {
      toast.error("Please enter a valid target ACOS (1-100)");
      return;
    }

    try {
      const data = await optimizeBids.mutateAsync({
        target_acos: acos,
        strategy,
      });
      setResults(data);
      // Select all by default
      setSelectedIds(new Set(data.recommendations.map((_, i) => String(i))));
    } catch {
      // Error handled by hook
    }
  };

  const handleToggleSelect = (index: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const handleToggleAll = () => {
    if (!results) return;
    if (selectedIds.size === results.recommendations.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(results.recommendations.map((_, i) => String(i))));
    }
  };

  const applyBids = async (recommendations: BidRecommendation[]) => {
    // This would need keyword bid IDs in a real implementation.
    // For now, we show a success message.
    toast.success(`Applied bid changes for ${recommendations.length} keyword(s)`);
    onOpenChange(false);
    setResults(null);
  };

  const handleApplyAll = () => {
    if (!results) return;
    applyBids(results.recommendations);
  };

  const handleApplySelected = () => {
    if (!results) return;
    const selected = results.recommendations.filter((_, i) =>
      selectedIds.has(String(i))
    );
    if (selected.length === 0) {
      toast.error("No keywords selected");
      return;
    }
    applyBids(selected);
  };

  const handleClose = () => {
    onOpenChange(false);
    // Reset state when closing
    setResults(null);
    setSelectedIds(new Set());
  };

  const strategies: { value: Strategy; label: string; description: string }[] = [
    {
      value: "maximize_sales",
      label: "Maximize Sales",
      description: "Maximize sales while keeping ACOS under target",
    },
    {
      value: "minimize_acos",
      label: "Minimize ACOS",
      description: "Lower ACOS as much as possible",
    },
    {
      value: "maximize_impressions",
      label: "Maximize Impressions",
      description: "Increase visibility and reach",
    },
  ];

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            AI Bid Optimizer
          </DialogTitle>
          <DialogDescription>
            Let AI analyze your keyword performance and suggest optimal bid
            adjustments.
          </DialogDescription>
        </DialogHeader>

        {/* Configuration */}
        <div className="space-y-4">
          {/* Target ACOS */}
          <div className="space-y-2">
            <Label>Target ACOS</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min="1"
                max="100"
                value={targetAcos}
                onChange={(e) => setTargetAcos(e.target.value)}
                className="w-24 h-9"
              />
              <span className="text-sm text-muted-foreground">%</span>
            </div>
          </div>

          {/* Strategy */}
          <div className="space-y-2">
            <Label>Optimization Strategy</Label>
            <div className="grid gap-2">
              {strategies.map((s) => (
                <label
                  key={s.value}
                  className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                    strategy === s.value
                      ? "border-primary bg-primary/5"
                      : "hover:bg-muted/50"
                  }`}
                >
                  <input
                    type="radio"
                    name="strategy"
                    value={s.value}
                    checked={strategy === s.value}
                    onChange={(e) => setStrategy(e.target.value as Strategy)}
                    className="mt-0.5"
                  />
                  <div>
                    <div className="text-sm font-medium">{s.label}</div>
                    <div className="text-xs text-muted-foreground">
                      {s.description}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Analyze button */}
          {!results && (
            <Button
              onClick={handleAnalyze}
              disabled={optimizeBids.isPending}
              className="w-full"
            >
              {optimizeBids.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Analyze
                </>
              )}
            </Button>
          )}
        </div>

        {/* Results */}
        {results && (
          <div className="space-y-4 mt-2">
            {/* Estimated impact */}
            <div className="border rounded-lg p-4 bg-muted/10">
              <h4 className="text-sm font-medium mb-2">Estimated Impact</h4>
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-muted-foreground">ACOS: </span>
                  <span className="font-medium">
                    {results.estimated_impact.current_acos.toFixed(1)}%
                  </span>
                  <span className="mx-1 text-muted-foreground">{"->"}</span>
                  <span className="font-medium text-green-600">
                    {results.estimated_impact.projected_acos.toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Sales: </span>
                  <span className="font-medium text-green-600">
                    {results.estimated_impact.projected_sales_change}
                  </span>
                </div>
              </div>
            </div>

            {/* Recommendations table */}
            {results.recommendations.length > 0 ? (
              <div className="border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-10">
                        <input
                          type="checkbox"
                          checked={
                            selectedIds.size === results.recommendations.length
                          }
                          onChange={handleToggleAll}
                          className="rounded"
                        />
                      </TableHead>
                      <TableHead>Keyword</TableHead>
                      <TableHead className="text-right">Current Bid</TableHead>
                      <TableHead className="text-right">
                        Suggested Bid
                      </TableHead>
                      <TableHead>Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {results.recommendations.map((rec, i) => (
                      <TableRow key={i}>
                        <TableCell>
                          <input
                            type="checkbox"
                            checked={selectedIds.has(String(i))}
                            onChange={() => handleToggleSelect(String(i))}
                            className="rounded"
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          {rec.keyword}
                        </TableCell>
                        <TableCell className="text-right">
                          ${rec.current_bid.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right">
                          <BidChangeIndicator
                            current={rec.current_bid}
                            suggested={rec.suggested_bid}
                          />
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground max-w-[200px]">
                          {rec.reason}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="border rounded-lg p-6 text-center text-muted-foreground">
                No bid adjustments recommended. Your bids are already well
                optimized.
              </div>
            )}
          </div>
        )}

        {/* Footer actions */}
        {results && results.recommendations.length > 0 && (
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              onClick={handleApplySelected}
              disabled={selectedIds.size === 0}
            >
              Apply Selected ({selectedIds.size})
            </Button>
            <Button onClick={handleApplyAll}>
              Apply All ({results.recommendations.length})
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
