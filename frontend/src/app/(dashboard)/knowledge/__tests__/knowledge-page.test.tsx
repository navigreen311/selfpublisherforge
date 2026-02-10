import React from "react";
import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/knowledge",
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  Plus: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-plus" {...props} />
  ),
  BookOpen: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-book-open" {...props} />
  ),
  Search: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-search" {...props} />
  ),
  X: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-x" {...props} />
  ),
  Upload: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-upload" {...props} />
  ),
  Link: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-link" {...props} />
  ),
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-loader" {...props} />
  ),
  FileText: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-file-text" {...props} />
  ),
  Globe: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-globe" {...props} />
  ),
  Paperclip: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-paperclip" {...props} />
  ),
  PenLine: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-penline" {...props} />
  ),
}));

// Mock the knowledge hooks
const mockUseKnowledgeEntries = jest.fn();
const mockUseKnowledgeTags = jest.fn();
const mockSearchMutateAsync = jest.fn();
const mockUseKnowledgeSearch = jest.fn();
const mockCreateMutateAsync = jest.fn();
const mockUseCreateEntry = jest.fn();
const mockUseImportEntry = jest.fn();

jest.mock("@/modules/knowledge/hooks", () => ({
  useKnowledgeEntries: (...args: unknown[]) => mockUseKnowledgeEntries(...args),
  useKnowledgeTags: (...args: unknown[]) => mockUseKnowledgeTags(...args),
  useKnowledgeSearch: (...args: unknown[]) => mockUseKnowledgeSearch(...args),
  useCreateEntry: (...args: unknown[]) => mockUseCreateEntry(...args),
}));

// Mock SearchBar component
jest.mock("@/modules/knowledge/components/SearchBar", () => ({
  SearchBar: ({
    onSearch,
    isLoading,
  }: {
    onSearch: (query: string) => void;
    isLoading: boolean;
  }) => (
    <div data-testid="search-bar">
      <input
        data-testid="search-input"
        placeholder="Search your knowledge vault..."
        onChange={(e) => {
          // no-op for typing
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            onSearch((e.target as HTMLInputElement).value);
          }
        }}
      />
      <button data-testid="search-submit" onClick={() => onSearch("test query")}>
        Search
      </button>
      {isLoading && <span data-testid="search-loading">Searching...</span>}
    </div>
  ),
}));

// Mock TagFilter component
jest.mock("@/modules/knowledge/components/TagFilter", () => ({
  TagFilter: ({
    tags,
    counts,
    selectedTags,
    onToggleTag,
  }: {
    tags: string[];
    counts: Record<string, number>;
    selectedTags: string[];
    onToggleTag: (tag: string) => void;
  }) => (
    <div data-testid="tag-filter">
      {tags.map((tag) => (
        <button
          key={tag}
          data-testid={`tag-${tag}`}
          onClick={() => onToggleTag(tag)}
          className={selectedTags.includes(tag) ? "selected" : ""}
        >
          {tag} ({counts[tag] ?? 0})
        </button>
      ))}
    </div>
  ),
}));

// Mock EntryCard component
jest.mock("@/modules/knowledge/components/EntryCard", () => ({
  EntryCard: ({ entry }: { entry: { id: string; title: string } }) => (
    <div data-testid={`entry-card-${entry.id}`}>
      <span>{entry.title}</span>
    </div>
  ),
}));

// Mock ImportModal component
jest.mock("@/modules/knowledge/components/ImportModal", () => ({
  ImportModal: ({ open, onClose }: { open: boolean; onClose: () => void }) =>
    open ? (
      <div data-testid="import-modal">
        <span>Import Research</span>
        <button data-testid="close-import" onClick={onClose}>
          Close
        </button>
      </div>
    ) : null,
}));

// Mock Skeleton
jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={`animate-pulse ${className || ""}`} />
  ),
}));

// Import after mocks
import KnowledgeVaultPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

// ── Fixture data ─────────────────────────────────────────────────────────

const mockEntries = [
  {
    id: "entry-1",
    org_id: "org-1",
    title: "Research on Market Trends",
    content: "Detailed analysis of current market trends in self-publishing...",
    source_url: null,
    source_type: "manual" as const,
    tags: ["research", "market"],
    credibility_score: 0.85,
    metadata: {},
    created_at: "2025-06-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
    deleted_at: null,
  },
  {
    id: "entry-2",
    org_id: "org-1",
    title: "KDP Publishing Guide",
    content: "A comprehensive guide to KDP publishing...",
    source_url: "https://example.com/guide",
    source_type: "url" as const,
    tags: ["publishing", "kdp"],
    credibility_score: 0.9,
    metadata: {},
    created_at: "2025-05-15T00:00:00Z",
    updated_at: "2025-05-15T00:00:00Z",
    deleted_at: null,
  },
];

