"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/use-websocket";
import type {
  Notification,
  NotificationPreference,
  NotificationPreferenceUpdate,
  PaginatedNotifications,
  UnreadCount,
  NotificationWSMessage,
} from "./types";

export type * from "./types";

const API_PREFIX = "/api/v1/notifications";

// ---------- Query Keys ----------

export const notificationKeys = {
  all: ["notifications"] as const,
  list: (cursor?: string) => [...notificationKeys.all, "list", cursor] as const,
  unreadCount: () => [...notificationKeys.all, "unread-count"] as const,
  preferences: () => [...notificationKeys.all, "preferences"] as const,
};

// ---------- Hooks ----------

/**
 * Fetch paginated list of notifications.
 */
export function useNotifications(cursor?: string) {
  return useQuery<PaginatedNotifications>({
    queryKey: notificationKeys.list(cursor),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (cursor) params.set("cursor", cursor);
      const { data } = await api.get(`${API_PREFIX}?${params}`);
      return data;
    },
  });
}

/**
 * Fetch unread notification count.
 */
export function useUnreadCount() {
  return useQuery<UnreadCount>({
    queryKey: notificationKeys.unreadCount(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/unread-count`);
      return data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds as fallback
  });
}

/**
 * Mark a single notification as read.
 */
export function useMarkAsRead() {
  const queryClient = useQueryClient();
  return useMutation<Notification, Error, string>({
    mutationFn: async (notificationId) => {
      const { data } = await api.patch(`${API_PREFIX}/${notificationId}/read`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

/**
 * Mark all notifications as read.
 */
export function useMarkAllAsRead() {
  const queryClient = useQueryClient();
  return useMutation<{ count: number }, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`${API_PREFIX}/read-all`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

/**
 * Fetch notification preferences.
 */
export function useNotificationPreferences() {
  return useQuery<NotificationPreference[]>({
    queryKey: notificationKeys.preferences(),
    queryFn: async () => {
      const { data } = await api.get(`${API_PREFIX}/preferences`);
      return data;
    },
  });
}

/**
 * Update notification preferences.
 */
export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  return useMutation<NotificationPreference[], Error, NotificationPreferenceUpdate>({
    mutationFn: async (update) => {
      const { data } = await api.put(`${API_PREFIX}/preferences`, update);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.preferences() });
    },
  });
}

/**
 * Subscribe to real-time notification updates via WebSocket.
 *
 * This hook connects to the "notifications" WebSocket channel using the current user's ID.
 * When a notification is created or marked as read, it will invalidate the relevant queries.
 */
export function useNotificationSubscription(userId: string) {
  const queryClient = useQueryClient();

  // Note: We need to add "notifications" to the WSChannel type in websocket.ts
  // For now, we'll use a type assertion. This should be updated in the WebSocket lib.
  const { lastMessage } = useWebSocket(
    "notifications" as any,
    userId,
    { enabled: !!userId }
  );

  useEffect(() => {
    if (!lastMessage) return;

    const msg = lastMessage as unknown as NotificationWSMessage;

    // Handle new notification or notification read
    if (msg.type === "notification" || msg.type === "notification_read") {
      // Invalidate queries to fetch fresh data
      queryClient.invalidateQueries({ queryKey: notificationKeys.unreadCount() });
      queryClient.invalidateQueries({ queryKey: notificationKeys.list() });
    }
  }, [lastMessage, queryClient]);
}
