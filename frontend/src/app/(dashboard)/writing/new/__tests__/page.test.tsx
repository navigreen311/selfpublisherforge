import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks -- set up before component imports
// ---------------------------------------------------------------------------

// Mock next/navigation
const mockPush = jest.fn();
const mockBack = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: mockBack }),
  usePathname: () => "/writing/new",
  useSearchParams: () => new URLSearchParams(),
}));

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
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  ArrowLeft: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-arrow-left" {...props} />
  ),
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-loader" {...props} />
  ),
  BookOpen: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-book-open" {...props} />
  ),
  PenLine: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-pen-line" {...props} />
  ),
  X: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="icon-x" {...props} />
  ),
}));

// Mock sonner toast
const mockToastSuccess = jest.fn();
const mockToastError = jest.fn();
jest.mock("sonner", () => ({
  toast: {
    success: (...args: unknown[]) => mockToastSuccess(...args),
    error: (...args: unknown[]) => mockToastError(...args),
  },
}));

// Mock the project creation hook (the writing/new page creates a book via
// useCreateProject, matching the projects/new pattern)
const mockMutateAsync = jest.fn();
const mockCreateHook = jest.fn();

jest.mock("@/modules/projects/hooks", () => ({
  useCreateProject: (...args: unknown[]) => mockCreateHook(...args),
}));

// Mock validation module -- the writing/new page likely uses projectSchema or
// a manuscriptSchema following the same validateForm pattern
jest.mock("@/lib/validation", () => {
  const actual = jest.requireActual("@/lib/validation");
  return {
    ...actual,
    // Re-export everything so projectSchema / validateForm work as normal
  };
});

// Mock Radix Select to avoid portal / pointer-event issues in jsdom
jest.mock("@radix-ui/react-select", () => {
  // Collect value change handlers so we can simulate selection
  let currentOnValueChange: ((v: string) => void) | undefined;

  const MockSelect = ({
    children,
    value,
    onValueChange,
  }: {
    children: React.ReactNode;
    value?: string;
    onValueChange?: (v: string) => void;
  }) => {
    currentOnValueChange = onValueChange;
    return <div data-testid="select-root">{children}</div>;
  };

  const MockTrigger = React.forwardRef<
    HTMLButtonElement,
    { children: React.ReactNode; className?: string; id?: string; [key: string]: unknown }
  >(({ children, className, ...props }, ref) => (
    <button ref={ref} className={className as string} {...props}>
      {children as React.ReactNode}
    </button>
  ));
  MockTrigger.displayName = "SelectTrigger";

  const MockContent = ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  );
  const MockItem = React.forwardRef<
    HTMLDivElement,
    { children: React.ReactNode; value: string }
  >(({ children, value, ...props }, ref) => (
    <div
      ref={ref}
      data-value={value}
      role="option"
      onClick={() => currentOnValueChange?.(value)}
      {...props}
    >
      {children}
    </div>
  ));
  MockItem.displayName = "SelectItem";

  const MockValue = ({ placeholder }: { placeholder?: string }) => (
    <span>{placeholder}</span>
  );
  const MockPortal = ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  );
  const MockViewport = ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  );
  const MockIcon = ({ children }: { children: React.ReactNode }) => (
    <span>{children}</span>
  );
  const MockItemText = ({ children }: { children: React.ReactNode }) => (
    <span>{children}</span>
  );
  const MockItemIndicator = ({ children }: { children: React.ReactNode }) => (
    <span>{children}</span>
  );
  const MockGroup = ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  );
  const MockLabel = React.forwardRef<HTMLDivElement, { children: React.ReactNode }>(
    ({ children, ...props }, ref) => (
      <div ref={ref} {...props}>
        {children}
      </div>
    )
  );
  MockLabel.displayName = "SelectLabel";
  const MockSeparator = React.forwardRef<HTMLDivElement>((props, ref) => (
    <div ref={ref} {...props} />
  ));
  MockSeparator.displayName = "SelectSeparator";
  const MockScrollUp = React.forwardRef<HTMLDivElement>((props, ref) => (
    <div ref={ref} {...props} />
  ));
  MockScrollUp.displayName = "ScrollUpButton";
  const MockScrollDown = React.forwardRef<HTMLDivElement>((props, ref) => (
    <div ref={ref} {...props} />
  ));
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

