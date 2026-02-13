"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  PlatformStats,
  AdminUser,
  AdminOrganization,
  AuditLogEntry,
  UserFilters,
  OrgFilters,
  AuditLogFilters,
  PaginatedResponse,
} from "./types";

export type * from "./types";

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const adminKeys = {
  stats: ["admin", "stats"] as const,
  users: (filters: UserFilters, page: number) => ["admin", "users", filters, page] as const,
  orgs: (filters: OrgFilters, page: number) => ["admin", "orgs", filters, page] as const,
  auditLog: (filters: AuditLogFilters, page: number) => ["admin", "audit-log", filters, page] as const,
};

// ─── Platform Stats Hooks ────────────────────────────────────────────────────

export function usePlatformStats() {
  return useQuery({
    queryKey: adminKeys.stats,
    queryFn: async () => {
      const { data } = await api.get<PlatformStats>("/api/v1/admin/stats");
      return data;
    },
  });
}

// ─── User Management Hooks ───────────────────────────────────────────────────

export function useAdminUsers(filters: UserFilters = {}, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: adminKeys.users(filters, page),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.search) params.append("search", filters.search);
      if (filters.role) params.append("role", filters.role);
      if (filters.is_active !== undefined) params.append("is_active", String(filters.is_active));
      if (filters.is_banned !== undefined) params.append("is_banned", String(filters.is_banned));
      params.append("page", String(page));
      params.append("page_size", String(pageSize));

      const { data } = await api.get<PaginatedResponse<AdminUser>>(
        `/api/v1/admin/users?${params.toString()}`
      );
      return data;
    },
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      userId,
      updates,
    }: {
      userId: string;
      updates: { role?: string; is_banned?: boolean };
    }) => {
      const { data } = await api.patch<AdminUser>(
        `/api/v1/admin/users/${userId}`,
        updates
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
      qc.invalidateQueries({ queryKey: adminKeys.stats });
    },
  });
}

// ─── Organization Management Hooks ───────────────────────────────────────────

export function useAdminOrgs(filters: OrgFilters = {}, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: adminKeys.orgs(filters, page),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.search) params.append("search", filters.search);
      if (filters.plan_tier) params.append("plan_tier", filters.plan_tier);
      if (filters.subscription_status) params.append("subscription_status", filters.subscription_status);
      params.append("page", String(page));
      params.append("page_size", String(pageSize));

      const { data } = await api.get<PaginatedResponse<AdminOrganization>>(
        `/api/v1/admin/organizations?${params.toString()}`
      );
      return data;
    },
  });
}

// ─── Audit Log Hooks ─────────────────────────────────────────────────────────

export function useAuditLog(filters: AuditLogFilters = {}, page = 1, pageSize = 50) {
  return useQuery({
    queryKey: adminKeys.auditLog(filters, page),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.user_id) params.append("user_id", filters.user_id);
      if (filters.action) params.append("action", filters.action);
      if (filters.resource_type) params.append("resource_type", filters.resource_type);
      if (filters.start_date) params.append("start_date", filters.start_date);
      if (filters.end_date) params.append("end_date", filters.end_date);
      params.append("page", String(page));
      params.append("page_size", String(pageSize));

      const { data } = await api.get<PaginatedResponse<AuditLogEntry>>(
        `/api/v1/admin/audit-log?${params.toString()}`
      );
      return data;
    },
  });
}
