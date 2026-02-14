"use client";

import { useDetailedPlatformStats } from "@/modules/admin/hooks";
import { SystemStats } from "@/modules/admin/components/SystemStats";
import { AuditLog } from "@/modules/admin/components/AuditLog";

export default function AdminOverviewPage() {
  const { data: stats, isLoading } = useDetailedPlatformStats();

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-xl font-semibold mb-4">Platform Statistics</h2>
        <SystemStats stats={stats} isLoading={isLoading} />
      </section>
      <section>
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <AuditLog />
      </section>
    </div>
  );
}
