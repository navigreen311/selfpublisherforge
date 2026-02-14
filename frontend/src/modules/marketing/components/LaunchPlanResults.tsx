"use client";

import { useState, useCallback } from "react";
import { format, parseISO } from "date-fns";
import {
  ChevronDown,
  ChevronRight,
  Mail,
  Share2,
  Users,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { LaunchPhaseTimeline } from "./LaunchPhaseTimeline";
import { useTogglePlanTask } from "../hooks";
import type { LaunchPlan, LaunchPhase, PhaseTask } from "../types";

interface LaunchPlanResultsProps {
  plan: LaunchPlan;
  onGenerateEmailSequence?: () => void;
  onGenerateSocialPosts?: () => void;
  onCreateARCCampaign?: () => void;
}

const phaseLabels: Record<string, string> = {
  pre_launch: "Pre-Launch",
  launch_week: "Launch Week",
  post_launch: "Post-Launch",
};

const phaseColors: Record<string, { bg: string; border: string; text: string }> = {
  pre_launch: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700" },
  launch_week: { bg: "bg-green-50", border: "border-green-200", text: "text-green-700" },
  post_launch: { bg: "bg-purple-50", border: "border-purple-200", text: "text-purple-700" },
};

const statusBadgeVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "secondary",
  active: "default",
  completed: "outline",
  archived: "destructive",
};

export function LaunchPlanResults({
  plan,
  onGenerateEmailSequence,
  onGenerateSocialPosts,
  onCreateARCCampaign,
}: LaunchPlanResultsProps) {
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(
    new Set(plan.phases.map((p) => p.id))
  );

  const togglePlanTask = useTogglePlanTask(plan.id);

  const togglePhase = useCallback((phaseId: string) => {
    setExpandedPhases((prev) => {
      const next = new Set(prev);
      if (next.has(phaseId)) {
        next.delete(phaseId);
      } else {
        next.add(phaseId);
      }
      return next;
    });
  }, []);

  const handleTaskToggle = useCallback(
    (task: PhaseTask) => {
      const newStatus = task.status === "completed" ? "pending" : "completed";
      togglePlanTask.mutate({ taskId: task.id, status: newStatus });
    },
    [togglePlanTask]
  );

  const totalTasks = plan.phases.reduce((sum, p) => sum + p.tasks.length, 0);
  const completedTasks = plan.phases.reduce(
    (sum, p) => sum + p.tasks.filter((t) => t.status === "completed").length,
    0
  );
  const completionPercent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const sortedPhases = [...plan.phases].sort((a, b) => a.order_index - b.order_index);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl sm:text-2xl font-bold">{plan.title}</h2>
            <Badge variant={statusBadgeVariant[plan.status] || "secondary"}>
              {plan.status}
            </Badge>
          </div>
          {plan.description && (
            <p className="text-sm text-muted-foreground mt-1">{plan.description}</p>
          )}
          <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-muted-foreground">
            {plan.launch_date && (
              <span>Launch: {format(parseISO(plan.launch_date), "MMM d, yyyy")}</span>
            )}
            {plan.budget != null && (
              <span>Budget: ${plan.budget.toLocaleString()}</span>
            )}
            {plan.genre && <span>Genre: {plan.genre}</span>}
          </div>
        </div>
      </div>

      {/* Phase Timeline Bar */}
      <LaunchPhaseTimeline phases={plan.phases} />

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">
            {completedTasks} of {totalTasks} tasks complete
          </span>
          <span className="text-muted-foreground">{completionPercent}%</span>
        </div>
        <Progress value={completionPercent} className="h-2" />
      </div>

      {/* Expandable Phase Sections */}
      <div className="space-y-4">
        {sortedPhases.map((phase) => {
          const isExpanded = expandedPhases.has(phase.id);
          const colors = phaseColors[phase.phase_type] || phaseColors.pre_launch;
          const phaseCompleted = phase.tasks.filter((t) => t.status === "completed").length;
          const phaseTotal = phase.tasks.length;

          return (
            <div
              key={phase.id}
              className={cn("rounded-lg border", colors.border, colors.bg)}
            >
              {/* Phase Header */}
              <button
                className="w-full flex items-center justify-between p-4 text-left"
                onClick={() => togglePhase(phase.id)}
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 flex-shrink-0" />
                  ) : (
                    <ChevronRight className="h-4 w-4 flex-shrink-0" />
                  )}
                  <div>
                    <h3 className={cn("font-semibold text-base", colors.text)}>
                      {phaseLabels[phase.phase_type] || phase.name}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {phase.start_date ? format(parseISO(phase.start_date), "MMM d") : "?"} -{" "}
                      {phase.end_date ? format(parseISO(phase.end_date), "MMM d, yyyy") : "?"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-muted-foreground">
                    {phaseCompleted}/{phaseTotal} tasks
                  </span>
                  <div className="w-20 h-2 bg-white/60 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full transition-all"
                      style={{
                        width: phaseTotal > 0 ? `${(phaseCompleted / phaseTotal) * 100}%` : "0%",
                      }}
                    />
                  </div>
                </div>
              </button>

              {/* Phase Tasks */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-2">
                  {phase.tasks.length === 0 ? (
                    <p className="text-sm text-muted-foreground py-2 text-center">
                      No tasks in this phase.
                    </p>
                  ) : (
                    phase.tasks
                      .sort((a, b) => a.order_index - b.order_index)
                      .map((task) => (
                        <div
                          key={task.id}
                          className="flex items-center gap-3 p-3 bg-white rounded-lg border"
                        >
                          <input
                            type="checkbox"
                            checked={task.status === "completed"}
                            onChange={() => handleTaskToggle(task)}
                            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <div className="flex-1 min-w-0">
                            <span
                              className={cn(
                                "text-sm font-medium",
                                task.status === "completed" && "line-through text-muted-foreground"
                              )}
                            >
                              {task.title}
                            </span>
                            {task.description && (
                              <p className="text-xs text-muted-foreground mt-0.5">{task.description}</p>
                            )}
                          </div>
                          {task.due_date && (
                            <span className="text-xs text-muted-foreground flex-shrink-0">
                              {format(parseISO(task.due_date), "MMM d")}
                            </span>
                          )}
                          {task.status === "completed" && (
                            <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                          )}
                        </div>
                      ))
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3 pt-2 border-t">
        <Button
          variant="outline"
          size="sm"
          onClick={onGenerateEmailSequence}
          className="gap-2"
        >
          <Mail className="h-4 w-4" />
          Generate Email Sequence
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onGenerateSocialPosts}
          className="gap-2"
        >
          <Share2 className="h-4 w-4" />
          Generate Social Posts
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onCreateARCCampaign}
          className="gap-2"
        >
          <Users className="h-4 w-4" />
          Create ARC Campaign
        </Button>
      </div>
    </div>
  );
}
