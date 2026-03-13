import React from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

// Mock hooks
const mockUseChildrensBooks = jest.fn();
jest.mock("../hooks", () => ({
  useChildrensBooks: (...args: unknown[]) => mockUseChildrensBooks(...args),
}));

import { ChildrensBookList } from "../components/ChildrensBookList";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("ChildrensBookList", () => {
  const onCreateNew = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders loading skeletons while fetching", () => {
    mockUseChildrensBooks.mockReturnValue({ data: undefined, isLoading: true });
    render(<ChildrensBookList onCreateNew={onCreateNew} />, { wrapper });
    // Skeletons rendered (6 skeleton cards)
    expect(document.querySelectorAll("[class*=skeleton], [class*=Skeleton]").length).toBeGreaterThanOrEqual(1);
  });

  it("renders empty state when no books exist", () => {
    mockUseChildrensBooks.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 100 },
      isLoading: false,
    });
    render(<ChildrensBookList onCreateNew={onCreateNew} />, { wrapper });
    expect(screen.getByText(/no children.*books yet/i)).toBeInTheDocument();
  });

  it("renders book cards when data exists", () => {
    mockUseChildrensBooks.mockReturnValue({
      data: {
        items: [
          {
            id: "1",
            title: "Luna the Kitten",
            age_range: "picture",
            status: "draft",
            page_count: 32,
            qa_score: 85,
            cover_url: null,
            created_at: "2026-01-01",
            updated_at: "2026-01-02",
          },
        ],
        total: 1,
        page: 1,
        page_size: 100,
      },
      isLoading: false,
    });
    render(<ChildrensBookList onCreateNew={onCreateNew} />, { wrapper });
    expect(screen.getByText("Luna the Kitten")).toBeInTheDocument();
    expect(screen.getByText("32 pages")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
  });
});
