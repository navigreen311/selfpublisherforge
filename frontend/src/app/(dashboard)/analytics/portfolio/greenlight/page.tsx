"use client";

import { GreenlightScorer } from "@/modules/analytics/components/GreenlightScorer";
import Link from "next/link";
import { useTranslations } from "@/hooks/use-translations";

export default function GreenlightPage() {
  const t = useTranslations("analytics");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/analytics/portfolio"
            className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block"
          >
            {t("greenlight.backToPortfolio")}
          </Link>
          <h1 className="text-2xl font-bold text-foreground">{t("greenlight.title")}</h1>
          <p className="text-sm text-gray-600 mt-1">
            {t("greenlight.subtitle")}
          </p>
        </div>
        <Link
          href="/analytics/portfolio/audience"
          className="px-4 py-2 text-sm font-medium text-foreground bg-card border rounded-md hover:bg-muted"
        >
          {t("greenlight.audienceDna")}
        </Link>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">{t("greenlight.infoBannerTitle")}</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                {t("greenlight.infoBannerDescription")}
              </p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>{t("greenlight.infoListItem1")}</li>
                <li>{t("greenlight.infoListItem2")}</li>
                <li>{t("greenlight.infoListItem3")}</li>
                <li>{t("greenlight.infoListItem4")}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Greenlight Scorer Component */}
      <GreenlightScorer />

      {/* Tips Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-base font-semibold text-gray-900 mb-3">{t("greenlight.tipsTitle")}</h3>
        <div className="space-y-2 text-sm text-gray-700">
          <div className="flex items-start">
            <span className="text-green-600 mr-2 font-bold">✓</span>
            <p>{t("greenlight.tipRealistic")}</p>
          </div>
          <div className="flex items-start">
            <span className="text-green-600 mr-2 font-bold">✓</span>
            <p>{t("greenlight.tipResearch")}</p>
          </div>
          <div className="flex items-start">
            <span className="text-green-600 mr-2 font-bold">✓</span>
            <p>{t("greenlight.tipSeries")}</p>
          </div>
          <div className="flex items-start">
            <span className="text-green-600 mr-2 font-bold">✓</span>
            <p>{t("greenlight.tipTime")}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
