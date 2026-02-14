import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  OrgSettings, OrgSettingsUpdate, ChangePasswordPayload,
  SessionInfo, LoginHistoryEntry, ApiKey, ApiKeyCreatePayload, ApiKeyCreated,
  Webhook, WebhookCreatePayload, WebhookUpdate,
  NotificationPrefs, NotificationPrefsUpdate, SettingsBilling,
} from "./types";

const settingsKeys = {
  all: ["settings"] as const,
  org: () => [...settingsKeys.all, "org"] as const,
  sessions: () => [...settingsKeys.all, "sessions"] as const,
  loginHistory: () => [...settingsKeys.all, "login-history"] as const,
  apiKeys: () => [...settingsKeys.all, "api-keys"] as const,
  webhooks: () => [...settingsKeys.all, "webhooks"] as const,
  notifications: () => [...settingsKeys.all, "notifications"] as const,
  billing: () => [...settingsKeys.all, "billing"] as const,
};

// Organization
export function useOrgSettings() { return useQuery({ queryKey: settingsKeys.org(), queryFn: async () => { const res = await api.get("/api/v1/settings/organization"); return res.data as OrgSettings; } }); }

export function useUpdateOrgSettings() { const qc = useQueryClient(); return useMutation({ mutationFn: async (data: OrgSettingsUpdate) => { const res = await api.patch("/api/v1/settings/organization", data); return res.data; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.org() }) }); }

// Security
export function useChangePassword() { return useMutation({ mutationFn: async (data: ChangePasswordPayload) => { const res = await api.post("/api/v1/settings/security/change-password", data); return res.data; } }); }

export function useEnable2FA() { return useMutation({ mutationFn: async () => { const res = await api.post("/api/v1/settings/security/enable-2fa"); return res.data; } }); }

export function useDisable2FA() { return useMutation({ mutationFn: async () => { const res = await api.post("/api/v1/settings/security/disable-2fa"); return res.data; } }); }

export function useSessions() { return useQuery({ queryKey: settingsKeys.sessions(), queryFn: async () => { const res = await api.get("/api/v1/settings/security/sessions"); return res.data as SessionInfo[]; } }); }

export function useRevokeSession() { const qc = useQueryClient(); return useMutation({ mutationFn: async (sessionId: string) => { const res = await api.delete(`/api/v1/settings/security/sessions/${sessionId}`); return res.data; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.sessions() }) }); }

export function useRevokeAllSessions() { const qc = useQueryClient(); return useMutation({ mutationFn: async () => { const res = await api.delete("/api/v1/settings/security/sessions"); return res.data; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.sessions() }) }); }

export function useLoginHistory() { return useQuery({ queryKey: settingsKeys.loginHistory(), queryFn: async () => { const res = await api.get("/api/v1/settings/security/login-history"); return res.data as LoginHistoryEntry[]; } }); }

// API Keys
export function useApiKeys() { return useQuery({ queryKey: settingsKeys.apiKeys(), queryFn: async () => { const res = await api.get("/api/v1/settings/api-keys"); return res.data as ApiKey[]; } }); }

export function useCreateApiKey() { const qc = useQueryClient(); return useMutation({ mutationFn: async (data: ApiKeyCreatePayload) => { const res = await api.post("/api/v1/settings/api-keys", data); return res.data as ApiKeyCreated; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.apiKeys() }) }); }

export function useDeleteApiKey() { const qc = useQueryClient(); return useMutation({ mutationFn: async (keyId: string) => { const res = await api.delete(`/api/v1/settings/api-keys/${keyId}`); return res.data; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.apiKeys() }) }); }

export function useRegenerateApiKey() { const qc = useQueryClient(); return useMutation({ mutationFn: async (keyId: string) => { const res = await api.post(`/api/v1/settings/api-keys/${keyId}/regenerate`); return res.data as ApiKeyCreated; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.apiKeys() }) }); }

// Webhooks
export function useWebhooks() { return useQuery({ queryKey: settingsKeys.webhooks(), queryFn: async () => { const res = await api.get("/api/v1/settings/webhooks"); return res.data as Webhook[]; } }); }

export function useCreateWebhook() { const qc = useQueryClient(); return useMutation({ mutationFn: async (data: WebhookCreatePayload) => { const res = await api.post("/api/v1/settings/webhooks", data); return res.data; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.webhooks() }) }); }

export function useUpdateWebhook() { const qc = useQueryClient(); return useMutation({ mutationFn: async ({ id, data }: { id: string; data: WebhookUpdate }) => { const res = await api.patch(`/api/v1/settings/webhooks/${id}`, data); return res.data; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.webhooks() }) }); }

export function useDeleteWebhook() { const qc = useQueryClient(); return useMutation({ mutationFn: async (id: string) => { const res = await api.delete(`/api/v1/settings/webhooks/${id}`); return res.data; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.webhooks() }) }); }

export function useTestWebhook() { return useMutation({ mutationFn: async (id: string) => { const res = await api.post(`/api/v1/settings/webhooks/${id}/test`); return res.data; } }); }

// Notifications
export function useNotificationPrefs() { return useQuery({ queryKey: settingsKeys.notifications(), queryFn: async () => { const res = await api.get("/api/v1/settings/notifications"); return res.data as NotificationPrefs; } }); }

export function useUpdateNotificationPrefs() { const qc = useQueryClient(); return useMutation({ mutationFn: async (data: NotificationPrefsUpdate) => { const res = await api.patch("/api/v1/settings/notifications", data); return res.data; }, onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.notifications() }) }); }

// Billing (from settings perspective)
export function useSettingsBilling() { return useQuery({ queryKey: settingsKeys.billing(), queryFn: async () => { const res = await api.get("/api/v1/settings/billing"); return res.data as SettingsBilling; }, retry: false }); }
