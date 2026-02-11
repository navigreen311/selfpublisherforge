import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockUsePlatformStats = jest.fn();
const mockUseAuditLog = jest.fn();

jest.mock("@/modules/admin/hooks", () => ({
  usePlatformStats: (...args: unknown[]) => mockUsePlatformStats(...args),
  useAuditLog: (...args: unknown[]) => mockUseAuditLog(...args),
}));

jest.mock("@/modules/admin/components/SystemStats", () => ({
  SystemStats: ({ stats, isLoading }: { stats: unknown; isLoading: boolean }) => (
    <div data-testid="system-stats">
      {isLoading ? "Loading stats..." : `Stats: ${stats ? "loaded" : "not loaded"}`}
    </div>
  ),
}));

jest.mock("@/modules/admin/components/AuditLog", () => ({
  AuditLog: () => <div data-testid="audit-log">Audit Log Component</div>,
}));

// ── Import component under test (after mocks) ───────────────────────────

import AdminOverviewPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

// ── Test Data ────────────────────────────────────────────────────────────

const mockStats = {
  total_users: 1500,
  active_users: 1200,
  total_organizations: 350,
  active_organizations: 280,
  mrr: 125000,
  active_subscriptions: 280,
  total_api_calls_today: 45000,
  total_storage_gb: 1250.5,
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("AdminOverviewPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the admin overview page with platform statistics", () => {
    mockUsePlatformStats.mockReturnValue({
      data: mockStats,
      isLoading: false,
      error: null,
    });
    mockUseAuditLog.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByText("Platform Statistics")).toBeInTheDocument();
    expect(screen.getByTestId("system-stats")).toBeInTheDocument();
    expect(screen.getByText("Stats: loaded")).toBeInTheDocument();
  });

  it("renders the audit log section", () => {
    mockUsePlatformStats.mockReturnValue({
      data: mockStats,
      isLoading: false,
      error: null,
    });
    mockUseAuditLog.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    expect(screen.getByTestId("audit-log")).toBeInTheDocument();
  });

  it("shows loading state for platform statistics", () => {
    mockUsePlatformStats.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
    mockUseAuditLog.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByTestId("system-stats")).toBeInTheDocument();
    expect(screen.getByText("Loading stats...")).toBeInTheDocument();
  });

  it("handles missing stats data gracefully", () => {
    mockUsePlatformStats.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
    mockUseAuditLog.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByTestId("system-stats")).toBeInTheDocument();
    expect(screen.getByText("Stats: not loaded")).toBeInTheDocument();
  });

  it("renders both platform statistics and audit log sections", () => {
    mockUsePlatformStats.mockReturnValue({
      data: mockStats,
      isLoading: false,
      error: null,
    });
    mockUseAuditLog.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    // Both sections should be present
    expect(screen.getByText("Platform Statistics")).toBeInTheDocument();
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    expect(screen.getByTestId("system-stats")).toBeInTheDocument();
    expect(screen.getByTestId("audit-log")).toBeInTheDocument();
  });
});
