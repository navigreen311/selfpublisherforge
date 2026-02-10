import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import type { Agent } from "../../types";

// ─── Import component ───────────────────────────────────────────────────────

import { WorkflowBuilder } from "../WorkflowBuilder";

// ─── Fixtures ───────────────────────────────────────────────────────────────

const mockAgents: Agent[] = [
  {
    id: "agent-1",
    org_id: "org-1",
    agent_type: "research",
    name: "Research Agent",
    description: "Handles research tasks",
    is_enabled: true,
    permission_level: "suggest",
    model_id: "gpt-4",
    system_prompt: null,
    max_tokens: 4096,
    temperature: 0.7,
    config: null,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
  {
    id: "agent-2",
    org_id: "org-1",
    agent_type: "editor",
    name: "Editor Agent",
    description: null,
    is_enabled: true,
    permission_level: "auto_execute_low",
    model_id: "gpt-4",
    system_prompt: null,
    max_tokens: 8192,
    temperature: 0.3,
    config: null,
    created_at: "2025-02-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
];

// ─── Helpers ────────────────────────────────────────────────────────────────

function renderBuilder(
  overrides: Partial<React.ComponentProps<typeof WorkflowBuilder>> = {}
) {
  const defaultProps = {
    agents: mockAgents,
    onSubmit: jest.fn(),
    ...overrides,
  };
  return {
    ...render(<WorkflowBuilder {...defaultProps} />),
    props: defaultProps,
  };
}

/** Set an input value via fireEvent (reliable in jsdom). */
function setInputValue(element: HTMLElement, value: string) {
  fireEvent.change(element, { target: { value } });
}

/** Click the "Add Step" button to add a new workflow step. */
function clickAddStep() {
  fireEvent.click(screen.getByRole("button", { name: /add step/i }));
}

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("WorkflowBuilder", () => {
  // ── Rendering ──────────────────────────────────────────────────────────

  it("renders workflow builder with add step button", () => {
    renderBuilder();

    expect(
      screen.getByRole("button", { name: /add step/i })
    ).toBeInTheDocument();
  });

  it("renders the create workflow submit button", () => {
    renderBuilder();

    expect(
      screen.getByRole("button", { name: /create workflow/i })
    ).toBeInTheDocument();
  });

  it("shows empty state message when no steps exist", () => {
    renderBuilder();

    expect(screen.getByText(/no steps yet/i)).toBeInTheDocument();
  });

  // ── Placeholder text ──────────────────────────────────────────────────

  it("displays proper placeholder text on workflow name input", () => {
    renderBuilder();

    const nameInput = screen.getByLabelText("Workflow name");
    expect(nameInput).toHaveAttribute("placeholder", "e.g., Research keywords");
  });

  it("displays proper placeholder text on workflow description input", () => {
    renderBuilder();

    const descriptionInput = screen.getByLabelText("Workflow description");
    expect(descriptionInput).toHaveAttribute(
      "placeholder",
      "What should this step accomplish?"
    );
  });

  it("displays proper placeholder text on step inputs after adding a step", () => {
    renderBuilder();
    clickAddStep();

    const stepTitleInput = screen.getByLabelText("Step 1 title");
    expect(stepTitleInput).toHaveAttribute(
      "placeholder",
      "e.g., Research keywords"
    );

    const stepDescInput = screen.getByLabelText("Step 1 description");
    expect(stepDescInput).toHaveAttribute(
      "placeholder",
      "What should this step accomplish?"
    );

    const conditionInput = screen.getByLabelText("Step 1 condition");
    expect(conditionInput).toHaveAttribute(
      "placeholder",
      "e.g., previous_step.success == true"
    );
  });

  // ── aria-label attributes ─────────────────────────────────────────────

  it("has aria-label attributes present on all workflow-level inputs", () => {
    renderBuilder();

    expect(screen.getByLabelText("Workflow name")).toBeInTheDocument();
    expect(screen.getByLabelText("Workflow description")).toBeInTheDocument();
  });

  it("has aria-label attributes present on all step-level inputs after adding a step", () => {
    renderBuilder();
    clickAddStep();

    expect(screen.getByLabelText("Step 1 title")).toBeInTheDocument();
    expect(screen.getByLabelText("Step 1 agent")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Step 1 on failure action")
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Step 1 max retries")).toBeInTheDocument();
    expect(screen.getByLabelText("Step 1 description")).toBeInTheDocument();
    expect(screen.getByLabelText("Step 1 condition")).toBeInTheDocument();
  });

  // ── Step name required validation (shows error on blur) ───────────────

  it("shows error on blur when step name is empty", () => {
    renderBuilder();
    clickAddStep();

    const stepTitleInput = screen.getByLabelText("Step 1 title");
    // Clear the default title and trigger blur
    setInputValue(stepTitleInput, "");
    fireEvent.blur(stepTitleInput);

    expect(screen.getByText("Step name is required.")).toBeInTheDocument();
  });

  // ── Step name max 100 characters ──────────────────────────────────────

  it("shows error when step name exceeds 100 characters", () => {
    renderBuilder();
    clickAddStep();

    const stepTitleInput = screen.getByLabelText("Step 1 title");
    setInputValue(stepTitleInput, "A".repeat(101));
    fireEvent.blur(stepTitleInput);

    expect(
      screen.getByText("Step name must be 100 characters or fewer.")
    ).toBeInTheDocument();
  });

  // ── Step description max 500 characters ───────────────────────────────

  it("shows error when step description exceeds 500 characters", () => {
    renderBuilder();
    clickAddStep();

    const stepDescInput = screen.getByLabelText("Step 1 description");
    setInputValue(stepDescInput, "B".repeat(501));
    fireEvent.blur(stepDescInput);

    expect(
      screen.getByText("Step description must be 500 characters or fewer.")
    ).toBeInTheDocument();
  });

  // ── Condition field validated when provided ───────────────────────────

  it("shows error when condition field is only whitespace", () => {
    renderBuilder();
    clickAddStep();

    const conditionInput = screen.getByLabelText("Step 1 condition");
    setInputValue(conditionInput, "   ");
    fireEvent.blur(conditionInput);

    expect(
      screen.getByText("Condition must not be blank if provided.")
    ).toBeInTheDocument();
  });

  // ── aria-invalid set on error fields ──────────────────────────────────

  it("sets aria-invalid on step title field when validation error exists", () => {
    renderBuilder();
    clickAddStep();

    const stepTitleInput = screen.getByLabelText("Step 1 title");
    setInputValue(stepTitleInput, "");
    fireEvent.blur(stepTitleInput);

    expect(stepTitleInput).toHaveAttribute("aria-invalid", "true");
  });

  it("sets aria-invalid on workflow name field when validation error exists", () => {
    renderBuilder();

    const nameInput = screen.getByLabelText("Workflow name");
    // Focus and blur without typing — name remains empty, triggers required error
    fireEvent.focus(nameInput);
    fireEvent.blur(nameInput);

    expect(nameInput).toHaveAttribute("aria-invalid", "true");
  });

  // ── Submit button disabled / enabled ──────────────────────────────────

  it("submit button is disabled when form is invalid (no name, no steps)", () => {
    renderBuilder();

    const submitButton = screen.getByRole("button", {
      name: /create workflow/i,
    });
    expect(submitButton).toBeDisabled();
  });

  it("submit button is enabled when form is valid (name + at least one valid step)", () => {
    renderBuilder();

    // Fill workflow name
    setInputValue(screen.getByLabelText("Workflow name"), "My Workflow");

    // Add a step (defaults have a valid title "Step 1")
    clickAddStep();

    const submitButton = screen.getByRole("button", {
      name: /create workflow/i,
    });
    expect(submitButton).toBeEnabled();
  });

  it("submit button becomes disabled when step has validation error", () => {
    renderBuilder();

    // Fill workflow name
    setInputValue(screen.getByLabelText("Workflow name"), "My Workflow");

    // Add a step
    clickAddStep();

    // Clear step title to trigger validation error
    const stepTitleInput = screen.getByLabelText("Step 1 title");
    setInputValue(stepTitleInput, "");

    const submitButton = screen.getByRole("button", {
      name: /create workflow/i,
    });
    expect(submitButton).toBeDisabled();
  });

  // ── Workflow name required validation ─────────────────────────────────

  it("shows error on blur when workflow name is empty", () => {
    renderBuilder();

    const nameInput = screen.getByLabelText("Workflow name");
    fireEvent.focus(nameInput);
    fireEvent.blur(nameInput);

    expect(
      screen.getByText("Workflow name is required.")
    ).toBeInTheDocument();
  });

  // ── Workflow name max 100 characters ──────────────────────────────────

  it("shows error when workflow name exceeds 100 characters", () => {
    renderBuilder();

    const nameInput = screen.getByLabelText("Workflow name");
    setInputValue(nameInput, "C".repeat(101));
    fireEvent.blur(nameInput);

    expect(
      screen.getByText("Workflow name must be 100 characters or fewer.")
    ).toBeInTheDocument();
  });

  // ── Workflow description max 500 characters ───────────────────────────

  it("shows error when workflow description exceeds 500 characters", () => {
    renderBuilder();

    const descInput = screen.getByLabelText("Workflow description");
    setInputValue(descInput, "D".repeat(501));
    fireEvent.blur(descInput);

    expect(
      screen.getByText("Description must be 500 characters or fewer.")
    ).toBeInTheDocument();
  });

  // ── Add Step button disabled when no agents ───────────────────────────

  it("add step button is disabled when agents list is empty", () => {
    renderBuilder({ agents: [] });

    const addStepButton = screen.getByRole("button", { name: /add step/i });
    expect(addStepButton).toBeDisabled();
  });

  // ── Form submission ───────────────────────────────────────────────────

  it("calls onSubmit with correct data when form is valid and submitted", () => {
    const onSubmit = jest.fn();
    renderBuilder({ onSubmit });

    // Fill workflow name
    setInputValue(screen.getByLabelText("Workflow name"), "My Workflow");

    // Add a step (defaults: title="Step 1", agent_id="agent-1", on_failure="stop")
    clickAddStep();

    // Submit the form
    fireEvent.click(
      screen.getByRole("button", { name: /create workflow/i })
    );

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "My Workflow",
        steps: expect.arrayContaining([
          expect.objectContaining({
            agent_id: "agent-1",
            title: "Step 1",
            on_failure: "stop",
          }),
        ]),
      })
    );
  });

  // ── Submitting state ──────────────────────────────────────────────────

  it("shows 'Creating...' text when isSubmitting is true", () => {
    renderBuilder({ isSubmitting: true });

    expect(screen.getByText("Creating...")).toBeInTheDocument();
  });

  // ── Remove step ───────────────────────────────────────────────────────

  it("removes a step when the remove button is clicked", () => {
    renderBuilder();
    clickAddStep();

    expect(screen.getByLabelText("Step 1 title")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /remove/i }));

    expect(screen.queryByLabelText("Step 1 title")).not.toBeInTheDocument();
    expect(screen.getByText(/no steps yet/i)).toBeInTheDocument();
  });
});
