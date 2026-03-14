import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AdminOverviewPage from "../page";

jest.mock("@/modules/admin/hooks", () => ({
  useDetailedPlatformStats: jest.fn(),
}));

jest.mock("@/modules/admin/components/SystemStats", () => ({
  SystemStats: ({ stats, isLoading, isError }: any) => {
    if (isLoading) return <div data-testid="system-stats-loading">Loading stats...</div>;
    if (isError) return <div data-testid="system-stats-error">Error loading stats</div>;
    if (!stats) return <div data-testid="system-stats-empty">No stats</div>;
    return <div data-testid="system-stats">Stats loaded</div>;
  },
}));

jest.mock("@/modules/admin/components/AuditLog", () => ({
  AuditLog: () => <div data-testid="audit-log">Audit log</div>,
}));

import { useDetailedPlatformStats } from "@/modules/admin/hooks";

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

describe("AdminOverviewPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders without crashing", () => {
    (useDetailedPlatformStats as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByText("Platform Statistics")).toBeInTheDocument();
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
  });

  it("shows empty state when no data and not loading", () => {
    (useDetailedPlatformStats as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByText("Platform Statistics")).toBeInTheDocument();
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    expect(screen.getByTestId("system-stats-empty")).toBeInTheDocument();
    expect(screen.getByTestId("audit-log")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (useDetailedPlatformStats as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByTestId("system-stats-loading")).toBeInTheDocument();
  });

  it("displays stats when data is available", () => {
    const mockStats = {
      users_total: 100,
      users_active_week: 42,
      organizations: 10,
      books: 50,
      ai_tasks_month: 200,
      tokens_month: 50000,
      storage_used_bytes: 1073741824,
      monthly_revenue: 5000,
    };

    (useDetailedPlatformStats as jest.Mock).mockReturnValue({
      data: mockStats,
      isLoading: false,
      isError: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByTestId("system-stats")).toBeInTheDocument();
  });

  it("displays error state when API call fails", () => {
    (useDetailedPlatformStats as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("Network error"),
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByTestId("system-stats-error")).toBeInTheDocument();
  });
});
