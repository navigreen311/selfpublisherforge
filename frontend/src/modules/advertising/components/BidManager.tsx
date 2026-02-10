"use client";

import { useState } from "react";
import { useKeywordBids, useUpdateKeywordBids } from "../hooks";
import type { KeywordBid } from "../hooks";
import { toast } from "sonner";

interface BidManagerProps {
  campaignId: string;
}

export function BidManager({ campaignId }: BidManagerProps) {
  const { data: bids, isLoading } = useKeywordBids(campaignId);
  const updateBids = useUpdateKeywordBids();
  const [editingBids, setEditingBids] = useState<Record<string, number>>({});

  const handleBidChange = (bidId: string, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0) {
      setEditingBids((prev) => ({ ...prev, [bidId]: numValue }));
    }
  };

  const handleSave = async () => {
    const updates = Object.entries(editingBids).map(([id, bid_amount]) => ({
      id,
      bid_amount,
    }));

    if (updates.length === 0) {
      toast.info("No changes to save");
      return;
    }

    try {
      await updateBids.mutateAsync(updates);
      setEditingBids({});
      toast.success(`Updated ${updates.length} keyword bid(s)`);
    } catch {
      toast.error("Failed to update bids");
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 bg-muted rounded" />
        ))}
      </div>
    );
  }

  const activeBids = (bids || []).filter((b) => !b.is_negative);
  const negativeBids = (bids || []).filter((b) => b.is_negative);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Keyword Bids</h3>
        {Object.keys(editingBids).length > 0 && (
          <button
            onClick={handleSave}
            disabled={updateBids.isPending}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:opacity-90 disabled:opacity-50"
          >
            {updateBids.isPending ? "Saving..." : `Save ${Object.keys(editingBids).length} change(s)`}
          </button>
        )}
      </div>

      {/* Active Keywords */}
      <div>
        <h4 className="text-sm font-medium text-muted-foreground mb-2">
          Active Keywords ({activeBids.length})
        </h4>
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Keyword</th>
                <th className="text-left px-4 py-2 font-medium">Match</th>
                <th className="text-right px-4 py-2 font-medium">Bid ($)</th>
                <th className="text-right px-4 py-2 font-medium">Impr.</th>
                <th className="text-right px-4 py-2 font-medium">Clicks</th>
                <th className="text-right px-4 py-2 font-medium">Spend</th>
                <th className="text-right px-4 py-2 font-medium">Sales</th>
                <th className="text-right px-4 py-2 font-medium">ACOS</th>
              </tr>
            </thead>
            <tbody>
              {activeBids.map((bid) => (
                <BidRow
                  key={bid.id}
                  bid={bid}
                  editValue={editingBids[bid.id]}
                  onChange={(val) => handleBidChange(bid.id, val)}
                />
              ))}
              {activeBids.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-muted-foreground">
                    No active keywords
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Negative Keywords */}
      {negativeBids.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">
            Negative Keywords ({negativeBids.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {negativeBids.map((bid) => (
              <span
                key={bid.id}
                className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm"
              >
                {bid.keyword}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BidRow({
  bid,
  editValue,
  onChange,
}: {
  bid: KeywordBid;
  editValue?: number;
  onChange: (value: string) => void;
}) {
  const acosClass =
    bid.acos > 50
      ? "text-red-600"
      : bid.acos > 30
      ? "text-yellow-600"
      : "text-green-600";

  return (
    <tr className="border-t hover:bg-muted/30">
      <td className="px-4 py-2 font-medium">{bid.keyword}</td>
      <td className="px-4 py-2">
        <span className="px-2 py-0.5 bg-muted rounded text-xs">
          {bid.match_type}
        </span>
      </td>
      <td className="px-4 py-2 text-right">
        <input
          type="number"
          step="0.01"
          min="0.01"
          className="w-20 text-right border rounded px-2 py-1 text-sm"
          value={editValue !== undefined ? editValue : bid.bid_amount}
          onChange={(e) => onChange(e.target.value)}
        />
      </td>
      <td className="px-4 py-2 text-right">{bid.impressions.toLocaleString()}</td>
      <td className="px-4 py-2 text-right">{bid.clicks.toLocaleString()}</td>
      <td className="px-4 py-2 text-right">${bid.spend.toFixed(2)}</td>
      <td className="px-4 py-2 text-right">${bid.sales.toFixed(2)}</td>
      <td className={`px-4 py-2 text-right font-medium ${acosClass}`}>
        {bid.acos.toFixed(1)}%
      </td>
    </tr>
  );
}
