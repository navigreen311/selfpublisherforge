"use client";

import { Bell, CheckCheck, Settings } from "lucide-react";
import Link from "next/link";
import { isToday, isYesterday, startOfDay } from "date-fns";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { NotificationBadge } from "./NotificationBadge";
import { NotificationItem } from "./NotificationItem";
import { useNotifications, useUnreadCount, useMarkAllAsRead, useNotificationSubscription } from "../hooks";
import type { Notification } from "../types";

interface NotificationCenterProps {
  userId: string;
}

/**
 * Groups notifications into "Today", "Yesterday", and "Earlier".
 */
function groupNotifications(notifications: Notification[]) {
  const today: Notification[] = [];
  const yesterday: Notification[] = [];
  const earlier: Notification[] = [];

  notifications.forEach((notification) => {
    const date = new Date(notification.created_at);
    if (isToday(date)) {
      today.push(notification);
    } else if (isYesterday(date)) {
      yesterday.push(notification);
    } else {
      earlier.push(notification);
    }
  });

  return { today, yesterday, earlier };
}

/**
 * Notification center dropdown component with bell icon and notification list.
 *
 * Features:
 * - Bell icon with unread count badge
 * - Dropdown showing last 10 notifications grouped by today/earlier
 * - Each notification: icon, title, description, time ago, read/unread indicator
 * - "Mark all as read" button
 * - Real-time updates via WebSocket
 */
export function NotificationCenter({ userId }: NotificationCenterProps) {
  const { data: notificationsData, isLoading } = useNotifications();
  const { data: unreadData } = useUnreadCount();
  const markAllAsRead = useMarkAllAsRead();

  // Subscribe to real-time notification updates
  useNotificationSubscription(userId);

  const notifications = notificationsData?.items.slice(0, 10) || [];
  const unreadCount = unreadData?.unread_count || 0;
  const hasNotifications = notifications.length > 0;

  const { today, yesterday, earlier } = groupNotifications(notifications);

  const handleMarkAllAsRead = () => {
    markAllAsRead.mutate();
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {/* The badge is decorative here: its number is already carried in the
              button's accessible name below, and leaving it exposed made the
              name read "2 Notifications (2 unread)". */}
          <span aria-hidden="true">
            <NotificationBadge count={unreadCount} />
          </span>
          <span className="sr-only">
            {unreadCount > 0
              ? `Notifications (${unreadCount} unread)`
              : "Notifications"}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-96 p-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <DropdownMenuLabel className="p-0 text-base font-semibold">
            Notifications
          </DropdownMenuLabel>
          <div className="flex items-center gap-1">
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMarkAllAsRead}
                disabled={markAllAsRead.isPending}
                className="h-8 text-xs"
              >
                <CheckCheck className="h-4 w-4 mr-1" />
                Mark all read
              </Button>
            )}
            <Button variant="ghost" size="icon" className="h-8 w-8" asChild>
              <Link href="/settings/notifications">
                <Settings className="h-4 w-4" />
                <span className="sr-only">Notification settings</span>
              </Link>
            </Button>
          </div>
        </div>

        {/* Notification List */}
        <div className="max-h-[480px] overflow-y-auto">
          {isLoading ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              Loading notifications...
            </div>
          ) : !hasNotifications ? (
            <div className="px-4 py-8 text-center">
              <Bell className="h-12 w-12 mx-auto text-muted-foreground/50 mb-2" />
              <p className="text-sm text-muted-foreground">No notifications yet</p>
            </div>
          ) : (
            <>
              {/* Today */}
              {today.length > 0 && (
                <>
                  <DropdownMenuLabel className="px-4 py-2 text-xs font-medium text-muted-foreground">
                    Today
                  </DropdownMenuLabel>
                  <div className="space-y-0">
                    {today.map((notification) => (
                      <NotificationItem key={notification.id} notification={notification} />
                    ))}
                  </div>
                </>
              )}

              {/* Yesterday */}
              {yesterday.length > 0 && (
                <>
                  {today.length > 0 && <DropdownMenuSeparator />}
                  <DropdownMenuLabel className="px-4 py-2 text-xs font-medium text-muted-foreground">
                    Yesterday
                  </DropdownMenuLabel>
                  <div className="space-y-0">
                    {yesterday.map((notification) => (
                      <NotificationItem key={notification.id} notification={notification} />
                    ))}
                  </div>
                </>
              )}

              {/* Earlier */}
              {earlier.length > 0 && (
                <>
                  {(today.length > 0 || yesterday.length > 0) && <DropdownMenuSeparator />}
                  <DropdownMenuLabel className="px-4 py-2 text-xs font-medium text-muted-foreground">
                    Earlier
                  </DropdownMenuLabel>
                  <div className="space-y-0">
                    {earlier.map((notification) => (
                      <NotificationItem key={notification.id} notification={notification} />
                    ))}
                  </div>
                </>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {hasNotifications && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild className="justify-center py-3 cursor-pointer">
              <Link href="/notifications" className="text-sm font-medium text-primary">
                View all notifications
              </Link>
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
