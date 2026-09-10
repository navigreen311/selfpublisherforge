import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/writing",
}));

jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { id: "1", org_id: "org1" },
    isAuthenticated: true,
  }),
}));

// Mock next/link to render a plain anchor
jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// Mock the writing module hooks
const mockUseBooks = jest.fn();
const mockUseWritingSessions = jest.fn();

jest.mock("@/modules/writing/hooks", () => ({
  useBooks: (...args: unknown[]) => mockUseBooks(...args),
  useWritingSessions: (...args: unknown[]) => mockUseWritingSessions(...args),
}));

// ---------------------------------------------------------------------------
// Import the component under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import WritingStudioPage from "../page";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const mockBooks = [
  {
    id: "book-1",
    title: "The Dragon's Oath",
    status: "writing",
    format: "epub",
    project_id: "proj-1",
    chapter_count: 12,
    word_count: 45000,
    created_at: "2025-01-15T00:00:00Z",
    updated_at: "2025-06-10T14:00:00Z",
  },
  {
    id: "book-2",
    title: "Quantum Horizons",
    status: "draft",
    format: "epub",
    project_id: "proj-2",
    chapter_count: 3,
    word_count: 8500,
    created_at: "2025-03-01T00:00:00Z",
    updated_at: "2025-07-01T09:00:00Z",
  },
];

const mockSessions = [
  {
    id: "sess-1",
    user_id: "user-1",
    book_id: "book-1",
    words_written: 1500,
    duration_minutes: 45,
    chapter_id: "ch-1",
    notes: "Good progress on chapter 5",
    created_at: new Date().toISOString(),
    book_title: "The Dragon's Oath",
  },
  {
    id: "sess-2",
    user_id: "user-1",
    book_id: "book-2",
    words_written: 800,
    duration_minutes: 30,
    chapter_id: null,
    notes: "",
    created_at: new Date(Date.now() - 86_400_000).toISOString(),
    book_title: "Quantum Horizons",
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupLoadedState() {
  mockUseBooks.mockReturnValue({
    data: mockBooks,
    isLoading: false,
    error: null,
  });
  mockUseWritingSessions.mockReturnValue({
    data: mockSessions,
    isLoading: false,
    error: null,
  });
}

function setupLoadingState() {
  mockUseBooks.mockReturnValue({
    data: undefined,
    isLoading: true,
    error: null,
  });
  mockUseWritingSessions.mockReturnValue({
    data: undefined,
    isLoading: true,
    error: null,
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("WritingStudioPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders writing studio page with heading and description", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    expect(
      screen.getByRole("heading", { level: 1 })
    ).toHaveTextContent("Writing Studio");
    expect(
      screen.getByText(
        "Write, edit, and polish your manuscripts with AI-powered assistance."
      )
    ).toBeInTheDocument();
  });

  it("shows quick action cards (New Manuscript, AI Outline Generator, Writing Analytics)", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    expect(screen.getByText("New Manuscript")).toBeInTheDocument();
    expect(screen.getByText("AI Outline Generator")).toBeInTheDocument();
    expect(screen.getByText("Writing Analytics")).toBeInTheDocument();

    // Descriptions for each card
    expect(
      screen.getByText(
        "Start a new book from scratch or with an AI-generated outline."
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Generate a complete book outline with chapter summaries."
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Track your writing sessions, word counts, and productivity."
      )
    ).toBeInTheDocument();
  });

  it("AI Outline Generator card links to /writing/outline", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    const outlineLink = screen.getByText("AI Outline Generator").closest("a");
    expect(outlineLink).toHaveAttribute("href", "/writing/outline");
  });

  it("shows recent writing projects (book list)", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    // Section heading
    expect(screen.getByText("Your Manuscripts")).toBeInTheDocument();

    // Book titles visible
    expect(
      screen.getAllByText("The Dragon's Oath").length
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("Quantum Horizons").length
    ).toBeGreaterThanOrEqual(1);

    // Status badges
    expect(screen.getByText("Writing")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();

    // Word counts
    expect(screen.getAllByText(/45,000\s+words/)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/8,500\s+words/)[0]).toBeInTheDocument();

    // Chapter counts
    expect(screen.getByText("12 chapters")).toBeInTheDocument();
    expect(screen.getByText("3 chapters")).toBeInTheDocument();
  });

  it("loading state displays skeletons", () => {
    setupLoadingState();

    const { container } = render(<WritingStudioPage />);

    // Page heading should still be visible during loading
    expect(
      screen.getByRole("heading", { level: 1 })
    ).toHaveTextContent("Writing Studio");

    // Loading skeleton elements should render with animate-pulse class
    const pulsingElements = container.querySelectorAll(".animate-pulse");
    expect(pulsingElements.length).toBeGreaterThanOrEqual(3);
  });

  it("shows recent writing sessions table", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    expect(screen.getByText("Recent Writing Sessions")).toBeInTheDocument();

    // Table headers
    expect(screen.getByText("Book")).toBeInTheDocument();
    expect(screen.getByText("Words Written")).toBeInTheDocument();
    expect(screen.getByText("Duration")).toBeInTheDocument();
    expect(screen.getByText("Date")).toBeInTheDocument();

    // Session data
    expect(screen.getByText("1,500")).toBeInTheDocument();
    expect(screen.getByText("800")).toBeInTheDocument();
    expect(screen.getByText("45 min")).toBeInTheDocument();
    expect(screen.getByText("30 min")).toBeInTheDocument();
  });

  it("shows empty state when no books exist", () => {
    mockUseBooks.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });
    mockUseWritingSessions.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    render(<WritingStudioPage />);

    expect(screen.getByText("No manuscripts yet")).toBeInTheDocument();
    expect(
      screen.getByText(/Start your first book to begin writing/i)
    ).toBeInTheDocument();

    const startLink = screen.getByRole("link", { name: /start your first book/i });
    expect(startLink).toHaveAttribute("href", "/writing/new");
  });

  it("shows error banner when books fail to load", () => {
    mockUseBooks.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network error"),
    });
    mockUseWritingSessions.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    render(<WritingStudioPage />);

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Network error")).toBeInTheDocument();
  });

  it("filters books by search query", async () => {
    const user = userEvent.setup();
    setupLoadedState();

    render(<WritingStudioPage />);

    const searchInput = screen.getByPlaceholderText("Search manuscripts...");
    await user.type(searchInput, "Dragon");

    // Only matching book link should remain
    const allLinks = screen.getAllByRole("link");
    const bookEditorLinks = allLinks.filter((link) =>
      link.getAttribute("href")?.match(/^\/writing\/book-\d+$/)
    );
    expect(bookEditorLinks).toHaveLength(1);
    expect(bookEditorLinks[0]).toHaveAttribute("href", "/writing/book-1");
  });

  it("book cards link to their respective editor pages", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    const allLinks = screen.getAllByRole("link");
    const bookEditorLinks = allLinks.filter((link) =>
      link.getAttribute("href")?.match(/^\/writing\/book-\d+$/)
    );
    // The list is sorted for display, so assert the set rather than the order.
    expect(bookEditorLinks.map((link) => link.getAttribute("href")).sort()).toEqual([
      "/writing/book-1",
      "/writing/book-2",
    ]);
  });
});
