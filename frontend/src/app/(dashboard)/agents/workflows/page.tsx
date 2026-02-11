"use client";

import { useState } from "react";
import { useAgents, useWorkflows, useCreateWorkflow } from "@/modules/agents/hooks";
import { WorkflowBuilder } from "@/modules/agents/components/WorkflowBuilder";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import type { AgentWorkflow, WorkflowCreate, WorkflowStatus } from "@/modules/agents/types";
import { useTranslations } from "@/hooks/use-translations";

const STATUS_STYLES: Record<WorkflowStatus, string> = {
  draft: "bg-gray-100 text-gray-800",
  running: "bg-blue-100 text-blue-800",
  paused: "bg-yellow-100 text-yellow-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-600",
};

export default function WorkflowsPage() {
  const t = useTranslations("agents");
  const [showBuilder, setShowBuilder] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<AgentWorkflow | null>(null);

  const { data: agentsData } = useAgents();
  const { data: workflowsData, isLoading } = useWorkflows();
  const createWorkflow = useCreateWorkflow();

  const agents = agentsData?.items || [];
  const workflows = workflowsData?.items || [];

  const handleCreateWorkflow = (payload: WorkflowCreate) => {
    createWorkflow.mutate(payload, {
      onSuccess: () => {
        setShowBuilder(false);
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("workflows.title")}</h1>
          <p className="text-muted-foreground">
            {t("workflows.subtitle")}
          </p>
        </div>
        <button
          onClick={() => setShowBuilder(!showBuilder)}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          {showBuilder ? t("workflows.cancelCreate") : t("workflows.newWorkflow")}
        </button>
      </div>

      {/* Workflow builder */}
      {showBuilder && (
        <div className="rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">{t("workflows.createWorkflow")}</h2>
          <WorkflowBuilder
            agents={agents}
            onSubmit={handleCreateWorkflow}
            isSubmitting={createWorkflow.isPending}
          />
        </div>
      )}

      {/* Workflow detail */}
      {selectedWorkflow && (
        <div className="rounded-lg border p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">{selectedWorkflow.name}</h2>
            <button
              onClick={() => setSelectedWorkflow(null)}
              className="rounded-md border px-3 py-1 text-sm hover:bg-accent"
            >
              {t("workflows.close")}
            </button>
          </div>
          {selectedWorkflow.description && (
            <p className="text-muted-foreground">{selectedWorkflow.description}</p>
          )}
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-muted-foreground">{t("workflows.status")}</span>{" "}
              <span className="capitalize">{selectedWorkflow.status.replace(/_/g, " ")}</span>
            </div>
            <div>
              <span className="font-medium text-muted-foreground">{t("workflows.steps")}</span>{" "}
              {selectedWorkflow.steps.length}
            </div>
            <div>
              <span className="font-medium text-muted-foreground">{t("workflows.currentStep")}</span>{" "}
              {selectedWorkflow.current_step_index + 1}
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-sm font-semibold">{t("workflows.stepsLabel")}</h3>
            {selectedWorkflow.steps.map((step, idx) => (
              <div
                key={idx}
                className={cn(
                  "rounded-md border p-3 text-sm",
                  idx === selectedWorkflow.current_step_index && "border-blue-300 bg-blue-50"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    {idx + 1}. {String(step.title || t("workflows.step", { number: idx + 1 }))}
                  </span>
                  <span className="text-xs capitalize text-muted-foreground">
                    {String(step.status || "pending")}
                  </span>
                </div>
                {step.description ? (
                  <p className="mt-1 text-xs text-muted-foreground">
                    {String(step.description)}
                  </p>
                ) : null}
              </div>
            ))}
          </div>

          {selectedWorkflow.error_message && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {selectedWorkflow.error_message}
            </div>
          )}
        </div>
      )}

      {/* Workflow list */}
      {isLoading ? (
        <div className="text-muted-foreground">{t("workflows.loadingWorkflows")}</div>
      ) : workflows.length === 0 ? (
        <div className="flex items-center justify-center rounded-lg border border-dashed p-8 text-muted-foreground">
          {t("workflows.noWorkflows")}
        </div>
      ) : (
        <div className="space-y-2">
          {workflows.map((wf) => (
            <div
              key={wf.id}
              className="flex items-center justify-between rounded-lg border p-3 cursor-pointer hover:bg-accent/50"
              onClick={() => setSelectedWorkflow(wf)}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-medium truncate">{wf.name}</h4>
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                      STATUS_STYLES[wf.status]
                    )}
                  >
                    {wf.status.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {t("workflows.stepsCount", { count: wf.steps.length })} |{" "}
                  {formatDistanceToNow(new Date(wf.created_at), {
                    addSuffix: true,
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
