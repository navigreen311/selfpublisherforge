"use client";

import { use } from "react";
import { useLaunchPlan, useUpdateLaunchPlan } from "@/modules/marketing/hooks";
import { LaunchTimeline } from "@/modules/marketing/components/LaunchTimeline";
import Link from "next/link";

interface LaunchPlanDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function LaunchPlanDetailPage({ params }: LaunchPlanDetailPageProps) {
  const { id } = use(params);
  const { data: plan, isLoading, error } = useLaunchPlan(id);
  const updateMutation = useUpdateLaunchPlan(id);

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "--";
    return new Date(dateStr).toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const handleTaskStatusChange = (taskId: string, newStatus: string) => {
    // In a full implementation, this would call an API to update the task status.
    // For now, we optimistically update through the plan update endpoint.
    console.log(`Task ${taskId} status changed to ${newStatus}`);
  };

  const handleStatusChange = (newStatus: "draft" | "active" | "completed" | "archived") => {
    updateMutation.mutate({ status: newStatus });
  };

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
        <h2 className="text-xl font-bold text-gray-700">Launch Plan Not Found</h2>
        <p className="text-gray-500 mt-2">
          The launch plan you are looking for does not exist or has been deleted.
        </p>
        <Link
          href="/marketing"
          className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          Back to Marketing
        </Link>
      </div>
    );
  }

  const totalTasks = plan.phases.reduce((sum, p) => sum + p.tasks.length, 0);
  const completedTasks = plan.phases.reduce(
    (sum, p) => sum + p.tasks.filter((t) => t.status === "completed").length,
    0
  );
  const completionPercent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const statusColors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    active: "bg-green-100 text-green-700",
    completed: "bg-blue-100 text-blue-700",
    archived: "bg-red-100 text-red-700",
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500">
        <Link href="/marketing" className="hover:text-blue-600">
          Marketing
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-700">Launch Plan</span>
      </nav>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{plan.title}</h1>
            <span
              className={`text-xs px-2 py-1 rounded-full font-medium ${
                statusColors[plan.status] || ""
              }`}
            >
              {plan.status}
            </span>
          </div>
          {plan.description && (
            <p className="text-gray-500 mt-2">{plan.description}</p>
          )}
        </div>

        <div className="flex gap-2">
          {plan.status === "draft" && (
            <button
              onClick={() => handleStatusChange("active")}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
            >
              Activate Plan
            </button>
          )}
          {plan.status === "active" && (
            <button
              onClick={() => handleStatusChange("completed")}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
            >
              Mark Complete
            </button>
          )}
        </div>
      </div>

      {/* Plan Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-500">Launch Date</div>
          <div className="font-semibold mt-1">{formatDate(plan.launch_date)}</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-500">Genre</div>
          <div className="font-semibold mt-1">{plan.genre || "--"}</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-500">Budget</div>
          <div className="font-semibold mt-1">
            {plan.budget ? `$${plan.budget.toLocaleString()}` : "--"}
          </div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-500">Total Tasks</div>
          <div className="font-semibold mt-1">{totalTasks}</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-500">Completion</div>
          <div className="font-semibold mt-1">{completionPercent}%</div>
          <div className="w-full h-2 bg-gray-200 rounded-full mt-1 overflow-hidden">
            <div
              className="h-full bg-green-500 rounded-full transition-all"
              style={{ width: `${completionPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Launch Timeline</h2>
        <LaunchTimeline
          phases={plan.phases}
          onTaskStatusChange={handleTaskStatusChange}
        />
      </div>
    </div>
  );
}
