/**
 * Tests for team management React Query hooks.
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
  useRoles,
  useTeam,
  useInvite,
  useAssignRole,
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

describe("team hooks", () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPost.mockReset();
    mockPatch.mockReset();
    mockDelete.mockReset();
  });

  it("useRoles fetches /api/v1/roles", async () => {
    mockGet.mockResolvedValue({
      data: [{ id: "r", name: "Owner", is_system: true, permissions: {} }],
    });
    const { result } = renderHook(() => useRoles(), { wrapper: wrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith("/api/v1/roles");
  });

  it("useTeam fetches /api/v1/team", async () => {
    mockGet.mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useTeam(), { wrapper: wrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith("/api/v1/team");
  });

  it("useInvite POSTs to /api/v1/team/invite", async () => {
    mockPost.mockResolvedValue({
      data: { id: "i", email: "x@y.co", status: "pending" },
    });
    const { result } = renderHook(() => useInvite(), { wrapper: wrapper() });
    await result.current.mutateAsync({ email: "x@y.co", role_id: "r1" });
    expect(mockPost).toHaveBeenCalledWith("/api/v1/team/invite", {
      email: "x@y.co",
      role_id: "r1",
    });
  });

  it("useAssignRole PATCHes role", async () => {
    mockPatch.mockResolvedValue({ data: { message: "ok" } });
    const { result } = renderHook(() => useAssignRole(), {
      wrapper: wrapper(),
    });
    await result.current.mutateAsync({ userId: "u1", roleId: "r2" });
    expect(mockPatch).toHaveBeenCalledWith("/api/v1/team/u1/role", {
      role_id: "r2",
    });
  });
});
