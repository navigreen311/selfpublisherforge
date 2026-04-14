"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useCreateRole } from "../hooks";
import type { PermissionsMap, PermissionAction } from "../types";

const MODULES: string[] = [
  "dashboard",
  "projects",
  "market",
  "competitors",
  "reviews",
  "writing",
  "cover_design",
  "audiobook",
  "childrens_books",
  "coloring_books",
  "puzzle_books",
  "comic_books",
  "cookbooks",
  "style_profiles",
  "pipeline",
  "marketing",
  "publishing",
  "advertising",
  "analytics",
  "analytics_revenue",
  "pricing",
  "agents",
  "admin",
  "settings",
  "team",
  "billing",
  "pen_names",
];

const ACTIONS: PermissionAction[] = [
  "view",
  "create",
  "edit",
  "delete",
  "publish",
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const EMPTY_ROW = {
  view: false,
  create: false,
  edit: false,
  delete: false,
  publish: false,
};

export function CustomRoleModal({ open, onOpenChange }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [perms, setPerms] = useState<PermissionsMap>(() =>
    Object.fromEntries(MODULES.map((m) => [m, { ...EMPTY_ROW }]))
  );
  const create = useCreateRole();

  const toggle = (m: string, a: PermissionAction, v: boolean) => {
    setPerms((p) => ({
      ...p,
      [m]: { ...(p[m] ?? EMPTY_ROW), [a]: v },
    }));
  };

  const submit = async () => {
    if (!name.trim()) return;
    await create.mutateAsync({
      name: name.trim(),
      description: description || null,
      permissions: perms,
    });
    onOpenChange(false);
    setName("");
    setDescription("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Custom Role</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="role-name">Role Name *</Label>
            <Input
              id="role-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div>
            <Label htmlFor="role-desc">Description</Label>
            <Textarea
              id="role-desc"
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="p-2">Module</th>
                  {ACTIONS.map((a) => (
                    <th key={a} className="p-2 capitalize">
                      {a}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MODULES.map((m) => (
                  <tr key={m} className="border-b last:border-b-0">
                    <td className="p-2 font-mono text-xs">{m}</td>
                    {ACTIONS.map((a) => (
                      <td key={a} className="p-2">
                        <Checkbox
                          aria-label={`${m}-${a}`}
                          checked={!!perms[m]?.[a]}
                          onCheckedChange={(v) => toggle(m, a, !!v)}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={create.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={submit}
            disabled={create.isPending || !name.trim()}
          >
            {create.isPending && (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            )}
            Create Role
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
