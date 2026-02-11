"use client";

import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingProps {
  className?: string;
  size?: "sm" | "default" | "lg";
  text?: string;
  fullPage?: boolean;
}

export function Loading({
  className,
  size = "default",
  text,
  fullPage = false,
}: LoadingProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    default: "h-8 w-8",
    lg: "h-12 w-12",
  };

  const content = (
    <div
      className={cn("flex flex-col items-center justify-center gap-3", className)}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <Loader2 className={cn("animate-spin text-primary", sizeClasses[size])} aria-hidden="true" />
      {text && <p className="text-sm text-muted-foreground">{text}</p>}
      {!text && <span className="sr-only">Loading...</span>}
    </div>
  );

  if (fullPage) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        {content}
      </div>
    );
  }

  return content;
}
