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

// A component type can be a plain function component OR an exotic component
// (forwardRef/memo), which is an object like {$$typeof, render} — NOT a function.
// Lucide icons are forwardRef components, so a `typeof === "function"` check
// alone misses them and they get rendered as a raw object (React throws).
function isComponentType(
  icon: React.ReactNode | LucideIcon
): icon is React.ElementType {
  return (
    typeof icon === "function" ||
    (typeof icon === "object" && icon !== null && !React.isValidElement(icon))
  );
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
        {isComponentType(icon) ? (
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
