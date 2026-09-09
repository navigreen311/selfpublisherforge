"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Webhook,
  WebhookCreatePayload,
  WebhookDelivery,
  WebhookTestResult,
  WebhookUpdatePayload,
  WebhookWithSecret,
} from "./types";

export const webhookKeys = {
  all: ["webhooks"] as const,
  list: ["webhooks", "list"] as const,
  deliveries: (id: string) => ["webhooks", id, "deliveries"] as const,
};

export function useWebhooks() {
  return useQuery({
    queryKey: webhookKeys.list,
    queryFn: async () => {
      const { data } = await api.get<Webhook[]>("/api/v1/webhooks");
      return data;
    },
  });
}

export function useCreateWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: WebhookCreatePayload) => {
      const { data } = await api.post<WebhookWithSecret>(
        "/api/v1/webhooks",
        body
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: webhookKeys.list });
    },
  });
}

export function useUpdateWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      body,
    }: {
      id: string;
      body: WebhookUpdatePayload;
    }) => {
      const { data } = await api.patch<Webhook>(
        `/api/v1/webhooks/${id}`,
        body
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: webhookKeys.list });
    },
  });
}

export function useDeleteWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/webhooks/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: webhookKeys.list });
    },
  });
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<WebhookTestResult>(
        `/api/v1/webhooks/${id}/test`
      );
      return data;
    },
  });
}

export function useWebhookDeliveries(id: string, enabled = true) {
  return useQuery({
    queryKey: webhookKeys.deliveries(id),
    enabled: enabled && !!id,
    queryFn: async () => {
      const { data } = await api.get<WebhookDelivery[]>(
        `/api/v1/webhooks/${id}/deliveries`
      );
      return data;
    },
  });
}

export function useRotateSecret() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<WebhookWithSecret>(
        `/api/v1/webhooks/${id}/rotate-secret`
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: webhookKeys.list });
    },
  });
}
