"use client";

import { useRouter } from "next/navigation";
import { Plus, Palette } from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import { CoverGallery } from "@/modules/cover-design/components/CoverGallery";
import { useCovers } from "@/modules/cover-design/hooks";

export default function CoverDesignPage() {
  const t = useTranslations("cover-design");
  const router = useRouter();
  const { data: covers, isPending } = useCovers();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Palette className="h-6 w-6 text-primary" aria-hidden="true" />
          <h1 className="text-2xl font-bold">{t("title")}</h1>
        </div>
        <button
          onClick={() => router.push("/cover-design/new")}
          aria-label={t("generateNewCover")}
          className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          {t("generateCover")}
        </button>
      </div>

      {/* Description */}
      <p className="text-muted-foreground">
        {t("description")}
      </p>

      {/* Cover gallery */}
      <CoverGallery
        covers={covers || []}
        isLoading={isPending}
        emptyMessage={t("noCoverMessage")}
      />
    </div>
  );
}
