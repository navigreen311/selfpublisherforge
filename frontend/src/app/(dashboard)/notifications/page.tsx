"use client";

import { useState } from "react";
import { Bell, CheckCheck } from "lucide-react";
import {
  useNotifications,
  useMarkAllAsRead,
  useMarkAsRead,
} from "@/modules/notifications/hooks";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export default function NotificationsPage() {
  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const { data, isLoading, isError, refetch } = useNotifications(cursor);
  const markAll = useMarkAllAsRead();
  const markOne = useMarkAsRead();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="h-6 w-6" /> Notifications
          </h1>
          <p className="text-sm text-muted-foreground">
            Stay updated with your platform activity.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => markAll.mutate()}
          disabled={markAll.isPending}
        >
          <CheckCheck className="h-4 w-4 mr-2" /> Mark all as read
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState message="Failed to load notifications" onRetry={() => refetch()} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          icon={<Bell className="h-10 w-10" />}
          title="No notifications"
          description="You're all caught up!"
        />
      ) : (
        <>
          <div className="space-y-2">
            {data.items.map((n) => (
              <div
                key={n.id}
                className={cn(
                  "flex items-start gap-3 p-4 border rounded-lg",
                  !n.read_at && "bg-accent/30 border-primary/20"
                )}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-sm">{n.title}</h3>
                    {!n.read_at && <Badge variant="secondary">New</Badge>}
                    <Badge variant="outline" className="text-xs">
                      {n.type}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {n.message}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </div>
                {!n.read_at && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => markOne.mutate(n.id)}
                  >
                    Mark read
                  </Button>
                )}
              </div>
            ))}
          </div>
          {data.has_more && (
            <div className="flex justify-center pt-2">
              <Button
                variant="outline"
                onClick={() => setCursor(data.next_cursor || undefined)}
              >
                Load more
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
