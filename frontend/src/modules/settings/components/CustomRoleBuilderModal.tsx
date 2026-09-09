"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  PERMISSION_ACTIONS,
  PERMISSION_MODULES,
  MODULE_CATEGORIES,
  emptyPermissions,
} from "../permissions";
import { useCreateRole, useUpdateRole } from "../hooks";
import type { PermissionAction, Role, RolePermissions } from "../types";

interface CustomRoleBuilderModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** If provided, the modal is in edit mode. */
  role?: Role;
}

export function CustomRoleBuilderModal({
  open,
  onOpenChange,
  role,
}: CustomRoleBuilderModalProps) {
  const isEditMode = !!role;
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [permissions, setPermissions] = useState<RolePermissions>(() =>
    emptyPermissions()
  );

  const createRole = useCreateRole();
  const updateRole = useUpdateRole();
  const isPending = createRole.isPending || updateRole.isPending;

  // Reset / load form state when dialog opens
  useEffect(() => {
    if (open) {
      if (role) {
        setName(role.name);
        setDescription(role.description || "");
        // Merge server permissions on top of empty scaffold so new modules default false
        const merged = emptyPermissions();
        for (const modKey of Object.keys(role.permissions || {})) {
          merged[modKey] = { ...(merged[modKey] || {}), ...role.permissions[modKey] };
        }
        setPermissions(merged);
      } else {
        setName("");
        setDescription("");
        setPermissions(emptyPermissions());
      }
    }
  }, [open, role]);

  const modulesByCategory = useMemo(() => {
    const map: Record<string, typeof PERMISSION_MODULES> = {};
    for (const cat of MODULE_CATEGORIES) map[cat] = [];
    for (const mod of PERMISSION_MODULES) map[mod.category].push(mod);
    return map;
  }, []);

  const togglePermission = (
    moduleKey: string,
    action: PermissionAction,
    value: boolean
  ) => {
    setPermissions((prev) => ({
      ...prev,
      [moduleKey]: { ...(prev[moduleKey] || {}), [action]: value },
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Role name is required");
      return;
    }
    try {
      if (isEditMode && role) {
        await updateRole.mutateAsync({
          id: role.id,
          data: {
            name: name.trim(),
            description: description.trim() || undefined,
            permissions,
          },
        });
        toast.success(`Role "${name}" updated`);
      } else {
        await createRole.mutateAsync({
          name: name.trim(),
          description: description.trim() || undefined,
          permissions,
        });
        toast.success(`Role "${name}" created`);
      }
      onOpenChange(false);
    } catch (err: any) {
      toast.error(err?.message || "Failed to save role");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "Edit Role" : "Create Custom Role"}
          </DialogTitle>
          <DialogDescription>
            Configure the module-level permissions for this role.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="role-name">
                Role Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="role-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Cookbook Editor"
                required
                disabled={role?.is_system}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role-description">Description</Label>
              <Input
                id="role-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Can edit cookbook recipes and illustrations"
                disabled={role?.is_system}
              />
            </div>
          </div>

          {role?.is_system && (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
              System roles cannot be modified. View-only.
            </div>
          )}

          <div className="space-y-2">
            <Label>Permissions</Label>
            <ScrollArea className="h-[420px] rounded-md border">
              <div className="divide-y">
                {/* Header row */}
                <div className="sticky top-0 grid grid-cols-[minmax(180px,2fr)_repeat(5,80px)] items-center gap-2 bg-gray-50 px-4 py-2 text-xs font-medium uppercase tracking-wide text-gray-600">
                  <div>Module</div>
                  {PERMISSION_ACTIONS.map((a) => (
                    <div key={a} className="text-center capitalize">
                      {a}
                    </div>
                  ))}
                </div>

                {MODULE_CATEGORIES.map((cat) => (
                  <div key={cat}>
                    <div className="bg-gray-50/60 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">
                      {cat}
                    </div>
                    {modulesByCategory[cat].map((mod) => (
                      <div
                        key={mod.key}
                        className="grid grid-cols-[minmax(180px,2fr)_repeat(5,80px)] items-center gap-2 px-4 py-2 text-sm hover:bg-gray-50"
                      >
                        <div className="font-medium">{mod.label}</div>
                        {PERMISSION_ACTIONS.map((action) => {
                          const applicable = mod.actions.includes(action);
                          if (!applicable) {
                            return (
                              <div
                                key={action}
                                className="text-center text-gray-300"
                                aria-hidden
                              >
                                —
                              </div>
                            );
                          }
                          const checked =
                            permissions[mod.key]?.[action] ?? false;
                          const id = `perm-${mod.key}-${action}`;
                          return (
                            <div
                              key={action}
                              className="flex items-center justify-center"
                            >
                              <Checkbox
                                id={id}
                                checked={checked}
                                disabled={role?.is_system}
                                onCheckedChange={(v) =>
                                  togglePermission(mod.key, action, !!v)
                                }
                                aria-label={`${mod.label} ${action}`}
                              />
                            </div>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || role?.is_system}>
              {isPending
                ? "Saving..."
                : isEditMode
                  ? "Save Changes"
                  : "Create Role"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
