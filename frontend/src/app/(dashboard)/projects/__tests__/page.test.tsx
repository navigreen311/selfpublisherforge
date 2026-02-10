import React from "react";
import { render, screen, within } from "@testing-library/react";
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

// Mock lucide-react icons to simple elements
jest.mock("lucide-react", () => ({
  Plus: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="plus-icon" {...props} />
  ),
  Search: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="search-icon" {...props} />
  ),
  FolderOpen: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="folder-open-icon" {...props} />
  ),
  AlertCircle: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="alert-circle-icon" {...props} />
  ),
  Inbox: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="inbox-icon" {...props} />
  ),
  Check: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="check-icon" {...props} />
  ),
  ChevronDown: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="chevron-down-icon" {...props} />
  ),
  ChevronUp: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="chevron-up-icon" {...props} />
  ),
}));

// Mock Radix Select to avoid portal / pointer-event issues in jsdom
jest.mock("@radix-ui/react-select", () => {
  const MockSelect = ({ children, value, onValueChange }: {
    children: React.ReactNode;
    value?: string;
    onValueChange?: (v: string) => void;
  }) => <div data-testid="select-root">{children}</div>;

  const MockTrigger = React.forwardRef<HTMLButtonElement, { children: React.ReactNode; className?: string }>(
    ({ children, className, ...props }, ref) => (
      <button ref={ref} className={className} {...props}>{children}</button>
    )
  );
  MockTrigger.displayName = "SelectTrigger";

  const MockContent = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  const MockItem = React.forwardRef<HTMLDivElement, { children: React.ReactNode; value: string }>(
    ({ children, value, ...props }, ref) => <div ref={ref} data-value={value} {...props}>{children}</div>
  );
  MockItem.displayName = "SelectItem";

  const MockValue = ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>;
  const MockPortal = ({ children }: { children: React.ReactNode }) => <>{children}</>;
  const MockViewport = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  const MockIcon = ({ children }: { children: React.ReactNode }) => <span>{children}</span>;
  const MockItemText = ({ children }: { children: React.ReactNode }) => <span>{children}</span>;
  const MockItemIndicator = ({ children }: { children: React.ReactNode }) => <span>{children}</span>;
  const MockGroup = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  const MockLabel = React.forwardRef<HTMLDivElement, { children: React.ReactNode }>(
    ({ children, ...props }, ref) => <div ref={ref} {...props}>{children}</div>
  );
  MockLabel.displayName = "SelectLabel";
  const MockSeparator = React.forwardRef<HTMLDivElement>((props, ref) => <div ref={ref} {...props} />);
  MockSeparator.displayName = "SelectSeparator";
  const MockScrollUp = React.forwardRef<HTMLDivElement>((props, ref) => <div ref={ref} {...props} />);
  MockScrollUp.displayName = "ScrollUpButton";
  const MockScrollDown = React.forwardRef<HTMLDivElement>((props, ref) => <div ref={ref} {...props} />);
  MockScrollDown.displayName = "ScrollDownButton";

  return {
    Root: MockSelect,
    Trigger: MockTrigger,
    Content: MockContent,
    Item: MockItem,
    Value: MockValue,
    Portal: MockPortal,
    Viewport: MockViewport,
    Icon: MockIcon,
    ItemText: MockItemText,
    ItemIndicator: MockItemIndicator,
    Group: MockGroup,
    Label: MockLabel,
    Separator: MockSeparator,
    ScrollUpButton: MockScrollUp,
    ScrollDownButton: MockScrollDown,
  };
});

// Mock useProjects hook — this is the core mock that controls page state
const mockUseProjects = jest.fn();
jest.mock("@/modules/projects/hooks", () => ({
  useProjects: (...args: unknown[]) => mockUseProjects(...args),
  // Re-export the Project type as a no-op; TypeScript types are erased at runtime
}));

