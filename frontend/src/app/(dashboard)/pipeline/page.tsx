"use client";

import { useState } from "react";
import { usePipelines, useCreatePipeline } from "@/modules/pipeline/hooks";
import { PipelineCard } from "@/modules/pipeline/components/PipelineCard";
import type { PipelineStatus } from "@/modules/pipeline/hooks";

const STATUS_FILTERS: { label: string; value: PipelineStatus | undefined }[] = [
  { label: "All", value: undefined },
  { label: "Draft", value: "draft" },
  { label: "Active", value: "active" },
  { label: "Paused", value: "paused" },
  { label: "Completed", value: "completed" },
];

export default function PipelineDashboardPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<PipelineStatus | undefined>(
    undefined
  );
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newBookId, setNewBookId] = useState("");

  const { data, isLoading, error } = usePipelines(page, 20, statusFilter);
  const createMutation = useCreatePipeline();

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim() || !newBookId.trim()) return;
    createMutation.mutate(
      { name: newName.trim(), book_id: newBookId.trim() },
      {
        onSuccess: () => {
          setShowCreate(false);
          setNewName("");
          setNewBookId("");
        },
      }
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Production Pipeline</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          New Pipeline
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-6 border rounded-lg p-4 space-y-3"
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="pl-name" className="block text-sm font-medium mb-1">
                Pipeline Name
              </label>
              <input
                id="pl-name"
                type="text"
                required
                className="w-full border rounded-md px-3 py-2 text-sm"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. My Novel Production"
              />
            </div>
            <div>
              <label htmlFor="pl-book" className="block text-sm font-medium mb-1">
                Book ID
              </label>
              <input
                id="pl-book"
                type="text"
                required
                className="w-full border rounded-md px-3 py-2 text-sm"
                value={newBookId}
                onChange={(e) => setNewBookId(e.target.value)}
                placeholder="UUID of the book"
              />
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {createMutation.isPending ? "Creating..." : "Create"}
            </button>
          </div>
        </form>
      )}

      {/* Status filters */}
      <div className="flex gap-2 mb-6">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.label}
            onClick={() => {
              setStatusFilter(f.value);
              setPage(1);
            }}
            className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
              statusFilter === f.value
                ? "bg-primary text-primary-foreground"
                : "bg-white hover:bg-gray-50"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Pipeline grid */}
      {isLoading && (
        <p className="text-muted-foreground text-sm">Loading pipelines...</p>
      )}
      {error && (
        <p className="text-red-600 text-sm">
          Failed to load pipelines. Please try again.
        </p>
      )}
      {data && data.items.length === 0 && (
        <div className="text-center py-16">
          <p className="text-muted-foreground">
            No pipelines found. Create one to get started.
          </p>
        </div>
      )}
      {data && data.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {data.items.map((pipeline) => (
              <PipelineCard key={pipeline.id} pipeline={pipeline} />
            ))}
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1 text-sm border rounded-md disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-muted-foreground">
                Page {data.page} of {data.pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page >= data.pages}
                className="px-3 py-1 text-sm border rounded-md disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
