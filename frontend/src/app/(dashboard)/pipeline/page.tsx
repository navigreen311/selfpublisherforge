"use client";

import { useState } from "react";
import { usePipelines } from "@/modules/pipeline/hooks";
import { PipelineCard } from "@/modules/pipeline/components/PipelineCard";
import { CreatePipelineModal } from "@/modules/pipeline/components/CreatePipelineModal";
import { Skeleton } from "@/components/ui/skeleton";
import type { PipelineStatus } from "@/modules/pipeline/hooks";
import { useTranslations } from "@/hooks/use-translations";
import { Plus } from "lucide-react";

const STATUS_FILTERS: { label: string; value: PipelineStatus | undefined }[] = [
  { label: "filterAll", value: undefined },
  { label: "filterDraft", value: "draft" },
  { label: "filterActive", value: "active" },
  { label: "filterPaused", value: "paused" },
  { label: "filterCompleted", value: "completed" },
];

export default function PipelineDashboardPage() {
  const t = useTranslations("pipeline");
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<PipelineStatus | undefined>(
    undefined
  );
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data, isLoading, error } = usePipelines(page, 20, statusFilter);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          {t("newPipeline")}
        </button>
      </div>

      {/* Create pipeline modal */}
      <CreatePipelineModal
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
      />

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
                : "bg-card hover:bg-muted"
            }`}
          >
            {t(f.label)}
          </button>
        ))}
      </div>

      {/* Pipeline grid */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      )}
      {error && (
        <p className="text-red-600 text-sm">
          {t("failedToLoad")}
        </p>
      )}
      {data && data.items.length === 0 && (
        <div className="text-center py-16">
          <p className="text-muted-foreground">
            {t("noPipelines")}
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
                {t("previous")}
              </button>
              <span className="text-sm text-muted-foreground">
                {t("page", { page: data.page, pages: data.pages })}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page >= data.pages}
                className="px-3 py-1 text-sm border rounded-md disabled:opacity-50"
              >
                {t("next")}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
