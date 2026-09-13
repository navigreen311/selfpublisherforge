"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useTranslations } from "@/hooks/use-translations";
import { AnalyticsDashboard } from "@/modules/analytics/components/AnalyticsDashboard";
import { FileText } from "lucide-react";

export default function AnalyticsDashboardPage() {
  const t = useTranslations("analytics");

  return (
    <div className="space-y-4 sm:space-y-6 px-4 sm:px-6 lg:px-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-muted-foreground">{t("subtitle")}</p>
        </div>
        <nav aria-label="Analytics navigation" className="flex flex-col sm:flex-row gap-2">
          <Button variant="outline" size="sm" asChild className="w-full sm:w-auto">
            <Link href="/analytics/revenue" aria-label="View detailed revenue analytics">
              {t("navigation.revenueDetails")}
            </Link>
          </Button>
          <Button size="sm" asChild className="gap-1.5 w-full sm:w-auto">
            <Link href="/analytics/reports" aria-label="Generate analytics reports">
              <FileText className="h-4 w-4" />
              Generate Report
            </Link>
          </Button>
        </nav>
      </div>

      {/* Main Dashboard */}
      <AnalyticsDashboard />
    </div>
  );
}
