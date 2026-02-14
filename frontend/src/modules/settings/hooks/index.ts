"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  OrgSettings,
  OrgSettingsUpdate,
  ChangePasswordPayload,
  SessionInfo,
  LoginHistoryEntry,
  ApiKey,
  ApiKeyCreatePayload,
  ApiKeyCreated,
  Webhook,
  WebhookCreatePayload,
  WebhookUpdate,
  NotificationPrefs,
  NotificationPrefsUpdate,
  SettingsBilling,
} from "../types";

export type * from "../types";

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const settingsKeys = {
  org: ["settings", "org"] as const,
  security: ["settings", "security"] as const,
  sessions: ["settings", "sessions"] as const,
  loginHistory: ["settings", "login-history"] as const,
  apiKeys: ["settings", "api-keys"] as const,
  webhooks: ["settings", "webhooks"] as const,
  notifications: ["settings", "notifications"] as const,
  billing: ["settings", "billing"] as const,
};

// ─── Organization Settings Hooks ─────────────────────────────────────────────

export function useOrgSettings() {
  return useQuery({
    queryKey: settingsKeys.org,
    queryFn: async () => {
      const { data } = await api.get<OrgSettings>("/api/v1/settings/organization");
      return data;
    },
  });
}

export function useUpdateOrgSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: OrgSettingsUpdate) => {
      const { data } = await api.patch<OrgSettings>(
        "/api/v1/settings/organization",
        body
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.org });
    },
  });
}

// ─── Security Hooks ──────────────────────────────────────────────────────────

export function useChangePassword() {
  return useMutation({
    mutationFn: async (body: ChangePasswordPayload) => {
      await api.post("/api/v1/settings/security/change-password", body);
    },
  });
}

export function useSessions() {
  return useQuery({
    queryKey: settingsKeys.sessions,
    queryFn: async () => {
      const { data } = await api.get<SessionInfo[]>("/api/v1/settings/security/sessions");
      return data;
    },
  });
}

export function useRevokeSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: string) => {
      await api.delete(`/api/v1/settings/security/sessions/${sessionId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.sessions });
    },
  });
}

export function useLoginHistory() {
  return useQuery({
    queryKey: settingsKeys.loginHistory,
    queryFn: async () => {
      const { data } = await api.get<LoginHistoryEntry[]>(
        "/api/v1/settings/security/login-history"
      );
      return data;
    },
  });
}

export function useEnable2FA() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<{ qr_code: string; secret: string }>(
        "/api/v1/settings/security/2fa/enable"
      );
      return data;
    },
  });
}

export function useVerify2FA() {
  return useMutation({
    mutationFn: async (code: string) => {
      await api.post("/api/v1/settings/security/2fa/verify", { code });
    },
  });
}

export function useDisable2FA() {
  return useMutation({
    mutationFn: async (password: string) => {
      await api.post("/api/v1/settings/security/2fa/disable", { password });
    },
  });
}

// ─── API Keys Hooks ──────────────────────────────────────────────────────────

export function useApiKeys() {
  return useQuery({
    queryKey: settingsKeys.apiKeys,
    queryFn: async () => {
      const { data } = await api.get<ApiKey[]>("/api/v1/settings/api-keys");
      return data;
    },
  });
}

export function useCreateApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: ApiKeyCreatePayload) => {
      const { data } = await api.post<ApiKeyCreated>(
        "/api/v1/settings/api-keys",
        body
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.apiKeys });
    },
  });
}

export function useRevokeApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (keyId: string) => {
      await api.delete(`/api/v1/settings/api-keys/${keyId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.apiKeys });
    },
  });
}

// ─── Webhooks Hooks ──────────────────────────────────────────────────────────

export function useWebhooks() {
  return useQuery({
    queryKey: settingsKeys.webhooks,
    queryFn: async () => {
      const { data } = await api.get<Webhook[]>("/api/v1/settings/webhooks");
      return data;
    },
  });
}

export function useCreateWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: WebhookCreatePayload) => {
      const { data } = await api.post<Webhook>("/api/v1/settings/webhooks", body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.webhooks });
    },
  });
}

export function useUpdateWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...body }: WebhookUpdate & { id: string }) => {
      const { data } = await api.patch<Webhook>(
        `/api/v1/settings/webhooks/${id}`,
        body
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.webhooks });
    },
  });
}

export function useDeleteWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/settings/webhooks/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.webhooks });
    },
  });
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/api/v1/settings/webhooks/${id}/test`);
    },
  });
}

// ─── Notifications Hooks ─────────────────────────────────────────────────────

export function useNotificationPrefs() {
  return useQuery({
    queryKey: settingsKeys.notifications,
    queryFn: async () => {
      const { data } = await api.get<NotificationPrefs>(
        "/api/v1/settings/notifications"
      );
      return data;
    },
  });
}

export function useUpdateNotificationPrefs() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: NotificationPrefsUpdate) => {
      const { data } = await api.patch<NotificationPrefs>(
        "/api/v1/settings/notifications",
        body
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.notifications });
    },
  });
}

// ─── Billing Hooks ───────────────────────────────────────────────────────────

export function useBilling() {
  return useQuery({
    queryKey: settingsKeys.billing,
    queryFn: async () => {
      const { data } = await api.get<SettingsBilling>("/api/v1/settings/billing");
      return data;
    },
  });
}

export function useUpdatePaymentMethod() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (paymentMethodId: string) => {
      await api.post("/api/v1/settings/billing/payment-method", {
        payment_method_id: paymentMethodId,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.billing });
    },
  });
}

export function useCancelSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post("/api/v1/settings/billing/cancel");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.billing });
    },
  });
}
