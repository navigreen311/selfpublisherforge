"use client";

import { useState, useCallback, useMemo } from "react";
import { cn } from "@/lib/utils";
import type { Agent, WorkflowStepDefinition, WorkflowCreate } from "../types";

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

const VALID_ON_FAILURE_ACTIONS = ["stop", "skip", "retry"] as const;

interface FieldError {
  message: string;
}

interface WorkflowErrors {
  name?: FieldError;
  description?: FieldError;
}

interface StepErrors {
  title?: FieldError;
  description?: FieldError;
  condition?: FieldError;
  on_failure?: FieldError;
}

function validateWorkflowName(value: string): FieldError | undefined {
  const trimmed = value.trim();
  if (!trimmed) {
    return { message: "Workflow name is required." };
  }
  if (trimmed.length > 100) {
    return { message: "Workflow name must be 100 characters or fewer." };
  }
  return undefined;
}

function validateWorkflowDescription(value: string): FieldError | undefined {
  if (value.length > 500) {
    return { message: "Description must be 500 characters or fewer." };
  }
  return undefined;
}

function validateStepTitle(value: string): FieldError | undefined {
  const trimmed = value.trim();
  if (!trimmed) {
    return { message: "Step name is required." };
  }
  if (trimmed.length > 100) {
    return { message: "Step name must be 100 characters or fewer." };
  }
  return undefined;
}

function validateStepDescription(value: string): FieldError | undefined {
  if (value.length > 500) {
    return { message: "Step description must be 500 characters or fewer." };
  }
  return undefined;
}

function validateCondition(value: string): FieldError | undefined {
  // Only validate if the user typed something (the field is optional)
  if (value.length > 0 && value.trim().length === 0) {
    return { message: "Condition must not be blank if provided." };
  }
  return undefined;
}

function validateOnFailure(value: string): FieldError | undefined {
  if (
    !VALID_ON_FAILURE_ACTIONS.includes(
      value as (typeof VALID_ON_FAILURE_ACTIONS)[number]
    )
  ) {
    return { message: "Action type must be stop, skip, or retry." };
  }
  return undefined;
}

// ---------------------------------------------------------------------------
// Touched-state type helpers
// ---------------------------------------------------------------------------

interface TouchedWorkflow {
  name: boolean;
  description: boolean;
}

interface TouchedStep {
  title: boolean;
  description: boolean;
  condition: boolean;
  on_failure: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

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

  // Touched state tracking
  const [touchedWorkflow, setTouchedWorkflow] = useState<TouchedWorkflow>({
    name: false,
    description: false,
  });
  const [touchedSteps, setTouchedSteps] = useState<TouchedStep[]>([]);

  // ---------------------------------------------------------------------------
  // Validation (computed every render for live disable / error state)
  // ---------------------------------------------------------------------------

  const workflowErrors = useMemo<WorkflowErrors>(() => {
    const errors: WorkflowErrors = {};
    const nameErr = validateWorkflowName(name);
    if (nameErr) errors.name = nameErr;
    const descErr = validateWorkflowDescription(description);
    if (descErr) errors.description = descErr;
    return errors;
  }, [name, description]);

  const stepsErrors = useMemo<StepErrors[]>(() => {
    return steps.map((step) => {
      const errors: StepErrors = {};
      const titleErr = validateStepTitle(step.title);
      if (titleErr) errors.title = titleErr;
      const descErr = validateStepDescription(step.description || "");
      if (descErr) errors.description = descErr;
      const condErr = validateCondition(step.condition || "");
      if (condErr) errors.condition = condErr;
      const failErr = validateOnFailure(step.on_failure || "stop");
      if (failErr) errors.on_failure = failErr;
      return errors;
    });
  }, [steps]);

  const hasAnyError = useMemo(() => {
    if (workflowErrors.name || workflowErrors.description) return true;
    return stepsErrors.some(
      (e) => e.title || e.description || e.condition || e.on_failure
    );
  }, [workflowErrors, stepsErrors]);

  const isFormInvalid = !name.trim() || steps.length === 0 || hasAnyError;

  // ---------------------------------------------------------------------------
  // Touch helpers
  // ---------------------------------------------------------------------------

  const touchWorkflowField = useCallback(
    (field: keyof TouchedWorkflow) => {
      if (!touchedWorkflow[field]) {
        setTouchedWorkflow((prev) => ({ ...prev, [field]: true }));
      }
    },
    [touchedWorkflow]
  );

  const touchStepField = useCallback(
    (index: number, field: keyof TouchedStep) => {
      setTouchedSteps((prev) => {
        const next = [...prev];
        if (next[index] && !next[index][field]) {
          next[index] = { ...next[index], [field]: true };
        }
        return next;
      });
    },
    []
  );

