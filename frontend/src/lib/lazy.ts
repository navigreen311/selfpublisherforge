import dynamic from "next/dynamic";
import { ComponentType } from "react";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Lazy load a component with dynamic import and Suspense fallback
 * @param importFn - Function that returns a dynamic import promise
 * @param fallback - Optional React node to show while loading (defaults to Skeleton)
 * @returns Dynamically loaded component with loading state
 */
export function lazyLoad<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  fallback?: React.ReactNode
) {
  return dynamic(importFn, {
    loading: () => (fallback ? <>{fallback}</> : <Skeleton className="h-64 w-full" />),
    ssr: false,
  });
}

/**
 * Lazy load a component with SSR enabled
 * @param importFn - Function that returns a dynamic import promise
 * @param fallback - Optional React node to show while loading
 * @returns Dynamically loaded component with SSR support
 */
export function lazyLoadSSR<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  fallback?: React.ReactNode
) {
  return dynamic(importFn, {
    loading: () => (fallback ? <>{fallback}</> : <Skeleton className="h-64 w-full" />),
    ssr: true,
  });
}

/**
 * Lazy load a named export from a module
 * @param importFn - Function that returns a dynamic import promise with named exports
 * @param exportName - Name of the export to load
 * @param fallback - Optional React node to show while loading
 * @returns Dynamically loaded component
 */
export function lazyLoadNamed<T extends ComponentType<any>>(
  importFn: () => Promise<any>,
  exportName: string,
  fallback?: React.ReactNode
) {
  return dynamic(() => importFn().then((mod) => ({ default: mod[exportName] })), {
    loading: () => (fallback ? <>{fallback}</> : <Skeleton className="h-64 w-full" />),
    ssr: false,
  });
}
