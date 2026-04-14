import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPatch = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...a: unknown[]) => mockGet(...a),
    post: (...a: unknown[]) => mockPost(...a),
    patch: (...a: unknown[]) => mockPatch(...a),
  },
}));

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

import {
  useProofStatus,
  useProofCostEstimate,
  useOrderProof,
  useProofReview,
  useSkipProof,
  useProofOrder,
} from "../hooks";

function createWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children);
}

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPatch.mockReset();
});

describe("useProofStatus", () => {
  it("returns null on 404", async () => {
    mockGet.mockRejectedValueOnce({ response: { status: 404 } });
    const { result } = renderHook(() => useProofStatus("pub-1"), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });

  it("returns order on success", async () => {
    mockGet.mockResolvedValueOnce({
      data: { id: "o1", approved: false, skipped: false, status: "ordered" },
    });
    const { result } = renderHook(() => useProofStatus("pub-1"), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.status).toBe("ordered");
  });
});

describe("useProofCostEstimate", () => {
  it("POSTs the estimate endpoint with params", async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        print_cost: "12.05",
        shipping_cost: "3.99",
        total: "16.04",
        currency: "USD",
      },
    });
    const { result } = renderHook(
      () => useProofCostEstimate(280, "standard_color", "standard"),
      { wrapper: createWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockPost).toHaveBeenCalledWith(
      expect.stringContaining("estimate-proof-cost"),
    );
    const url = mockPost.mock.calls[0][0] as string;
    expect(url).toContain("page_count=280");
    expect(url).toContain("interior_type=standard_color");
    expect(url).toContain("shipping_method=standard");
  });
});

describe("useOrderProof", () => {
  it("POSTs order payload to correct publishing id", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "o1" } });
    const { result } = renderHook(() => useOrderProof("pub-abc"), {
      wrapper: createWrapper(),
    });
    await result.current.mutateAsync({
      interior_file_url: "x",
      cover_file_url: "y",
      page_count: 200,
      interior_type: "black_white",
      shipping_method: "standard",
      shipping_address: {
        name: "A",
        address: "1 Main",
        city: "LV",
        state: "NV",
        zip: "89101",
      },
    });
    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/publishing/pub-abc/order-proof",
      expect.objectContaining({ page_count: 200 }),
    );
  });
});

describe("useSkipProof", () => {
  it("POSTs skip endpoint", async () => {
    mockPost.mockResolvedValueOnce({ data: { skipped: true, approved: true } });
    const { result } = renderHook(() => useSkipProof("p1"), {
      wrapper: createWrapper(),
    });
    await result.current.mutateAsync({ reason: "confident" });
    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/publishing/p1/skip-proof",
      expect.objectContaining({ reason: "confident" }),
    );
  });
});

describe("useProofReview", () => {
  it("PATCHes review with checklist + approved flag", async () => {
    mockPatch.mockResolvedValueOnce({
      data: { approved: true, approved_at: "2026-04-10" },
    });
    const { result } = renderHook(() => useProofReview("p1"), {
      wrapper: createWrapper(),
    });
    await result.current.mutateAsync({
      checklist: {
        print_quality: true,
        colors: true,
        text: true,
        pages: true,
        cover: true,
        spine: true,
        barcode: true,
        overall: true,
      },
      issues: "none",
      approved: true,
    });
    expect(mockPatch).toHaveBeenCalledWith(
      "/api/v1/publishing/p1/proof-review",
      expect.objectContaining({ approved: true }),
    );
  });
});

describe("useProofOrder (aggregate)", () => {
  it("exposes status, order, skip, review", () => {
    mockGet.mockResolvedValueOnce({ data: null });
    const { result } = renderHook(() => useProofOrder("p1"), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBeDefined();
    expect(result.current.order).toBeDefined();
    expect(result.current.skip).toBeDefined();
    expect(result.current.review).toBeDefined();
  });
});
