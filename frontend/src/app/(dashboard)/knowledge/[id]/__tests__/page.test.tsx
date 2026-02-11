import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks -- set up before component imports
// ---------------------------------------------------------------------------

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  useParams: () => mockParams,
  usePathname: () => "/knowledge/entry-1",
  useSearchParams: () => new URLSearchParams(),
}));

let mockParams: Record<string, string | string[]> = { id: "entry-1" };

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

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  ArrowLeft: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-arrow-left" {...props} />
  ),
  Globe: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-globe" {...props} />
  ),
  FileText: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-file-text" {...props} />
  ),
  PenLine: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-penline" {...props} />
  ),
  Paperclip: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-paperclip" {...props} />
  ),
  Sparkles: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-sparkles" {...props} />
  ),
  Trash2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-trash" {...props} />
  ),
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-loader" {...props} />
  ),
  X: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-x" {...props} />
  ),
}));

// Mock knowledge hooks
const mockUseKnowledgeEntry = jest.fn();
const mockDeleteMutateAsync = jest.fn();
const mockUseDeleteEntry = jest.fn();
const mockSummarizeMutateAsync = jest.fn();
const mockUseSummarizeEntry = jest.fn();

jest.mock("@/modules/knowledge/hooks", () => ({
  useKnowledgeEntry: (...args: unknown[]) => mockUseKnowledgeEntry(...args),
  useDeleteEntry: (...args: unknown[]) => mockUseDeleteEntry(...args),
  useSummarizeEntry: (...args: unknown[]) => mockUseSummarizeEntry(...args),
}));

// Mock Radix UI Dialog primitives for ConfirmDialog
let capturedOnOpenChange: ((open: boolean) => void) | undefined;

jest.mock("@radix-ui/react-dialog", () => ({
  Root: ({
    children,
    open,
    onOpenChange,
  }: {
    children: React.ReactNode;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
  }) => {
    capturedOnOpenChange = onOpenChange;
    return open ? <div data-testid="dialog-root">{children}</div> : null;
  },
  Portal: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-portal">{children}</div>
  ),
  Overlay: React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
    (props, ref) => <div ref={ref} data-testid="dialog-overlay" {...props} />
  ),
  Content: React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
    ({ children, ...props }, ref) => (
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        data-testid="dialog-content"
        {...props}
      >
        {children}
      </div>
    )
  ),
  Title: React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
    ({ children, ...props }, ref) => (
      <h2 ref={ref} {...props}>
        {children}
      </h2>
    )
  ),
  Description: React.forwardRef<
    HTMLParagraphElement,
    React.HTMLAttributes<HTMLParagraphElement>
  >(({ children, ...props }, ref) => (
    <p ref={ref} {...props}>
      {children}
    </p>
  )),
  Close: React.forwardRef<
    HTMLButtonElement,
    React.ButtonHTMLAttributes<HTMLButtonElement>
  >(({ children, ...props }, ref) => (
    <button ref={ref} {...props}>
      {children}
    </button>
  )),
}));

// Mock Radix Slot so that Button renders correctly
jest.mock("@radix-ui/react-slot", () => ({
  Slot: React.forwardRef(
    (
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLDivElement>
    ) => {
      if (React.isValidElement(children)) {
        return React.cloneElement(children, {
          ...props,
          ref,
        } as Record<string, unknown>);
      }
      return (
        <div ref={ref} {...props}>
          {children}
        </div>
      );
    }
  ),
}));

// ---------------------------------------------------------------------------
// Import the component under test AFTER mocks are established
// ---------------------------------------------------------------------------
import KnowledgeEntryDetailPage from "../page";

// ---------------------------------------------------------------------------
// Fixture data
// ---------------------------------------------------------------------------

