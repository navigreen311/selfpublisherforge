"use client";

import { useCallback } from "react";
import { useUIStore } from "@/lib/store";

export function useSidebar() {
  const {
    sidebarCollapsed,
    sidebarMobileOpen,
    toggleSidebar,
    setSidebarCollapsed,
    setSidebarMobileOpen,
  } = useUIStore();

  const collapse = useCallback(() => {
    setSidebarCollapsed(true);
  }, [setSidebarCollapsed]);

  const expand = useCallback(() => {
    setSidebarCollapsed(false);
  }, [setSidebarCollapsed]);

  const openMobile = useCallback(() => {
    setSidebarMobileOpen(true);
  }, [setSidebarMobileOpen]);

  const closeMobile = useCallback(() => {
    setSidebarMobileOpen(false);
  }, [setSidebarMobileOpen]);

  return {
    collapsed: sidebarCollapsed,
    mobileOpen: sidebarMobileOpen,
    toggle: toggleSidebar,
    collapse,
    expand,
    openMobile,
    closeMobile,
  };
}
