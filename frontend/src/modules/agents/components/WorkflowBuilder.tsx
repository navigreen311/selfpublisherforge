"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { Agent, WorkflowStepDefinition, WorkflowCreate } from "../types";

interface WorkflowBuilderProps {
  agents: Agent[];
  onSubmit: (workflow: WorkflowCreate) => void;
  isSubmitting?: boolean;
}

export function WorkflowBuilder({
  agents,
  onSubmit,
  isSubmitting = false,
}: WorkflowBuilderProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [steps, setSteps] = useState<WorkflowStepDefinition[]>([]);

  const addStep = () => {
    if (agents.length === 0) return;
    setSteps([
      ...steps,
      {
        agent_id: agents[0].id,
        title: `Step ${steps.length + 1}`,
        on_failure: "stop",
        max_retries: 0,
      },
    ]);
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const updateStep = (
    index: number,
    updates: Partial<WorkflowStepDefinition>
  ) => {
    setSteps(
      steps.map((step, i) => (i === index ? { ...step, ...updates } : step))
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || steps.length === 0) return;
    onSubmit({ name, description, steps });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Workflow Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Research & Write Pipeline"
            className="w-full rounded-md border px-3 py-2 text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description..."
            className="w-full rounded-md border px-3 py-2 text-sm"
            rows={2}
          />
        </div>
      </div>

      {/* Steps */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold">Steps</h3>
          <button
            type="button"
            onClick={addStep}
            className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
          >
            Add Step
          </button>
        </div>

        {steps.length === 0 ? (
          <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            No steps yet. Click "Add Step" to begin building your workflow.
          </div>
        ) : (
          <div className="space-y-3">
            {steps.map((step, index) => (
              <div
                key={index}
                className="rounded-lg border p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground">
                    Step {index + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeStep(index)}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    Remove
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Title
                    </label>
                    <input
                      type="text"
                      value={step.title}
                      onChange={(e) =>
                        updateStep(index, { title: e.target.value })
                      }
                      className="w-full rounded-md border px-2 py-1.5 text-sm"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Agent
                    </label>
                    <select
                      value={step.agent_id}
                      onChange={(e) =>
                        updateStep(index, { agent_id: e.target.value })
                      }
                      className="w-full rounded-md border px-2 py-1.5 text-sm"
                    >
                      {agents.map((agent) => (
                        <option key={agent.id} value={agent.id}>
                          {agent.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      On Failure
                    </label>
                    <select
                      value={step.on_failure || "stop"}
                      onChange={(e) =>
                        updateStep(index, {
                          on_failure: e.target.value as "stop" | "skip" | "retry",
                        })
                      }
                      className="w-full rounded-md border px-2 py-1.5 text-sm"
                    >
                      <option value="stop">Stop Workflow</option>
                      <option value="skip">Skip Step</option>
                      <option value="retry">Retry</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Max Retries
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={5}
                      value={step.max_retries || 0}
                      onChange={(e) =>
                        updateStep(index, {
                          max_retries: parseInt(e.target.value, 10),
                        })
                      }
                      className="w-full rounded-md border px-2 py-1.5 text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium mb-1">
                    Description
                  </label>
                  <input
                    type="text"
                    value={step.description || ""}
                    onChange={(e) =>
                      updateStep(index, { description: e.target.value })
                    }
                    placeholder="Optional step description..."
                    className="w-full rounded-md border px-2 py-1.5 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium mb-1">
                    Condition (optional)
                  </label>
                  <input
                    type="text"
                    value={step.condition || ""}
                    onChange={(e) =>
                      updateStep(index, { condition: e.target.value })
                    }
                    placeholder="e.g., step_0_output.text"
                    className="w-full rounded-md border px-2 py-1.5 text-sm"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={!name.trim() || steps.length === 0 || isSubmitting}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
      >
        {isSubmitting ? "Creating..." : "Create Workflow"}
      </button>
    </form>
  );
}
