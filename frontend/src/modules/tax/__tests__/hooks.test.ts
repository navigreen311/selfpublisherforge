import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPatch = jest.fn();
const mockDelete = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...a: unknown[]) => mockGet(...a),
    post: (...a: unknown[]) => mockPost(...a),
    patch: (...a: unknown[]) => mockPatch(...a),
    delete: (...a: unknown[]) => mockDelete(...a),
  },
}));

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

import {
  useTaxDashboard,
  useTaxExpenses,
  useCreateExpense,
  useMarkQuarterlyPaid,
} from "../hooks";

import { TAX_DISCLAIMER_TEXT } from "../components/TaxDisclaimer";

function createWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children);
}

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPatch.mockReset();
  mockDelete.mockReset();
});

describe("TaxDisclaimer constant", () => {
  it("contains required disclaimer language", () => {
    expect(TAX_DISCLAIMER_TEXT).toMatch(/estimate/i);
    expect(TAX_DISCLAIMER_TEXT).toMatch(/tax professional/i);
    expect(TAX_DISCLAIMER_TEXT).toMatch(/not a tax advisor/i);
  });
});

describe("useTaxDashboard", () => {
  it("fetches with year and rate", async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        tax_year: 2026,
        tax_rate: "0.25",
        filing_status: "single",
        gross_income: "14280.00",
        estimated_expenses: "480.00",
        net_income: "13800.00",
        estimated_tax_owed: "3450.00",
        income_by_source: [],
        quarterly_estimates: [],
        disclaimer: "...",
      },
    });
    const { result } = renderHook(
      () => useTaxDashboard(2026, "0.25", "single"),
      { wrapper: createWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const called = mockGet.mock.calls[0][0] as string;
    expect(called).toContain("year=2026");
    expect(called).toContain("tax_rate=0.25");
    expect(called).toContain("filing_status=single");
  });
});

describe("useTaxExpenses", () => {
  it("fetches expenses for a year", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });
    const { result } = renderHook(() => useTaxExpenses(2026), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith("/api/v1/tax/expenses?year=2026");
  });
});

describe("useCreateExpense", () => {
  it("POSTs expense payload", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "x" } });
    const { result } = renderHook(() => useCreateExpense(), {
      wrapper: createWrapper(),
    });
    await result.current.mutateAsync({
      category: "Software",
      amount: "50.00",
      tax_year: 2026,
    });
    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/tax/expenses",
      expect.objectContaining({ category: "Software" }),
    );
  });
});

describe("useMarkQuarterlyPaid", () => {
  it("PATCHes quarterly endpoint", async () => {
    mockPatch.mockResolvedValueOnce({ data: { paid: true } });
    const { result } = renderHook(() => useMarkQuarterlyPaid(), {
      wrapper: createWrapper(),
    });
    await result.current.mutateAsync({
      year: 2026,
      quarter: 2,
      paid: true,
    });
    expect(mockPatch).toHaveBeenCalledWith(
      "/api/v1/tax/quarterly-payment/2?year=2026",
      expect.objectContaining({ paid: true }),
    );
  });
});