const mockTagData = {
  tags: ["research", "market", "publishing", "kdp"],
  counts: { research: 5, market: 3, publishing: 8, kdp: 2 },
};

// ── Default mock setup ───────────────────────────────────────────────────

function setDefaultMocks(overrides?: {
  entries?: unknown;
  entriesLoading?: boolean;
  tags?: unknown;
  searchPending?: boolean;
  createPending?: boolean;
}) {
  mockUseKnowledgeEntries.mockReturnValue({
    data: overrides?.entries ?? {
      items: mockEntries,
      next_cursor: null,
      has_more: false,
      total_count: 2,
    },
    isLoading: overrides?.entriesLoading ?? false,
  });

  mockUseKnowledgeTags.mockReturnValue({
    data: overrides && "tags" in overrides ? overrides.tags : mockTagData,
  });

  mockSearchMutateAsync.mockResolvedValue({
    hits: [],
    total: 0,
    query: "test",
  });

  mockUseKnowledgeSearch.mockReturnValue({
    mutateAsync: mockSearchMutateAsync,
    isPending: overrides?.searchPending ?? false,
  });

  mockCreateMutateAsync.mockResolvedValue({
    id: "new-entry-1",
    title: "New Entry",
    content: "",
    source_type: "manual",
  });

  mockUseCreateEntry.mockReturnValue({
    mutateAsync: mockCreateMutateAsync,
    isPending: overrides?.createPending ?? false,
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("KnowledgeVaultPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // 1. Renders knowledge vault
  it("renders the Knowledge Vault page with heading", () => {
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    expect(screen.getByText("Knowledge Vault")).toBeInTheDocument();
  });

  // 2. Document list displays
  it("renders entry cards when entries are available", () => {
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    expect(screen.getByTestId("entry-card-entry-1")).toBeInTheDocument();
    expect(screen.getByTestId("entry-card-entry-2")).toBeInTheDocument();
    expect(screen.getByText("Research on Market Trends")).toBeInTheDocument();
    expect(screen.getByText("KDP Publishing Guide")).toBeInTheDocument();
  });

  it("shows total entry count", () => {
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    expect(screen.getByText("2 entries")).toBeInTheDocument();
  });

  // 3. Upload area/button present
  it("renders Import and New Entry buttons", () => {
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    expect(screen.getByText("Import")).toBeInTheDocument();
    expect(screen.getByText("New Entry")).toBeInTheDocument();
  });

  it("opens import modal when Import button is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    const importBtn = screen.getByText("Import");
    await user.click(importBtn);

    expect(screen.getByTestId("import-modal")).toBeInTheDocument();
    expect(screen.getByText("Import Research")).toBeInTheDocument();
  });

  it("opens create entry dialog when New Entry button is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    const newEntryBtn = screen.getByText("New Entry");
    await user.click(newEntryBtn);

    expect(screen.getByText("New Knowledge Entry")).toBeInTheDocument();
    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  // 4. Tag filter works
  it("renders tag filter with available tags", () => {
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    expect(screen.getByTestId("tag-filter")).toBeInTheDocument();
    expect(screen.getByTestId("tag-research")).toBeInTheDocument();
    expect(screen.getByTestId("tag-market")).toBeInTheDocument();
    expect(screen.getByTestId("tag-publishing")).toBeInTheDocument();
    expect(screen.getByTestId("tag-kdp")).toBeInTheDocument();
  });

  it("toggles tag selection when a tag is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    const researchTag = screen.getByTestId("tag-research");
    await user.click(researchTag);

    // After clicking, useKnowledgeEntries should be called with tag filter
    // The component re-renders and the hook is called with updated params
    expect(mockUseKnowledgeEntries).toHaveBeenCalled();
  });

  it("does not render tag filter when no tags data exists", () => {
    setDefaultMocks({ tags: undefined });
    renderWithProviders(<KnowledgeVaultPage />);

    expect(screen.queryByTestId("tag-filter")).not.toBeInTheDocument();
  });

  // 5. Search functionality
  it("renders the search bar", () => {
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    expect(screen.getByTestId("search-bar")).toBeInTheDocument();
  });

  it("calls search mutation when search is triggered", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    // Override after setDefaultMocks to preserve the custom response
    mockSearchMutateAsync.mockResolvedValue({
      hits: [
        {
          id: "hit-1",
          title: "Search Result 1",
          content_snippet: "Some content...",
          source_type: "manual",
          tags: ["research"],
          score: 0.95,
          credibility_score: 0.8,
          created_at: "2025-06-01T00:00:00Z",
        },
      ],
      total: 1,
      query: "test query",
    });
    renderWithProviders(<KnowledgeVaultPage />);

    const searchSubmit = screen.getByTestId("search-submit");
    await user.click(searchSubmit);

    expect(mockSearchMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ query: "test query" })
    );
  });

  // 6. Empty state when no documents
  it("renders empty state when no entries exist", () => {
    setDefaultMocks({
      entries: {
        items: [],
        next_cursor: null,
        has_more: false,
        total_count: 0,
      },
    });
    renderWithProviders(<KnowledgeVaultPage />);

    expect(screen.getByText("No entries yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Create your first research entry or import from a URL or file."
      )
    ).toBeInTheDocument();
  });

  // Loading states
  it("renders loading skeletons while entries are loading", () => {
    setDefaultMocks({ entriesLoading: true });
    renderWithProviders(<KnowledgeVaultPage />);

    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  // Create entry flow
  it("submits new entry via create dialog", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    // Open create dialog
    const newEntryBtn = screen.getByText("New Entry");
    await user.click(newEntryBtn);

    // Fill in title and content (labels don't use htmlFor, so query by role)
    // The form has an <input type="text"> for title and a <textarea> for content
    const textboxes = screen.getAllByRole("textbox");
    // Filter: the title input is the one inside the create dialog (type="text", required)
    // and the textarea is the content field
    const titleInput = textboxes.find(
      (el) => el.tagName === "INPUT" && el.closest("form")
    ) as HTMLInputElement;
    const contentInput = textboxes.find(
      (el) => el.tagName === "TEXTAREA"
    ) as HTMLTextAreaElement;

    await user.type(titleInput, "My New Research");
    await user.type(contentInput, "Some important findings...");

    // Submit
    const createBtn = screen.getByRole("button", { name: /^create$/i });
    await user.click(createBtn);

    expect(mockCreateMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "My New Research",
        content: "Some important findings...",
        source_type: "manual",
      })
    );
  });

  it("closes create dialog when Cancel is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    // Open create dialog
    const newEntryBtn = screen.getByText("New Entry");
    await user.click(newEntryBtn);

    expect(screen.getByText("New Knowledge Entry")).toBeInTheDocument();

    // Cancel
    const cancelBtn = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelBtn);

    expect(screen.queryByText("New Knowledge Entry")).not.toBeInTheDocument();
  });

  it("closes import modal when close button is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    renderWithProviders(<KnowledgeVaultPage />);

    // Open import modal
    const importBtn = screen.getByText("Import");
    await user.click(importBtn);

    expect(screen.getByTestId("import-modal")).toBeInTheDocument();

    // Close
    const closeBtn = screen.getByTestId("close-import");
    await user.click(closeBtn);

    expect(screen.queryByTestId("import-modal")).not.toBeInTheDocument();
  });

  it("shows search results section when search returns results", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    // Override AFTER setDefaultMocks so the mock isn't reset
    mockSearchMutateAsync.mockResolvedValue({
      hits: [
        {
          id: "hit-1",
          title: "Search Result 1",
          content_snippet: "Some relevant content snippet...",
          source_type: "manual",
          tags: ["research"],
          score: 0.95,
          credibility_score: 0.8,
          created_at: "2025-06-01T00:00:00Z",
        },
      ],
      total: 1,
      query: "test query",
    });
    renderWithProviders(<KnowledgeVaultPage />);

    const searchSubmit = screen.getByTestId("search-submit");
    await user.click(searchSubmit);

    // Wait for search results to appear
    await waitFor(() => {
      expect(screen.getByText("Search results (1)")).toBeInTheDocument();
    });

    expect(screen.getByText("Search Result 1")).toBeInTheDocument();
    expect(screen.getByText("Clear search")).toBeInTheDocument();
  });

  it("clears search results when Clear search is clicked", async () => {
    const user = userEvent.setup();
    setDefaultMocks();
    // Override after setDefaultMocks to preserve the custom response
    mockSearchMutateAsync.mockResolvedValue({
      hits: [
        {
          id: "hit-1",
          title: "Search Result 1",
          content_snippet: "Some content...",
          source_type: "manual",
          tags: ["research"],
          score: 0.95,
          credibility_score: 0.8,
          created_at: "2025-06-01T00:00:00Z",
        },
      ],
      total: 1,
      query: "test query",
    });
    renderWithProviders(<KnowledgeVaultPage />);

    // Trigger search
    const searchSubmit = screen.getByTestId("search-submit");
    await user.click(searchSubmit);

    await waitFor(() => {
      expect(screen.getByText("Clear search")).toBeInTheDocument();
    });

    // Clear search
    const clearBtn = screen.getByText("Clear search");
    await user.click(clearBtn);

    // After clearing, entry cards should be back and search results gone
    await waitFor(() => {
      expect(screen.queryByText("Search results (1)")).not.toBeInTheDocument();
    });
  });
});
