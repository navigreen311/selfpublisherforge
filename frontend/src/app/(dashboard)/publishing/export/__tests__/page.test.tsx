import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks -- set up before component imports
// ---------------------------------------------------------------------------

// Mock next/link to render a plain anchor
jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} {...rest}>
        {children}
      </a>
    );
  };
});

// Mock Skeleton to render a simple div
jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
    <div data-testid="skeleton" className={className} {...props} />
  ),
}));

// Configurable mock return values for useBooks and useChapters
const mockUseBooks = jest.fn<ReturnType<typeof import("@/modules/writing/hooks").useBooks>, []>();
const mockUseChapters = jest.fn<ReturnType<typeof import("@/modules/writing/hooks").useChapters>, [string]>();

jest.mock("@/modules/writing/hooks", () => ({
  useBooks: (...args: unknown[]) => mockUseBooks(...(args as [])),
  useChapters: (...args: unknown[]) => mockUseChapters(...(args as [string])),
}));

// Track props passed to ExportWizard so we can assert on them
const mockExportWizardProps = jest.fn();

jest.mock("@/modules/publishing/components/ExportWizard", () => ({
  ExportWizard: (props: Record<string, unknown>) => {
    mockExportWizardProps(props);
    return <div data-testid="export-wizard">ExportWizard Mock</div>;
  },
}));

// ---------------------------------------------------------------------------
// Import the component under test AFTER mocks are established
// ---------------------------------------------------------------------------
import ExportPage from "../page";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MOCK_BOOKS = [
  { id: "book-1", title: "My First Novel", status: "draft" },
  { id: "book-2", title: "Sequel", status: "published" },
];

const MOCK_CHAPTERS = [
  {
    id: "ch-1",
    book_id: "book-1",
    title: "Chapter 1: The Beginning",
    content: "Once upon a time...",
    order: 1,
    synopsis: "",
    word_count: 100,
    created_at: "2025-01-01",
    updated_at: "2025-01-01",
  },
  {
    id: "ch-2",
    book_id: "book-1",
    title: "Chapter 2: The Middle",
    content: "Things happened.",
    order: 2,
    synopsis: "",
    word_count: 200,
    created_at: "2025-01-02",
    updated_at: "2025-01-02",
  },
];

/** Standard query result shape for "loaded successfully" */
function loadedQuery<T>(data: T) {
  return {
    data,
    isLoading: false,
    error: null,
    isError: false,
    isPending: false,
    isSuccess: true,
    status: "success" as const,
  } as unknown as ReturnType<typeof import("@/modules/writing/hooks").useBooks>;
}

/** Standard query result shape for "loading" */
function loadingQuery() {
  return {
    data: undefined,
    isLoading: true,
    error: null,
    isError: false,
    isPending: true,
    isSuccess: false,
    status: "pending" as const,
  } as unknown as ReturnType<typeof import("@/modules/writing/hooks").useBooks>;
}

/** Standard query result shape for "error" */
function errorQuery(message: string) {
  return {
    data: undefined,
    isLoading: false,
    error: new Error(message),
    isError: true,
    isPending: false,
    isSuccess: false,
    status: "error" as const,
  } as unknown as ReturnType<typeof import("@/modules/writing/hooks").useBooks>;
}

