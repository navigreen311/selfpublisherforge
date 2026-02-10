/**
 * Generic React Query hooks with typed error handling.
 *
 * Provides:
 *   - useApiQuery      – wraps useQuery with API error extraction
 *   - useApiMutation   – wraps useMutation with API error extraction
 *   - useApiInfinite   – wraps useInfiniteQuery for cursor-based pagination
 *
 * All hooks rely on the shared axios instance from `@/lib/api`.
 */

import {
  useQuery,
  useMutation,
  useInfiniteQuery,
  type UseQueryOptions,
  type UseMutationOptions,
  type UseInfiniteQueryOptions,
  type QueryKey,
  type InfiniteData,
} from "@tanstack/react-query";
import { AxiosError } from "axios";

import { api } from "@/lib/api";
import type { ApiError, PaginatedSuccessResponse } from "@/types/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Extract a user-friendly error message from an Axios error that follows
 * the backend's ErrorEnvelope shape.
 */
export function extractApiError(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiError | undefined;
    if (data?.error?.message) {
      return data.error.message;
    }
    if (error.message) {
      return error.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred.";
}

/**
 * Type-guard for our standard API error shape.
 */
export function isApiError(error: unknown): error is AxiosError<ApiError> {
  return error instanceof AxiosError && !!(error.response?.data as ApiError)?.error;
}

// ---------------------------------------------------------------------------
// useApiQuery
// ---------------------------------------------------------------------------

export interface UseApiQueryOptions<TData>
  extends Omit<UseQueryOptions<TData, AxiosError<ApiError>>, "queryFn"> {
  /** Endpoint path, e.g. "/api/v1/books". */
  url: string;
  /** Optional query parameters appended to the URL. */
  params?: Record<string, unknown>;
}

/**
 * Typed `useQuery` wrapper that performs a GET request via the shared
 * axios instance.
 *
 * ```tsx
 * const { data, isLoading, error } = useApiQuery<Book[]>({
 *   queryKey: ["books"],
 *   url: "/api/v1/books",
 *   params: { limit: 20 },
 * });
 * ```
 */
export function useApiQuery<TData = unknown>(options: UseApiQueryOptions<TData>) {
  const { url, params, ...queryOptions } = options;

  return useQuery<TData, AxiosError<ApiError>>({
    ...queryOptions,
    queryFn: async () => {
      const response = await api.get<TData>(url, { params });
      return response.data;
    },
  });
}

// ---------------------------------------------------------------------------
// useApiMutation
// ---------------------------------------------------------------------------

export interface UseApiMutationOptions<TData, TVariables>
  extends Omit<UseMutationOptions<TData, AxiosError<ApiError>, TVariables>, "mutationFn"> {
  /** Endpoint path, e.g. "/api/v1/books". */
  url: string;
  /** HTTP method (default: "POST"). */
  method?: "POST" | "PUT" | "PATCH" | "DELETE";
}

/**
 * Typed `useMutation` wrapper.
 *
 * ```tsx
 * const mutation = useApiMutation<Book, CreateBookPayload>({
 *   url: "/api/v1/books",
 *   method: "POST",
 *   onSuccess: (book) => { ... },
 * });
 * mutation.mutate({ title: "My Book" });
 * ```
 */
export function useApiMutation<TData = unknown, TVariables = unknown>(
  options: UseApiMutationOptions<TData, TVariables>,
) {
  const { url, method = "POST", ...mutationOptions } = options;

  return useMutation<TData, AxiosError<ApiError>, TVariables>({
    ...mutationOptions,
    mutationFn: async (variables: TVariables) => {
      const response = await api.request<TData>({
        url,
        method,
        data: variables,
      });
      return response.data;
    },
  });
}

// ---------------------------------------------------------------------------
// useApiInfinite
// ---------------------------------------------------------------------------

export interface UseApiInfiniteOptions<TItem>
  extends Omit<
    UseInfiniteQueryOptions<
      PaginatedSuccessResponse<TItem>,
      AxiosError<ApiError>,
      InfiniteData<PaginatedSuccessResponse<TItem>>,
      QueryKey,
      string | null
    >,
    "queryFn" | "getNextPageParam" | "initialPageParam"
  > {
  /** Endpoint path, e.g. "/api/v1/books". */
  url: string;
  /** Additional static query params. */
  params?: Record<string, unknown>;
  /** Items per page (default: 20). */
  pageSize?: number;
}

/**
 * Typed `useInfiniteQuery` for cursor-based pagination.
 *
 * Expects the backend to return `PaginatedSuccessResponse<T>`:
 * ```json
 * { "data": [...], "meta": { "next_cursor": "...", "has_more": true, "total_count": 42 } }
 * ```
 *
 * ```tsx
 * const { data, fetchNextPage, hasNextPage, isLoading } = useApiInfinite<Book>({
 *   queryKey: ["books"],
 *   url: "/api/v1/books",
 *   pageSize: 20,
 * });
 *
 * const allBooks = data?.pages.flatMap((page) => page.data) ?? [];
 * ```
 */
export function useApiInfinite<TItem = unknown>(options: UseApiInfiniteOptions<TItem>) {
  const { url, params, pageSize = 20, ...queryOptions } = options;

  return useInfiniteQuery<
    PaginatedSuccessResponse<TItem>,
    AxiosError<ApiError>,
    InfiniteData<PaginatedSuccessResponse<TItem>>,
    QueryKey,
    string | null
  >({
    ...queryOptions,
    initialPageParam: null,
    queryFn: async ({ pageParam }) => {
      const response = await api.get<PaginatedSuccessResponse<TItem>>(url, {
        params: {
          ...params,
          cursor: pageParam ?? undefined,
          limit: pageSize,
        },
      });
      return response.data;
    },
    getNextPageParam: (lastPage) => {
      if (lastPage.meta.has_more && lastPage.meta.next_cursor) {
        return lastPage.meta.next_cursor;
      }
      return null;
    },
  });
}
