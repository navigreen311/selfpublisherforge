"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { User, Organization, PaginatedResponse } from "@/types";
import type {
  UserProfile,
  Session,
  OrgDetails,
  OrgMember,
  ApiKey,
} from "./types";

export type * from "./types";

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const userKeys = {
  me: ["users", "me"] as const,
  sessions: ["users", "me", "sessions"] as const,
  org: (id: string) => ["orgs", id] as const,
  members: (orgId: string) => ["orgs", orgId, "members"] as const,
  apiKeys: (orgId: string) => ["orgs", orgId, "api-keys"] as const,
};

// ─── User Profile Hooks ──────────────────────────────────────────────────────

export function useCurrentUser() {
  return useQuery({
    queryKey: userKeys.me,
    queryFn: async () => {
      const { data } = await api.get<UserProfile>("/api/v1/users/me");
      return data;
    },
  });
}

export function useUpdateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      name?: string;
      avatar_url?: string | null;
      preferences?: Record<string, unknown>;
    }) => {
      const { data } = await api.patch<UserProfile>("/api/v1/users/me", body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.me });
    },
  });
}

export function useUpdatePreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (preferences: Record<string, unknown>) => {
      const { data } = await api.patch<UserProfile>(
        "/api/v1/users/me/preferences",
        { preferences }
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.me });
    },
  });
}

export function useDeleteAccount() {
  return useMutation({
    mutationFn: async (password: string) => {
      await api.post("/api/v1/users/me/delete", { password });
    },
  });
}

// ─── Sessions Hooks ──────────────────────────────────────────────────────────

export function useSessions() {
  return useQuery({
    queryKey: userKeys.sessions,
    queryFn: async () => {
      const { data } = await api.get<Session[]>("/api/v1/users/me/sessions");
      return data;
    },
  });
}

export function useRevokeSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: string) => {
      await api.delete(`/api/v1/users/me/sessions/${sessionId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.sessions });
    },
  });
}

// ─── Organization Hooks ──────────────────────────────────────────────────────

export function useOrg(orgId: string) {
  return useQuery({
    queryKey: userKeys.org(orgId),
    queryFn: async () => {
      const { data } = await api.get<OrgDetails>(`/api/v1/orgs/${orgId}`);
      return data;
    },
    enabled: !!orgId,
  });
}

export function useUpdateOrg(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      name?: string;
      slug?: string;
      logo_url?: string | null;
    }) => {
      const { data } = await api.patch<OrgDetails>(
        `/api/v1/orgs/${orgId}`,
        body
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.org(orgId) });
    },
  });
}

export function useOrgMembers(orgId: string) {
  return useQuery({
    queryKey: userKeys.members(orgId),
    queryFn: async () => {
      const { data } = await api.get<OrgMember[]>(
        `/api/v1/orgs/${orgId}/members`
      );
      return data;
    },
    enabled: !!orgId,
  });
}

export function useInviteMember(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { email: string; role: string }) => {
      const { data } = await api.post(`/api/v1/orgs/${orgId}/invite`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.members(orgId) });
    },
  });
}

export function useChangeMemberRole(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      userId,
      role,
    }: {
      userId: string;
      role: string;
    }) => {
      const { data } = await api.patch(
        `/api/v1/orgs/${orgId}/members/${userId}/role`,
        { role }
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.members(orgId) });
    },
  });
}

export function useRemoveMember(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      await api.delete(`/api/v1/orgs/${orgId}/members/${userId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.members(orgId) });
    },
  });
}

// ─── API Keys Hooks ──────────────────────────────────────────────────────────

export function useApiKeys(orgId: string) {
  return useQuery({
    queryKey: userKeys.apiKeys(orgId),
    queryFn: async () => {
      const { data } = await api.get<ApiKey[]>(
        `/api/v1/orgs/${orgId}/api-keys`
      );
      return data;
    },
    enabled: !!orgId,
  });
}

export function useCreateApiKey(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      name: string;
      scopes?: string[];
      expires_in_days?: number | null;
    }) => {
      const { data } = await api.post<ApiKey>(
        `/api/v1/orgs/${orgId}/api-keys`,
        body
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.apiKeys(orgId) });
    },
  });
}

export function useRevokeApiKey(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (keyId: string) => {
      await api.delete(`/api/v1/orgs/${orgId}/api-keys/${keyId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.apiKeys(orgId) });
    },
  });
}
