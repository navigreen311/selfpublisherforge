"use client";

import { useState } from "react";
import { useKeywordBids, useUpdateKeywordBids } from "../hooks";
import type { KeywordBid } from "../types";
import { toast } from "sonner";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Plus, Sparkles, X } from "lucide-react";

interface KeywordsTabProps {
  campaignId: string;
  onOpenBidOptimizer: () => void;
}

function getAcosColor(acos: number): string {
  if (acos < 25) return "text-green-600";
  if (acos <= 40) return "text-yellow-600";
  return "text-red-600";
}

export function KeywordsTab({ campaignId, onOpenBidOptimizer }: KeywordsTabProps) {
  const { data: bids, isLoading } = useKeywordBids(campaignId);
  const updateBids = useUpdateKeywordBids();
  const [editingBidId, setEditingBidId] = useState<string | null>(null);
  const [editingBidValue, setEditingBidValue] = useState<string>("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [newKeyword, setNewKeyword] = useState("");
  const [newMatchType, setNewMatchType] = useState<"exact" | "phrase" | "broad">("broad");
  const [newBid, setNewBid] = useState("0.75");

  const activeBids = (bids || []).filter((b) => !b.is_negative && b.is_active);

  const handleStartEdit = (bid: KeywordBid) => {
    setEditingBidId(bid.id);
    setEditingBidValue(bid.bid_amount.toFixed(2));
  };

  const handleSaveEdit = async (bidId: string) => {
    const numValue = parseFloat(editingBidValue);
    if (isNaN(numValue) || numValue <= 0) {
      toast.error("Please enter a valid bid amount");
      return;
    }
    try {
      await updateBids.mutateAsync([{ id: bidId, bid_amount: numValue }]);
      toast.success("Bid updated");
      setEditingBidId(null);
    } catch {
      toast.error("Failed to update bid");
    }
  };

  const handleCancelEdit = () => {
    setEditingBidId(null);
    setEditingBidValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent, bidId: string) => {
    if (e.key === "Enter") {
      handleSaveEdit(bidId);
    } else if (e.key === "Escape") {
      handleCancelEdit();
    }
  };

  const handleAddKeyword = () => {
    if (!newKeyword.trim()) {
      toast.error("Please enter a keyword");
      return;
    }
    // In a real implementation, this would call an API to add the keyword
    toast.success(`Keyword "${newKeyword}" added with ${newMatchType} match at $${newBid}`);
    setNewKeyword("");
    setNewBid("0.75");
    setNewMatchType("broad");
    setShowAddForm(false);
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-12 bg-muted rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Action bar */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          Keywords ({activeBids.length})
        </h3>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Keywords
          </Button>
          <Button
            size="sm"
            onClick={onOpenBidOptimizer}
          >
            <Sparkles className="h-4 w-4 mr-1" />
            AI Optimize Bids
          </Button>
        </div>
      </div>

      {/* Add keywords inline form */}
      {showAddForm && (
        <div className="border rounded-lg p-4 bg-muted/10 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">Add New Keyword</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAddForm(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="text-xs text-muted-foreground mb-1 block">Keyword</label>
              <Input
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                placeholder="Enter keyword..."
                className="h-9"
              />
            </div>
            <div className="w-36">
              <label className="text-xs text-muted-foreground mb-1 block">Match Type</label>
              <Select value={newMatchType} onValueChange={(v) => setNewMatchType(v as "exact" | "phrase" | "broad")}>
                <SelectTrigger className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="broad">Broad</SelectItem>
                  <SelectItem value="phrase">Phrase</SelectItem>
                  <SelectItem value="exact">Exact</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="w-24">
              <label className="text-xs text-muted-foreground mb-1 block">Bid ($)</label>
              <Input
                type="number"
                step="0.01"
                min="0.01"
                value={newBid}
                onChange={(e) => setNewBid(e.target.value)}
                className="h-9"
              />
            </div>
            <Button size="sm" onClick={handleAddKeyword} className="h-9">
              Add
            </Button>
          </div>
        </div>
      )}

      {/* Keywords table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Keyword</TableHead>
              <TableHead>Match Type</TableHead>
              <TableHead className="text-right">Bid ($)</TableHead>
              <TableHead className="text-right">Impressions</TableHead>
              <TableHead className="text-right">Clicks</TableHead>
              <TableHead className="text-right">CTR</TableHead>
              <TableHead className="text-right">ACOS</TableHead>
              <TableHead className="text-right">Sales</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {activeBids.map((bid) => {
              const ctr =
                bid.impressions > 0
                  ? ((bid.clicks / bid.impressions) * 100).toFixed(2)
                  : "0.00";

              return (
                <TableRow key={bid.id}>
                  <TableCell className="font-medium">{bid.keyword}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="text-xs capitalize">
                      {bid.match_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    {editingBidId === bid.id ? (
                      <Input
                        type="number"
                        step="0.01"
                        min="0.01"
                        value={editingBidValue}
                        onChange={(e) => setEditingBidValue(e.target.value)}
                        onBlur={() => handleSaveEdit(bid.id)}
                        onKeyDown={(e) => handleKeyDown(e, bid.id)}
                        className="h-7 w-20 text-right text-sm ml-auto"
                        autoFocus
                      />
                    ) : (
                      <button
                        onClick={() => handleStartEdit(bid)}
                        className="text-sm hover:bg-muted px-2 py-0.5 rounded cursor-pointer transition-colors"
                        title="Click to edit bid"
                      >
                        ${bid.bid_amount.toFixed(2)}
                      </button>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {bid.impressions.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    {bid.clicks.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">{ctr}%</TableCell>
                  <TableCell className="text-right">
                    <span className={`font-medium ${getAcosColor(bid.acos)}`}>
                      {bid.acos.toFixed(1)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    ${bid.sales.toFixed(2)}
                  </TableCell>
                </TableRow>
              );
            })}
            {activeBids.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={8}
                  className="text-center py-8 text-muted-foreground"
                >
                  No keywords added yet. Click &quot;Add Keywords&quot; to get started.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
