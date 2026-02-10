"use client";

import { useState, useMemo } from "react";
import { z } from "zod";
import { validateForm } from "@/lib/validation";
import type { TaskType } from "../hooks";

const TASK_TYPES: TaskType[] = [
  "writing",
  "editing",
  "proofreading",
  "formatting",
  "review",
];

const taskFormSchema = z.object({
  title: z
    .string()
    .trim()
    .min(1, "Title is required")
    .max(200, "Title must be 200 characters or fewer"),
  description: z
    .string()
    .max(2000, "Description must be 2000 characters or fewer")
    .optional()
    .default(""),
  type: z.enum(["writing", "editing", "proofreading", "formatting", "review"]),
  due_date: z
    .string()
    .optional()
    .refine(
      (val) => !val || new Date(val) > new Date(),
      "Due date must be in the future",
    ),
});

type TaskFormData = z.infer<typeof taskFormSchema>;

interface TaskFormProps {
  onSubmit: (data: {
    title: string;
    type: TaskType;
    description: string;
    due_date: string;
  }) => void;
  onCancel?: () => void;
  isLoading?: boolean;
}

export function TaskForm({ onSubmit, onCancel, isLoading }: TaskFormProps) {
  const [title, setTitle] = useState("");
  const [type, setType] = useState<TaskType>("writing");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");

  const [touched, setTouched] = useState<Record<string, boolean>>({});

  function markTouched(field: string) {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }

  // Validate on every render so errors stay in sync with field values
  const { errors, isValid } = useMemo(() => {
    const result = validateForm(taskFormSchema, {
      title,
      type,
      description: description || undefined,
      due_date: dueDate || undefined,
    });
    return {
      errors: result.errors ?? {},
      isValid: result.success,
    };
  }, [title, type, description, dueDate]);

  function fieldError(field: string): string | undefined {
    return touched[field] ? errors[field] : undefined;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    // Mark all fields touched so errors are visible
    setTouched({ title: true, description: true, due_date: true, type: true });

    if (!isValid) return;

    onSubmit({
      title: title.trim(),
      type,
      description,
      due_date: dueDate,
    });
    setTitle("");
    setDescription("");
    setDueDate("");
    setTouched({});
  }

  const titleError = fieldError("title");
  const descriptionError = fieldError("description");
  const dueDateError = fieldError("due_date");

  return (
    <form onSubmit={handleSubmit} className="space-y-4 border rounded-lg p-4">
      <div>
        <label
          htmlFor="task-title"
          className="block text-sm font-medium mb-1"
        >
          Title
        </label>
        <input
          id="task-title"
          type="text"
          required
          className={`w-full border rounded-md px-3 py-2 text-sm${titleError ? " border-red-500" : ""}`}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={() => markTouched("title")}
          placeholder="Task title..."
          aria-invalid={titleError ? true : undefined}
          aria-describedby={titleError ? "task-title-error" : undefined}
        />
        {titleError && (
          <p id="task-title-error" className="text-sm text-red-600 mt-1">
            {titleError}
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label
            htmlFor="task-type"
            className="block text-sm font-medium mb-1"
          >
            Type
          </label>
          <select
            id="task-type"
            className="w-full border rounded-md px-3 py-2 text-sm"
            value={type}
            onChange={(e) => setType(e.target.value as TaskType)}
          >
            {TASK_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label
            htmlFor="task-due"
            className="block text-sm font-medium mb-1"
          >
            Due Date
          </label>
          <input
            id="task-due"
            type="date"
            className={`w-full border rounded-md px-3 py-2 text-sm${dueDateError ? " border-red-500" : ""}`}
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            onBlur={() => markTouched("due_date")}
            aria-invalid={dueDateError ? true : undefined}
            aria-describedby={dueDateError ? "task-due-error" : undefined}
          />
          {dueDateError && (
            <p id="task-due-error" className="text-sm text-red-600 mt-1">
              {dueDateError}
            </p>
          )}
        </div>
      </div>

      <div>
        <label
          htmlFor="task-desc"
          className="block text-sm font-medium mb-1"
        >
          Description
        </label>
        <textarea
          id="task-desc"
          className={`w-full border rounded-md px-3 py-2 text-sm${descriptionError ? " border-red-500" : ""}`}
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onBlur={() => markTouched("description")}
          placeholder="Optional description..."
          aria-invalid={descriptionError ? true : undefined}
          aria-describedby={descriptionError ? "task-desc-error" : undefined}
        />
        {descriptionError && (
          <p id="task-desc-error" className="text-sm text-red-600 mt-1">
            {descriptionError}
          </p>
        )}
      </div>

      <div className="flex gap-2 justify-end">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isLoading || !isValid}
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          {isLoading ? "Adding..." : "Add Task"}
        </button>
      </div>
    </form>
  );
}
