import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

const mockGet = jest.fn();
const mockPost = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...a: unknown[]) => mockGet(...a),
    post: (...a: unknown[]) => mockPost(...a),
  },
}));

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

import {
  useRoyaltyDashboard,
  useMonthlyStatement,
  useRoyalties,
  useManualRoyaltyEntry,
} from "../hooks";

function createWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children);
}

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
});

describe("useRoyaltyDashboard", () => {
  it("fetches dashboard for a given year", async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        ytd_earnings: "1000.00",
        this_month_earnings: "300.00",
        pending_payout: "100.00",
        next_payout_date: null,
        by_distributor: [],
        total: "1000.00",
        period: "ytd",
        year: 2026,
      },
    });
    const { result } = renderHook(() => useRoyaltyDashboard(2026), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/royalties/by-distributor?year=2026"),
    );
    expect(result.current.data?.ytd_earnings).toBe("1000.00");
  });
});

describe("useMonthlyStatement", () => {
  it("requires a year parameter", async () => {
    mockGet.mockResolvedValueOnce({
      data: { year: 2026, rows: [], ytd_totals: {} },
    });
    const { result } = renderHook(() => useMonthlyStatement(2026), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining("year=2026"),
    );
  });
});

describe("useRoyalties", () => {
  it("passes filters as query params", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });
    const { result } = renderHook(
      () =>
        useRoyalties({ period: "year", year: 2026, distributor: "kdp" }),
      { wrapper: createWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const called = mockGet.mock.calls[0][0] as string;
    expect(called).toContain("period=year");
    expect(called).toContain("year=2026");
    expect(called).toContain("distributor=kdp");
  });
});

describe("useManualRoyaltyEntry", () => {
  it("POSTs manual entry payload", async () => {
    mockPost.mockResolvedValueOnce({
      data: { id: "abc", source: "manual" },
    });
    const { result } = renderHook(() => useManualRoyaltyEntry(), {
      wrapper: createWrapper(),
    });
    await result.current.mutateAsync({
      distributor: "kdp",
      royalty_type: "kindle_ebook",
      amount: "100.00",
      period_month: 3,
      period_year: 2026,
    });
    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/royalties/manual-entry",
      expect.objectContaining({ distributor: "kdp", amount: "100.00" }),
    );
  });
});
