"use client";

import { useEffect, useRef, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2 } from "lucide-react";

interface InfiniteScrollProps {
  /**
   * Child elements to render (list items)
   */
  children: ReactNode;
  /**
   * Callback fired when the user scrolls to the bottom
   */
  onLoadMore: () => void;
  /**
   * Whether more data is available to load
   */
  hasMore: boolean;
  /**
   * Whether data is currently being loaded
   */
  isLoading: boolean;
  /**
   * Optional loading skeleton to show while loading
   */
  loader?: ReactNode;
  /**
   * Distance from bottom (in pixels) to trigger load more
   * @default 200
   */
  threshold?: number;
  /**
   * Optional className for the container
   */
  className?: string;
  /**
   * Whether to show a "Load More" button instead of automatic loading
   * @default false
   */
  showLoadMoreButton?: boolean;
}

/**
 * Infinite scroll component using Intersection Observer API
 * Works with React Query's useInfiniteQuery
 */
export function InfiniteScroll({
  children,
  onLoadMore,
  hasMore,
  isLoading,
  loader,
  threshold = 200,
  className,
  showLoadMoreButton = false,
}: InfiniteScrollProps) {
  const loadMoreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Don't set up observer if we're using the button approach
    if (showLoadMoreButton) return;

    if (!hasMore || isLoading) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const first = entries[0];
        if (first.isIntersecting) {
          onLoadMore();
        }
      },
      {
        rootMargin: `${threshold}px`,
      }
    );

    const currentRef = loadMoreRef.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [hasMore, isLoading, onLoadMore, threshold, showLoadMoreButton]);

  const defaultLoader = (
    <div className="flex items-center justify-center py-4">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      <span className="ml-2 text-sm text-muted-foreground">Loading more...</span>
    </div>
  );

  return (
    <div className={className}>
      {children}

      {hasMore && !showLoadMoreButton && (
        <div ref={loadMoreRef}>
          {isLoading && (loader || defaultLoader)}
        </div>
      )}

      {hasMore && showLoadMoreButton && (
        <div className="flex justify-center py-6">
          <Button
            variant="outline"
            onClick={onLoadMore}
            disabled={isLoading}
            className="gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              "Load More"
            )}
          </Button>
        </div>
      )}

      {!hasMore && (
        <div className="py-4 text-center text-sm text-muted-foreground">
          No more items to load
        </div>
      )}
    </div>
  );
}

/**
 * Default skeleton loader for infinite scroll
 */
export function InfiniteScrollSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {[...Array(count)].map((_, i) => (
        <Skeleton key={i} className="h-24 w-full" />
      ))}
    </div>
  );
}
