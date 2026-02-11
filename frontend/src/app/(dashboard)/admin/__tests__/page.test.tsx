import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AdminOverviewPage from "../page";

jest.mock("@/modules/admin/hooks", () => ({
  usePlatformStats: jest.fn(),
}));

jest.mock("@/modules/admin/components/SystemStats", () => ({
  SystemStats: ({ stats, isLoading }: any) => {
    if (isLoading) return <div data-testid="system-stats-loading">Loading stats...</div>;
    if (!stats) return <div data-testid="system-stats-empty">No stats</div>;
    return <div data-testid="system-stats">Stats loaded</div>;
  },
}));

jest.mock("@/modules/admin/components/AuditLog", () => ({
  AuditLog: () => <div data-testid="audit-log">Audit log</div>,
}));

import { usePlatformStats } from "@/modules/admin/hooks";

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
    (usePlatformStats as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByText("Platform Statistics")).toBeInTheDocument();
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
  });

  it("shows key sections", () => {
    (usePlatformStats as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByText("Platform Statistics")).toBeInTheDocument();
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    expect(screen.getByTestId("system-stats-empty")).toBeInTheDocument();
    expect(screen.getByTestId("audit-log")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (usePlatformStats as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByTestId("system-stats-loading")).toBeInTheDocument();
  });

  it("displays stats when data is available", () => {
    const mockStats = {
      total_users: 100,
      total_orgs: 10,
      active_subscriptions: 50,
    };

    (usePlatformStats as jest.Mock).mockReturnValue({
      data: mockStats,
      isLoading: false,
      error: null,
    });

    renderWithProviders(<AdminOverviewPage />);

    expect(screen.getByTestId("system-stats")).toBeInTheDocument();
  });
});
