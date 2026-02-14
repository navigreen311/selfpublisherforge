"use client";
import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  useTaskDetail,
  useApproveTaskMutation,
  useRegenerateTask,
  useStopTask,
  useRateTask,
} from "../hooks";

interface TaskExecutionViewProps {
  taskId: string;
  onClose: () => void;
}

export function TaskExecutionView({ taskId, onClose }: TaskExecutionViewProps) {
  const { data: task, isLoading, error } = useTaskDetail(taskId);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [streamOutput, setStreamOutput] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [editedOutput, setEditedOutput] = useState("");
  const outputRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const approveMutation = useApproveTaskMutation();
  const regenerateMutation = useRegenerateTask();
  const stopMutation = useStopTask();
  const rateMutation = useRateTask();

  const isRunning = task?.status === "running";
  const isComplete = task?.status === "completed";
  const isFailed = task?.status === "failed";

  // Timer for elapsed time
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning]);

  // Streaming output via EventSource
  useEffect(() => {
    if (!isRunning) return;

    const eventSource = new EventSource(
      `/api/v1/agents/tasks/${taskId}/stream`
    );
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.chunk) {
        setStreamOutput((prev) => prev + data.chunk);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [taskId, isRunning]);

  // Auto-scroll output to bottom
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [streamOutput, task?.output]);

  // Format elapsed time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins} min ${secs} sec`;
  };

  // Calculate progress percentage
  const getProgress = () => {
    if (!task?.steps) return 0;
    const completedSteps = task.steps.filter(
      (s: any) => s.status === "completed"
    ).length;
    return (completedSteps / task.steps.length) * 100;
  };

  // Handle approve
  const handleApprove = () => {
    approveMutation.mutate(taskId);
  };

  // Handle regenerate
  const handleRegenerate = () => {
    regenerateMutation.mutate(taskId);
    setElapsedSeconds(0);
    setStreamOutput("");
  };

  // Handle stop
  const handleStop = () => {
    stopMutation.mutate(taskId);
  };

  // Handle rating
  const handleRate = (rating: number) => {
    rateMutation.mutate({ taskId, rating });
  };

  // Handle copy to clipboard
  const handleCopy = () => {
    const text = task?.output || "";
    navigator.clipboard.writeText(text);
  };

  // Handle edit toggle
  const handleEditToggle = () => {
    if (!isEditing) {
      setEditedOutput(task?.output || "");
    }
    setIsEditing(!isEditing);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Loading task...</div>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4">Failed to load task details.</p>
            <Button onClick={onClose}>Close</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="border-b p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-xl">
            {task.agentIcon || "🤖"}
          </div>
          <div>
            <h1 className="text-xl font-semibold">{task.agentName}</h1>
            <p className="text-sm text-muted-foreground">{task.taskType}</p>
          </div>
        </div>
        <Button variant="ghost" onClick={onClose}>
          ✕
        </Button>
      </div>

      {/* Status Bar */}
      <div className="border-b p-4">
        {isRunning && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">⏳</span>
              <span className="font-medium">
                Running... ({elapsedSeconds} seconds elapsed)
              </span>
            </div>
            <Progress value={getProgress()} className="h-2" />
          </div>
        )}

        {isComplete && (
          <div className="flex items-center gap-2 text-green-600">
            <span className="text-lg">✅</span>
            <span className="font-medium">
              Complete ({formatTime(task.duration || 0)} · {task.tokens || 0}{" "}
              tokens · ${(task.cost || 0).toFixed(2)})
            </span>
          </div>
        )}

        {isFailed && (
          <div className="flex items-center gap-2 text-destructive">
            <span className="text-lg">❌</span>
            <span className="font-medium">Failed</span>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Steps */}
        {task.steps && task.steps.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Steps</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {task.steps.map((step: any, index: number) => (
                <div key={index} className="flex items-center gap-3">
                  {step.status === "completed" && (
                    <span className="text-green-600 text-lg">✅</span>
                  )}
                  {step.status === "running" && (
                    <span className="text-blue-600 text-lg animate-spin">
                      ⏳
                    </span>
                  )}
                  {step.status === "pending" && (
                    <span className="text-muted-foreground text-lg">○</span>
                  )}
                  <div className="flex-1">
                    <div className="font-medium">{step.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {step.status}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Output Panel */}
        <Card className="flex-1">
          <CardHeader>
            <CardTitle className="text-base">
              {isRunning ? "Live Output" : "Output"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <Textarea
                value={editedOutput}
                onChange={(e) => setEditedOutput(e.target.value)}
                className="min-h-[400px] font-mono text-sm"
              />
            ) : (
              <div
                ref={outputRef}
                className="max-h-[500px] overflow-auto bg-muted/30 p-4 rounded-md"
              >
                <pre className="whitespace-pre-wrap font-mono text-sm">
                  {isRunning ? streamOutput : task.output}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Error Message */}
        {isFailed && task.error && (
          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-base text-destructive">
                Error
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4">{task.error}</p>
              <Button onClick={handleRegenerate} variant="outline">
                Retry
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Action Bar */}
      <div className="border-t p-4 bg-muted/30">
        {isRunning && (
          <div className="flex gap-2">
            <Button
              onClick={handleStop}
              variant="destructive"
              disabled={stopMutation.isPending}
            >
              ⏹ Stop
            </Button>
            <Button variant="outline" disabled>
              ⏸ Pause
            </Button>
          </div>
        )}

        {isComplete && (
          <div className="space-y-4">
            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={handleApprove}
                disabled={approveMutation.isPending}
              >
                ✅ Approve & Save
              </Button>
              <Button onClick={handleEditToggle} variant="outline">
                {isEditing ? "💾 Save Edit" : "✏️ Edit Output"}
              </Button>
              <Button
                onClick={handleRegenerate}
                variant="outline"
                disabled={regenerateMutation.isPending}
              >
                🔃 Regenerate
              </Button>
              <Button onClick={handleCopy} variant="outline">
                📋 Copy to Clipboard
              </Button>
              <Button variant="outline" disabled>
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
                    (task.rating || 0) >= star
                      ? "text-yellow-500"
                      : "text-muted-foreground"
                  } hover:text-yellow-500`}
                >
                  ★
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
