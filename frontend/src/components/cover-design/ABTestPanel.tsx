"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, BarChart3, Trophy, Share2, Plus } from "lucide-react";

interface ABTest {
  id: string;
  name: string;
  coverIds: string[];
  shareToken: string;
  status: "active" | "ended";
  votes: Record<string, number>;
  winnerCoverId?: string;
}

interface ABTestPanelProps {
  coverId?: string;
  coverIds?: string[];
}

export function ABTestPanel({ coverId, coverIds = [] }: ABTestPanelProps) {
  const [tests, setTests] = useState<ABTest[]>([]);
  const [creating, setCreating] = useState(false);

  const handleCreateTest = () => {
    if (coverIds.length < 2) return;
    const newTest: ABTest = {
      id: `test-${Date.now()}`,
      name: `A/B Test ${tests.length + 1}`,
      coverIds: coverIds.slice(0, 4),
      shareToken: Math.random().toString(36).substring(2, 10),
      status: "active",
      votes: {},
    };
    setTests([...tests, newTest]);
    setCreating(false);
  };

  const handleCopyLink = (token: string) => {
    const url = `${window.location.origin}/vote/${token}`;
    navigator.clipboard.writeText(url);
  };

  const totalVotes = (test: ABTest) =>
    Object.values(test.votes).reduce((sum, v) => sum + v, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">A/B Testing</h3>
          <p className="text-sm text-muted-foreground">
            Compare cover designs and collect feedback
          </p>
        </div>
        <Button onClick={() => setCreating(true)} disabled={coverIds.length < 2}>
          <Plus className="mr-2 h-4 w-4" />
          New Test
        </Button>
      </div>

      {creating && (
        <div className="rounded-lg border bg-card p-4 space-y-3">
          <p className="text-sm">
            Create a new A/B test with {coverIds.length} cover variations?
          </p>
          <div className="flex gap-2">
            <Button size="sm" onClick={handleCreateTest}>Create</Button>
            <Button size="sm" variant="outline" onClick={() => setCreating(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {tests.length === 0 && !creating ? (
        <div className="rounded-lg border bg-card p-8 text-center">
          <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
          <p className="text-sm text-muted-foreground">
            No A/B tests yet. Select multiple covers and create a test to gather feedback.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {tests.map((test) => (
            <div key={test.id} className="rounded-lg border bg-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{test.name}</span>
                  <Badge variant={test.status === "active" ? "default" : "secondary"}>
                    {test.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopyLink(test.shareToken)}
                  >
                    <Share2 className="h-4 w-4 mr-1" />
                    Share
                  </Button>
                </div>
              </div>

              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>{test.coverIds.length} variants</span>
                <span>{totalVotes(test)} votes</span>
                {test.winnerCoverId && (
                  <span className="flex items-center gap-1 text-green-600">
                    <Trophy className="h-3 w-3" /> Winner selected
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
