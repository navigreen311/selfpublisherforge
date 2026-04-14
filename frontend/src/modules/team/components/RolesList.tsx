"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDeleteRole, useRoles } from "../hooks";
import { CustomRoleModal } from "./CustomRoleModal";

export function RolesList() {
  const { data: roles = [] } = useRoles();
  const [open, setOpen] = useState(false);
  const del = useDeleteRole();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-medium">Roles & Permissions</h3>
          <p className="text-sm text-muted-foreground">
            Built-in roles cannot be modified. Create custom roles for your team.
          </p>
        </div>
        <Button size="sm" variant="outline" onClick={() => setOpen(true)}>
          + Create Custom Role
        </Button>
      </div>
      <div className="space-y-2">
        {roles.map((r) => (
          <div
            key={r.id}
            className="flex items-center justify-between rounded-md border p-3"
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium">{r.name}</span>
                {r.is_system && <Badge variant="secondary">Built-in</Badge>}
              </div>
              {r.description && (
                <p className="text-xs text-muted-foreground mt-0.5">
                  {r.description}
                </p>
              )}
            </div>
            {!r.is_system && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  if (confirm(`Delete role "${r.name}"?`)) del.mutate(r.id);
                }}
              >
                Delete
              </Button>
            )}
          </div>
        ))}
      </div>
      <CustomRoleModal open={open} onOpenChange={setOpen} />
    </div>
  );
}