const mockEntry = {
  id: "entry-1",
  org_id: "org-1",
  title: "Research on Publishing Trends",
  content: "This is the detailed content of the knowledge entry about publishing trends in 2025.",
  source_url: "https://example.com/research",
  source_type: "url" as const,
  tags: ["research", "publishing"],
  credibility_score: 0.85,
  metadata: { author: "Jane Doe" },
  created_at: "2025-06-01T00:00:00Z",
  updated_at: "2025-06-15T00:00:00Z",
  deleted_at: null,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupDefaultMocks(overrides?: {
  entry?: unknown;
  isLoading?: boolean;
  deletePending?: boolean;
  summarizePending?: boolean;
}) {
  mockUseKnowledgeEntry.mockReturnValue({
    data: overrides?.entry !== undefined ? overrides.entry : mockEntry,
    isLoading: overrides?.isLoading ?? false,
    error: null,
    isError: false,
  });

  mockDeleteMutateAsync.mockResolvedValue(undefined);
  mockUseDeleteEntry.mockReturnValue({
    mutateAsync: mockDeleteMutateAsync,
    isPending: overrides?.deletePending ?? false,
  });

  mockSummarizeMutateAsync.mockResolvedValue({
    entry_id: "entry-1",
    summary: "This is a summary of the entry.",
    key_points: ["Point A", "Point B"],
    suggested_tags: ["trend", "2025"],
  });
  mockUseSummarizeEntry.mockReturnValue({
    mutateAsync: mockSummarizeMutateAsync,
    isPending: overrides?.summarizePending ?? false,
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("KnowledgeEntryDetailPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockParams = { id: "entry-1" };
    capturedOnOpenChange = undefined;
    setupDefaultMocks();
  });

  // -----------------------------------------------------------------------
  // 1. Basic render
  // -----------------------------------------------------------------------
  it("renders without crashing", () => {
    const { container } = render(<KnowledgeEntryDetailPage />);
    expect(container).toBeTruthy();
  });

  // -----------------------------------------------------------------------
  // 2. Entry title and content display
  // -----------------------------------------------------------------------
  it("displays the entry title and content when loaded", () => {
    render(<KnowledgeEntryDetailPage />);

    expect(
      screen.getByRole("heading", { name: /Research on Publishing Trends/i })
    ).toBeInTheDocument();

    expect(
      screen.getByText(/detailed content of the knowledge entry/i)
    ).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 3. Back button navigates to /knowledge
  // -----------------------------------------------------------------------
  it("has a back button that navigates to /knowledge", async () => {
    const user = userEvent.setup();
    render(<KnowledgeEntryDetailPage />);

    const backButton = screen.getByText(/Back to Knowledge Vault/i);
    expect(backButton).toBeInTheDocument();

    await user.click(backButton);

    expect(mockPush).toHaveBeenCalledWith("/knowledge");
  });

  // -----------------------------------------------------------------------
  // 4. Loading state
  // -----------------------------------------------------------------------
  it("shows a loading spinner while entry data is loading", () => {
    setupDefaultMocks({ isLoading: true, entry: undefined });
    const { container } = render(<KnowledgeEntryDetailPage />);

    // The loading state renders an animated spinner
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();

    // Entry title should NOT be present during loading
    expect(
      screen.queryByText("Research on Publishing Trends")
    ).not.toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 5. Error state -- entry not found
  // -----------------------------------------------------------------------
  it("shows 'Entry not found' when the entry does not exist", () => {
    setupDefaultMocks({ entry: null });
    render(<KnowledgeEntryDetailPage />);

    expect(screen.getByText("Entry not found")).toBeInTheDocument();
    expect(
      screen.getByText(/Back to Knowledge Vault/i)
    ).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 6. Invalid route param shows error state
  // -----------------------------------------------------------------------
  it("shows 'Invalid entry ID' when route param is empty", () => {
    mockParams = { id: "" };
    render(<KnowledgeEntryDetailPage />);

    expect(screen.getByText("Invalid entry ID")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 7. ConfirmDialog appears on delete click (NOT native confirm)
  // -----------------------------------------------------------------------
  it("opens the ConfirmDialog when the Delete button is clicked", async () => {
    const user = userEvent.setup();
    render(<KnowledgeEntryDetailPage />);

    // Confirm dialog should NOT be visible initially
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    // Click the delete button
    const deleteButton = screen.getByRole("button", { name: /delete/i });
    await user.click(deleteButton);

    // ConfirmDialog should now be visible
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(
      screen.getByText(/are you sure you want to delete this entry/i)
    ).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 8. ConfirmDialog cancel does not delete
  // -----------------------------------------------------------------------
  it("does not delete when Cancel is clicked in the ConfirmDialog", async () => {
    const user = userEvent.setup();
    render(<KnowledgeEntryDetailPage />);

    // Open the confirm dialog
    const deleteButton = screen.getByRole("button", { name: /delete/i });
    await user.click(deleteButton);

    expect(screen.getByRole("dialog")).toBeInTheDocument();

    // Click the Cancel button
    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);

    // Delete mutation should NOT have been called
    expect(mockDeleteMutateAsync).not.toHaveBeenCalled();

    // Dialog should close
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 9. ConfirmDialog confirm triggers delete
  // -----------------------------------------------------------------------
  it("calls delete mutation and navigates away when confirm is clicked", async () => {
    const user = userEvent.setup();
    mockDeleteMutateAsync.mockResolvedValue(undefined);
    render(<KnowledgeEntryDetailPage />);

    // Open the confirm dialog
    const deleteButton = screen.getByRole("button", { name: /delete/i });
    await user.click(deleteButton);

    // Click the confirm/Delete button in the dialog
    // The ConfirmDialog has confirmText="Delete"
    const confirmButtons = screen.getAllByRole("button", { name: /delete/i });
    // The second "Delete" button is the one inside the dialog
    const confirmDeleteButton = confirmButtons[confirmButtons.length - 1];
    await user.click(confirmDeleteButton);

    await waitFor(() => {
      expect(mockDeleteMutateAsync).toHaveBeenCalledWith("entry-1");
    });

    // Should navigate back to knowledge vault
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/knowledge");
    });
  });

  // -----------------------------------------------------------------------
  // 10. Tags display
  // -----------------------------------------------------------------------
  it("displays the entry tags", () => {
    render(<KnowledgeEntryDetailPage />);

    expect(screen.getByText("research")).toBeInTheDocument();
    expect(screen.getByText("publishing")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 11. Source URL display
  // -----------------------------------------------------------------------
  it("displays the source URL as a link", () => {
    render(<KnowledgeEntryDetailPage />);

    const sourceLink = screen.getByText("https://example.com/research");
    expect(sourceLink).toBeInTheDocument();
    expect(sourceLink.closest("a")).toHaveAttribute(
      "href",
      "https://example.com/research"
    );
    expect(sourceLink.closest("a")).toHaveAttribute("target", "_blank");
  });

  // -----------------------------------------------------------------------
  // 12. AI Summary button triggers summarization
  // -----------------------------------------------------------------------
  it("calls summarize mutation when AI Summary button is clicked", async () => {
    const user = userEvent.setup();
    render(<KnowledgeEntryDetailPage />);

    const summaryButton = screen.getByRole("button", { name: /ai summary/i });
    await user.click(summaryButton);

    await waitFor(() => {
      expect(mockSummarizeMutateAsync).toHaveBeenCalledTimes(1);
    });
  });

  // -----------------------------------------------------------------------
  // 13. AI Summary results display
  // -----------------------------------------------------------------------
  it("displays AI summary results after successful summarization", async () => {
    const user = userEvent.setup();
    render(<KnowledgeEntryDetailPage />);

    const summaryButton = screen.getByRole("button", { name: /ai summary/i });
    await user.click(summaryButton);

    await waitFor(() => {
      expect(
        screen.getByText("This is a summary of the entry.")
      ).toBeInTheDocument();
    });

    // Key points
    expect(screen.getByText("Point A")).toBeInTheDocument();
    expect(screen.getByText("Point B")).toBeInTheDocument();

    // Suggested tags
    expect(screen.getByText("trend")).toBeInTheDocument();
    expect(screen.getByText("2025")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 14. Credibility score display
  // -----------------------------------------------------------------------
  it("displays the credibility score as a percentage", () => {
    render(<KnowledgeEntryDetailPage />);

    expect(screen.getByText("85% credibility")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 15. Metadata display
  // -----------------------------------------------------------------------
  it("displays the metadata section when metadata exists", () => {
    render(<KnowledgeEntryDetailPage />);

    expect(screen.getByText("Metadata")).toBeInTheDocument();
    // The metadata is rendered as JSON
    expect(screen.getByText(/"author": "Jane Doe"/)).toBeInTheDocument();
  });
});