// ---------------------------------------------------------------------------
// Import the component under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import ProjectsPage from "../page";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const mockProjects = [
  {
    id: "proj-1",
    title: "Fantasy Novel",
    type: "book" as const,
    status: "active" as const,
    settings: null,
    pen_name_id: null,
    books: [{ id: "b1", title: "Book One", format: "epub", status: "draft" }],
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-06-15T12:00:00Z",
  },
  {
    id: "proj-2",
    title: "Sci-Fi Series",
    type: "series" as const,
    status: "draft" as const,
    settings: null,
    pen_name_id: null,
    books: [
      { id: "b2", title: "Part 1", format: "epub", status: "draft" },
      { id: "b3", title: "Part 2", format: "epub", status: "draft" },
    ],
    created_at: "2025-02-01T00:00:00Z",
    updated_at: "2025-07-20T10:00:00Z",
  },
  {
    id: "proj-3",
    title: "Online Course",
    type: "course" as const,
    status: "archived" as const,
    settings: null,
    pen_name_id: null,
    books: [],
    created_at: "2024-06-01T00:00:00Z",
    updated_at: "2024-12-01T08:00:00Z",
  },
];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("ProjectsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders loading skeletons while data is being fetched", () => {
    mockUseProjects.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    });

    const { container } = render(<ProjectsPage />);

    // The page heading should still be visible during loading
    expect(
      screen.getByRole("heading", { level: 1 })
    ).toHaveTextContent("Projects");

    // Loading state renders 6 skeleton cards — each card has Skeleton divs
    // with the animate-pulse class
    const pulsingElements = container.querySelectorAll(".animate-pulse");
    expect(pulsingElements.length).toBeGreaterThanOrEqual(6);
  });

  it("renders project cards from API data", () => {
    mockUseProjects.mockReturnValue({
      data: mockProjects,
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<ProjectsPage />);

    // All three project titles should be rendered
    expect(screen.getByText("Fantasy Novel")).toBeInTheDocument();
    expect(screen.getByText("Sci-Fi Series")).toBeInTheDocument();
    expect(screen.getByText("Online Course")).toBeInTheDocument();

    // Status badges should be visible
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("draft")).toBeInTheDocument();
    expect(screen.getByText("archived")).toBeInTheDocument();

    // Book counts should be displayed
    expect(screen.getByText("1 book")).toBeInTheDocument();
    expect(screen.getByText("2 books")).toBeInTheDocument();
    expect(screen.getByText("0 books")).toBeInTheDocument();
  });

  it("renders project cards as links to their detail pages", () => {
    mockUseProjects.mockReturnValue({
      data: mockProjects,
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<ProjectsPage />);

    // Each project card should be wrapped in a link to /projects/<id>
    const links = screen.getAllByRole("link");
    const projectLinks = links.filter((link) =>
      link.getAttribute("href")?.startsWith("/projects/proj-")
    );
    expect(projectLinks).toHaveLength(3);
    expect(projectLinks[0]).toHaveAttribute("href", "/projects/proj-1");
    expect(projectLinks[1]).toHaveAttribute("href", "/projects/proj-2");
    expect(projectLinks[2]).toHaveAttribute("href", "/projects/proj-3");
  });

  it("shows empty state when no projects match", () => {
    mockUseProjects.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<ProjectsPage />);

    expect(screen.getByText("No projects found")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Try adjusting your search or filters, or create a new project to get started."
      )
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create project/i })
    ).toBeInTheDocument();
  });

  it("navigates to new project page via the create button link", () => {
    mockUseProjects.mockReturnValue({
      data: mockProjects,
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<ProjectsPage />);

    const newProjectLink = screen.getByRole("link", { name: /new project/i });
    expect(newProjectLink).toBeInTheDocument();
    expect(newProjectLink).toHaveAttribute("href", "/projects/new");
  });

  it("displays an error card when the API fails", () => {
    mockUseProjects.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: { message: "Network timeout" },
    });

    render(<ProjectsPage />);

    expect(screen.getByText("Failed to load projects")).toBeInTheDocument();
    expect(screen.getByText("Network timeout")).toBeInTheDocument();
  });

  it("renders a search input for filtering projects", () => {
    mockUseProjects.mockReturnValue({
      data: mockProjects,
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<ProjectsPage />);

    const searchInput = screen.getByPlaceholderText("Search projects...");
    expect(searchInput).toBeInTheDocument();
  });

  it("passes debounced search term to the useProjects hook", async () => {
    jest.useFakeTimers();
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

    mockUseProjects.mockReturnValue({
      data: mockProjects,
      isLoading: false,
      isError: false,
      error: null,
    });

    const { rerender } = render(<ProjectsPage />);

    const searchInput = screen.getByPlaceholderText("Search projects...");
    await user.type(searchInput, "Fantasy");

    // Before debounce fires, search param should still be undefined
    expect(mockUseProjects).toHaveBeenLastCalledWith(
      expect.objectContaining({ search: undefined })
    );

    // Advance timers past the 300ms debounce, wrapped in act for state update
    await React.act(async () => {
      jest.advanceTimersByTime(350);
    });

    // After debounce, the hook should be called with the search term
    expect(mockUseProjects).toHaveBeenLastCalledWith(
      expect.objectContaining({ search: "Fantasy" })
    );

    jest.useRealTimers();
  });

  it("renders the page description text", () => {
    mockUseProjects.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<ProjectsPage />);

    expect(
      screen.getByText("Manage all your publishing projects")
    ).toBeInTheDocument();
  });
});