/** Default setup: books loaded, no chapters yet (no book selected) */
function setupDefaults() {
  mockUseBooks.mockReturnValue(loadedQuery(MOCK_BOOKS) as never);
  mockUseChapters.mockReturnValue(loadedQuery([]) as never);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("Export Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setupDefaults();
  });

  // -----------------------------------------------------------------------
  // 1. Basic render
  // -----------------------------------------------------------------------
  it("renders without crashing", () => {
    const { container } = render(<ExportPage />);
    expect(container).toBeTruthy();
  });

  // -----------------------------------------------------------------------
  // 2. Breadcrumb navigation
  // -----------------------------------------------------------------------
  it("renders breadcrumb navigation with Publishing link and Export text", () => {
    render(<ExportPage />);

    const nav = screen.getByRole("navigation", { name: /breadcrumb/i });
    expect(nav).toBeInTheDocument();

    // Publishing link
    const publishingLink = within(nav).getByRole("link", {
      name: /publishing/i,
    });
    expect(publishingLink).toHaveAttribute("href", "/publishing");

    // Export as plain text (not a link)
    const exportText = within(nav).getByText("Export");
    expect(exportText.tagName).toBe("SPAN");
    expect(exportText.closest("a")).toBeNull();

    // Separator
    expect(within(nav).getByText("/")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 3. Page header
  // -----------------------------------------------------------------------
  it("renders the page heading and description", () => {
    render(<ExportPage />);

    expect(
      screen.getByRole("heading", { level: 1, name: /export manuscript/i })
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /generate an epub for digital distribution or a print-ready pdf for kdp/i
      )
    ).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 4. Book selector renders when books are loaded
  // -----------------------------------------------------------------------
  it("renders the book selector dropdown when books are loaded", () => {
    render(<ExportPage />);

    const selector = screen.getByRole("combobox", {
      name: /select a book/i,
    });
    expect(selector).toBeInTheDocument();

    // The placeholder option plus two book options
    const options = within(selector).getAllByRole("option");
    expect(options).toHaveLength(3); // placeholder + 2 books
    expect(options[0]).toHaveTextContent("-- Choose a book --");
    expect(options[1]).toHaveTextContent("My First Novel");
    expect(options[2]).toHaveTextContent("Sequel");
  });

  // -----------------------------------------------------------------------
  // 5. Loading state shows skeleton when books are loading
  // -----------------------------------------------------------------------
  it("displays a loading skeleton while books are loading", () => {
    mockUseBooks.mockReturnValue(loadingQuery() as never);

    render(<ExportPage />);

    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(1);

    // Book selector should NOT be present
    expect(
      screen.queryByRole("combobox", { name: /select a book/i })
    ).not.toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 6. Empty state when no books exist
  // -----------------------------------------------------------------------
  it("shows empty state when no books exist", () => {
    mockUseBooks.mockReturnValue(loadedQuery([]) as never);

    render(<ExportPage />);

    expect(screen.getByText(/no books found/i)).toBeInTheDocument();
    expect(
      screen.getByText(/create a project first before exporting/i)
    ).toBeInTheDocument();

    // Should have a link to create a project
    const createLink = screen.getByRole("link", {
      name: /create a project/i,
    });
    expect(createLink).toHaveAttribute("href", "/writing/new");
  });

  // -----------------------------------------------------------------------
  // 7. Error state handles API failures for books
  // -----------------------------------------------------------------------
  it("shows error alert when books API fails", () => {
    mockUseBooks.mockReturnValue(
      errorQuery("Network connection lost") as never
    );

    render(<ExportPage />);

    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
    expect(
      within(alert).getByText(/failed to load books/i)
    ).toBeInTheDocument();
    expect(
      within(alert).getByText(/network connection lost/i)
    ).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 8. ExportWizard is NOT shown before selecting a book
  // -----------------------------------------------------------------------
  it("does not render ExportWizard before a book is selected", () => {
    render(<ExportPage />);

    expect(screen.queryByTestId("export-wizard")).not.toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 9. Selecting a book and loading chapters shows chapter loading state
  // -----------------------------------------------------------------------
  it("shows chapters loading state after selecting a book", async () => {
    // Initially chapters are "loading" once a book is selected
    mockUseChapters.mockReturnValue(loadingQuery() as never);

    render(<ExportPage />);

    const selector = screen.getByRole("combobox", {
      name: /select a book/i,
    });

    await userEvent.selectOptions(selector, "book-1");

    // Should show a loading skeleton for chapters
    const chaptersLoading = screen.getByRole("status", {
      name: /loading chapters/i,
    });
    expect(chaptersLoading).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 10. ExportWizard receives proper props when book and chapters are ready
  // -----------------------------------------------------------------------
  it("renders ExportWizard with correct props when book is selected and chapters loaded", async () => {
    mockUseChapters.mockReturnValue(loadedQuery(MOCK_CHAPTERS) as never);

    render(<ExportPage />);

    const selector = screen.getByRole("combobox", {
      name: /select a book/i,
    });
    await userEvent.selectOptions(selector, "book-1");

    // ExportWizard should now be visible
    expect(screen.getByTestId("export-wizard")).toBeInTheDocument();

    // Check props
    expect(mockExportWizardProps).toHaveBeenCalledWith(
      expect.objectContaining({
        bookId: "book-1",
        chapters: expect.arrayContaining([
          expect.objectContaining({
            title: "Chapter 1: The Beginning",
            content: "Once upon a time...",
            order: 1,
          }),
        ]),
      })
    );
  });

  // -----------------------------------------------------------------------
  // 11. Chapters error state
  // -----------------------------------------------------------------------
  it("shows error alert when chapters API fails", async () => {
    mockUseChapters.mockReturnValue(
      errorQuery("Chapters fetch error") as never
    );

    render(<ExportPage />);

    const selector = screen.getByRole("combobox", {
      name: /select a book/i,
    });
    await userEvent.selectOptions(selector, "book-1");

    const alerts = screen.getAllByRole("alert");
    const chaptersAlert = alerts.find((el) =>
      el.textContent?.includes("Failed to load chapters")
    );
    expect(chaptersAlert).toBeTruthy();
    expect(chaptersAlert!.textContent).toContain("Chapters fetch error");
  });

  // -----------------------------------------------------------------------
  // 12. Empty chapters state
  // -----------------------------------------------------------------------
  it("shows empty chapters state when selected book has no chapters", async () => {
    mockUseChapters.mockReturnValue(loadedQuery([]) as never);

    render(<ExportPage />);

    const selector = screen.getByRole("combobox", {
      name: /select a book/i,
    });
    await userEvent.selectOptions(selector, "book-1");

    expect(screen.getByText(/no chapters yet/i)).toBeInTheDocument();
    expect(
      screen.getByText(/this book has no chapters to export/i)
    ).toBeInTheDocument();

    // Link to open in Writing Studio
    const studioLink = screen.getByRole("link", {
      name: /open in writing studio/i,
    });
    expect(studioLink).toHaveAttribute("href", "/writing/book-1");
  });

  // -----------------------------------------------------------------------
  // 13. Top-level layout classes
  // -----------------------------------------------------------------------
  it("applies space-y-6 to the top-level layout container", () => {
    const { container } = render(<ExportPage />);
    const topDiv = container.firstElementChild;
    expect(topDiv).toHaveClass("space-y-6");
  });

  // -----------------------------------------------------------------------
  // 14. ExportWizard card wrapper has correct styling
  // -----------------------------------------------------------------------
  it("wraps ExportWizard in a styled card container with book title info", async () => {
    mockUseChapters.mockReturnValue(loadedQuery(MOCK_CHAPTERS) as never);

    render(<ExportPage />);

    const selector = screen.getByRole("combobox", {
      name: /select a book/i,
    });
    await userEvent.selectOptions(selector, "book-1");

    // Find the wrapper around ExportWizard
    const wizard = screen.getByTestId("export-wizard");
    const wrapper = wizard.parentElement;
    // bg-card, not bg-white: the surface follows the theme token.
    expect(wrapper).toHaveClass(
      "rounded-lg",
      "border",
      "bg-card",
      "p-6",
      "shadow-sm"
    );

    // The title and chapter count are one interpolated sentence now, not a
    // bolded span inside surrounding text.
    expect(
      screen.getByText("Exporting My First Novel (2 chapters)")
    ).toBeInTheDocument();
  });
});
