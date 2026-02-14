"use client";

import { useState, useCallback } from "react";

export interface Toast {
  title: string;
  description?: string;
  variant?: "default" | "destructive";
}

let toastCallback: ((toast: Toast) => void) | null = null;

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((toast: Toast) => {
    setToasts((prev) => [...prev, toast]);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
      setToasts((prev) => prev.slice(1));
    }, 3000);
  }, []);

  // Register global toast callback
  if (!toastCallback) {
    toastCallback = toast;
  }

  return {
    toast,
    toasts,
  };
}

// Global toast function for use outside React components
export function toast(toast: Toast) {
  if (toastCallback) {
    toastCallback(toast);
  } else {
    console.warn("Toast hook not initialized");
  }
}
