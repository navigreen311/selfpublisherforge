"use client";

import React from "react";
import { type LucideIcon, Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  icon?: React.ReactNode | LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

function isLucideIcon(
  icon: React.ReactNode | LucideIcon
): icon is LucideIcon {
  return typeof icon === "function";
}

export function EmptyState({
  icon = Inbox,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center border-2 border-dashed border-muted-foreground/25 rounded-lg">
      <div className="rounded-full bg-muted p-4 mb-4">
        {isLucideIcon(icon) ? (
          React.createElement(icon, {
            className: "h-10 w-10 text-muted-foreground",
          })
        ) : (
          <span className="h-10 w-10 text-muted-foreground flex items-center justify-center">
            {icon}
          </span>
        )}
      </div>
      <h3 className="text-lg font-semibold mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-sm mb-4">
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <Button onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}
