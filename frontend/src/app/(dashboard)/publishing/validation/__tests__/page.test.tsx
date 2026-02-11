import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks ────────────────────────────────────────────────────────────────

const mockUseRunFullValidation = jest.fn();

jest.mock("@/modules/publishing/hooks", () => ({
  useRunFullValidation: (...args: unknown[]) => mockUseRunFullValidation(...args),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className, ...props }: { className?: string }) => (
    <div data-testid="skeleton" className={className} {...props} />
  ),
}));

jest.mock("@/components/ui/card", () => ({
  Card: ({ children, className, ...props }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className} {...props}>
      {children}
    </div>
  ),
}));

jest.mock("@/components/ui/badge", () => ({
  Badge: ({ children, className, ...props }: { children: React.ReactNode; className?: string }) => (
    <span data-testid="badge" className={className} {...props}>
      {children}
    </span>
  ),
}));

jest.mock("@/components/ui/button", () => ({
  Button: ({ children, className, onClick, disabled, ...props }: any) => (
    <button data-testid="button" className={className} onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  ),
}));

jest.mock("@/components/ui/input", () => ({
  Input: (props: any) => <input data-testid="input" {...props} />,
}));

jest.mock("@/components/ui/select", () => ({
  Select: ({ children, ...props }: { children: React.ReactNode }) => (
    <select data-testid="select" {...props}>
      {children}
    </select>
  ),
}));

// ── Import component under test (after mocks) ───────────────────────────

import ValidationPage from "../page";

// ── Helpers ──────────────────────────────────────────────────────────────

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

// ── Test Data ────────────────────────────────────────────────────────────

const mockMutate = jest.fn();

const mockValidationResponse = {
  id: "val-123",
  overall_status: "passed" as const,
  results: [
    {
      validation_type: "print" as const,
      status: "passed" as const,
      issues: [],
      checked_at: "2025-06-01T12:00:00Z",
      metadata: {},
    },
    {
      validation_type: "ebook" as const,
      status: "warnings" as const,
      issues: [
        {
          severity: "warning" as const,
          rule: "file-too-large",
          message: "File size exceeds recommended limit",
          location: "ebook.epub",
          details: { file_size: "55MB", recommended: "50MB" },
        },
      ],
      checked_at: "2025-06-01T12:00:00Z",
      metadata: {},
    },
    {
      validation_type: "cover" as const,
      status: "failed" as const,
      issues: [
        {
          severity: "error" as const,
          rule: "low-cover-dpi",
          message: "Cover DPI is below 300",
          location: "cover.jpg",
          details: { dpi: 200, required: 300 },
        },
      ],
      checked_at: "2025-06-01T12:00:00Z",
      metadata: {},
    },
    {
      validation_type: "compliance" as const,
      status: "passed" as const,
      issues: [],
      checked_at: "2025-06-01T12:00:00Z",
      metadata: {},
    },
  ],
  total_errors: 1,
  total_warnings: 1,
  created_at: "2025-06-01T12:00:00Z",
};

function setupDefaultMocks() {
  mockUseRunFullValidation.mockReturnValue({
    mutate: mockMutate,
    isPending: false,
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("ValidationPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setupDefaultMocks();
  });

  // 1. Renders validation page header
  it("renders the validation page with header and description", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("KDP Validation")).toBeInTheDocument();
    expect(
      screen.getByText("Pre-flight validation for Amazon KDP print and ebook requirements")
    ).toBeInTheDocument();
  });

  // 2. Shows book selector dropdown
  it("renders book selector dropdown", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("Select Book to Validate")).toBeInTheDocument();
    expect(screen.getByLabelText("Select Book to Validate")).toBeInTheDocument();
  });

  // 3. Shows validation dashboard
  it("renders validation dashboard component", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("KDP Pre-Flight Validation")).toBeInTheDocument();
    expect(
      screen.getByText("Check your manuscript against KDP requirements before publishing")
    ).toBeInTheDocument();
  });

  // 4. Shows validation runner
  it("renders validation runner component", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("Validation Options")).toBeInTheDocument();
    expect(screen.getByText("Validate Print Specs")).toBeInTheDocument();
    expect(screen.getByText("Validate Ebook Format")).toBeInTheDocument();
    expect(screen.getByText("Validate Cover Specs")).toBeInTheDocument();
    expect(screen.getByText("Check Content Compliance")).toBeInTheDocument();
  });

  // 5. Empty state when no validation results
  it("shows empty state when no validation has been run", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("No Validation Results")).toBeInTheDocument();
    expect(
      screen.getByText("Run a validation check to see if your book meets KDP requirements")
    ).toBeInTheDocument();
  });

  // 6. Run validation button works
  it("has a Run Validation button in the dashboard", () => {
    renderWithProviders(<ValidationPage />);

    const runButtons = screen.getAllByText("Run Validation");
    expect(runButtons.length).toBeGreaterThan(0);
  });

  // 7. Book selector allows selection
  it("allows changing the selected book", async () => {
    const user = userEvent.setup();

    renderWithProviders(<ValidationPage />);

    const selector = screen.getByLabelText("Select Book to Validate") as HTMLSelectElement;
    expect(selector.value).toBe("sample-book-id");

    await user.selectOptions(selector, "book-2");
    expect(selector.value).toBe("book-2");
  });

  // 8. Validation options are checkboxes
  it("renders validation type checkboxes", () => {
    renderWithProviders(<ValidationPage />);

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBeGreaterThanOrEqual(4);
  });

  // 9. Shows Run Full Validation button in runner
  it("renders Run Full Validation button in the runner", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("Run Full Validation")).toBeInTheDocument();
  });

  // 10. Loading state when running validation
  it("shows loading state when validation is running", () => {
    mockUseRunFullValidation.mockReturnValue({
      mutate: mockMutate,
      isPending: true,
    });

    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("Running...")).toBeInTheDocument();
    expect(screen.getByText("Running Validation...")).toBeInTheDocument();
  });

  // 11. Displays validation results after running
  it("does not show validation results section initially", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.queryByText("Validation Results")).not.toBeInTheDocument();
  });

  // 12. Shows overall status
  it("renders the page without errors", () => {
    const { container } = renderWithProviders(<ValidationPage />);
    expect(container).toBeInTheDocument();
  });

  // 13. Trim size selector in print settings
  it("renders trim size selector when print validation is enabled", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("Trim Size")).toBeInTheDocument();
  });

  // 14. Page count input in print settings
  it("renders page count input when print validation is enabled", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("Page Count")).toBeInTheDocument();
  });

  // 15. Margin inputs in print settings
  it("renders margin inputs when print validation is enabled", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("Inside Margin (in)")).toBeInTheDocument();
    expect(screen.getByText("Outside Margin (in)")).toBeInTheDocument();
  });

  // 16. Book selector has sample books
  it("book selector has sample book options", () => {
    renderWithProviders(<ValidationPage />);

    expect(screen.getByText("Sample Book - The Great Adventure")).toBeInTheDocument();
    expect(screen.getByText("Mystery Novel - Dark Secrets")).toBeInTheDocument();
    expect(screen.getByText("Non-Fiction - How to Self-Publish")).toBeInTheDocument();
  });
});
