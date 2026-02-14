"use client";

import { useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useLaunchPlan, useUpdateLaunchPlan } from "@/modules/marketing/hooks";
import { LaunchPlanResults } from "@/modules/marketing/components/LaunchPlanResults";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "@/hooks/use-translations";

export default function LaunchPlanDetailPage() {
  const t = useTranslations("marketing");
  const params = useParams();
  const router = useRouter();
  const id = typeof params.id === "string" ? params.id : Array.isArray(params.id) ? params.id[0] : "";
  const { data: plan, isLoading, error } = useLaunchPlan(id);
  const updateMutation = useUpdateLaunchPlan(id);

  const handleStatusChange = useCallback(
    (newStatus: "draft" | "active" | "completed" | "archived") => {
      updateMutation.mutate({ status: newStatus });
    },
    [updateMutation]
  );

  const handleGenerateEmailSequence = useCallback(() => {
    router.push("/marketing/email");
  }, [router]);

  const handleGenerateSocialPosts = useCallback(() => {
    router.push("/marketing?tab=social");
  }, [router]);

  const handleCreateARCCampaign = useCallback(() => {
    router.push("/marketing?tab=arc");
  }, [router]);

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3" />
        <div className="h-4 bg-gray-200 rounded w-2/3" />
        <div className="h-64 bg-gray-200 rounded" />
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-bold text-gray-700">{t("launchPlanDetail.notFound")}</h2>
        <p className="text-gray-500 mt-2">
          {t("launchPlanDetail.notFoundMessage")}
        </p>
        <Link
          href="/marketing"
          className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          {t("launchPlanDetail.backToMarketing")}
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back to Marketing link */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/marketing" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Marketing
          </Link>
        </Button>
      </div>

      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500">
        <Link href="/marketing" className="hover:text-blue-600">
          {t("title")}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-700">{t("launchPlanDetail.breadcrumb")}</span>
      </nav>

      {/* Status Actions */}
      <div className="flex justify-end gap-2">
        {plan.status === "draft" && (
          <Button
            onClick={() => handleStatusChange("active")}
            variant="default"
            size="sm"
            className="bg-green-600 hover:bg-green-700"
          >
            {t("launchPlanDetail.activatePlan")}
          </Button>
        )}
        {plan.status === "active" && (
          <Button
            onClick={() => handleStatusChange("completed")}
            variant="default"
            size="sm"
          >
            {t("launchPlanDetail.markComplete")}
          </Button>
        )}
      </div>

      {/* Full LaunchPlanResults component */}
      <LaunchPlanResults
        plan={plan}
        onGenerateEmailSequence={handleGenerateEmailSequence}
        onGenerateSocialPosts={handleGenerateSocialPosts}
        onCreateARCCampaign={handleCreateARCCampaign}
      />
    </div>
  );
}
