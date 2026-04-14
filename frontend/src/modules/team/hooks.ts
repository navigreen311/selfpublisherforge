"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Invitation,
  InvitationInput,
  PermissionAction,
  Role,
  RoleInput,
  TeamMember,
} from "./types";

export type * from "./types";

const BASE = "/api/v1";

export const teamKeys = {
  all: ["team"] as const,
  team: () => [...teamKeys.all, "members"] as const,
  roles: () => [...teamKeys.all, "roles"] as const,
  role: (id: string) => [...teamKeys.all, "role", id] as const,
  invitations: () => [...teamKeys.all, "invitations"] as const,
};

// Roles ----------------------------------------------------------------------

export function useRoles() {
  return useQuery<Role[]>({
    queryKey: teamKeys.roles(),
    queryFn: async () => (await api.get(`${BASE}/roles`)).data,
  });
}

export function useCreateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: RoleInput) =>
      (await api.post(`${BASE}/roles`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: teamKeys.roles() }),
  });
}

export function useUpdateRole(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: Partial<RoleInput>) =>
      (await api.patch(`${BASE}/roles/${id}`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: teamKeys.roles() }),
  });
}

export function useDeleteRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      (await api.delete(`${BASE}/roles/${id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: teamKeys.roles() }),
  });
}

// Team members ---------------------------------------------------------------

export function useTeam() {
  return useQuery<TeamMember[]>({
    queryKey: teamKeys.team(),
    queryFn: async () => (await api.get(`${BASE}/team`)).data,
  });
}

export function useAssignRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      userId,
      roleId,
    }: {
      userId: string;
      roleId: string;
    }) =>
      (
        await api.patch(`${BASE}/team/${userId}/role`, {
          role_id: roleId,
        })
      ).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: teamKeys.team() }),
  });
}

export function useRemoveMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) =>
      (await api.delete(`${BASE}/team/${userId}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: teamKeys.team() }),
  });
}

// Invitations ----------------------------------------------------------------

export function useInvitations() {
  return useQuery<Invitation[]>({
    queryKey: teamKeys.invitations(),
    queryFn: async () => (await api.get(`${BASE}/team/invitations`)).data,
  });
}

export function useInvite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: InvitationInput) =>
      (await api.post(`${BASE}/team/invite`, body)).data,
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: teamKeys.invitations() }),
  });
}

export function useResendInvite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      (await api.post(`${BASE}/team/invite/${id}/resend`)).data,
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: teamKeys.invitations() }),
  });
}

// UI permission helper -------------------------------------------------------

/**
 * Look up whether the current user's role allows a particular action on a
 * module. Falls back to "deny" while roles are still loading.
 */
export function useCanI(
  module: string,
  action: PermissionAction,
  currentRoleName: string | null | undefined
) {
  const { data: roles = [] } = useRoles();
  if (!currentRoleName) return false;
  const role = roles.find((r) => r.name === currentRoleName);
  return !!role?.permissions?.[module]?.[action];
}
