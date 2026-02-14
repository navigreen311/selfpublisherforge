"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  useApproveTaskMutation,
  useRegenerateTask,
  useRateTask,
} from "../hooks";

interface TaskResultActionsProps {
  taskId: string;
  output: string;
  onEdit?: () => void;
  currentRating?: number;
}

export function TaskResultActions({
  taskId,
  output,
  onEdit,
  currentRating = 0,
}: TaskResultActionsProps) {
  const approveMutation = useApproveTaskMutation();
  const regenerateMutation = useRegenerateTask();
  const rateMutation = useRateTask();
  const [rating, setRating] = useState(currentRating);

  const handleApprove = () => {
    approveMutation.mutate(taskId);
  };

  const handleRegenerate = () => {
    regenerateMutation.mutate(taskId);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(output);
  };

  const handleRate = (newRating: number) => {
    setRating(newRating);
    rateMutation.mutate({ taskId, rating: newRating });
  };

  const handleSaveToVault = () => {
    // Placeholder action
    console.log("Save to Knowledge Vault:", taskId);
  };

  return (
    <div className="space-y-4">
      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2">
        <Button
          onClick={handleApprove}
          disabled={approveMutation.isPending}
          size="sm"
        >
          ✅ Approve & Save
        </Button>
        {onEdit && (
          <Button onClick={onEdit} variant="outline" size="sm">
            ✏️ Edit Output
          </Button>
        )}
        <Button
          onClick={handleRegenerate}
          variant="outline"
          size="sm"
          disabled={regenerateMutation.isPending}
        >
          🔃 Regenerate
        </Button>
        <Button onClick={handleCopy} variant="outline" size="sm">
          📋 Copy to Clipboard
        </Button>
        <Button onClick={handleSaveToVault} variant="outline" size="sm">
          📁 Save to Knowledge Vault
        </Button>
      </div>

      {/* Rating */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Rate:</span>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => handleRate(star)}
            className={`text-2xl transition-colors ${
              rating >= star ? "text-yellow-500" : "text-muted-foreground"
            } hover:text-yellow-500`}
          >
            ★
          </button>
        ))}
      </div>
    </div>
  );
}
