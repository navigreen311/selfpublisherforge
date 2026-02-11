"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface NotificationBadgeProps {
  count: number;
  className?: string;
}

/**
 * Badge displaying the count of unread notifications.
 * Only renders when count > 0.
 */
export function NotificationBadge({ count, className }: NotificationBadgeProps) {
  if (count === 0) return null;

  const displayCount = count > 99 ? "99+" : count.toString();

  return (
    <Badge
      variant="destructive"
      className={cn(
        "absolute -top-1 -right-1 h-5 min-w-[1.25rem] px-1 flex items-center justify-center text-[10px] font-bold",
        className
      )}
    >
      {displayCount}
    </Badge>
  );
}
