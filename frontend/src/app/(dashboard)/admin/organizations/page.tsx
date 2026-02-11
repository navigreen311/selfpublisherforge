"use client";

import { OrgTable } from "@/modules/admin/components/OrgTable";

export default function AdminOrganizationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-foreground">Organization Management</h2>
        <p className="text-sm text-muted-foreground mt-1">
          View and manage organization accounts and subscription plans
        </p>
      </div>
      <OrgTable />
    </div>
  );
}
