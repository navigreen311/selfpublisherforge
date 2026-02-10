import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// ── Mock the API module ──────────────────────────────────────────────────

const mockGet = jest.fn();
const mockPost = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

// ── Import hooks under test (after mocks) ────────────────────────────────

import {
  useDashboard,
  useRevenue,
  useRoyalties,
  usePortfolioMetrics,
  useReports,
  useTrends,
  useImportRoyalties,
  useGenerateReport,
  useDownloadReport,
  useRecordEvent,
  analyticsKeys,
} from "../hooks";

// ── Helpers ──────────────────────────────────────────────────────────────

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
}

// ── Test Data ────────────────────────────────────────────────────────────

const mockDashboardData = {
  kpis: [
    {
      label: "Total Revenue",
      value: "$12,450.00",
      change_percent: 12.5,
      change_direction: "up",
      period: "last_30_days",
    },
  ],
  revenue_chart: [
    { period: "2025-01-01", revenue: 500, units: 50 },
    { period: "2025-02-01", revenue: 700, units: 65 },
  ],
  top_books: [{ title: "Book A", revenue: 500, units: 50 }],
  platform_breakdown: { kdp: 500, ingram_spark: 200 },
  recent_royalties: [],
  period_start: "2025-01-01",
  period_end: "2025-03-31",
};

const mockRevenueData = {
  total_revenue: 1200,
  total_units: 115,
  data_points: [
    { period: "2025-01-01", revenue: 500, units: 50 },
    { period: "2025-02-01", revenue: 700, units: 65 },
  ],
  period_start: "2025-01-01",
  period_end: "2025-02-28",
  aggregation: "monthly",
  by_platform: { kdp: 800, ingram_spark: 400 },
  by_book: [
    { title: "Book A", revenue: 700, units: 65 },
    { title: "Book B", revenue: 500, units: 50 },
  ],
};

const mockPortfolioData = {
  total_books: 5,
  total_revenue: 3500,
  total_units_sold: 350,
  total_expenses: 500,
  net_profit: 3000,
  avg_roi: 6.0,
  platform_breakdown: { kdp: 2000, ingram_spark: 1500 },
  format_breakdown: { ebook: 2500, paperback: 1000 },
  top_books: [],
  snapshot_date: "2025-06-01",
};

const mockReportsData = {
  items: [
    {
      id: "rpt-1",
      org_id: "org-1",
      title: "Q1 Report",
      report_type: "revenue_summary",
      status: "completed",
      output_format: "pdf",
      parameters: {},
      file_path: "/reports/rpt-1.pdf",
      file_size: 51200,
      generated_by: "user-1",
      generated_at: "2025-04-01T00:00:00Z",
      error_message: null,
      created_at: "2025-04-01T00:00:00Z",
      updated_at: "2025-04-01T00:00:00Z",
    },
  ],
  next_cursor: null,
  has_more: false,
  total_count: 1,
};

const mockTrendData = {
  metric: "revenue",
  data_points: [
    { period: "2025-01", value: 500 },
    { period: "2025-02", value: 700 },
    { period: "2025-03", value: 600 },
  ],
  aggregation: "monthly",
  period_start: "2025-01-01",
  period_end: "2025-03-31",
  total: 1800,
  average: 600,
  change_percent: 20.0,
};

