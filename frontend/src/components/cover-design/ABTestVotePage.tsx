"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ThumbsUp, Loader2, CheckCircle2 } from "lucide-react";

interface CoverOption {
  id: string;
  imageUrl: string;
  label: string;
}

interface ABTestVotePageProps {
  testName: string;
  covers: CoverOption[];
  onVote: (coverId: string) => Promise<void>;
  hasVoted?: boolean;
  votedCoverId?: string;
}

export function ABTestVotePageComponent({
  testName,
  covers,
  onVote,
  hasVoted = false,
  votedCoverId,
}: ABTestVotePageProps) {
  const [voting, setVoting] = useState<string | null>(null);

  const handleVote = async (coverId: string) => {
    if (hasVoted) return;
    setVoting(coverId);
    try {
      await onVote(coverId);
    } finally {
      setVoting(null);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center py-12 px-4">
      <div className="max-w-4xl w-full space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">Which cover do you prefer?</h1>
          <p className="text-muted-foreground">{testName}</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {covers.map((cover) => (
            <div
              key={cover.id}
              className={`rounded-lg border-2 overflow-hidden transition-all ${
                votedCoverId === cover.id
                  ? "border-primary ring-2 ring-primary/20"
                  : "border-transparent hover:border-primary/50"
              }`}
            >
              <div className="aspect-[2/3] bg-muted flex items-center justify-center">
                {cover.imageUrl ? (
                  <img
                    src={cover.imageUrl}
                    alt={cover.label}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-muted-foreground text-sm">{cover.label}</span>
                )}
              </div>
              <div className="p-3">
                <Button
                  className="w-full"
                  variant={votedCoverId === cover.id ? "default" : "outline"}
                  disabled={hasVoted || voting !== null}
                  onClick={() => handleVote(cover.id)}
                >
                  {voting === cover.id ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : votedCoverId === cover.id ? (
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                  ) : (
                    <ThumbsUp className="h-4 w-4 mr-2" />
                  )}
                  {votedCoverId === cover.id ? "Voted!" : "Vote"}
                </Button>
              </div>
            </div>
          ))}
        </div>

        {hasVoted && (
          <p className="text-center text-sm text-muted-foreground">
            Thanks for voting! Your feedback helps choose the best cover.
          </p>
        )}
      </div>
    </div>
  );
}