  // ---------------------------------------------------------------------------
  // Step CRUD
  // ---------------------------------------------------------------------------

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
    setTouchedSteps((prev) => [
      ...prev,
      { title: false, description: false, condition: false, on_failure: false },
    ]);
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
    setTouchedSteps((prev) => prev.filter((_, i) => i !== index));
  };

  const updateStep = (
    index: number,
    updates: Partial<WorkflowStepDefinition>
  ) => {
    setSteps(
      steps.map((step, i) => (i === index ? { ...step, ...updates } : step))
    );
  };

  // ---------------------------------------------------------------------------
  // Submit
  // ---------------------------------------------------------------------------

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isFormInvalid) return;
    onSubmit({ name, description, steps });
  };

  // ---------------------------------------------------------------------------
  // Inline error display helper
  // ---------------------------------------------------------------------------

  const InlineError = ({ message }: { message?: string }) => {
    if (!message) return null;
    return (
      <p className="mt-1 text-xs text-red-500" role="alert">
        {message}
      </p>
    );
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        {/* Workflow Name */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Workflow Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => touchWorkflowField("name")}
            placeholder="e.g., Research keywords"
            aria-label="Workflow name"
            aria-invalid={
              touchedWorkflow.name && !!workflowErrors.name ? "true" : undefined
            }
            className={cn(
              "w-full rounded-md border px-3 py-2 text-sm",
              touchedWorkflow.name &&
                workflowErrors.name &&
                "border-red-500 focus:ring-red-500"
            )}
            required
          />
          {touchedWorkflow.name && (
            <InlineError message={workflowErrors.name?.message} />
          )}
        </div>

        {/* Workflow Description */}
        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            onBlur={() => touchWorkflowField("description")}
            placeholder="What should this step accomplish?"
            aria-label="Workflow description"
            aria-invalid={
              touchedWorkflow.description && !!workflowErrors.description
                ? "true"
                : undefined
            }
            className={cn(
              "w-full rounded-md border px-3 py-2 text-sm",
              touchedWorkflow.description &&
                workflowErrors.description &&
                "border-red-500 focus:ring-red-500"
            )}
            rows={2}
          />
          {touchedWorkflow.description && (
            <InlineError message={workflowErrors.description?.message} />
          )}
        </div>
      </div>

      {/* Steps */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold">Steps</h3>
          <button
            type="button"
            onClick={addStep}
            disabled={agents.length === 0}
            className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            Add Step
          </button>
        </div>

        {steps.length === 0 ? (
          <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            No steps yet. Click &quot;Add Step&quot; to begin building your workflow.
          </div>
        ) : (
          <div className="space-y-3">
            {steps.map((step, index) => {
              const errs = stepsErrors[index] || {};
              const touched = touchedSteps[index] || {
                title: false,
                description: false,
                condition: false,
                on_failure: false,
              };

              return (
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
                    {/* Step Title / Name */}
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
                        onBlur={() => touchStepField(index, "title")}
                        placeholder="e.g., Research keywords"
                        aria-label={`Step ${index + 1} title`}
                        aria-invalid={
                          touched.title && !!errs.title ? "true" : undefined
                        }
                        className={cn(
                          "w-full rounded-md border px-2 py-1.5 text-sm",
                          touched.title &&
                            errs.title &&
                            "border-red-500 focus:ring-red-500"
                        )}
                        required
                      />
                      {touched.title && (
                        <InlineError message={errs.title?.message} />
                      )}
                    </div>

                    {/* Agent */}
                    <div>
                      <label className="block text-xs font-medium mb-1">
                        Agent
                      </label>
                      <select
                        value={step.agent_id}
                        onChange={(e) =>
                          updateStep(index, { agent_id: e.target.value })
                        }
                        aria-label={`Step ${index + 1} agent`}
                        className="w-full rounded-md border px-2 py-1.5 text-sm"
                      >
                        {agents.map((agent) => (
                          <option key={agent.id} value={agent.id}>
                            {agent.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* On Failure (action type) */}
                    <div>
                      <label className="block text-xs font-medium mb-1">
                        On Failure
                      </label>
                      <select
                        value={step.on_failure || "stop"}
                        onChange={(e) =>
                          updateStep(index, {
                            on_failure: e.target.value as
                              | "stop"
                              | "skip"
                              | "retry",
                          })
                        }
                        onBlur={() => touchStepField(index, "on_failure")}
                        aria-label={`Step ${index + 1} on failure action`}
                        aria-invalid={
                          touched.on_failure && !!errs.on_failure
                            ? "true"
                            : undefined
                        }
                        className={cn(
                          "w-full rounded-md border px-2 py-1.5 text-sm",
                          touched.on_failure &&
                            errs.on_failure &&
                            "border-red-500 focus:ring-red-500"
                        )}
                      >
                        <option value="stop">Stop Workflow</option>
                        <option value="skip">Skip Step</option>
                        <option value="retry">Retry</option>
                      </select>
                      {touched.on_failure && (
                        <InlineError message={errs.on_failure?.message} />
                      )}
                    </div>

                    {/* Max Retries */}
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
                        aria-label={`Step ${index + 1} max retries`}
                        className="w-full rounded-md border px-2 py-1.5 text-sm"
                      />
                    </div>
                  </div>

                  {/* Step Description */}
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
                      onBlur={() => touchStepField(index, "description")}
                      placeholder="What should this step accomplish?"
                      aria-label={`Step ${index + 1} description`}
                      aria-invalid={
                        touched.description && !!errs.description
                          ? "true"
                          : undefined
                      }
                      className={cn(
                        "w-full rounded-md border px-2 py-1.5 text-sm",
                        touched.description &&
                          errs.description &&
                          "border-red-500 focus:ring-red-500"
                      )}
                    />
                    {touched.description && (
                      <InlineError message={errs.description?.message} />
                    )}
                  </div>

                  {/* Condition */}
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
                      onBlur={() => touchStepField(index, "condition")}
                      placeholder="e.g., previous_step.success == true"
                      aria-label={`Step ${index + 1} condition`}
                      aria-invalid={
                        touched.condition && !!errs.condition
                          ? "true"
                          : undefined
                      }
                      className={cn(
                        "w-full rounded-md border px-2 py-1.5 text-sm",
                        touched.condition &&
                          errs.condition &&
                          "border-red-500 focus:ring-red-500"
                      )}
                    />
                    {touched.condition && (
                      <InlineError message={errs.condition?.message} />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={isFormInvalid || isSubmitting}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
      >
        {isSubmitting ? "Creating..." : "Create Workflow"}
      </button>
    </form>
  );
}
