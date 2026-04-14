"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import EmptyState from "@/components/shared/EmptyState";
import ErrorState from "@/components/shared/ErrorState";
import { FilterBar } from "@/components/shared/FilterBar";
import { useAuthStore } from "@/lib/store";
import {
  useRoles,
  useTeamMembers,
  useUpdateMemberRole,
  useRemoveMember,
  useDeleteRole,
} from "../hooks";
import { BUILT_IN_ROLE_ICONS } from "../permissions";
import { InviteMemberModal } from "./InviteMemberModal";
import { CustomRoleBuilderModal } from "./CustomRoleBuilderModal";
import type { Role, TeamMember } from "../types";

function roleLabel(role: Role | undefined): string {
  if (!role) return "Unknown";
  const icon = BUILT_IN_ROLE_ICONS[role.name];
  return icon ? `${icon} ${role.name}` : role.name;
}

function StatusBadge({ status }: { status?: TeamMember["status"] }) {
  const s = status ?? "active";
  const variants: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    invited: "bg-amber-100 text-amber-800",
    suspended: "bg-gray-100 text-gray-700",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${variants[s]}`}
    >
      {s.charAt(0).toUpperCase() + s.slice(1)}
    </span>
  );
}

export function TeamManagement() {
  const user = useAuthStore((s) => s.user);
  const orgId = user?.org_id;

  const {
    data: members = [],
    isLoading: membersLoading,
    error: membersError,
    refetch: refetchMembers,
  } = useTeamMembers(orgId);
  const {
    data: roles = [],
    isLoading: rolesLoading,
    error: rolesError,
    refetch: refetchRoles,
  } = useRoles();

  const updateRole = useUpdateMemberRole(orgId);
  const removeMember = useRemoveMember(orgId);
  const deleteRole = useDeleteRole();

  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [inviteOpen, setInviteOpen] = useState(false);
  const [roleBuilderOpen, setRoleBuilderOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | undefined>(undefined);

  const rolesById = useMemo(() => {
    const m = new Map<string, Role>();
    for (const r of roles) m.set(r.id, r);
    return m;
  }, [roles]);

  const filteredMembers = useMemo(() => {
    return members.filter((m) => {
      if (search) {
        const q = search.toLowerCase();
        if (
          !m.name?.toLowerCase().includes(q) &&
          !m.email?.toLowerCase().includes(q)
        )
          return false;
      }
      if (roleFilter && roleFilter !== "all") {
        if (m.role_id !== roleFilter && m.role !== roleFilter) return false;
      }
      return true;
    });
  }, [members, search, roleFilter]);

  const handleRoleChange = async (member: TeamMember, newRoleId: string) => {
    if (!member.id || newRoleId === member.role_id) return;
    try {
      await updateRole.mutateAsync({ userId: member.id, roleId: newRoleId });
      toast.success(`Updated role for ${member.name || member.email}`);
    } catch (err: any) {
      toast.error(err?.message || "Failed to update role");
    }
  };

  const handleRemove = async (member: TeamMember) => {
    if (
      !confirm(
        `Remove ${member.name || member.email} from the organization? This cannot be undone.`
      )
    )
      return;
    try {
      await removeMember.mutateAsync(member.id);
      toast.success("Member removed");
    } catch (err: any) {
      toast.error(err?.message || "Failed to remove member");
    }
  };

  const handleEditRole = (role: Role) => {
    setEditingRole(role);
    setRoleBuilderOpen(true);
  };

  const handleDeleteRole = async (role: Role) => {
    if (role.is_system) {
      toast.error("System roles cannot be deleted");
      return;
    }
    if (!confirm(`Delete role "${role.name}"?`)) return;
    try {
      await deleteRole.mutateAsync(role.id);
      toast.success(`Role "${role.name}" deleted`);
    } catch (err: any) {
      toast.error(err?.message || "Failed to delete role");
    }
  };

  const handleCreateRole = () => {
    setEditingRole(undefined);
    setRoleBuilderOpen(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Team Management</h2>
        <p className="text-sm text-muted-foreground">
          Invite teammates, manage their roles, and define custom permission sets.
        </p>
      </div>

      {/* Team Members */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Team Members</CardTitle>
          <Button
            size="sm"
            onClick={() => setInviteOpen(true)}
            disabled={!orgId || roles.length === 0}
          >
            + Invite Team Member
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <FilterBar
            searchPlaceholder="Search by name or email"
            onSearch={setSearch}
            statusOptions={[
              { value: "all", label: "All roles" },
              ...roles.map((r) => ({ value: r.id, label: r.name })),
            ]}
            onStatusChange={setRoleFilter}
            initialStatus={roleFilter}
          />

          {membersLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : membersError ? (
            <ErrorState
              message={(membersError as Error)?.message || "Failed to load members"}
              onRetry={() => refetchMembers()}
            />
          ) : filteredMembers.length === 0 ? (
            <EmptyState
              icon="👥"
              title="No team members yet"
              description="Invite teammates to collaborate on your publishing workflow."
              actionLabel="Invite Team Member"
              onAction={() => setInviteOpen(true)}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Member</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredMembers.map((member) => {
                  const memberRole = member.role_id
                    ? rolesById.get(member.role_id)
                    : roles.find((r) => r.name === member.role);
                  const isOwner = memberRole?.name === "Owner";
                  return (
                    <TableRow key={member.id}>
                      <TableCell className="font-medium">
                        {member.name || "—"}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {member.email}
                      </TableCell>
                      <TableCell>
                        {isOwner ? (
                          <Badge variant="secondary">
                            {roleLabel(memberRole)}
                          </Badge>
                        ) : (
                          <Select
                            value={memberRole?.id || ""}
                            onValueChange={(v) => handleRoleChange(member, v)}
                            disabled={updateRole.isPending || rolesLoading}
                          >
                            <SelectTrigger className="h-8 w-[180px]">
                              <SelectValue placeholder="Select role" />
                            </SelectTrigger>
                            <SelectContent>
                              {roles
                                .filter((r) => r.name !== "Owner")
                                .map((r) => (
                                  <SelectItem key={r.id} value={r.id}>
                                    {roleLabel(r)}
                                  </SelectItem>
                                ))}
                            </SelectContent>
                          </Select>
                        )}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={member.status} />
                      </TableCell>
                      <TableCell className="text-right">
                        {isOwner ? (
                          <span className="text-xs text-muted-foreground">—</span>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemove(member)}
                            disabled={removeMember.isPending}
                          >
                            Remove
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Roles */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Roles & Permissions</CardTitle>
          <Button size="sm" variant="outline" onClick={handleCreateRole}>
            + Create Custom Role
          </Button>
        </CardHeader>
        <CardContent>
          {rolesLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </div>
          ) : rolesError ? (
            <ErrorState
              message={(rolesError as Error)?.message || "Failed to load roles"}
              onRetry={() => refetchRoles()}
            />
          ) : roles.length === 0 ? (
            <EmptyState
              icon="🛡️"
              title="No roles defined"
              description="Create your first custom role to control team member access."
              actionLabel="Create Custom Role"
              onAction={handleCreateRole}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Role</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roles.map((role) => (
                  <TableRow key={role.id}>
                    <TableCell className="font-medium">
                      {roleLabel(role)}
                    </TableCell>
                    <TableCell className="max-w-md truncate text-muted-foreground">
                      {role.description || "—"}
                    </TableCell>
                    <TableCell>
                      {role.is_system ? (
                        <Badge variant="secondary">System</Badge>
                      ) : (
                        <Badge>Custom</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            Manage
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleEditRole(role)}>
                            {role.is_system ? "View permissions" : "Edit"}
                          </DropdownMenuItem>
                          {!role.is_system && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-red-600 focus:text-red-700"
                                onClick={() => handleDeleteRole(role)}
                              >
                                Delete
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <InviteMemberModal
        open={inviteOpen}
        onOpenChange={setInviteOpen}
        orgId={orgId}
        roles={roles.filter((r) => r.name !== "Owner")}
      />
      <CustomRoleBuilderModal
        open={roleBuilderOpen}
        onOpenChange={(o) => {
          setRoleBuilderOpen(o);
          if (!o) setEditingRole(undefined);
        }}
        role={editingRole}
      />
    </div>
  );
}