const mockGeneratedReport = {
  id: "rpt-new",
  org_id: "org-1",
  title: "New Report",
  report_type: "revenue_summary",
  status: "processing",
  output_format: "pdf",
  parameters: {},
  file_path: null,
  file_size: null,
  generated_by: "user-1",
  generated_at: null,
  error_message: null,
  created_at: "2025-06-01T00:00:00Z",
  updated_at: "2025-06-01T00:00:00Z",
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("Analytics hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ---------- Query key structure ----------

  describe("analyticsKeys", () => {
    it("generates correct keys for dashboard", () => {
      expect(analyticsKeys.dashboard()).toEqual([
        "analytics",
        "dashboard",
        undefined,
        undefined,
      ]);
    });

    it("generates correct keys for dashboard with dates", () => {
      expect(analyticsKeys.dashboard("2025-01-01", "2025-03-31")).toEqual([
        "analytics",
        "dashboard",
        "2025-01-01",
        "2025-03-31",
      ]);
    });

    it("generates correct keys for revenue", () => {
      expect(analyticsKeys.revenue({ aggregation: "monthly" })).toEqual([
        "analytics",
        "revenue",
        { aggregation: "monthly" },
      ]);
    });

    it("generates correct keys for portfolio", () => {
      expect(analyticsKeys.portfolio()).toEqual(["analytics", "portfolio"]);
    });

    it("generates correct keys for reports", () => {
      expect(analyticsKeys.reports()).toEqual([
        "analytics",
        "reports",
        undefined,
      ]);
    });

    it("generates correct keys for trends", () => {
      expect(analyticsKeys.trends("revenue")).toEqual([
        "analytics",
        "trends",
        "revenue",
        undefined,
      ]);
    });
  });

  // ---------- useDashboard (useRevenueSummary equivalent) ----------

  describe("useDashboard", () => {
    it("fetches dashboard data successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockDashboardData });

      const { result } = renderHook(() => useDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/analytics/dashboard")
      );
      expect(result.current.data).toEqual(mockDashboardData);
    });

    it("passes date parameters when provided", async () => {
      mockGet.mockResolvedValueOnce({ data: mockDashboardData });

      const { result } = renderHook(
        () => useDashboard("2025-01-01", "2025-03-31"),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const calledUrl = mockGet.mock.calls[0][0] as string;
      expect(calledUrl).toContain("start_date=2025-01-01");
      expect(calledUrl).toContain("end_date=2025-03-31");
    });

    it("handles errors", async () => {
      mockGet.mockRejectedValueOnce(new Error("Server error"));

      const { result } = renderHook(() => useDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Server error");
    });
  });

  // ---------- useRevenue ----------

  describe("useRevenue", () => {
    it("fetches revenue data with parameters", async () => {
      mockGet.mockResolvedValueOnce({ data: mockRevenueData });

      const { result } = renderHook(
        () =>
          useRevenue({
            aggregation: "monthly",
            platform: "kdp",
            start_date: "2025-01-01",
            end_date: "2025-02-28",
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const calledUrl = mockGet.mock.calls[0][0] as string;
      expect(calledUrl).toContain("/api/v1/analytics/revenue");
      expect(calledUrl).toContain("aggregation=monthly");
      expect(calledUrl).toContain("platform=kdp");
      expect(calledUrl).toContain("start_date=2025-01-01");
      expect(calledUrl).toContain("end_date=2025-02-28");

      expect(result.current.data?.total_revenue).toBe(1200);
      expect(result.current.data?.total_units).toBe(115);
      expect(result.current.data?.data_points).toHaveLength(2);
    });

    it("verifies data transformation correctness for revenue", async () => {
      mockGet.mockResolvedValueOnce({ data: mockRevenueData });

      const { result } = renderHook(() => useRevenue({ aggregation: "monthly" }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const data = result.current.data!;
      // Verify by_platform totals match total_revenue
      const platformTotal = Object.values(data.by_platform).reduce(
        (sum, val) => sum + val,
        0
      );
      expect(platformTotal).toBe(data.total_revenue);

      // Verify data_points have correct structure
      data.data_points.forEach((dp) => {
        expect(dp).toHaveProperty("period");
        expect(dp).toHaveProperty("revenue");
        expect(dp).toHaveProperty("units");
        expect(typeof dp.revenue).toBe("number");
        expect(typeof dp.units).toBe("number");
      });
    });
  });

  // ---------- useReports (list hook) ----------

  describe("useReports", () => {
    it("fetches reports list successfully", async () => {
      mockGet.mockResolvedValueOnce({ data: mockReportsData });

      const { result } = renderHook(() => useReports(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/analytics/reports")
      );
      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].title).toBe("Q1 Report");
      expect(result.current.data?.has_more).toBe(false);
    });

    it("passes cursor parameter for pagination", async () => {
      mockGet.mockResolvedValueOnce({ data: mockReportsData });

      const { result } = renderHook(() => useReports("cursor-abc"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const calledUrl = mockGet.mock.calls[0][0] as string;
      expect(calledUrl).toContain("cursor=cursor-abc");
    });

    it("handles errors fetching reports", async () => {
      mockGet.mockRejectedValueOnce(new Error("Unauthorized"));

      const { result } = renderHook(() => useReports(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Unauthorized");
    });
  });

  // ---------- useGenerateReport (mutation) ----------

  describe("useGenerateReport", () => {
    it("generates a report via POST", async () => {
      mockPost.mockResolvedValueOnce({ data: mockGeneratedReport });

      const { result } = renderHook(() => useGenerateReport(), {
        wrapper: createWrapper(),
      });

      const request = {
        title: "New Report",
        report_type: "revenue_summary" as const,
        output_format: "pdf" as const,
        parameters: {},
      };

      act(() => {
        result.current.mutate(request);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/analytics/reports/generate",
        request
      );
      expect(result.current.data).toEqual(mockGeneratedReport);
    });

    it("handles report generation errors", async () => {
      mockPost.mockRejectedValueOnce(new Error("Report generation failed"));

      const { result } = renderHook(() => useGenerateReport(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          title: "Failed Report",
          report_type: "revenue_summary",
          output_format: "pdf",
          parameters: {},
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe("Report generation failed");
    });
  });

  // ---------- useDownloadReport (mutation) ----------

  describe("useDownloadReport", () => {
    it("downloads a report blob", async () => {
      const mockBlob = new Blob(["pdf content"], { type: "application/pdf" });
      mockGet.mockResolvedValueOnce({ data: mockBlob });

      const { result } = renderHook(() => useDownloadReport(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate("rpt-1");
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        "/api/v1/analytics/reports/rpt-1/download",
        { responseType: "blob" }
      );
    });
  });

  // ---------- usePortfolioMetrics ----------

  describe("usePortfolioMetrics", () => {
    it("fetches portfolio metrics", async () => {
      mockGet.mockResolvedValueOnce({ data: mockPortfolioData });

      const { result } = renderHook(() => usePortfolioMetrics(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith("/api/v1/analytics/portfolio");
      expect(result.current.data?.total_books).toBe(5);
      expect(result.current.data?.total_revenue).toBe(3500);
      expect(result.current.data?.net_profit).toBe(3000);
    });
  });

  // ---------- useTrends ----------

  describe("useTrends", () => {
    it("fetches trend data with metric and parameters", async () => {
      mockGet.mockResolvedValueOnce({ data: mockTrendData });

      const { result } = renderHook(
        () =>
          useTrends("revenue", {
            start_date: "2025-01-01",
            end_date: "2025-03-31",
            aggregation: "monthly",
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const calledUrl = mockGet.mock.calls[0][0] as string;
      expect(calledUrl).toContain("/api/v1/analytics/trends");
      expect(calledUrl).toContain("metric=revenue");
      expect(calledUrl).toContain("aggregation=monthly");

      expect(result.current.data?.total).toBe(1800);
      expect(result.current.data?.average).toBe(600);
      expect(result.current.data?.data_points).toHaveLength(3);
    });
  });

  // ---------- useImportRoyalties (mutation) ----------

  describe("useImportRoyalties", () => {
    it("imports royalties via POST", async () => {
      const importResponse = {
        import_batch_id: "batch-1",
        records_imported: 50,
        records_skipped: 2,
        errors: [],
        platform: "kdp",
      };
      mockPost.mockResolvedValueOnce({ data: importResponse });

      const { result } = renderHook(() => useImportRoyalties(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          platform: "kdp",
          file_content: "csv-content-here",
          file_name: "royalties.csv",
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/analytics/royalties/import",
        {
          platform: "kdp",
          file_content: "csv-content-here",
          file_name: "royalties.csv",
        }
      );
      expect(result.current.data?.records_imported).toBe(50);
    });
  });

  // ---------- useRecordEvent (mutation) ----------

  describe("useRecordEvent", () => {
    it("records an event via POST", async () => {
      mockPost.mockResolvedValueOnce({ data: { ok: true } });

      const { result } = renderHook(() => useRecordEvent(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({
          event_type: "page_view",
          event_source: "analytics",
          data: { page: "/analytics" },
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith("/api/v1/analytics/events", {
        event_type: "page_view",
        event_source: "analytics",
        data: { page: "/analytics" },
      });
    });
  });

  // ---------- Data transformation correctness ----------

  describe("data transformation correctness", () => {
    it("verifies dashboard KPI data structure is preserved", async () => {
      mockGet.mockResolvedValueOnce({ data: mockDashboardData });

      const { result } = renderHook(() => useDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const dashboard = result.current.data!;
      expect(dashboard.kpis).toBeInstanceOf(Array);
      expect(dashboard.kpis[0]).toHaveProperty("label");
      expect(dashboard.kpis[0]).toHaveProperty("value");
      expect(dashboard.kpis[0]).toHaveProperty("change_percent");
      expect(dashboard.kpis[0]).toHaveProperty("change_direction");
    });

    it("verifies revenue data_points structure", async () => {
      mockGet.mockResolvedValueOnce({ data: mockRevenueData });

      const { result } = renderHook(() => useRevenue(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const revenue = result.current.data!;
      expect(revenue.data_points).toBeInstanceOf(Array);
      expect(revenue.by_platform).toBeDefined();
      expect(revenue.by_book).toBeInstanceOf(Array);

      // Verify numeric fields are numbers
      expect(typeof revenue.total_revenue).toBe("number");
      expect(typeof revenue.total_units).toBe("number");
    });

    it("verifies portfolio metrics structure", async () => {
      mockGet.mockResolvedValueOnce({ data: mockPortfolioData });

      const { result } = renderHook(() => usePortfolioMetrics(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const portfolio = result.current.data!;
      expect(typeof portfolio.total_books).toBe("number");
      expect(typeof portfolio.total_revenue).toBe("number");
      expect(typeof portfolio.net_profit).toBe("number");
      expect(typeof portfolio.avg_roi).toBe("number");
      // Verify net_profit = total_revenue - total_expenses
      expect(portfolio.net_profit).toBe(
        portfolio.total_revenue - portfolio.total_expenses
      );
    });
  });

  // ---------- useRoyalties ----------

  describe("useRoyalties", () => {
    it("fetches paginated royalties", async () => {
      const royaltiesData = {
        items: [
          {
            id: "r-1",
            org_id: "org-1",
            book_id: "book-1",
            platform: "kdp",
            marketplace: "US",
            title: "Book A",
            asin: "B00TEST",
            isbn: null,
            format_type: "ebook",
            units_sold: 100,
            units_refunded: 2,
            net_units: 98,
            list_price: 9.99,
            royalty_rate: 0.7,
            gross_revenue: 999.0,
            net_revenue: 685.3,
            currency: "USD",
            period_start: "2025-01-01",
            period_end: "2025-01-31",
            import_batch_id: "batch-1",
            created_at: "2025-02-01T00:00:00Z",
            updated_at: "2025-02-01T00:00:00Z",
          },
        ],
        next_cursor: null,
        has_more: false,
        total_count: 1,
      };
      mockGet.mockResolvedValueOnce({ data: royaltiesData });

      const { result } = renderHook(() => useRoyalties(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/analytics/royalties")
      );
      expect(result.current.data?.items).toHaveLength(1);
    });

    it("passes cursor and platform parameters", async () => {
      mockGet.mockResolvedValueOnce({
        data: { items: [], next_cursor: null, has_more: false, total_count: 0 },
      });

      const { result } = renderHook(
        () => useRoyalties("cursor-xyz", "kdp"),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const calledUrl = mockGet.mock.calls[0][0] as string;
      expect(calledUrl).toContain("cursor=cursor-xyz");
      expect(calledUrl).toContain("platform=kdp");
    });
  });
});
