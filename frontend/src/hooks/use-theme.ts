"use client";

import { useEffect, useCallback } from "react";
import { useUIStore } from "@/lib/store";

type Theme = "light" | "dark" | "system";

export function useTheme() {
  const { theme, setTheme } = useUIStore();

  const applyTheme = useCallback((t: Theme) => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");

    if (t === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
        .matches
        ? "dark"
        : "light";
      root.classList.add(systemTheme);
    } else {
      root.classList.add(t);
    }
  }, []);

  useEffect(() => {
    applyTheme(theme);
  }, [theme, applyTheme]);

  useEffect(() => {
    if (theme !== "system") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => applyTheme("system");
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, [theme, applyTheme]);

  const toggleTheme = useCallback(() => {
    const nextTheme: Record<Theme, Theme> = {
      light: "dark",
      dark: "system",
      system: "light",
    };
    setTheme(nextTheme[theme]);
  }, [theme, setTheme]);

  const resolvedTheme =
    theme === "system"
      ? typeof window !== "undefined" &&
        window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
      : theme;

  return {
    theme,
    resolvedTheme,
    setTheme,
    toggleTheme,
  };
}
