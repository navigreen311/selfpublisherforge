"use client";

import { formatDistanceToNow } from "date-fns";
import {
  CheckCircle2,
  Info,
  AlertTriangle,
  XCircle,
  Sparkles,
  Rocket,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Notification, NotificationType } from "../types";
import { useMarkAsRead } from "../hooks";

interface NotificationItemProps {
  notification: Notification;
  onClick?: () => void;
}

/**
 * Returns the appropriate icon component for a notification type.
 */
function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case "success":
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    case "warning":
      return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    case "error":
      return <XCircle className="h-5 w-5 text-red-600" />;
    case "ai_complete":
      return <Sparkles className="h-5 w-5 text-purple-600" />;
    case "publish_status":
      return <Rocket className="h-5 w-5 text-blue-600" />;
    case "team_invite":
      return <Users className="h-5 w-5 text-indigo-600" />;
    case "info":
    default:
      return <Info className="h-5 w-5 text-blue-600" />;
  }
}

/**
 * Single notification item row.
 * Shows icon, title, message, time ago, and read/unread indicator.
 */
export function NotificationItem({ notification, onClick }: NotificationItemProps) {
  const markAsRead = useMarkAsRead();
  const isUnread = !notification.read_at;

  const handleClick = () => {
    if (isUnread) {
      markAsRead.mutate(notification.id);
    }
    onClick?.();
  };

  const timeAgo = formatDistanceToNow(new Date(notification.created_at), {
    addSuffix: true,
  });

  return (
    <button
      onClick={handleClick}
      className={cn(
        "w-full text-left px-4 py-3 hover:bg-accent transition-colors focus:outline-none focus:bg-accent",
        isUnread && "bg-blue-50 dark:bg-blue-950/20"
      )}
    >
      <div className="flex gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          {getNotificationIcon(notification.type)}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={cn("text-sm font-medium", isUnread && "font-semibold")}>
              {notification.title}
            </p>
            {isUnread && (
              <div className="flex-shrink-0 w-2 h-2 bg-blue-600 rounded-full mt-1" />
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-0.5 line-clamp-2">
            {notification.message}
          </p>
          <p className="text-xs text-muted-foreground mt-1">{timeAgo}</p>
        </div>
      </div>
    </button>
  );
}
