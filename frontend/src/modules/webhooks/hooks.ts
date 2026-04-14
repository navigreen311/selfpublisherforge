import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  EventCatalogEntry,
  WebhookEndpoint,
  WebhookEndpointCreatePayload,
  WebhookEndpointCreated,
  WebhookEndpointUpdatePayload,
  WebhookLog,
  WebhookTestResponse,
} from "./types";

const keys = {
  all: ["webhooks"] as const,
  list: () => [...keys.all, "list"] as const,
  catalog: () => [...keys.all, "catalog"] as const,
  logs: (id: string) => [...keys.all, "logs", id] as const,
};

export function useWebhookEndpoints() {
  return useQuery({
    queryKey: keys.list(),
    queryFn: async () => {
      const res = await api.get("/api/v1/webhooks");
      return res.data as WebhookEndpoint[];
    },
  });
}

export function useWebhookEventCatalog() {
  return useQuery({
    queryKey: keys.catalog(),
    queryFn: async () => {
      const res = await api.get("/api/v1/webhooks/events");
      return res.data as EventCatalogEntry[];
    },
  });
}

export function useCreateWebhookEndpoint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: WebhookEndpointCreatePayload) => {
      const res = await api.post("/api/v1/webhooks", payload);
      return res.data as WebhookEndpointCreated;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.list() }),
  });
}

export function useUpdateWebhookEndpoint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (args: {
      id: string;
      payload: WebhookEndpointUpdatePayload;
    }) => {
      const res = await api.patch(`/api/v1/webhooks/${args.id}`, args.payload);
      return res.data as WebhookEndpoint;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.list() }),
  });
}

export function useDeleteWebhookEndpoint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/webhooks/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.list() }),
  });
}

export function useTestWebhookEndpoint() {
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`/api/v1/webhooks/${id}/test`);
      return res.data as WebhookTestResponse;
    },
  });
}

export function useWebhookLogs(endpointId: string | null) {
  return useQuery({
    queryKey: keys.logs(endpointId ?? ""),
    queryFn: async () => {
      const res = await api.get(`/api/v1/webhooks/${endpointId}/logs`);
      return res.data as WebhookLog[];
    },
    enabled: !!endpointId,
  });
}

export function useRetryWebhookLog() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (logId: string) => {
      const res = await api.post(`/api/v1/webhooks/logs/${logId}/retry`);
      return res.data as WebhookLog;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}
