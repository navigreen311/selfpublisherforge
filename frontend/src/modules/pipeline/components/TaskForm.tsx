"use client";

import { useState } from "react";
import type { TaskType } from "../hooks";

const TASK_TYPES: TaskType[] = [
  "writing",
  "editing",
  "proofreading",
  "formatting",
  "review",
];

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

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    onSubmit({ title: title.trim(), type, description, due_date: dueDate });
    setTitle("");
    setDescription("");
    setDueDate("");
  }

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
          className="w-full border rounded-md px-3 py-2 text-sm"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Task title..."
        />
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
            className="w-full border rounded-md px-3 py-2 text-sm"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
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
          className="w-full border rounded-md px-3 py-2 text-sm"
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description..."
        />
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
          disabled={isLoading || !title.trim()}
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          {isLoading ? "Adding..." : "Add Task"}
        </button>
      </div>
    </form>
  );
}
