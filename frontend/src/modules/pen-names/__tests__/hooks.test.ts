/**
 * Tests for pen-names React Query hooks.
 */
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPatch = jest.fn();
const mockDelete = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
}));

import {
  usePenNames,
  useCreatePenName,
  useDeletePenName,
} from "../hooks";

function wrapper() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children);
}

describe("pen-names hooks", () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPost.mockReset();
    mockPatch.mockReset();
    mockDelete.mockReset();
  });

  it("usePenNames fetches from /api/v1/pen-names", async () => {
    mockGet.mockResolvedValue({ data: [{ id: "a", display_name: "A" }] });
    const { result } = renderHook(() => usePenNames(), { wrapper: wrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith("/api/v1/pen-names");
    expect(result.current.data?.[0].id).toBe("a");
  });

  it("useCreatePenName POSTs the body", async () => {
    mockPost.mockResolvedValue({
      data: { id: "x", display_name: "X", is_default: false },
    });
    const { result } = renderHook(() => useCreatePenName(), {
      wrapper: wrapper(),
    });
    await result.current.mutateAsync({ display_name: "X" });
    expect(mockPost).toHaveBeenCalledWith("/api/v1/pen-names", {
      display_name: "X",
    });
  });

  it("useDeletePenName DELETEs by id", async () => {
    mockDelete.mockResolvedValue({ data: { message: "ok" } });
    const { result } = renderHook(() => useDeletePenName(), {
      wrapper: wrapper(),
    });
    await result.current.mutateAsync("abc");
    expect(mockDelete).toHaveBeenCalledWith("/api/v1/pen-names/abc");
  });
});
