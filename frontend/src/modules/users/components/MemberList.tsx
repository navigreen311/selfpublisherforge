"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  useCurrentUser,
  useOrgMembers,
  useChangeMemberRole,
  useRemoveMember,
  type OrgMember,
} from "../hooks";

const ROLES = ["owner", "admin", "editor", "writer", "viewer"] as const;

interface MemberListProps {
  orgId: string;
}

export function MemberList({ orgId }: MemberListProps) {
  const { data: currentUser } = useCurrentUser();
  const { data: members, isLoading } = useOrgMembers(orgId);
  const changeRole = useChangeMemberRole(orgId);
  const removeMember = useRemoveMember(orgId);
  const [confirmRemove, setConfirmRemove] = useState<string | null>(null);

  const isOwner = currentUser?.role === "owner";
  const isAdminOrOwner =
    currentUser?.role === "owner" || currentUser?.role === "admin";

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await changeRole.mutateAsync({ userId, role: newRole });
      toast.success("Role updated");
    } catch {
      toast.error("Failed to update role");
    }
  };

  const handleRemove = async (userId: string) => {
    try {
      await removeMember.mutateAsync(userId);
      toast.success("Member removed");
      setConfirmRemove(null);
    } catch {
      toast.error("Failed to remove member");
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-14 bg-gray-100 rounded" />
        ))}
      </div>
    );
  }

  if (!members?.length) {
    return (
      <p className="text-sm text-gray-500">No members found.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="pb-2 font-medium">Name</th>
            <th className="pb-2 font-medium">Email</th>
            <th className="pb-2 font-medium">Role</th>
            <th className="pb-2 font-medium">Joined</th>
            <th className="pb-2 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {members.map((member: OrgMember) => {
            const isSelf = member.user_id === currentUser?.id;
            return (
              <tr key={member.user_id} className="border-b last:border-0">
                <td className="py-3 pr-4">
                  <span className="font-medium">{member.name}</span>
                  {isSelf && (
                    <span className="ml-2 text-xs text-gray-400">(you)</span>
                  )}
                </td>
                <td className="py-3 pr-4 text-gray-600">{member.email}</td>
                <td className="py-3 pr-4">
                  {isOwner && !isSelf ? (
                    <select
                      value={member.role}
                      onChange={(e) =>
                        handleRoleChange(member.user_id, e.target.value)
                      }
                      className="rounded border border-gray-300 px-2 py-1 text-sm"
                    >
                      {ROLES.map((role) => (
                        <option key={role} value={role}>
                          {role}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs capitalize">
                      {member.role}
                    </span>
                  )}
                </td>
                <td className="py-3 pr-4 text-gray-500">
                  {new Date(member.joined_at).toLocaleDateString()}
                </td>
                <td className="py-3">
                  {isAdminOrOwner && !isSelf && member.role !== "owner" && (
                    <>
                      {confirmRemove === member.user_id ? (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleRemove(member.user_id)}
                            className="text-xs text-red-600 hover:text-red-800 font-medium"
                          >
                            Confirm
                          </button>
                          <button
                            onClick={() => setConfirmRemove(null)}
                            className="text-xs text-gray-500 hover:text-gray-700"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setConfirmRemove(member.user_id)}
                          className="text-xs text-red-500 hover:text-red-700"
                        >
                          Remove
                        </button>
                      )}
                    </>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
