import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

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
  {
    id: "book-3",
    title: "Cooking with Code",
    status: "editing",
    format: "pdf",
    project_id: "proj-3",
    chapter_count: 8,
    word_count: 22000,
    created_at: "2025-02-10T00:00:00Z",
    updated_at: "2025-05-20T11:00:00Z",
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
    created_at: new Date().toISOString(), // Today
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
    created_at: new Date(Date.now() - 86_400_000).toISOString(), // Yesterday
    book_title: "Quantum Horizons",
  },
  {
    id: "sess-3",
    user_id: "user-1",
    book_id: "book-3",
    words_written: 2200,
    duration_minutes: 60,
    chapter_id: "ch-3",
    notes: "Finished editing chapter 2",
    created_at: new Date(Date.now() - 3 * 86_400_000).toISOString(), // 3 days ago
    book_title: "Cooking with Code",
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Default mock state: loaded with data, no errors.
 */
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

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("WritingStudioPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders loading skeletons while books are being fetched", () => {
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

    const { container } = render(<WritingStudioPage />);

    // Page header should be visible even during loading
    expect(
      screen.getByRole("heading", { level: 1 })
    ).toHaveTextContent("Writing Studio");

    // Loading state renders skeleton elements with animate-pulse
    const pulsingElements = container.querySelectorAll(".animate-pulse");
    expect(pulsingElements.length).toBeGreaterThanOrEqual(3);
  });

  it("renders book list from API data", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    // All book titles should appear (they also appear in sessions table, so use getAllByText)
    expect(screen.getAllByText("The Dragon's Oath").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Quantum Horizons").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Cooking with Code").length).toBeGreaterThanOrEqual(1);

    // Status badges should be displayed (capitalized first letter)
    expect(screen.getByText("Writing")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Editing")).toBeInTheDocument();

    // Word counts should be displayed
    expect(screen.getByText("45,000 words")).toBeInTheDocument();
    expect(screen.getByText("8,500 words")).toBeInTheDocument();
    expect(screen.getByText("22,000 words")).toBeInTheDocument();

    // Chapter counts should be displayed
    expect(screen.getByText("12 chapters")).toBeInTheDocument();
    expect(screen.getByText("3 chapters")).toBeInTheDocument();
    expect(screen.getByText("8 chapters")).toBeInTheDocument();
  });

  it("shows empty state for new users with no books", () => {
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

    // There should be a link to start a new book
    const startLink = screen.getByRole("link", { name: /start your first book/i });
    expect(startLink).toBeInTheDocument();
    expect(startLink).toHaveAttribute("href", "/writing/new");
  });

  it("shows writing sessions table with session data", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    // The "Recent Writing Sessions" section heading
    expect(screen.getByText("Recent Writing Sessions")).toBeInTheDocument();

    // Table column headers
    expect(screen.getByText("Book")).toBeInTheDocument();
    expect(screen.getByText("Words Written")).toBeInTheDocument();
    expect(screen.getByText("Duration")).toBeInTheDocument();
    expect(screen.getByText("Date")).toBeInTheDocument();

    // Session data: word counts (formatted with commas)
    expect(screen.getByText("1,500")).toBeInTheDocument();
    expect(screen.getByText("800")).toBeInTheDocument();
    expect(screen.getByText("2,200")).toBeInTheDocument();

    // Duration values
    expect(screen.getByText("45 min")).toBeInTheDocument();
    expect(screen.getByText("30 min")).toBeInTheDocument();
    expect(screen.getByText("60 min")).toBeInTheDocument();

    // Date labels
    expect(screen.getByText("Today")).toBeInTheDocument();
    expect(screen.getByText("Yesterday")).toBeInTheDocument();
    expect(screen.getByText("3 days ago")).toBeInTheDocument();
  });

  it("shows no-sessions message when there are no writing sessions", () => {
    mockUseBooks.mockReturnValue({
      data: mockBooks,
      isLoading: false,
      error: null,
    });
    mockUseWritingSessions.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    render(<WritingStudioPage />);

    expect(
      screen.getByText(/No writing sessions recorded yet/i)
    ).toBeInTheDocument();
  });

  it("renders book cards as links to their editor pages", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    // Find links specifically pointing to /writing/<bookId>
    const allLinks = screen.getAllByRole("link");
    const bookEditorLinks = allLinks.filter((link) =>
      link.getAttribute("href")?.match(/^\/writing\/book-\d+$/)
    );
    expect(bookEditorLinks).toHaveLength(3);
    expect(bookEditorLinks[0]).toHaveAttribute("href", "/writing/book-1");
    expect(bookEditorLinks[1]).toHaveAttribute("href", "/writing/book-2");
    expect(bookEditorLinks[2]).toHaveAttribute("href", "/writing/book-3");
  });

  it("displays an error banner when book loading fails", () => {
    mockUseBooks.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Server is unavailable"),
    });
    mockUseWritingSessions.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    render(<WritingStudioPage />);

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Server is unavailable")).toBeInTheDocument();
  });

  it("renders quick action cards for New Manuscript, AI Outline, and Analytics", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    expect(screen.getByText("New Manuscript")).toBeInTheDocument();
    expect(screen.getByText("AI Outline Generator")).toBeInTheDocument();
    expect(screen.getByText("Writing Analytics")).toBeInTheDocument();

    // New Manuscript should link to /writing/new
    const newManuscriptLink = screen.getByText("New Manuscript").closest("a");
    expect(newManuscriptLink).toHaveAttribute("href", "/writing/new");
  });

  it("filters books by search query", async () => {
    const user = userEvent.setup();
    setupLoadedState();

    render(<WritingStudioPage />);

    // All books visible initially (titles may appear in both book list and sessions)
    expect(screen.getAllByText("The Dragon's Oath").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Quantum Horizons").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Cooking with Code").length).toBeGreaterThanOrEqual(1);

    // Type a search query
    const searchInput = screen.getByPlaceholderText("Search manuscripts...");
    await user.type(searchInput, "Dragon");

    // The book list section: only the matching book link should remain.
    // Non-matching book links should be gone from the book list.
    const allLinks = screen.getAllByRole("link");
    const bookEditorLinks = allLinks.filter((link) =>
      link.getAttribute("href")?.match(/^\/writing\/book-\d+$/)
    );
    // Only 1 book card link should remain (book-1 = Dragon's Oath)
    expect(bookEditorLinks).toHaveLength(1);
    expect(bookEditorLinks[0]).toHaveAttribute("href", "/writing/book-1");
  });

  it("shows no-match message when search matches nothing", async () => {
    const user = userEvent.setup();
    setupLoadedState();

    render(<WritingStudioPage />);

    const searchInput = screen.getByPlaceholderText("Search manuscripts...");
    await user.type(searchInput, "NonExistentTitle");

    expect(
      screen.getByText(/No manuscripts found matching/i)
    ).toBeInTheDocument();
  });

  it("renders the page description text", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    expect(
      screen.getByText(
        "Write, edit, and polish your manuscripts with AI-powered assistance."
      )
    ).toBeInTheDocument();
  });

  it("renders the Your Manuscripts section heading", () => {
    setupLoadedState();

    render(<WritingStudioPage />);

    expect(screen.getByText("Your Manuscripts")).toBeInTheDocument();
  });
});
