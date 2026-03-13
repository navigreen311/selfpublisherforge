import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

import { CreatePuzzleBookWizard } from "../components/CreatePuzzleBookWizard";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("CreatePuzzleBookWizard", () => {
  const mockOnOpenChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders when open", () => {
    render(
      <CreatePuzzleBookWizard open={true} onOpenChange={mockOnOpenChange} />,
    );

    expect(screen.getByText("Create Puzzle Book")).toBeInTheDocument();
    expect(
      screen.getByText("Follow the steps to configure your new puzzle book."),
    ).toBeInTheDocument();
  });

  it("renders step 1 - Book Details by default", () => {
    render(
      <CreatePuzzleBookWizard open={true} onOpenChange={mockOnOpenChange} />,
    );

    expect(
      screen.getByPlaceholderText("My Awesome Puzzle Book"),
    ).toBeInTheDocument();
    expect(screen.getByText("AI Suggest")).toBeInTheDocument();
  });

  it("has the Back button disabled on step 1", () => {
    render(
      <CreatePuzzleBookWizard open={true} onOpenChange={mockOnOpenChange} />,
    );

    const backButton = screen.getByRole("button", { name: /back/i });
    expect(backButton).toBeDisabled();
  });

  it("has the Next button disabled when title is empty", () => {
    render(
      <CreatePuzzleBookWizard open={true} onOpenChange={mockOnOpenChange} />,
    );

    const nextButton = screen.getByRole("button", { name: /next/i });
    expect(nextButton).toBeDisabled();
  });

  it("enables Next button when title is entered", async () => {
    const user = userEvent.setup();
    render(
      <CreatePuzzleBookWizard open={true} onOpenChange={mockOnOpenChange} />,
    );

    const titleInput = screen.getByPlaceholderText("My Awesome Puzzle Book");
    await user.type(titleInput, "Test Puzzle Book");

    const nextButton = screen.getByRole("button", { name: /next/i });
    expect(nextButton).toBeEnabled();
  });

  it("does not render when closed", () => {
    render(
      <CreatePuzzleBookWizard open={false} onOpenChange={mockOnOpenChange} />,
    );

    expect(screen.queryByText("Create Puzzle Book")).not.toBeInTheDocument();
  });

  it("renders with initial template", () => {
    const template = {
      id: "word-search-classic",
      name: "Word Search Classic",
      description: "Traditional word search puzzles",
      icon: "search",
      defaultPuzzleTypes: ["word_search" as const],
      defaultAudience: "adults" as const,
      defaultDifficulty: "medium" as const,
      defaultPuzzleCount: 50,
    };

    render(
      <CreatePuzzleBookWizard
        open={true}
        onOpenChange={mockOnOpenChange}
        initialTemplate={template}
      />,
    );

    expect(screen.getByText("Create Puzzle Book")).toBeInTheDocument();
  });
});
