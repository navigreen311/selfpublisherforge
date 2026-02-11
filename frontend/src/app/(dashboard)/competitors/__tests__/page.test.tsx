import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CompetitorsPage from "../page";

jest.mock("@/modules/competitors/components/CompetitorDashboard", () => ({
  CompetitorDashboard: () => (
    <div data-testid="competitor-dashboard">
      <h1>Competitor Analysis</h1>
      <p>Track and analyze your competition</p>
    </div>
  ),
}));

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

describe("CompetitorsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders without crashing", () => {
    renderWithProviders(<CompetitorsPage />);

    expect(screen.getByTestId("competitor-dashboard")).toBeInTheDocument();
  });

  it("shows the competitor dashboard component", () => {
    renderWithProviders(<CompetitorsPage />);

    expect(screen.getByText("Competitor Analysis")).toBeInTheDocument();
    expect(screen.getByText("Track and analyze your competition")).toBeInTheDocument();
  });
});
