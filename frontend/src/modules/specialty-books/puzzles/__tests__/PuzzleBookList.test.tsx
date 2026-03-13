import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
}));

jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn().mockReturnValue({
    data: null,
    isLoading: false,
    error: null,
  }),
  useQueryClient: jest.fn().mockReturnValue({
    invalidateQueries: jest.fn(),
  }),
  useMutation: jest.fn().mockReturnValue({
    mutate: jest.fn(),
    isPending: false,
  }),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
  },
}));

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

jest.mock("@/hooks/use-api", () => ({
  extractApiError: jest.fn((e: Error) => e.message),
}));

// ─── Import after mocks ────────────────────────────────────────────────────

import { PuzzleBookList } from "../components/PuzzleBookList";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("PuzzleBookList", () => {
  const mockOnCreateNew = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the component with empty state", () => {
    render(<PuzzleBookList onCreateNew={mockOnCreateNew} />);

    expect(screen.getByText("No puzzle books yet")).toBeInTheDocument();
    expect(
      screen.getByText("Create your first puzzle book to get started."),
    ).toBeInTheDocument();
  });

  it("renders search input", () => {
    render(<PuzzleBookList onCreateNew={mockOnCreateNew} />);

    expect(
      screen.getByPlaceholderText("Search puzzle books..."),
    ).toBeInTheDocument();
  });

  it("renders the new puzzle book button in empty state", () => {
    render(<PuzzleBookList onCreateNew={mockOnCreateNew} />);

    const button = screen.getByRole("button", { name: /new puzzle book/i });
    expect(button).toBeInTheDocument();
  });

  it("renders with loading skeletons", () => {
    const { useQuery } = require("@tanstack/react-query");
    useQuery.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    const { container } = render(
      <PuzzleBookList onCreateNew={mockOnCreateNew} />,
    );

    // Should show skeleton cards
    const skeletons = container.querySelectorAll("[class*='animate-pulse']");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders book cards when data is available", () => {
    const { useQuery } = require("@tanstack/react-query");
    useQuery.mockReturnValue({
      data: {
        items: [
          {
            id: "1",
            title: "My Word Search Book",
            puzzle_types: ["word_search"],
            puzzle_count: 50,
            difficulty_mode: "progressive",
            audience: "adults",
            status: "draft",
            qa_score: 85,
            created_at: "2026-01-01T00:00:00Z",
          },
          {
            id: "2",
            title: "Kids Maze Fun",
            puzzle_types: ["maze", "word_search"],
            puzzle_count: 30,
            difficulty_mode: "fixed",
            audience: "kids",
            status: "generating",
            created_at: "2026-01-02T00:00:00Z",
          },
        ],
        total: 2,
        page: 1,
        page_size: 50,
      },
      isLoading: false,
      error: null,
    });

    render(<PuzzleBookList onCreateNew={mockOnCreateNew} />);

    expect(screen.getByText("My Word Search Book")).toBeInTheDocument();
    expect(screen.getByText("Kids Maze Fun")).toBeInTheDocument();
    expect(screen.getByText("50 puzzles")).toBeInTheDocument();
    expect(screen.getByText("30 puzzles")).toBeInTheDocument();
  });
});
