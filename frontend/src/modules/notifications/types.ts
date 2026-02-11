/**
 * TypeScript types for the Notifications module.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type NotificationType =
  | "info"
  | "success"
  | "warning"
  | "error"
  | "ai_complete"
  | "publish_status"
  | "team_invite";

export type NotificationChannel = "email" | "in_app" | "push";

// ---------------------------------------------------------------------------
// Notification
// ---------------------------------------------------------------------------

export interface Notification {
  id: string;
  org_id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  data: Record<string, unknown> | null;
  read_at: string | null;
  created_at: string;
}

export interface UnreadCount {
  unread_count: number;
}

// ---------------------------------------------------------------------------
// Notification Preferences
// ---------------------------------------------------------------------------

export interface NotificationPreference {
  id: string;
  user_id: string;
  channel: NotificationChannel;
  category: string;
  enabled: boolean;
}

export interface PreferenceItem {
  channel: NotificationChannel;
  category: string;
  enabled: boolean;
}

export interface NotificationPreferenceUpdate {
  preferences: PreferenceItem[];
}

// ---------------------------------------------------------------------------
// Paginated Response
// ---------------------------------------------------------------------------

export interface PaginatedNotifications {
  items: Notification[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

// ---------------------------------------------------------------------------
// WebSocket Message
// ---------------------------------------------------------------------------

export interface NotificationWSMessage {
  type: "notification" | "notification_read";
  notification?: Notification;
  notification_id?: string;
}
