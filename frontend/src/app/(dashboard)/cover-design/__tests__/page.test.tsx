import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CoverDesignPage from "../page";

jest.mock("@/modules/cover-design/hooks", () => ({
  useCovers: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
  })),
}));

jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  Plus: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-plus" {...props} />
  ),
  Palette: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-palette" {...props} />
  ),
}));

jest.mock("@/modules/cover-design/components/CoverGallery", () => ({
  CoverGallery: ({ covers, isLoading, emptyMessage }: any) => {
    if (isLoading) return <div data-testid="cover-gallery-loading">Loading...</div>;
    if (!covers || covers.length === 0) return <div data-testid="cover-gallery-empty">{emptyMessage}</div>;
    return <div data-testid="cover-gallery">{covers.length} covers</div>;
  },
}));

import { useCovers } from "@/modules/cover-design/hooks";

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

describe("CoverDesignPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders without crashing", () => {
    (useCovers as jest.Mock).mockReturnValue({
      data: [],
      isPending: false,
      error: null,
    });

    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByText("Cover Design Studio")).toBeInTheDocument();
  });

  it("shows key elements and description", () => {
    (useCovers as jest.Mock).mockReturnValue({
      data: [],
      isPending: false,
      error: null,
    });

    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByText("Cover Design Studio")).toBeInTheDocument();
    expect(
      screen.getByText(/Create stunning book covers with AI-powered design/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generate new cover/i })).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (useCovers as jest.Mock).mockReturnValue({
      data: undefined,
      isPending: true,
      error: null,
    });

    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByTestId("cover-gallery-loading")).toBeInTheDocument();
  });

  it("shows empty state when no covers exist", () => {
    (useCovers as jest.Mock).mockReturnValue({
      data: [],
      isPending: false,
      error: null,
    });

    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByTestId("cover-gallery-empty")).toBeInTheDocument();
    expect(
      screen.getByText(/No covers yet. Click 'Generate Cover' to create your first design./i)
    ).toBeInTheDocument();
  });

  it("displays covers when data is available", () => {
    const mockCovers = [
      { id: "1", title: "Cover 1" },
      { id: "2", title: "Cover 2" },
    ];

    (useCovers as jest.Mock).mockReturnValue({
      data: mockCovers,
      isPending: false,
      error: null,
    });

    renderWithProviders(<CoverDesignPage />);

    expect(screen.getByTestId("cover-gallery")).toBeInTheDocument();
  });
});
