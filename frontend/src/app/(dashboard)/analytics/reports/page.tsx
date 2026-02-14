"use client";

import { EnhancedReportBuilder } from "@/modules/analytics/components/EnhancedReportBuilder";
import { useTranslations } from "@/hooks/use-translations";

export default function ReportsPage() {
  const t = useTranslations("analytics");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">
          {t("reports.title")}
        </h1>
        <a
          href="/analytics"
          aria-label={t("reports.backToDashboard")}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {t("reports.backToDashboard")}
        </a>
      </div>

      <EnhancedReportBuilder />
    </div>
  );
}
