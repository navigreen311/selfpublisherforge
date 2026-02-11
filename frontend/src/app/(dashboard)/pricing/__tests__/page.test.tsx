import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PricingPage from "../page";

jest.mock("@/modules/pricing/components/PricingDashboard", () => ({
  PricingDashboard: () => (
    <div data-testid="pricing-dashboard">
      <h1>Pricing Strategy</h1>
      <p>Optimize your book pricing</p>
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

describe("PricingPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders without crashing", () => {
    renderWithProviders(<PricingPage />);

    expect(screen.getByTestId("pricing-dashboard")).toBeInTheDocument();
  });

  it("shows the pricing dashboard component", () => {
    renderWithProviders(<PricingPage />);

    expect(screen.getByText("Pricing Strategy")).toBeInTheDocument();
    expect(screen.getByText("Optimize your book pricing")).toBeInTheDocument();
  });
});
