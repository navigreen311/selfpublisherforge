"use client";

import { useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Trash2, Wand2 } from "lucide-react";
import { CoverPreview } from "@/modules/cover-design/components/CoverPreview";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useCover,
  useDeleteCover,
  useGenerateVariations,
} from "@/modules/cover-design/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslations } from "@/hooks/use-translations";

export default function CoverDetailPage() {
  const router = useRouter();
  const params = useParams();
  const coverId = params?.id as string;
  const t = useTranslations("cover-design");

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [variationsOpen, setVariationsOpen] = useState(false);
  const [variationCount, setVariationCount] = useState(3);

  const { data: cover, isPending } = useCover(coverId);
  const deleteMutation = useDeleteCover();
  const variationsMutation = useGenerateVariations(coverId);

  const handleDelete = useCallback(async () => {
    await deleteMutation.mutateAsync(coverId);
    router.push("/cover-design");
  }, [coverId, deleteMutation, router]);

  const handleGenerateVariations = useCallback(async () => {
    await variationsMutation.mutateAsync({
      variation_count: variationCount,
      variation_type: "style",
    });
    setVariationsOpen(false);
  }, [variationCount, variationsMutation]);

  if (isPending) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-lg" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Skeleton className="aspect-[2/3] w-full" />
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-6 w-1/2" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (!cover) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">{t("detail.notFound")}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            aria-label={t("detail.goBack")}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold">{t("detail.title")}</h1>
            <p className="text-sm text-muted-foreground">
              {t("detail.subtitle")}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setVariationsOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-accent transition-colors"
          >
            <Wand2 className="h-4 w-4" />
            {t("detail.generateVariations")}
          </button>
          <button
            onClick={() => setDeleteOpen(true)}
            aria-label={t("detail.deleteLabel")}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-destructive text-destructive rounded-lg hover:bg-destructive/10 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            {t("detail.delete")}
          </button>
        </div>
      </div>

      {/* Cover preview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <CoverPreview cover={cover} />
        </div>
        <div className="space-y-6">
          <div className="p-6 border rounded-lg bg-card">
            <h2 className="text-lg font-semibold mb-4">{t("detail.coverInfo")}</h2>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="font-medium">{t("detail.status")}</dt>
                <dd className="text-muted-foreground capitalize">
                  {cover.status}
                </dd>
              </div>
              <div>
                <dt className="font-medium">{t("detail.created")}</dt>
                <dd className="text-muted-foreground">
                  {new Date(cover.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="font-medium">{t("detail.lastUpdated")}</dt>
                <dd className="text-muted-foreground">
                  {new Date(cover.updated_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>

          {cover.metadata && Object.keys(cover.metadata).length > 0 && (
            <div className="p-6 border rounded-lg bg-card">
              <h2 className="text-lg font-semibold mb-4">{t("detail.metadata")}</h2>
              <pre className="text-xs bg-muted p-3 rounded overflow-auto">
                {JSON.stringify(cover.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title={t("detail.deleteConfirmTitle")}
        description={t("detail.deleteConfirmMessage", { title: cover.title })}
        confirmLabel={t("detail.delete")}
        cancelLabel={t("detail.cancel")}
        variant="destructive"
        onConfirm={handleDelete}
        onCancel={() => setDeleteOpen(false)}
        loading={deleteMutation.isPending}
      />

      {/* Variations dialog */}
      {variationsOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="variations-dialog-title"
        >
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setVariationsOpen(false)}
            aria-label={t("detail.closeDialog")}
          />
          <div className="relative bg-background border rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
            <h2 id="variations-dialog-title" className="text-lg font-semibold mb-4">
              {t("detail.generateVariations")}
            </h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="variation-count" className="block text-sm font-medium mb-2">
                  {t("detail.numberOfVariations")}
                </label>
                <input
                  id="variation-count"
                  type="number"
                  min="1"
                  max="10"
                  value={variationCount}
                  onChange={(e) => setVariationCount(Number(e.target.value))}
                  className="w-full border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setVariationsOpen(false)}
                  className="px-4 py-2 text-sm border rounded-lg hover:bg-accent"
                >
                  {t("detail.cancel")}
                </button>
                <button
                  onClick={handleGenerateVariations}
                  disabled={variationsMutation.isPending}
                  className="px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {variationsMutation.isPending ? t("detail.generating") : t("detail.generate")}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
