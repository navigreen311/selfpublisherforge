import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ValidationPage from "../page";

jest.mock("@/modules/publishing/hooks", () => ({
  useRunFullValidation: jest.fn(() => ({
    mutate: jest.fn(),
    isPending: false,
  })),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock("@/modules/publishing/components/ValidationDashboard", () => ({
  ValidationDashboard: ({ validation, onRunValidation, isRunning }: any) => (
    <div data-testid="validation-dashboard">
      {isRunning ? "Running validation..." : "Validation dashboard"}
    </div>
  ),
}));

jest.mock("@/modules/publishing/components/ValidationRunner", () => ({
  ValidationRunner: ({ bookId, onRun, isRunning }: any) => (
    <div data-testid="validation-runner">
      Validation runner for {bookId}
    </div>
  ),
}));

jest.mock("@/modules/publishing/components/ValidationResults", () => ({
  ValidationResults: ({ validation, onExportPdf }: any) => (
    <div data-testid="validation-results">Validation results</div>
  ),
}));

import { useRunFullValidation } from "@/modules/publishing/hooks";

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

describe("ValidationPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders without crashing", () => {
    (useRunFullValidation as jest.Mock).mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    });

    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("KDP Validation")).toBeInTheDocument();
  });

  it("shows key elements and description", () => {
    (useRunFullValidation as jest.Mock).mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    });

    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("KDP Validation")).toBeInTheDocument();
    expect(
      screen.getByText(/Pre-flight validation for Amazon KDP print and ebook requirements/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Select Book to Validate")).toBeInTheDocument();
  });

  it("shows validation dashboard and runner", () => {
    (useRunFullValidation as jest.Mock).mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    });

    renderWithProviders(<ValidationPage />);

    expect(screen.getByTestId("validation-dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("validation-runner")).toBeInTheDocument();
  });

  it("shows book selector with options", () => {
    (useRunFullValidation as jest.Mock).mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    });

    renderWithProviders(<ValidationPage />);

    const selector = screen.getByRole("combobox", { name: /select book to validate/i });
    expect(selector).toBeInTheDocument();
    expect(screen.getByText(/Sample Book - The Great Adventure/i)).toBeInTheDocument();
  });

  it("does not show results initially", () => {
    (useRunFullValidation as jest.Mock).mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    });

    renderWithProviders(<ValidationPage />);

    expect(screen.queryByTestId("validation-results")).not.toBeInTheDocument();
  });

  it("shows loading state when validation is running", () => {
    (useRunFullValidation as jest.Mock).mockReturnValue({
      mutate: jest.fn(),
      isPending: true,
    });

    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("Running validation...")).toBeInTheDocument();
  });
});
