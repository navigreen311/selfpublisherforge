"use client";

import { usePlatformStats } from "@/modules/admin/hooks";
import { SystemStats } from "@/modules/admin/components/SystemStats";
import { AuditLog } from "@/modules/admin/components/AuditLog";

export default function AdminOverviewPage() {
  const { data: stats, isLoading } = usePlatformStats();

  return (
    <div className="space-y-8">
      {/* Platform Statistics */}
      <section>
        <h2 className="text-xl font-semibold text-foreground mb-4">Platform Statistics</h2>
        <SystemStats stats={stats} isLoading={isLoading} />
      </section>

      {/* Recent Activity */}
      <section>
        <h2 className="text-xl font-semibold text-foreground mb-4">Recent Activity</h2>
        <AuditLog />
      </section>
    </div>
  );
}