// Mock Radix Slot so that Button asChild renders correctly
jest.mock("@radix-ui/react-slot", () => ({
  // @radix-ui/react-primitive calls createSlot() at module load, so a mock
  // without it throws before any test in the file runs.
  createSlot: () =>
    React.forwardRef(function MockSlot(
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLElement>
    ) {
      return React.isValidElement(children)
        ? React.cloneElement(children, { ...props, ref } as Record<string, unknown>)
        : React.createElement("span", { ref, ...props }, children as React.ReactNode);
    }),
  createSlottable: () =>
    function MockSlottable({ children }: { children?: React.ReactNode }) {
      return children as React.ReactElement;
    },
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
import NewManuscriptPage from "../page";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupDefaultHook(overrides: Record<string, unknown> = {}) {
  mockCreateHook.mockReturnValue({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
    error: null,
    ...overrides,
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("NewManuscriptPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setupDefaultHook();
    mockMutateAsync.mockResolvedValue({ id: "book-new-1" });
  });

  // -----------------------------------------------------------------------
  // 1. Basic render
  // -----------------------------------------------------------------------
  it("renders without crashing", () => {
    const { container } = render(<NewManuscriptPage />);
    expect(container).toBeTruthy();
  });

  // -----------------------------------------------------------------------
  // 2. Page title
  // -----------------------------------------------------------------------
  it("displays the 'New Manuscript' page title", () => {
    render(<NewManuscriptPage />);

    expect(
      screen.getByRole("heading", { name: /new manuscript/i })
    ).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 3. Breadcrumb / back navigation to /writing
  // -----------------------------------------------------------------------
  it("has a back link or button that navigates to /writing", () => {
    render(<NewManuscriptPage />);

    // The page should have a link or button pointing back to /writing
    // Following the projects/new pattern, this is a Link with href="/writing"
    const backLink = screen.getByRole("link", { name: /back/i }) ||
      screen.getByLabelText(/back/i);
    expect(backLink).toBeInTheDocument();
    expect(backLink).toHaveAttribute("href", "/writing");
  });

  // -----------------------------------------------------------------------
  // 4. Title form field exists
  // -----------------------------------------------------------------------
  it("renders the title input field", () => {
    render(<NewManuscriptPage />);

    // The Input component with label prop generates a label + input
    const titleInput =
      screen.getByLabelText(/title/i) ||
      screen.getByPlaceholderText(/title/i);
    expect(titleInput).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 5. Genre form field exists
  // -----------------------------------------------------------------------
  it("renders the genre selection field", () => {
    render(<NewManuscriptPage />);

    expect(screen.getByText(/genre/i)).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 6. Description form field exists
  // -----------------------------------------------------------------------
  it("renders the description field", () => {
    render(<NewManuscriptPage />);

    const descField =
      screen.queryByLabelText(/description/i) ||
      screen.queryByPlaceholderText(/description/i);
    expect(descField).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // 7. Validation errors show on empty submit
  // -----------------------------------------------------------------------
  it("shows validation errors when submitting an empty form", async () => {
    const user = userEvent.setup();
    render(<NewManuscriptPage />);

    // Find and click the submit button
    const submitButton = screen.getByRole("button", { name: /create/i });
    await user.click(submitButton);

    // After submit attempt with empty title, validation error should appear
    await waitFor(() => {
      const errorMessages = screen.getAllByText(/required|at least|must/i);
      expect(errorMessages.length).toBeGreaterThanOrEqual(1);
    });
  });

  // -----------------------------------------------------------------------
  // 8. Validation errors show on blur
  // -----------------------------------------------------------------------
  it("shows validation error for title field on blur when empty", async () => {
    const user = userEvent.setup();
    render(<NewManuscriptPage />);

    // Find the title input, focus it, then blur
    const titleInput =
      screen.getByLabelText(/title/i) ||
      screen.getByPlaceholderText(/title/i);
    await user.click(titleInput);
    await user.tab(); // blur the field

    // Error should appear after blur
    await waitFor(() => {
      const errorMessages = screen.getAllByText(/required|at least|must/i);
      expect(errorMessages.length).toBeGreaterThanOrEqual(1);
    });
  });

  // -----------------------------------------------------------------------
  // 9. Successful submission calls mutation
  // -----------------------------------------------------------------------
  it("calls the create mutation with correct data on valid submit", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockResolvedValue({ id: "book-created-1" });
    render(<NewManuscriptPage />);

    // Fill in the title
    const titleInput =
      screen.getByLabelText(/title/i) ||
      screen.getByPlaceholderText(/title/i);
    await user.type(titleInput, "My Amazing Novel");

    // Select a project type if present (following projects/new pattern)
    const typeOption = screen.queryByRole("option", { name: /book/i });
    if (typeOption) {
      await user.click(typeOption);
    }

    // Submit the form
    const submitButton = screen.getByRole("button", { name: /create/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledTimes(1);
    });

    // Verify mutation was called with the title
    expect(mockMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        title: expect.stringContaining("My Amazing Novel"),
      })
    );
  });

  // -----------------------------------------------------------------------
  // 10. Loading state on submit button
  // -----------------------------------------------------------------------
  it("shows loading state on the submit button while creating", () => {
    setupDefaultHook({ isPending: true });
    render(<NewManuscriptPage />);

    // The submit button should show a loading state
    const submitButton = screen.getByRole("button", {
      name: /creating|loading|submitting/i,
    });
    expect(submitButton).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  // -----------------------------------------------------------------------
  // 11. Cancel / back navigation
  // -----------------------------------------------------------------------
  it("has a cancel button or link that navigates back to /writing", () => {
    render(<NewManuscriptPage />);

    // Following the projects/new pattern, there is a Cancel button/link
    const cancelLink =
      screen.queryByRole("link", { name: /cancel/i }) ||
      screen.queryByRole("button", { name: /cancel/i });
    expect(cancelLink).toBeInTheDocument();

    // If it's a link, it should point to /writing
    if (cancelLink?.tagName === "A") {
      expect(cancelLink).toHaveAttribute("href", "/writing");
    }
  });

  // -----------------------------------------------------------------------
  // 12. Successful submit navigates to the created book
  // -----------------------------------------------------------------------
  it("navigates to the new manuscript page after successful creation", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockResolvedValue({ id: "book-new-123" });
    render(<NewManuscriptPage />);

    // Fill in required fields
    const titleInput =
      screen.getByLabelText(/title/i) ||
      screen.getByPlaceholderText(/title/i);
    await user.type(titleInput, "My Novel");

    // Select type if present
    const typeOption = screen.queryByRole("option", { name: /book/i });
    if (typeOption) {
      await user.click(typeOption);
    }

    // Submit
    const submitButton = screen.getByRole("button", { name: /create/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalled();
    });
  });

  // -----------------------------------------------------------------------
  // 13. Failed submit shows error toast
  // -----------------------------------------------------------------------
  it("shows an error toast when creation fails", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockRejectedValue(new Error("Server error"));
    render(<NewManuscriptPage />);

    // Fill in required fields
    const titleInput =
      screen.getByLabelText(/title/i) ||
      screen.getByPlaceholderText(/title/i);
    await user.type(titleInput, "My Novel");

    // Select type if present
    const typeOption = screen.queryByRole("option", { name: /book/i });
    if (typeOption) {
      await user.click(typeOption);
    }

    // Submit
    const submitButton = screen.getByRole("button", { name: /create/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalled();
    });
  });

  // -----------------------------------------------------------------------
  // 14. Submit button is disabled when form is invalid after submit attempt
  // -----------------------------------------------------------------------
  it("disables the submit button after a failed validation attempt", async () => {
    const user = userEvent.setup();
    render(<NewManuscriptPage />);

    // Click submit with empty form
    const submitButton = screen.getByRole("button", { name: /create/i });
    await user.click(submitButton);

    // After submit attempt, button should be disabled because form is invalid
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });
});
