"use client";

import { AlertTriangle } from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";
import { BackOfBookOptimizer } from "./BackOfBookOptimizer";
import { ARCManager } from "./ARCManager";
import { EmailSequenceBuilder } from "./EmailSequenceBuilder";

interface ReviewAcquisitionProps {
  bookId?: string;
}

export function ReviewAcquisition({ bookId }: ReviewAcquisitionProps) {
  const t = useTranslations("reviews");

  return (
    <div className="space-y-6">
      {/* Section 1: Back-of-Book Optimizer */}
      <BackOfBookOptimizer bookId={bookId} />

      {/* Section 2: ARC Manager */}
      <ARCManager bookId={bookId} />

      {/* Section 3: Email Sequence Builder */}
      <EmailSequenceBuilder bookId={bookId} />

      {/* Amazon Compliance Notice */}
      <div className="flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-700 dark:bg-amber-950/30">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
        <div className="space-y-1">
          <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
            {t("acquisition.complianceTitle")}
          </p>
          <p className="text-sm text-amber-700 dark:text-amber-400">
            {t("acquisition.complianceNote")}
          </p>
        </div>
      </div>
    </div>
  );
}
