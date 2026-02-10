import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskForm } from "../TaskForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock the validation module — use the real implementation so we test actual
// Zod validation logic, but we need to make sure the module resolves.
jest.mock("@/lib/validation", () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { z } = require("zod");

  function validateForm<T>(
    schema: z.ZodSchema<T>,
    data: unknown,
  ): { success: boolean; data?: T; errors?: Record<string, string> } {
    const result = schema.safeParse(data);
    if (result.success) {
      return { success: true, data: result.data };
    }
    const errors: Record<string, string> = {};
    for (const issue of result.error.issues) {
      const key = issue.path.join(".");
      if (!errors[key]) {
        errors[key] = issue.message;
      }
    }
    return { success: false, errors };
  }

  return { validateForm };
});

// Mock the pipeline hooks module (TaskType is imported from there)
jest.mock("../../hooks", () => ({
  __esModule: true,
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderForm(props: Partial<React.ComponentProps<typeof TaskForm>> = {}) {
  const defaultProps: React.ComponentProps<typeof TaskForm> = {
    onSubmit: jest.fn(),
    onCancel: jest.fn(),
    isLoading: false,
    ...props,
  };
  return {
    ...render(<TaskForm {...defaultProps} />),
    props: defaultProps,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("TaskForm", () => {
  // 1. Renders all expected form fields
  it("renders form with title, description, type, and due date fields", () => {
    renderForm();

    expect(screen.getByLabelText("Title")).toBeInTheDocument();
    expect(screen.getByLabelText("Description")).toBeInTheDocument();
    expect(screen.getByLabelText("Type")).toBeInTheDocument();
    expect(screen.getByLabelText("Due Date")).toBeInTheDocument();
  });

  // 2. Validation error when title is empty on blur
  it("shows validation error when title is empty on blur", async () => {
    const user = userEvent.setup();
    renderForm();

    const titleInput = screen.getByLabelText("Title");
    await user.click(titleInput);
    await user.tab(); // blur away

    await waitFor(() => {
      expect(screen.getByText("Title is required")).toBeInTheDocument();
    });
  });

  // 3. Validation error when title exceeds 200 characters
  it("shows validation error when title exceeds 200 characters", async () => {
    const user = userEvent.setup();
    renderForm();

    const titleInput = screen.getByLabelText("Title");
    const longTitle = "a".repeat(201);
    await user.click(titleInput);
    await user.paste(longTitle);
    await user.tab(); // blur to trigger touched

    await waitFor(() => {
      expect(
        screen.getByText("Title must be 200 characters or fewer"),
      ).toBeInTheDocument();
    });
  });

  // 4. Validation error when description exceeds 2000 characters
  it("shows validation error when description exceeds 2000 characters", async () => {
    const user = userEvent.setup();
    renderForm();

    const descInput = screen.getByLabelText("Description");
    const longDescription = "x".repeat(2001);
    await user.click(descInput);
    await user.paste(longDescription);
    await user.tab();

    await waitFor(() => {
      expect(
        screen.getByText("Description must be 2000 characters or fewer"),
      ).toBeInTheDocument();
    });
  });

  // 5. Validation error when due date is in the past
  it("shows validation error when due date is in the past", async () => {
    const user = userEvent.setup();
    renderForm();

    const dueDateInput = screen.getByLabelText("Due Date");
    // Use a date clearly in the past
    await user.clear(dueDateInput);
    // fireEvent is more reliable for date inputs
    const { fireEvent } = require("@testing-library/react");
    fireEvent.change(dueDateInput, { target: { value: "2020-01-01" } });
    fireEvent.blur(dueDateInput);

    await waitFor(() => {
      expect(
        screen.getByText("Due date must be in the future"),
      ).toBeInTheDocument();
    });
  });

  // 6. Submit button is disabled when form is invalid (empty title)
  it("submit button is disabled when form is invalid", () => {
    renderForm();

    const submitBtn = screen.getByRole("button", { name: /add task/i });
    expect(submitBtn).toBeDisabled();
  });

  // 7. Submit button is enabled when form is valid
  it("submit button is enabled when form is valid", async () => {
    const user = userEvent.setup();
    renderForm();

    const titleInput = screen.getByLabelText("Title");
    await user.type(titleInput, "My valid task");

    await waitFor(() => {
      const submitBtn = screen.getByRole("button", { name: /add task/i });
      expect(submitBtn).toBeEnabled();
    });
  });

  // 8. Calls onSubmit with valid data
  it("calls onSubmit with valid data when the form is submitted", async () => {
    const user = userEvent.setup();
    const { props } = renderForm();

    const titleInput = screen.getByLabelText("Title");
    await user.type(titleInput, "Write chapter 1");

    const descInput = screen.getByLabelText("Description");
    await user.type(descInput, "First draft of the opening chapter");

    const submitBtn = screen.getByRole("button", { name: /add task/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(props.onSubmit).toHaveBeenCalledTimes(1);
      expect(props.onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Write chapter 1",
          description: "First draft of the opening chapter",
          type: "writing", // default value
          due_date: "", // no date entered
        }),
      );
    });
  });

  // 9. Shows all validation errors on submit attempt with invalid data
  it("shows all validation errors on submit attempt with invalid data", async () => {
    const user = userEvent.setup();
    renderForm();

    // Fill in a past due date and long description, but leave title empty
    const descInput = screen.getByLabelText("Description");
    const longDescription = "y".repeat(2001);
    await user.click(descInput);
    await user.paste(longDescription);

    const { fireEvent } = require("@testing-library/react");
    const dueDateInput = screen.getByLabelText("Due Date");
    fireEvent.change(dueDateInput, { target: { value: "2020-01-01" } });

    // Submit the form — this should mark all fields as touched
    const form = screen.getByRole("button", { name: /add task/i }).closest("form")!;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText("Title is required")).toBeInTheDocument();
      expect(
        screen.getByText("Description must be 2000 characters or fewer"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Due date must be in the future"),
      ).toBeInTheDocument();
    });
  });

  // 10. Does not call onSubmit when form is invalid
  it("does not call onSubmit when form is invalid", async () => {
    const { props } = renderForm();

    // Submit without filling anything
    const { fireEvent } = require("@testing-library/react");
    const form = screen.getByRole("button", { name: /add task/i }).closest("form")!;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(props.onSubmit).not.toHaveBeenCalled();
    });
  });

  // 11. Submit button shows loading state
  it("submit button shows loading text and is disabled when isLoading is true", async () => {
    const user = userEvent.setup();
    renderForm({ isLoading: true });

    // Even with valid title the button should be disabled due to isLoading
    const titleInput = screen.getByLabelText("Title");
    await user.type(titleInput, "Some title");

    await waitFor(() => {
      const submitBtn = screen.getByRole("button", { name: /adding/i });
      expect(submitBtn).toBeDisabled();
      expect(submitBtn).toHaveTextContent("Adding...");
    });
  });

  // 12. Cancel button calls onCancel
  it("cancel button calls onCancel when clicked", async () => {
    const user = userEvent.setup();
    const { props } = renderForm();

    const cancelBtn = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelBtn);

    expect(props.onCancel).toHaveBeenCalledTimes(1);
  });

  // 13. Cancel button is not rendered when onCancel is not provided
  it("does not render cancel button when onCancel is not provided", () => {
    renderForm({ onCancel: undefined });

    expect(screen.queryByRole("button", { name: /cancel/i })).not.toBeInTheDocument();
  });

  // 14. Type select has all expected options
  it("type select has all expected task type options", () => {
    renderForm();

    const typeSelect = screen.getByLabelText("Type") as HTMLSelectElement;
    const options = Array.from(typeSelect.options).map((o) => o.value);

    expect(options).toEqual([
      "writing",
      "editing",
      "proofreading",
      "formatting",
      "review",
    ]);
  });

  // 15. Form resets after successful submit
  it("resets form fields after successful submit", async () => {
    const user = userEvent.setup();
    renderForm();

    const titleInput = screen.getByLabelText("Title") as HTMLInputElement;
    await user.type(titleInput, "Task to reset");

    const submitBtn = screen.getByRole("button", { name: /add task/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(titleInput.value).toBe("");
    });
  });

  // 16. Title with only whitespace triggers validation error
  it("shows validation error when title is only whitespace", async () => {
    const user = userEvent.setup();
    renderForm();

    const titleInput = screen.getByLabelText("Title");
    await user.type(titleInput, "   ");
    await user.tab();

    await waitFor(() => {
      // Zod .trim().min(1) will catch whitespace-only strings
      expect(screen.getByText("Title is required")).toBeInTheDocument();
    });
  });

  // 17. aria-invalid attribute is set on invalid fields
  it("sets aria-invalid on the title field when there is a validation error", async () => {
    const user = userEvent.setup();
    renderForm();

    const titleInput = screen.getByLabelText("Title");
    await user.click(titleInput);
    await user.tab();

    await waitFor(() => {
      expect(titleInput).toHaveAttribute("aria-invalid", "true");
    });
  });
});
