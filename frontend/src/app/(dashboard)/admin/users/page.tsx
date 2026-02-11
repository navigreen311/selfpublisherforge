"use client";

import { UserTable } from "@/modules/admin/components/UserTable";

export default function AdminUsersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-foreground">User Management</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Manage user accounts, roles, and access permissions
        </p>
      </div>
      <UserTable />
    </div>
  );
}
